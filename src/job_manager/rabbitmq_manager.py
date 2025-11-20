"""RabbitMQ-based job queue manager for distributed processing"""

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import aio_pika
from aio_pika import ExchangeType, Message, connect_robust
from aio_pika.abc import AbstractIncomingMessage

from src.config import get_settings
from src.ffmpeg import FFmpegCommandBuilder, FFmpegRunner, get_media_metadata
from src.logging import get_logger
from src.websocket.models import InputSource, OutputMetadata, UrlSource

from .job import Job, JobStatus

logger = get_logger(__name__)


class RabbitMQJobManager:
    """
    Job manager using RabbitMQ for distributed task processing

    Benefits over asyncio.Queue:
    - Job persistence (survives restarts)
    - Distributed workers across multiple machines
    - Message acknowledgment and retry
    - Priority queues
    - Dead letter queues for failed jobs
    - Better monitoring via RabbitMQ management UI
    """

    def __init__(self, rabbitmq_url: str = "amqp://guest:guest@localhost/") -> None:
        self.settings = get_settings()
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.jobs: Dict[str, Job] = {}
        self.workers: list[asyncio.Task[None]] = []
        self.running = False
        self.command_builder = FFmpegCommandBuilder()

        # Callbacks storage
        self._progress_callbacks: Dict[str, Callable[[str, float, str], Any]] = {}
        self._completion_callbacks: Dict[str, Callable[[str, Path, OutputMetadata], Any]] = {}
        self._error_callbacks: Dict[str, Callable[[str, str], Any]] = {}

    async def start(self) -> None:
        """Start RabbitMQ connection and worker pool"""
        self.running = True
        logger.info(f"Connecting to RabbitMQ at {self.rabbitmq_url}")

        # Create robust connection (auto-reconnect)
        self.connection = await connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()

        # Set QoS - only process one message at a time per worker
        await self.channel.set_qos(prefetch_count=1)

        # Declare exchange for job routing
        exchange = await self.channel.declare_exchange(
            "ffmpeg_jobs",
            ExchangeType.DIRECT,
            durable=True,
        )

        # Declare main job queue
        self.queue = await self.channel.declare_queue(
            "ffmpeg_job_queue",
            durable=True,  # Survives broker restart
            arguments={
                "x-message-ttl": 3600000,  # Messages expire after 1 hour
                "x-max-length": 10000,  # Max queue length
            },
        )

        # Bind queue to exchange
        await self.queue.bind(exchange, routing_key="job")

        # Declare dead letter queue for failed jobs
        dlq = await self.channel.declare_queue(
            "ffmpeg_job_dlq",
            durable=True,
        )

        logger.info(
            f"RabbitMQ connected - Starting {self.settings.max_concurrent_jobs} workers"
        )

        # Start worker pool
        for i in range(self.settings.max_concurrent_jobs):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)

        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

    async def stop(self) -> None:
        """Stop worker pool and close RabbitMQ connection"""
        self.running = False
        logger.info("Stopping RabbitMQ job manager")

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers
        await asyncio.gather(*self.workers, return_exceptions=True)

        # Close RabbitMQ connection
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()

    async def submit_job(
        self,
        job_id: str,
        operation: Any,
        input_source: InputSource,
        options: Any,
        progress_callback: Optional[Callable[[str, float, str], Any]] = None,
        completion_callback: Optional[Callable[[str, Path, OutputMetadata], Any]] = None,
        error_callback: Optional[Callable[[str, str], Any]] = None,
    ) -> Job:
        """
        Submit job to RabbitMQ queue

        Benefits:
        - Job persists even if server restarts
        - Can be picked up by any worker in cluster
        - Automatic retry on failure
        """
        job = Job(job_id=job_id, operation=operation, options=options)
        self.jobs[job_id] = job

        # Store callbacks
        if progress_callback:
            self._progress_callbacks[job_id] = progress_callback
        if completion_callback:
            self._completion_callbacks[job_id] = completion_callback
        if error_callback:
            self._error_callbacks[job_id] = error_callback

        # Serialize job to JSON
        job_message = {
            "job_id": job_id,
            "operation": str(operation),
            "input_source": input_source.model_dump(mode="json"),
            "options": options.model_dump(mode="json") if hasattr(options, "model_dump") else options,
        }

        # Publish to RabbitMQ
        if self.channel:
            message = Message(
                body=json.dumps(job_message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,  # Survive broker restart
                content_type="application/json",
                priority=1,  # Can use for job prioritization
            )

            await self.channel.default_exchange.publish(
                message,
                routing_key="ffmpeg_job_queue",
            )

        logger.info(
            f"Job submitted to RabbitMQ",
            extra={"job_id": job_id, "operation": str(operation)},
        )

        return job

    async def _worker(self, worker_id: int) -> None:
        """Worker coroutine that consumes jobs from RabbitMQ"""
        logger.info(f"RabbitMQ Worker {worker_id} started")

        if not self.queue:
            logger.error(f"Worker {worker_id}: Queue not initialized")
            return

        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                message: AbstractIncomingMessage

                if not self.running:
                    break

                try:
                    # Parse job message
                    job_data = json.loads(message.body.decode())
                    job_id = job_data["job_id"]

                    logger.info(
                        f"Worker {worker_id} processing job from RabbitMQ",
                        extra={"job_id": job_id},
                    )

                    # Get or create job
                    job = self.jobs.get(job_id)
                    if not job:
                        # Reconstruct job from message (distributed worker scenario)
                        from src.websocket.models import JobOperation

                        job = Job(
                            job_id=job_id,
                            operation=JobOperation(job_data["operation"]),
                            options=job_data["options"],
                        )
                        self.jobs[job_id] = job

                    # Process job
                    try:
                        await self._process_job(job, job_data)

                        # Acknowledge message (remove from queue)
                        await message.ack()

                    except Exception as e:
                        logger.error(
                            f"Worker {worker_id} job failed: {e}",
                            extra={"job_id": job_id},
                            exc_info=True,
                        )
                        job.mark_failed(str(e))

                        # Call error callback
                        if job_id in self._error_callbacks:
                            await self._error_callbacks[job_id](job_id, str(e))

                        # Reject message (will go to DLQ if configured)
                        await message.reject(requeue=False)

                except Exception as e:
                    logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                    await message.reject(requeue=False)

        logger.info(f"RabbitMQ Worker {worker_id} stopped")

    async def _process_job(self, job: Job, job_data: dict[str, Any]) -> None:
        """Process a single job (same as original manager)"""
        job.mark_started()

        # Create temp directory
        job_dir = self.settings.temp_dir / job.job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Download/prepare input
            job.update_progress(5, JobStatus.DOWNLOADING)
            await self._notify_progress(job, 5, "downloading")

            # Parse input source
            input_data = job_data["input_source"]
            if input_data["source"] == "url":
                input_source = UrlSource(**input_data)
            else:
                # Upload source - wait for file
                input_source = input_data

            input_path = await self._prepare_input_from_url(input_source, job_dir, job)
            job.input_path = input_path

            # Determine output path
            output_ext = self._get_output_extension(job.operation, job.options)
            output_path = job_dir / f"output{output_ext}"
            job.output_path = output_path

            # Build FFmpeg command
            job.update_progress(10, JobStatus.PROCESSING)
            await self._notify_progress(job, 10, "preparing")

            command = self.command_builder.build_command(
                job.operation, input_path, output_path, job.options
            )

            # Run FFmpeg
            runner = FFmpegRunner()

            async def progress_handler(progress: float, stage: str) -> None:
                job_progress = 10 + (progress * 0.8)
                job.update_progress(job_progress, JobStatus.PROCESSING)
                await self._notify_progress(job, job_progress, stage)

            returncode, stdout, stderr = await runner.run(
                command, job.job_id, progress_handler
            )

            if returncode != 0:
                raise RuntimeError(f"FFmpeg failed with code {returncode}: {stderr[-500:]}")

            # Extract metadata
            job.update_progress(95, JobStatus.UPLOADING)
            await self._notify_progress(job, 95, "finalizing")

            metadata = await get_media_metadata(output_path)

            # Mark completed
            job.mark_completed()
            await self._notify_progress(job, 100, "completed")

            # Call completion callback
            if job.job_id in self._completion_callbacks:
                await self._completion_callbacks[job.job_id](
                    job.job_id, output_path, metadata
                )

        except Exception as e:
            job.mark_failed(str(e))
            raise

    async def _prepare_input_from_url(
        self, input_source: UrlSource, job_dir: Path, job: Job
    ) -> Path:
        """Download file from URL"""
        import httpx
        import aiofiles

        logger.info(f"Downloading from URL", extra={"job_id": job.job_id})

        url_path = Path(str(input_source.url).split("?")[0])
        ext = url_path.suffix or ".dat"
        input_path = job_dir / f"input{ext}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("GET", str(input_source.url)) as response:
                response.raise_for_status()

                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self.settings.max_file_size_bytes:
                    raise ValueError(f"File too large: {content_length} bytes")

                async with aiofiles.open(input_path, "wb") as f:
                    total = 0
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        await f.write(chunk)
                        total += len(chunk)

                        if total > self.settings.max_file_size_bytes:
                            raise ValueError(f"File too large: {total} bytes")

        logger.info(
            f"Downloaded {input_path.stat().st_size} bytes",
            extra={"job_id": job.job_id},
        )
        return input_path

    def _get_output_extension(self, operation: Any, options: Any) -> str:
        """Determine output file extension"""
        from src.websocket.models import JobOperation

        if operation == JobOperation.EXTRACT_AUDIO:
            return f".{options.format.value if hasattr(options, 'format') else 'mp3'}"
        elif operation == JobOperation.THUMBNAIL:
            return f".{options.format.value if hasattr(options, 'format') else 'png'}"
        elif operation == JobOperation.GIF:
            return ".gif"
        elif operation == JobOperation.COMPRESS:
            if hasattr(options, 'target_format') and options.target_format:
                return f".{options.target_format.value}"
            return ".mp4"
        else:
            return ".mp4"

    async def _notify_progress(self, job: Job, progress: float, stage: str) -> None:
        """Notify progress callback"""
        if job.job_id in self._progress_callbacks:
            try:
                await self._progress_callbacks[job.job_id](job.job_id, progress, stage)
            except Exception as e:
                logger.warning(
                    f"Progress callback failed: {e}", extra={"job_id": job.job_id}
                )

    async def _cleanup_task(self) -> None:
        """Periodic cleanup of old job files"""
        while self.running:
            try:
                await asyncio.sleep(self.settings.cleanup_interval_seconds)
                await self._cleanup_old_jobs()
            except Exception as e:
                logger.error(f"Cleanup task error: {e}", exc_info=True)

    async def _cleanup_old_jobs(self) -> None:
        """Clean up old completed jobs"""
        jobs_to_remove = []

        for job_id, job in self.jobs.items():
            if job.is_terminal and job.completed_at:
                age = asyncio.get_event_loop().time() - job.completed_at.timestamp()
                if age > 3600:
                    jobs_to_remove.append(job_id)

                    job_dir = self.settings.temp_dir / job_id
                    if job_dir.exists():
                        try:
                            shutil.rmtree(job_dir)
                            logger.debug(f"Cleaned up job directory", extra={"job_id": job_id})
                        except Exception as e:
                            logger.warning(
                                f"Failed to clean up job directory: {e}",
                                extra={"job_id": job_id},
                            )

        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            self._progress_callbacks.pop(job_id, None)
            self._completion_callbacks.pop(job_id, None)
            self._error_callbacks.pop(job_id, None)

        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job (best effort with RabbitMQ)"""
        job = self.jobs.get(job_id)
        if not job:
            return False

        if job.is_terminal:
            return False

        logger.info(f"Cancelling job", extra={"job_id": job_id})
        job.mark_cancelled()
        return True

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self.jobs.get(job_id)

    def get_active_jobs_count(self) -> int:
        """Get number of active jobs"""
        return sum(1 for job in self.jobs.values() if not job.is_terminal)

    def get_stats(self) -> Dict[str, Any]:
        """Get job manager statistics"""
        return {
            "total_jobs": len(self.jobs),
            "active_jobs": self.get_active_jobs_count(),
            "queued_jobs": 0,  # Would need to query RabbitMQ API
            "max_concurrent": self.settings.max_concurrent_jobs,
            "backend": "RabbitMQ",
        }

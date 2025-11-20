"""Job queue and worker pool manager"""

import asyncio
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

import aiofiles
import httpx

from src.config import get_settings
from src.ffmpeg import FFmpegCommandBuilder, FFmpegRunner, get_media_metadata
from src.logging import get_logger
from src.websocket.models import (
    ConcatOptions,
    InputSource,
    JobOperation,
    OutputMetadata,
    UrlSource,
)

from .job import Job, JobStatus

logger = get_logger(__name__)


class JobManager:
    """Manages job queue and worker pool"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.jobs: Dict[str, Job] = {}
        self.queue: asyncio.Queue[Job] = asyncio.Queue()
        self.workers: list[asyncio.Task[None]] = []
        self.running = False
        self.command_builder = FFmpegCommandBuilder()

    async def start(self) -> None:
        """Start worker pool"""
        self.running = True
        logger.info(f"Starting job manager with {self.settings.max_concurrent_jobs} workers")

        for i in range(self.settings.max_concurrent_jobs):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)

        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

    async def stop(self) -> None:
        """Stop worker pool"""
        self.running = False
        logger.info("Stopping job manager")

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers
        await asyncio.gather(*self.workers, return_exceptions=True)

    async def submit_job(
        self,
        job_id: str,
        operation: JobOperation,
        input_source: InputSource,
        options: Any,
        progress_callback: Optional[Callable[[str, float, str], Any]] = None,
        completion_callback: Optional[Callable[[str, Path, OutputMetadata], Any]] = None,
        error_callback: Optional[Callable[[str, str], Any]] = None,
    ) -> Job:
        """
        Submit a new job to the queue

        Args:
            job_id: Unique job identifier
            operation: FFmpeg operation to perform
            input_source: Input source (upload or URL)
            options: Operation-specific options
            progress_callback: Optional callback(job_id, progress, stage)
            completion_callback: Optional callback(job_id, output_path, metadata)
            error_callback: Optional callback(job_id, error_message)

        Returns:
            Job object
        """
        job = Job(job_id=job_id, operation=operation, options=options)
        self.jobs[job_id] = job

        # Store callbacks
        job.progress_callback = progress_callback  # type: ignore
        job.completion_callback = completion_callback  # type: ignore
        job.error_callback = error_callback  # type: ignore
        job.input_source = input_source  # type: ignore

        await self.queue.put(job)
        logger.info(f"Job submitted", extra={"job_id": job_id, "operation": operation.value})

        return job

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
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
        """Get number of active (non-terminal) jobs"""
        return sum(1 for job in self.jobs.values() if not job.is_terminal)

    def get_stats(self) -> Dict[str, Any]:
        """Get job manager statistics"""
        return {
            "total_jobs": len(self.jobs),
            "active_jobs": self.get_active_jobs_count(),
            "queued_jobs": self.queue.qsize(),
            "max_concurrent": self.settings.max_concurrent_jobs,
        }

    async def _worker(self, worker_id: int) -> None:
        """Worker coroutine"""
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Get job from queue with timeout
                try:
                    job = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Check if cancelled
                if job.status == JobStatus.CANCELLED:
                    self.queue.task_done()
                    continue

                logger.info(
                    f"Worker {worker_id} processing job",
                    extra={"job_id": job.job_id, "operation": job.operation.value},
                )

                # Process job
                try:
                    await self._process_job(job)
                except Exception as e:
                    logger.error(
                        f"Worker {worker_id} job failed: {e}",
                        extra={"job_id": job.job_id},
                        exc_info=True,
                    )
                    job.mark_failed(str(e))
                    if hasattr(job, "error_callback") and job.error_callback:  # type: ignore
                        await job.error_callback(job.job_id, str(e))  # type: ignore

                self.queue.task_done()

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)

        logger.info(f"Worker {worker_id} stopped")

    async def _process_job(self, job: Job) -> None:
        """Process a single job"""
        job.mark_started()

        # Create temp directory for this job
        job_dir = self.settings.temp_dir / job.job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Download/prepare input
            job.update_progress(5, JobStatus.DOWNLOADING)
            await self._notify_progress(job, 5, "downloading")

            input_path = await self._prepare_input(job, job_dir)
            job.input_path = input_path

            # Determine output path
            output_ext = self._get_output_extension(job.operation, job.options)
            output_path = job_dir / f"output{output_ext}"
            job.output_path = output_path

            # Build FFmpeg command
            job.update_progress(10, JobStatus.PROCESSING)
            await self._notify_progress(job, 10, "preparing")

            # Get input metadata for validation
            input_metadata = await get_media_metadata(input_path)

            # Validate audio stream exists for audio extraction
            if job.operation == JobOperation.EXTRACT_AUDIO:
                logger.info(f"Validating audio stream", extra={"job_id": job.job_id})
                if not input_metadata.audio_codec:
                    raise ValueError(
                        "This media file does not contain any audio stream. "
                        "Audio extraction is not possible for video-only files."
                    )

            # For speed operations on video-only files, disable audio processing
            if job.operation == JobOperation.SPEED and not input_metadata.audio_codec:
                logger.info(f"Video has no audio, disabling audio filters", extra={"job_id": job.job_id})
                # Set maintain_pitch to None to indicate no audio
                job.options.has_audio = False

            command = self.command_builder.build_command(
                job.operation, input_path, output_path, job.options
            )

            # Run FFmpeg
            runner = FFmpegRunner()

            async def progress_handler(progress: float, stage: str) -> None:
                # Map FFmpeg progress (0-100) to job progress (10-90)
                job_progress = 10 + (progress * 0.8)
                job.update_progress(job_progress, JobStatus.PROCESSING)
                await self._notify_progress(job, job_progress, stage)

            returncode, stdout, stderr = await runner.run(
                command, job.job_id, progress_handler
            )

            if returncode != 0:
                raise RuntimeError(f"FFmpeg failed with code {returncode}: {stderr[-500:]}")

            # Check for cancellation
            if job.cancel_event.is_set():
                raise asyncio.CancelledError()

            # Extract metadata
            job.update_progress(95, JobStatus.UPLOADING)
            await self._notify_progress(job, 95, "finalizing")

            metadata = await get_media_metadata(output_path)

            # Mark completed
            job.mark_completed()
            await self._notify_progress(job, 100, "completed")

            # Call completion callback
            if hasattr(job, "completion_callback") and job.completion_callback:  # type: ignore
                await job.completion_callback(job.job_id, output_path, metadata)  # type: ignore

        except asyncio.CancelledError:
            job.mark_cancelled()
            raise
        except Exception as e:
            job.mark_failed(str(e))
            raise
        finally:
            # Cleanup will be handled by cleanup task
            pass

    async def _prepare_input(self, job: Job, job_dir: Path) -> Path:
        """Prepare input file (download or wait for upload)"""
        input_source: InputSource = job.input_source  # type: ignore

        if isinstance(input_source, UrlSource):
            # Download from URL
            logger.info(f"Downloading from URL", extra={"job_id": job.job_id})

            # Determine extension from URL
            url_path = Path(str(input_source.url).split("?")[0])
            ext = url_path.suffix or ".dat"
            input_path = job_dir / f"input{ext}"

            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("GET", str(input_source.url)) as response:
                    response.raise_for_status()

                    # Check size
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > self.settings.max_file_size_bytes:
                        raise ValueError(f"File too large: {content_length} bytes")

                    # Stream to file
                    async with aiofiles.open(input_path, "wb") as f:
                        total = 0
                        async for chunk in response.aiter_bytes(chunk_size=65536):
                            await f.write(chunk)
                            total += len(chunk)

                            # Check size during download
                            if total > self.settings.max_file_size_bytes:
                                raise ValueError(f"File too large: {total} bytes")

            logger.info(
                f"Downloaded {input_path.stat().st_size} bytes",
                extra={"job_id": job.job_id},
            )
            return input_path
        else:
            # Upload source - file should already be in job_dir
            # This is handled by WebSocket server
            input_files = list(job_dir.glob("input.*"))
            if not input_files:
                # Wait for file to appear (uploaded via WebSocket)
                for _ in range(100):  # Wait up to 10 seconds
                    await asyncio.sleep(0.1)
                    input_files = list(job_dir.glob("input.*"))
                    if input_files:
                        break

            if not input_files:
                raise RuntimeError("Input file not uploaded")

            return input_files[0]

    def _get_output_extension(self, operation: JobOperation, options: Any) -> str:
        """Determine output file extension based on operation"""
        if operation == JobOperation.EXTRACT_AUDIO:
            return f".{options.format.value}"
        elif operation == JobOperation.THUMBNAIL:
            return f".{options.format.value}"
        elif operation == JobOperation.GIF:
            return ".gif"
        elif operation == JobOperation.COMPRESS:
            if options.target_format:
                return f".{options.target_format.value}"
            return ".mp4"
        elif operation == JobOperation.CONVERT:
            return f".{options.target_format}"
        elif operation == JobOperation.EXTRACT_SUBTITLES:
            return f".{options.format or 'srt'}"
        else:
            return ".mp4"  # Default

    async def _notify_progress(self, job: Job, progress: float, stage: str) -> None:
        """Notify progress callback if set"""
        if hasattr(job, "progress_callback") and job.progress_callback:  # type: ignore
            try:
                await job.progress_callback(job.job_id, progress, stage)  # type: ignore
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}", extra={"job_id": job.job_id})

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
                # Clean up after 1 hour
                age = (asyncio.get_event_loop().time() - job.completed_at.timestamp())
                if age > 3600:
                    jobs_to_remove.append(job_id)

                    # Remove job directory
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

        # Remove from tracking
        for job_id in jobs_to_remove:
            del self.jobs[job_id]

        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")

"""WebSocket server implementation"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional, Set, TYPE_CHECKING

import aiofiles
import websockets
from pydantic import ValidationError
from websockets.server import WebSocketServerProtocol

from src.config import get_settings
from src.logging import get_logger
from src.websocket.models import (
    AckMessage,
    CancelJobMessage,
    ClientMessage,
    CompletedMessage,
    ErrorMessage,
    OutputMetadata,
    PingMessage,
    PongMessage,
    ProgressMessage,
    ServerMessage,
    StartJobMessage,
    UploadSource,
)

logger = get_logger(__name__)

if TYPE_CHECKING:
    from src.job_manager import JobManager


class WebSocketServer:
    """WebSocket server for media processing"""

    def __init__(self, job_manager: "JobManager") -> None:
        self.settings = get_settings()
        self.job_manager = job_manager
        self.connections: Set[WebSocketServerProtocol] = set()
        self.connection_jobs: Dict[WebSocketServerProtocol, Set[str]] = {}

    async def start(self) -> None:
        """Start WebSocket server"""
        logger.info(
            f"Starting WebSocket server on {self.settings.ws_host}:{self.settings.ws_port}"
        )

        async with websockets.serve(
            self.handle_connection,
            self.settings.ws_host,
            self.settings.ws_port,
            max_size=self.settings.ws_max_size,
            ping_interval=self.settings.ws_ping_interval,
            ping_timeout=self.settings.ws_ping_timeout,
        ):
            # Run forever
            await asyncio.Future()

    async def handle_connection(self, websocket: WebSocketServerProtocol) -> None:
        """Handle WebSocket connection"""
        client_id = id(websocket)
        logger.info(f"Client connected: {client_id}")

        self.connections.add(websocket)
        self.connection_jobs[websocket] = set()

        try:
            await self._handle_messages(websocket)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Connection error: {e}", exc_info=True)
        finally:
            # Clean up
            self.connections.discard(websocket)

            # Cancel all jobs for this connection
            job_ids = self.connection_jobs.pop(websocket, set())
            for job_id in job_ids:
                await self.job_manager.cancel_job(job_id)

    async def _handle_messages(self, websocket: WebSocketServerProtocol) -> None:
        """Handle incoming messages from client"""
        async for raw_message in websocket:
            try:
                # Handle binary messages (file uploads)
                if isinstance(raw_message, bytes):
                    await self._handle_binary_message(websocket, raw_message)
                    continue

                # Parse JSON message
                try:
                    data = json.loads(raw_message)
                except json.JSONDecodeError as e:
                    await self._send_error(websocket, None, "INVALID_JSON", f"Invalid JSON: {e}")
                    continue

                # Validate and route message
                try:
                    msg_type = data.get("type")

                    if msg_type == "start_job":
                        message = StartJobMessage(**data)
                        await self._handle_start_job(websocket, message)
                    elif msg_type == "cancel_job":
                        message = CancelJobMessage(**data)
                        await self._handle_cancel_job(websocket, message)
                    elif msg_type == "ping":
                        message = PingMessage(**data)
                        await self._handle_ping(websocket, message)
                    else:
                        await self._send_error(
                            websocket, None, "UNKNOWN_MESSAGE_TYPE", f"Unknown message type: {msg_type}"
                        )

                except ValidationError as e:
                    await self._send_error(
                        websocket, None, "VALIDATION_ERROR", f"Message validation failed: {e}"
                    )

            except Exception as e:
                logger.error(f"Message handling error: {e}", exc_info=True)
                await self._send_error(websocket, None, "INTERNAL_ERROR", "Internal server error")

    async def _handle_start_job(
        self, websocket: WebSocketServerProtocol, message: StartJobMessage
    ) -> None:
        """Handle start_job message"""
        job_id = message.job_id

        logger.info(
            f"Received start_job",
            extra={"job_id": job_id, "operation": message.operation.value},
        )

        # Track job for this connection
        self.connection_jobs[websocket].add(job_id)

        # Send acknowledgment
        await self._send_message(
            websocket, AckMessage(job_id=job_id, message="Job accepted and queued")
        )

        # Submit job
        try:
            await self.job_manager.submit_job(
                job_id=job_id,
                operation=message.operation,
                input_source=message.input,
                options=message.options,
                progress_callback=lambda jid, prog, stage: self._send_progress(
                    websocket, jid, prog, stage
                ),
                completion_callback=lambda jid, path, meta: self._send_completion(
                    websocket, jid, path, meta
                ),
                error_callback=lambda jid, error: self._send_error(
                    websocket, jid, "JOB_FAILED", error
                ),
            )
        except Exception as e:
            logger.error(f"Failed to submit job: {e}", extra={"job_id": job_id}, exc_info=True)
            await self._send_error(websocket, job_id, "SUBMIT_FAILED", str(e))

    async def _handle_cancel_job(
        self, websocket: WebSocketServerProtocol, message: CancelJobMessage
    ) -> None:
        """Handle cancel_job message"""
        job_id = message.job_id

        logger.info(f"Received cancel_job", extra={"job_id": job_id})

        success = await self.job_manager.cancel_job(job_id)

        if success:
            await self._send_error(websocket, job_id, "JOB_CANCELLED", "Job cancelled by user")
        else:
            await self._send_error(
                websocket, job_id, "CANCEL_FAILED", "Job not found or already completed"
            )

    async def _handle_ping(
        self, websocket: WebSocketServerProtocol, message: PingMessage
    ) -> None:
        """Handle ping message"""
        await self._send_message(websocket, PongMessage())

    async def _handle_binary_message(
        self, websocket: WebSocketServerProtocol, data: bytes
    ) -> None:
        """Handle binary file upload"""
        # Binary messages should have a preceding metadata message
        # For simplicity, we'll parse a small JSON header from first bytes

        # Expected format: first 4 bytes = header length (uint32)
        # followed by JSON header, then file data
        if len(data) < 4:
            await self._send_error(websocket, None, "INVALID_BINARY", "Binary message too short")
            return

        header_length = int.from_bytes(data[:4], "big")
        if header_length > 1024:  # Max 1KB header
            await self._send_error(websocket, None, "INVALID_BINARY", "Header too large")
            return

        try:
            header_json = data[4 : 4 + header_length].decode("utf-8")
            header = json.loads(header_json)
            job_id = header.get("job_id")
            filename = header.get("filename", "input.dat")
            file_data = data[4 + header_length :]

            if not job_id:
                await self._send_error(
                    websocket, None, "INVALID_BINARY", "Missing job_id in header"
                )
                return

            # Save file
            job_dir = self.settings.temp_dir / job_id
            job_dir.mkdir(parents=True, exist_ok=True)

            # Determine extension
            ext = Path(filename).suffix or ".dat"
            input_path = job_dir / f"input{ext}"

            async with aiofiles.open(input_path, "wb") as f:
                await f.write(file_data)

            logger.info(
                f"Received binary upload: {len(file_data)} bytes",
                extra={"job_id": job_id},
            )

        except Exception as e:
            logger.error(f"Binary message handling error: {e}", exc_info=True)
            await self._send_error(websocket, None, "BINARY_ERROR", str(e))

    async def _send_progress(
        self, websocket: WebSocketServerProtocol, job_id: str, progress: float, stage: str
    ) -> None:
        """Send progress update"""
        message = ProgressMessage(job_id=job_id, percentage=progress, stage=stage)
        await self._send_message(websocket, message)

    async def _send_completion(
        self,
        websocket: WebSocketServerProtocol,
        job_id: str,
        output_path: Path,
        metadata: OutputMetadata,
    ) -> None:
        """Send completion message and output file"""
        # Send completion message
        message = CompletedMessage(
            job_id=job_id,
            output_metadata=metadata,
            delivery_method="binary",
        )
        await self._send_message(websocket, message)

        # Send output file as binary
        try:
            async with aiofiles.open(output_path, "rb") as f:
                file_data = await f.read()

            # Build binary message with header
            header = {"job_id": job_id, "filename": output_path.name}
            header_json = json.dumps(header).encode("utf-8")
            header_length = len(header_json)

            binary_message = (
                header_length.to_bytes(4, "big") + header_json + file_data
            )

            await websocket.send(binary_message)

            logger.info(
                f"Sent output file: {len(file_data)} bytes",
                extra={"job_id": job_id},
            )

        except Exception as e:
            logger.error(f"Failed to send output file: {e}", extra={"job_id": job_id}, exc_info=True)
            await self._send_error(websocket, job_id, "OUTPUT_SEND_FAILED", str(e))

    async def _send_error(
        self,
        websocket: WebSocketServerProtocol,
        job_id: Optional[str],
        code: str,
        message: str,
        details: Optional[str] = None,
    ) -> None:
        """Send error message"""
        error_msg = ErrorMessage(job_id=job_id, code=code, message=message, details=details)
        await self._send_message(websocket, error_msg)

    async def _send_message(
        self, websocket: WebSocketServerProtocol, message: ServerMessage
    ) -> None:
        """Send JSON message to client"""
        try:
            json_data = message.model_dump_json()
            await websocket.send(json_data)
        except Exception as e:
            logger.error(f"Failed to send message: {e}", exc_info=True)

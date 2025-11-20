"""FFmpeg process runner with streaming I/O and progress tracking"""

import asyncio
import re
from pathlib import Path
from typing import Any, Callable, Optional

from src.config import get_settings
from src.logging import get_logger

logger = get_logger(__name__)


class FFmpegRunner:
    """Async FFmpeg process runner"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.process: Optional[asyncio.subprocess.Process] = None

    async def run(
        self,
        command: list[str],
        job_id: str,
        progress_callback: Optional[Callable[[float, str], Any]] = None,
    ) -> tuple[int, str, str]:
        """
        Run FFmpeg command with progress tracking

        Args:
            command: FFmpeg command as list
            job_id: Job identifier
            progress_callback: Optional callback(percentage, stage)

        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        logger.info(f"Starting FFmpeg process", extra={"job_id": job_id})

        # Redact sensitive paths for logging
        safe_command = self._redact_command(command)
        logger.debug(f"FFmpeg command: {' '.join(safe_command)}", extra={"job_id": job_id})

        # Add progress reporting
        cmd_with_progress = command.copy()
        if "-progress" not in cmd_with_progress:
            # Insert progress reporting before output file
            insert_idx = len(cmd_with_progress) - 2  # Before -y and output
            cmd_with_progress[insert_idx:insert_idx] = ["-progress", "pipe:2"]

        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd_with_progress,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Track stderr for progress
            stderr_lines: list[str] = []
            stdout_data = b""

            # Read stderr asynchronously for progress
            async def read_stderr() -> bytes:
                stderr_data = b""
                if self.process and self.process.stderr:
                    async for line in self.process.stderr:
                        stderr_data += line
                        line_str = line.decode("utf-8", errors="ignore").strip()
                        stderr_lines.append(line_str)

                        # Parse progress
                        if progress_callback:
                            progress = self._parse_progress(line_str)
                            if progress is not None:
                                await progress_callback(progress, "processing")
                return stderr_data

            # Read stdout
            async def read_stdout() -> bytes:
                if self.process and self.process.stdout:
                    return await self.process.stdout.read()
                return b""

            # Wait for both with timeout
            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    asyncio.gather(read_stdout(), read_stderr()),
                    timeout=self.settings.ffmpeg_timeout_seconds,
                )
            except asyncio.TimeoutError:
                logger.error(f"FFmpeg process timed out", extra={"job_id": job_id})
                if self.process:
                    self.process.kill()
                    await self.process.wait()
                raise TimeoutError(f"FFmpeg process exceeded {self.settings.ffmpeg_timeout_seconds}s timeout")

            # Wait for process to complete
            returncode = await self.process.wait()

            stdout = stdout_data.decode("utf-8", errors="ignore")
            stderr = "\n".join(stderr_lines)

            if returncode != 0:
                logger.error(
                    f"FFmpeg process failed with code {returncode}",
                    extra={"job_id": job_id, "stderr": stderr[-500:]},
                )
            else:
                logger.info(f"FFmpeg process completed successfully", extra={"job_id": job_id})

            return returncode, stdout, stderr

        except Exception as e:
            logger.error(f"FFmpeg process error: {e}", extra={"job_id": job_id}, exc_info=True)
            raise

        finally:
            self.process = None

    async def cancel(self) -> None:
        """Cancel running FFmpeg process"""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()

    def _parse_progress(self, line: str) -> Optional[float]:
        """
        Parse FFmpeg progress from stderr output

        FFmpeg progress format:
        frame=  123 fps= 45 q=28.0 size=    1024kB time=00:00:05.00 bitrate=1677.7kbits/s speed=1.23x
        """
        # Look for time= pattern
        time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})", line)
        if time_match:
            hours, minutes, seconds = time_match.groups()
            total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            # We don't know total duration here, so return rough estimate
            # This would need duration from metadata for accurate percentage
            return min(total_seconds / 100.0, 99.0)  # Cap at 99% until completion

        return None

    def _redact_command(self, command: list[str]) -> list[str]:
        """Redact sensitive information from command for logging"""
        redacted = []
        skip_next = False

        for i, arg in enumerate(command):
            if skip_next:
                redacted.append("[REDACTED]")
                skip_next = False
                continue

            # Redact URLs
            if arg.startswith("http://") or arg.startswith("https://"):
                redacted.append("[URL]")
            # Redact file paths but keep filename
            elif "/" in arg and i > 0:
                path = Path(arg)
                redacted.append(f"[.../{path.name}]")
            else:
                redacted.append(arg)

        return redacted

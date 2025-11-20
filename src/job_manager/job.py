"""Job model and status tracking"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.websocket.models import JobOperation


class JobStatus(str, Enum):
    """Job execution status"""

    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Job representation"""

    job_id: str
    operation: Any  # JobOperation from websocket.models
    options: Any
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    progress: float = 0.0
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)

    def __post_init__(self) -> None:
        """Initialize cancel event if not set"""
        if not isinstance(self.cancel_event, asyncio.Event):
            self.cancel_event = asyncio.Event()

    def mark_started(self) -> None:
        """Mark job as started"""
        self.started_at = datetime.utcnow()

    def mark_completed(self) -> None:
        """Mark job as completed"""
        self.completed_at = datetime.utcnow()
        self.status = JobStatus.COMPLETED
        self.progress = 100.0

    def mark_failed(self, error: str) -> None:
        """Mark job as failed"""
        self.completed_at = datetime.utcnow()
        self.status = JobStatus.FAILED
        self.error_message = error

    def mark_cancelled(self) -> None:
        """Mark job as cancelled"""
        self.completed_at = datetime.utcnow()
        self.status = JobStatus.CANCELLED
        self.cancel_event.set()

    def update_progress(self, progress: float, status: Optional[JobStatus] = None) -> None:
        """Update job progress"""
        self.progress = min(progress, 100.0)
        if status:
            self.status = status

    @property
    def is_terminal(self) -> bool:
        """Check if job is in terminal state"""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get job duration in seconds"""
        if self.started_at:
            end = self.completed_at or datetime.utcnow()
            return (end - self.started_at).total_seconds()
        return None

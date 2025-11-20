"""Tests for job manager"""

import asyncio
from pathlib import Path

import pytest

from src.job_manager import Job, JobManager, JobStatus
from src.websocket.models import (
    JobOperation,
    SpeedOptions,
    UploadSource,
)


class TestJob:
    """Test Job model"""

    def test_job_creation(self) -> None:
        """Test job creation"""
        options = SpeedOptions(speed_factor=2.0)
        job = Job(job_id="test-123", operation=JobOperation.SPEED, options=options)

        assert job.job_id == "test-123"
        assert job.operation == JobOperation.SPEED
        assert job.status == JobStatus.QUEUED
        assert not job.is_terminal

    def test_job_lifecycle(self) -> None:
        """Test job lifecycle"""
        options = SpeedOptions(speed_factor=2.0)
        job = Job(job_id="test-123", operation=JobOperation.SPEED, options=options)

        job.mark_started()
        assert job.started_at is not None

        job.update_progress(50.0, JobStatus.PROCESSING)
        assert job.progress == 50.0
        assert job.status == JobStatus.PROCESSING

        job.mark_completed()
        assert job.status == JobStatus.COMPLETED
        assert job.progress == 100.0
        assert job.is_terminal

    def test_job_failure(self) -> None:
        """Test job failure"""
        options = SpeedOptions(speed_factor=2.0)
        job = Job(job_id="test-123", operation=JobOperation.SPEED, options=options)

        job.mark_failed("Test error")
        assert job.status == JobStatus.FAILED
        assert job.error_message == "Test error"
        assert job.is_terminal

    def test_job_cancellation(self) -> None:
        """Test job cancellation"""
        options = SpeedOptions(speed_factor=2.0)
        job = Job(job_id="test-123", operation=JobOperation.SPEED, options=options)

        job.mark_cancelled()
        assert job.status == JobStatus.CANCELLED
        assert job.is_terminal
        assert job.cancel_event.is_set()


class TestJobManager:
    """Test JobManager"""

    @pytest.fixture
    async def manager(self) -> JobManager:
        """Create job manager"""
        mgr = JobManager()
        await mgr.start()
        yield mgr
        await mgr.stop()

    @pytest.mark.asyncio
    async def test_manager_start_stop(self) -> None:
        """Test starting and stopping manager"""
        manager = JobManager()
        await manager.start()
        assert manager.running
        assert len(manager.workers) > 0

        await manager.stop()
        assert not manager.running

    @pytest.mark.asyncio
    async def test_submit_job(self, manager: JobManager) -> None:
        """Test job submission"""
        options = SpeedOptions(speed_factor=2.0)
        job = await manager.submit_job(
            job_id="test-123",
            operation=JobOperation.SPEED,
            input_source=UploadSource(),
            options=options,
        )

        assert job.job_id == "test-123"
        assert job.status == JobStatus.QUEUED
        assert manager.get_job("test-123") == job

    @pytest.mark.asyncio
    async def test_cancel_job(self, manager: JobManager) -> None:
        """Test job cancellation"""
        options = SpeedOptions(speed_factor=2.0)
        await manager.submit_job(
            job_id="test-123",
            operation=JobOperation.SPEED,
            input_source=UploadSource(),
            options=options,
        )

        success = await manager.cancel_job("test-123")
        assert success

        job = manager.get_job("test-123")
        assert job is not None
        assert job.status == JobStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_get_stats(self, manager: JobManager) -> None:
        """Test getting stats"""
        stats = manager.get_stats()

        assert "total_jobs" in stats
        assert "active_jobs" in stats
        assert "queued_jobs" in stats
        assert "max_concurrent" in stats

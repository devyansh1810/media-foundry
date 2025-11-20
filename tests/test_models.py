"""Tests for Pydantic models and validation"""

import pytest
from pydantic import ValidationError

from src.websocket.models import (
    AudioFormat,
    CancelJobMessage,
    CompressionOptions,
    CompressionPreset,
    ExtractAudioOptions,
    GifOptions,
    JobOperation,
    PingMessage,
    SpeedOptions,
    StartJobMessage,
    ThumbnailOptions,
    TrimOptions,
    UploadSource,
    UrlSource,
)


class TestMessageValidation:
    """Test message validation"""

    def test_start_job_valid(self) -> None:
        """Test valid start_job message"""
        msg = StartJobMessage(
            job_id="test-123",
            operation=JobOperation.SPEED,
            input=UploadSource(),
            options=SpeedOptions(speed_factor=2.0),
        )
        assert msg.job_id == "test-123"
        assert msg.operation == JobOperation.SPEED
        assert msg.options.speed_factor == 2.0

    def test_start_job_invalid_speed(self) -> None:
        """Test invalid speed factor"""
        with pytest.raises(ValidationError):
            StartJobMessage(
                job_id="test-123",
                operation=JobOperation.SPEED,
                input=UploadSource(),
                options=SpeedOptions(speed_factor=20.0),  # Too high
            )

    def test_cancel_job_valid(self) -> None:
        """Test valid cancel_job message"""
        msg = CancelJobMessage(job_id="test-123")
        assert msg.job_id == "test-123"

    def test_ping_message(self) -> None:
        """Test ping message"""
        msg = PingMessage()
        assert msg.type == "ping"


class TestOperationOptions:
    """Test operation-specific options"""

    def test_speed_options_valid(self) -> None:
        """Test valid speed options"""
        opts = SpeedOptions(speed_factor=2.0, maintain_pitch=True)
        assert opts.speed_factor == 2.0
        assert opts.maintain_pitch is True

    def test_compression_options_presets(self) -> None:
        """Test compression presets"""
        opts = CompressionOptions(preset=CompressionPreset.LOW)
        assert opts.preset == CompressionPreset.LOW

    def test_compression_options_custom(self) -> None:
        """Test custom compression options"""
        opts = CompressionOptions(
            preset=CompressionPreset.CUSTOM,
            crf=23,
            max_width=1920,
            max_height=1080,
        )
        assert opts.crf == 23
        assert opts.max_width == 1920

    def test_extract_audio_options(self) -> None:
        """Test audio extraction options"""
        opts = ExtractAudioOptions(
            format=AudioFormat.MP3, bitrate_kbps=192, sample_rate=48000
        )
        assert opts.format == AudioFormat.MP3
        assert opts.bitrate_kbps == 192

    def test_extract_audio_invalid_sample_rate(self) -> None:
        """Test invalid sample rate"""
        with pytest.raises(ValidationError):
            ExtractAudioOptions(format=AudioFormat.MP3, sample_rate=12345)

    def test_thumbnail_options_timestamp(self) -> None:
        """Test thumbnail with timestamp"""
        opts = ThumbnailOptions(timestamp=5.0)
        assert opts.timestamp == 5.0
        assert opts.count is None

    def test_thumbnail_options_count(self) -> None:
        """Test thumbnail with count"""
        opts = ThumbnailOptions(count=3)
        assert opts.count == 3
        assert opts.timestamp is None

    def test_trim_options_valid(self) -> None:
        """Test valid trim options"""
        opts = TrimOptions(start_time=10.0, end_time=30.0)
        assert opts.start_time == 10.0
        assert opts.end_time == 30.0

    def test_trim_options_invalid_range(self) -> None:
        """Test invalid time range"""
        with pytest.raises(ValidationError):
            TrimOptions(start_time=30.0, end_time=10.0)

    def test_gif_options_valid(self) -> None:
        """Test valid GIF options"""
        opts = GifOptions(start_time=5.0, duration=10.0, fps=15, width=640)
        assert opts.start_time == 5.0
        assert opts.duration == 10.0
        assert opts.fps == 15


class TestInputSources:
    """Test input source validation"""

    def test_upload_source(self) -> None:
        """Test upload source"""
        src = UploadSource()
        assert src.source == "upload"

    def test_url_source_valid(self) -> None:
        """Test valid URL source"""
        src = UrlSource(url="https://example.com/video.mp4")
        assert src.source == "url"
        assert str(src.url) == "https://example.com/video.mp4"

    def test_url_source_invalid(self) -> None:
        """Test invalid URL"""
        with pytest.raises(ValidationError):
            UrlSource(url="not-a-url")

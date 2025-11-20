"""Tests for FFmpeg command builder"""

from pathlib import Path

import pytest

from src.ffmpeg import FFmpegCommandBuilder
from src.websocket.models import (
    AudioFormat,
    CompressionOptions,
    CompressionPreset,
    ConvertOptions,
    ExtractAudioOptions,
    GifOptions,
    JobOperation,
    RemoveAudioOptions,
    SpeedOptions,
    ThumbnailOptions,
    TrimOptions,
    VideoFormat,
)


class TestFFmpegCommandBuilder:
    """Test FFmpeg command builder"""

    @pytest.fixture
    def builder(self) -> FFmpegCommandBuilder:
        """Create command builder"""
        return FFmpegCommandBuilder()

    @pytest.fixture
    def input_path(self, tmp_path: Path) -> Path:
        """Create temporary input path"""
        return tmp_path / "input.mp4"

    @pytest.fixture
    def output_path(self, tmp_path: Path) -> Path:
        """Create temporary output path"""
        return tmp_path / "output.mp4"

    def test_speed_command(
        self, builder: FFmpegCommandBuilder, input_path: Path, output_path: Path
    ) -> None:
        """Test speed conversion command"""
        options = SpeedOptions(speed_factor=2.0, maintain_pitch=False)
        cmd = builder.build_command(JobOperation.SPEED, input_path, output_path, options)

        assert "ffmpeg" in cmd
        assert "-i" in cmd
        assert str(input_path) in cmd
        assert str(output_path) in cmd
        assert any("setpts" in arg for arg in cmd)
        assert any("atempo" in arg for arg in cmd)

    def test_compress_command_low(
        self, builder: FFmpegCommandBuilder, input_path: Path, output_path: Path
    ) -> None:
        """Test compression with low preset"""
        options = CompressionOptions(preset=CompressionPreset.LOW)
        cmd = builder.build_command(JobOperation.COMPRESS, input_path, output_path, options)

        assert "ffmpeg" in cmd
        assert "-crf" in cmd
        crf_idx = cmd.index("-crf")
        assert int(cmd[crf_idx + 1]) == 32  # Low quality

    def test_compress_command_custom(
        self, builder: FFmpegCommandBuilder, input_path: Path, output_path: Path
    ) -> None:
        """Test compression with custom options"""
        options = CompressionOptions(
            preset=CompressionPreset.CUSTOM,
            crf=23,
            video_bitrate_kbps=2000,
            max_width=1920,
        )
        cmd = builder.build_command(JobOperation.COMPRESS, input_path, output_path, options)

        assert "-crf" in cmd
        assert "23" in cmd
        assert "-b:v" in cmd
        assert "2000k" in cmd

    def test_extract_audio_command(
        self, builder: FFmpegCommandBuilder, input_path: Path, tmp_path: Path
    ) -> None:
        """Test audio extraction command"""
        output_path = tmp_path / "output.mp3"
        options = ExtractAudioOptions(format=AudioFormat.MP3, bitrate_kbps=192)
        cmd = builder.build_command(
            JobOperation.EXTRACT_AUDIO, input_path, output_path, options
        )

        assert "ffmpeg" in cmd
        assert "-vn" in cmd  # No video
        assert "-c:a" in cmd
        assert "-b:a" in cmd
        assert "192k" in cmd

    def test_remove_audio_command(
        self, builder: FFmpegCommandBuilder, input_path: Path, output_path: Path
    ) -> None:
        """Test remove audio command"""
        options = RemoveAudioOptions(keep_video_quality=True)
        cmd = builder.build_command(
            JobOperation.REMOVE_AUDIO, input_path, output_path, options
        )

        assert "ffmpeg" in cmd
        assert "-an" in cmd  # No audio
        assert "-c:v" in cmd
        assert "copy" in cmd

    def test_convert_command_stream_copy(
        self, builder: FFmpegCommandBuilder, input_path: Path, output_path: Path
    ) -> None:
        """Test format conversion with stream copy"""
        options = ConvertOptions(target_format="mkv", stream_copy=True)
        cmd = builder.build_command(JobOperation.CONVERT, input_path, output_path, options)

        assert "ffmpeg" in cmd
        assert "-c" in cmd
        assert "copy" in cmd
        assert "-f" in cmd
        assert "mkv" in cmd

    def test_thumbnail_command_timestamp(
        self, builder: FFmpegCommandBuilder, input_path: Path, tmp_path: Path
    ) -> None:
        """Test thumbnail generation at timestamp"""
        output_path = tmp_path / "thumb.png"
        options = ThumbnailOptions(timestamp=5.0)
        cmd = builder.build_command(
            JobOperation.THUMBNAIL, input_path, output_path, options
        )

        assert "ffmpeg" in cmd
        assert "-ss" in cmd
        assert "5.0" in cmd
        assert "-frames:v" in cmd
        assert "1" in cmd

    def test_trim_command(
        self, builder: FFmpegCommandBuilder, input_path: Path, output_path: Path
    ) -> None:
        """Test trim/clip command"""
        options = TrimOptions(start_time=10.0, end_time=30.0)
        cmd = builder.build_command(JobOperation.TRIM, input_path, output_path, options)

        assert "ffmpeg" in cmd
        assert "-ss" in cmd
        assert "10.0" in cmd
        assert "-t" in cmd
        assert "20.0" in cmd  # Duration

    def test_gif_command(
        self, builder: FFmpegCommandBuilder, input_path: Path, tmp_path: Path
    ) -> None:
        """Test GIF creation command"""
        output_path = tmp_path / "output.gif"
        options = GifOptions(start_time=5.0, duration=10.0, fps=15, width=640)
        cmd = builder.build_command(JobOperation.GIF, input_path, output_path, options)

        assert "ffmpeg" in cmd
        assert "-ss" in cmd
        assert "5.0" in cmd
        assert "-t" in cmd
        assert "10.0" in cmd

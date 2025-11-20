"""Media metadata extraction using ffprobe"""

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

from src.websocket.models import OutputMetadata


async def get_media_metadata(file_path: Path) -> OutputMetadata:
    """Extract media metadata using ffprobe"""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {stderr.decode()}")

    data = json.loads(stdout.decode())

    # Extract format info
    format_info = data.get("format", {})
    streams = data.get("streams", [])

    # Find video and audio streams
    video_stream: Optional[dict[str, Any]] = None
    audio_stream: Optional[dict[str, Any]] = None

    for stream in streams:
        codec_type = stream.get("codec_type")
        if codec_type == "video" and not video_stream:
            video_stream = stream
        elif codec_type == "audio" and not audio_stream:
            audio_stream = stream

    # Build metadata
    metadata = OutputMetadata(
        format=format_info.get("format_name", "unknown"),
        duration=float(format_info.get("duration", 0)) if format_info.get("duration") else None,
        size_bytes=int(format_info.get("size", 0)),
        bitrate=int(format_info.get("bit_rate", 0)) if format_info.get("bit_rate") else None,
    )

    # Add video metadata
    if video_stream:
        metadata.video_codec = video_stream.get("codec_name")
        metadata.width = video_stream.get("width")
        metadata.height = video_stream.get("height")

        # Calculate FPS
        fps_str = video_stream.get("r_frame_rate", "0/1")
        if "/" in fps_str:
            num, den = fps_str.split("/")
            if int(den) != 0:
                metadata.fps = float(num) / float(den)

    # Add audio metadata
    if audio_stream:
        metadata.audio_codec = audio_stream.get("codec_name")

    return metadata

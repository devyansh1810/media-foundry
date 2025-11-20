#!/usr/bin/env python3
"""Example WebSocket client for FFmpeg media processing service"""

import asyncio
import json
from pathlib import Path
from typing import Optional
from uuid import uuid4

try:
    import websockets
except ImportError:
    print("Please install websockets: pip install websockets")
    exit(1)


async def process_video_speed(
    ws_url: str,
    video_url: str,
    speed_factor: float = 2.0,
    output_file: Optional[str] = None,
) -> None:
    """Process video with speed conversion"""
    job_id = str(uuid4())
    print(f"Starting job {job_id}: Speed conversion ({speed_factor}x)")

    async with websockets.connect(ws_url, max_size=500 * 1024 * 1024) as websocket:
        # Send start job message
        message = {
            "type": "start_job",
            "job_id": job_id,
            "operation": "speed",
            "input": {"source": "url", "url": video_url},
            "options": {"speed_factor": speed_factor, "maintain_pitch": False},
        }

        await websocket.send(json.dumps(message))
        print(f"✓ Job submitted")

        # Receive messages
        async for msg in websocket:
            if isinstance(msg, bytes):
                # Binary message - output file
                header_len = int.from_bytes(msg[:4], "big")
                header = json.loads(msg[4 : 4 + header_len])
                file_data = msg[4 + header_len :]

                # Save file
                output_path = output_file or f"output_{header['filename']}"
                with open(output_path, "wb") as f:
                    f.write(file_data)
                print(f"✓ Saved output: {output_path} ({len(file_data):,} bytes)")
                break
            else:
                # JSON message
                data = json.loads(msg)
                msg_type = data.get("type")

                if msg_type == "ack":
                    print(f"✓ {data['message']}")
                elif msg_type == "progress":
                    percentage = data.get("percentage", 0)
                    stage = data.get("stage", "")
                    print(f"  Progress: {percentage:.1f}% - {stage}")
                elif msg_type == "completed":
                    print(f"✓ Job completed!")
                    meta = data["output_metadata"]
                    print(f"  Format: {meta['format']}")
                    print(f"  Size: {meta['size_bytes']:,} bytes")
                    if meta.get("duration"):
                        print(f"  Duration: {meta['duration']:.2f}s")
                    if meta.get("width") and meta.get("height"):
                        print(f"  Resolution: {meta['width']}x{meta['height']}")
                elif msg_type == "error":
                    print(f"✗ Error: {data['message']}")
                    if data.get("details"):
                        print(f"  Details: {data['details']}")
                    break


async def compress_video(
    ws_url: str,
    video_url: str,
    preset: str = "medium",
    max_width: Optional[int] = None,
    output_file: Optional[str] = None,
) -> None:
    """Compress video with quality preset"""
    job_id = str(uuid4())
    print(f"Starting job {job_id}: Compression (preset={preset})")

    async with websockets.connect(ws_url, max_size=500 * 1024 * 1024) as websocket:
        options = {"preset": preset}
        if max_width:
            options["max_width"] = max_width

        message = {
            "type": "start_job",
            "job_id": job_id,
            "operation": "compress",
            "input": {"source": "url", "url": video_url},
            "options": options,
        }

        await websocket.send(json.dumps(message))
        print(f"✓ Job submitted")

        async for msg in websocket:
            if isinstance(msg, bytes):
                header_len = int.from_bytes(msg[:4], "big")
                header = json.loads(msg[4 : 4 + header_len])
                file_data = msg[4 + header_len :]

                output_path = output_file or f"compressed_{header['filename']}"
                with open(output_path, "wb") as f:
                    f.write(file_data)
                print(f"✓ Saved output: {output_path} ({len(file_data):,} bytes)")
                break
            else:
                data = json.loads(msg)
                msg_type = data.get("type")

                if msg_type == "ack":
                    print(f"✓ {data['message']}")
                elif msg_type == "progress":
                    percentage = data.get("percentage", 0)
                    stage = data.get("stage", "")
                    print(f"  Progress: {percentage:.1f}% - {stage}")
                elif msg_type == "completed":
                    print(f"✓ Job completed!")
                    meta = data["output_metadata"]
                    print(f"  Size: {meta['size_bytes']:,} bytes")
                elif msg_type == "error":
                    print(f"✗ Error: {data['message']}")
                    break


async def extract_audio(
    ws_url: str, video_url: str, format: str = "mp3", output_file: Optional[str] = None
) -> None:
    """Extract audio from video"""
    job_id = str(uuid4())
    print(f"Starting job {job_id}: Extract audio (format={format})")

    async with websockets.connect(ws_url, max_size=500 * 1024 * 1024) as websocket:
        message = {
            "type": "start_job",
            "job_id": job_id,
            "operation": "extract_audio",
            "input": {"source": "url", "url": video_url},
            "options": {"format": format, "bitrate_kbps": 192},
        }

        await websocket.send(json.dumps(message))
        print(f"✓ Job submitted")

        async for msg in websocket:
            if isinstance(msg, bytes):
                header_len = int.from_bytes(msg[:4], "big")
                header = json.loads(msg[4 : 4 + header_len])
                file_data = msg[4 + header_len :]

                output_path = output_file or f"audio_{header['filename']}"
                with open(output_path, "wb") as f:
                    f.write(file_data)
                print(f"✓ Saved output: {output_path} ({len(file_data):,} bytes)")
                break
            else:
                data = json.loads(msg)
                msg_type = data.get("type")

                if msg_type == "ack":
                    print(f"✓ {data['message']}")
                elif msg_type == "progress":
                    percentage = data.get("percentage", 0)
                    stage = data.get("stage", "")
                    print(f"  Progress: {percentage:.1f}% - {stage}")
                elif msg_type == "completed":
                    print(f"✓ Job completed!")
                elif msg_type == "error":
                    print(f"✗ Error: {data['message']}")
                    break


async def create_thumbnail(
    ws_url: str, video_url: str, timestamp: float = 5.0, output_file: Optional[str] = None
) -> None:
    """Generate thumbnail from video"""
    job_id = str(uuid4())
    print(f"Starting job {job_id}: Thumbnail at {timestamp}s")

    async with websockets.connect(ws_url, max_size=500 * 1024 * 1024) as websocket:
        message = {
            "type": "start_job",
            "job_id": job_id,
            "operation": "thumbnail",
            "input": {"source": "url", "url": video_url},
            "options": {"timestamp": timestamp, "format": "png", "width": 640},
        }

        await websocket.send(json.dumps(message))
        print(f"✓ Job submitted")

        async for msg in websocket:
            if isinstance(msg, bytes):
                header_len = int.from_bytes(msg[:4], "big")
                header = json.loads(msg[4 : 4 + header_len])
                file_data = msg[4 + header_len :]

                output_path = output_file or f"thumb_{header['filename']}"
                with open(output_path, "wb") as f:
                    f.write(file_data)
                print(f"✓ Saved output: {output_path} ({len(file_data):,} bytes)")
                break
            else:
                data = json.loads(msg)
                msg_type = data.get("type")

                if msg_type == "ack":
                    print(f"✓ {data['message']}")
                elif msg_type == "progress":
                    percentage = data.get("percentage", 0)
                    print(f"  Progress: {percentage:.1f}%")
                elif msg_type == "completed":
                    print(f"✓ Job completed!")
                elif msg_type == "error":
                    print(f"✗ Error: {data['message']}")
                    break


async def main() -> None:
    """Main function with example operations"""
    ws_url = "ws://localhost:8080"
    test_video = "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4"

    print("FFmpeg WebSocket Service - Client Examples\n")
    print(f"WebSocket URL: {ws_url}")
    print(f"Test video: {test_video}\n")

    # Example 1: Speed conversion
    print("=" * 60)
    print("Example 1: Speed Conversion (2x)")
    print("=" * 60)
    await process_video_speed(ws_url, test_video, speed_factor=2.0)
    print()

    # Example 2: Compression
    print("=" * 60)
    print("Example 2: Compression (low quality)")
    print("=" * 60)
    await compress_video(ws_url, test_video, preset="low", max_width=640)
    print()

    # Example 3: Extract audio
    print("=" * 60)
    print("Example 3: Extract Audio (MP3)")
    print("=" * 60)
    await extract_audio(ws_url, test_video, format="mp3")
    print()

    # Example 4: Thumbnail
    print("=" * 60)
    print("Example 4: Generate Thumbnail")
    print("=" * 60)
    await create_thumbnail(ws_url, test_video, timestamp=2.0)
    print()

    print("All examples completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")

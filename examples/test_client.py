#!/usr/bin/env python3
"""Quick test client for FFmpeg WebSocket service"""

import asyncio
import json
from uuid import uuid4

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    subprocess.check_call(["pip", "install", "websockets"])
    import websockets


async def test_thumbnail():
    """Test thumbnail generation"""
    uri = "ws://localhost:8080"
    job_id = str(uuid4())

    print(f"Connecting to {uri}...")
    async with websockets.connect(uri, max_size=100*1024*1024) as ws:
        # Use a public test video
        message = {
            "type": "start_job",
            "job_id": job_id,
            "operation": "thumbnail",
            "input": {
                "source": "url",
                "url": "https://sample-videos.com/video321/mp4/240/big_buck_bunny_240p_1mb.mp4"
            },
            "options": {
                "timestamp": 2.0,
                "format": "png",
                "width": 320
            }
        }

        print(f"Sending start_job message for job {job_id[:8]}...")
        await ws.send(json.dumps(message))

        # Receive messages
        async for msg in ws:
            if isinstance(msg, bytes):
                # Binary message - output file
                header_len = int.from_bytes(msg[:4], 'big')
                header = json.loads(msg[4:4+header_len])
                file_data = msg[4+header_len:]

                filename = f"test_output_{header['filename']}"
                with open(filename, 'wb') as f:
                    f.write(file_data)

                print(f"✓ SUCCESS! Saved thumbnail: {filename} ({len(file_data):,} bytes)")
                break
            else:
                # JSON message
                data = json.loads(msg)
                msg_type = data.get('type')

                if msg_type == 'ack':
                    print(f"✓ {data['message']}")
                elif msg_type == 'progress':
                    percentage = data.get('percentage', 0)
                    stage = data.get('stage', '')
                    print(f"  Progress: {percentage:.1f}% - {stage}")
                elif msg_type == 'completed':
                    print(f"✓ Job completed!")
                    meta = data['output_metadata']
                    print(f"  Format: {meta['format']}")
                    print(f"  Size: {meta['size_bytes']:,} bytes")
                elif msg_type == 'error':
                    print(f"✗ Error: {data['message']}")
                    if data.get('details'):
                        print(f"  Details: {data['details']}")
                    break


if __name__ == "__main__":
    print("FFmpeg WebSocket Service - Test Client")
    print("=" * 50)
    print()

    try:
        asyncio.run(test_thumbnail())
    except KeyboardInterrupt:
        print("\n\nInterrupted")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

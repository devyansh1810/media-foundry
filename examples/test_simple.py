#!/usr/bin/env python3
"""Simple test with local HTTP server"""

import asyncio
import json
from uuid import uuid4
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import os

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "websockets"])
    import websockets


def start_http_server():
    """Start a simple HTTP server to serve the test video"""
    os.chdir('/home/aryan/Desktop/doramee')
    handler = SimpleHTTPRequestHandler
    httpd = HTTPServer(('127.0.0.1', 8888), handler)
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


async def test_thumbnail():
    """Test thumbnail generation with local file"""
    # Start HTTP server
    httpd = start_http_server()
    await asyncio.sleep(1)  # Wait for server

    uri = "ws://localhost:8080"
    job_id = str(uuid4())

    print(f"Connecting to {uri}...")
    async with websockets.connect(uri, max_size=100*1024*1024) as ws:
        message = {
            "type": "start_job",
            "job_id": job_id,
            "operation": "thumbnail",
            "input": {
                "source": "url",
                "url": "http://127.0.0.1:8888/test_video.mp4"
            },
            "options": {
                "timestamp": 2.0,
                "format": "png",
                "width": 320
            }
        }

        print(f"Testing thumbnail generation...")
        await ws.send(json.dumps(message))

        # Receive messages
        async for msg in ws:
            if isinstance(msg, bytes):
                header_len = int.from_bytes(msg[:4], 'big')
                header = json.loads(msg[4:4+header_len])
                file_data = msg[4+header_len:]

                filename = f"thumbnail_output.png"
                with open(filename, 'wb') as f:
                    f.write(file_data)

                print(f"\n✅ SUCCESS! Generated thumbnail: {filename} ({len(file_data):,} bytes)")
                httpd.shutdown()
                return True
            else:
                data = json.loads(msg)
                msg_type = data.get('type')

                if msg_type == 'ack':
                    print(f"✓ Job accepted")
                elif msg_type == 'progress':
                    percentage = data.get('percentage', 0)
                    stage = data.get('stage', '')
                    print(f"  {percentage:.0f}% - {stage}")
                elif msg_type == 'completed':
                    print(f"✓ Processing completed!")
                elif msg_type == 'error':
                    print(f"\n❌ Error: {data['message']}")
                    httpd.shutdown()
                    return False


if __name__ == "__main__":
    print("=" * 60)
    print("FFmpeg WebSocket Service - Integration Test")
    print("=" * 60)
    print()

    try:
        result = asyncio.run(test_thumbnail())
        if result:
            print("\n" + "=" * 60)
            print("✅ Test PASSED! Service is working correctly!")
            print("=" * 60)
        else:
            print("\n❌ Test FAILED")
    except Exception as e:
        print(f"\n❌ Test ERROR: {e}")
        import traceback
        traceback.print_exc()

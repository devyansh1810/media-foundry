#!/usr/bin/env python3
"""Test speed conversion operation"""

import asyncio
import json
from uuid import uuid4
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import os

import websockets


def start_http_server():
    """Start HTTP server"""
    os.chdir('/home/aryan/Desktop/doramee')
    httpd = HTTPServer(('127.0.0.1', 8889), SimpleHTTPRequestHandler)
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


async def test_speed_conversion():
    """Test 2x speed conversion"""
    httpd = start_http_server()
    await asyncio.sleep(0.5)

    uri = "ws://localhost:8080"
    job_id = str(uuid4())

    print(f"Testing 2x speed conversion...")
    async with websockets.connect(uri, max_size=100*1024*1024) as ws:
        message = {
            "type": "start_job",
            "job_id": job_id,
            "operation": "speed",
            "input": {
                "source": "url",
                "url": "http://127.0.0.1:8889/test_video.mp4"
            },
            "options": {
                "speed_factor": 2.0,
                "maintain_pitch": False
            }
        }

        await ws.send(json.dumps(message))

        async for msg in ws:
            if isinstance(msg, bytes):
                header_len = int.from_bytes(msg[:4], 'big')
                header = json.loads(msg[4:4+header_len])
                file_data = msg[4+header_len:]

                filename = "speed_2x_output.mp4"
                with open(filename, 'wb') as f:
                    f.write(file_data)

                print(f"\n✅ SUCCESS! Created 2x speed video: {filename} ({len(file_data):,} bytes)")
                httpd.shutdown()
                return True
            else:
                data = json.loads(msg)
                msg_type = data.get('type')

                if msg_type == 'ack':
                    print(f"✓ Job accepted")
                elif msg_type == 'progress':
                    percentage = data.get('percentage', 0)
                    print(f"  {percentage:.0f}% complete", end='\r')
                elif msg_type == 'completed':
                    print(f"\n✓ Processing completed!")
                elif msg_type == 'error':
                    print(f"\n❌ Error: {data['message']}")
                    httpd.shutdown()
                    return False


if __name__ == "__main__":
    print("Testing Speed Conversion (2x)...")
    result = asyncio.run(test_speed_conversion())
    if result:
        print("\n✅ Speed conversion test PASSED!")
    else:
        print("\n❌ Test FAILED")

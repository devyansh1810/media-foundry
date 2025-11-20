#!/usr/bin/env python3
import asyncio, json, websockets, os
from uuid import uuid4
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread

def start_http():
    os.chdir('/home/aryan/Desktop/doramee')
    httpd = HTTPServer(('127.0.0.1', 8890), SimpleHTTPRequestHandler)
    Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

async def test():
    httpd = start_http()
    await asyncio.sleep(0.5)
    
    async with websockets.connect("ws://localhost:8080", max_size=100*1024*1024) as ws:
        await ws.send(json.dumps({
            "type": "start_job",
            "job_id": str(uuid4()),
            "operation": "extract_audio",
            "input": {"source": "url", "url": "http://127.0.0.1:8890/test_video.mp4"},
            "options": {"format": "mp3", "bitrate_kbps": 128}
        }))
        
        async for msg in ws:
            if isinstance(msg, bytes):
                with open("audio_output.mp3", 'wb') as f:
                    f.write(msg[4+int.from_bytes(msg[:4],'big')+len(json.dumps({"job_id":"x","filename":"x"})):])
                print("✅ Audio extracted: audio_output.mp3")
                httpd.shutdown()
                return True
            else:
                data = json.loads(msg)
                if data['type'] == 'completed':
                    print("✓ Completed")
                elif data['type'] == 'error':
                    print(f"❌ {data['message']}")
                    return False

print("Testing Audio Extraction...")
result = asyncio.run(test())
print("✅ PASSED!" if result else "❌ FAILED")

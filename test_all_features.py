#!/usr/bin/env python3
"""
Comprehensive test script for all media-foundry backend features
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

import websockets

# Test configuration
WS_URL = "ws://localhost:8080"
TEST_VIDEO = "/home/divyanshu/Downloads/office/seo-stack-site/public/sample.mp4"
OUTPUT_DIR = Path("/tmp/media-foundry-tests")
OUTPUT_DIR.mkdir(exist_ok=True)

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class TestRunner:
    def __init__(self):
        self.results = []
        self.ws = None

    async def connect(self):
        """Connect to WebSocket server"""
        print(f"{BLUE}Connecting to {WS_URL}...{RESET}")
        # Increase max_size to 100MB to handle large video files
        self.ws = await websockets.connect(WS_URL, max_size=100 * 1024 * 1024)
        print(f"{GREEN}✓ Connected{RESET}\n")

    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.ws:
            await self.ws.close()

    async def run_test(self, name: str, job_data: Dict[str, Any]) -> bool:
        """Run a single test"""
        print(f"{BLUE}Testing: {name}{RESET}")
        job_id = f"test-{int(time.time() * 1000)}"

        # Add job_id to the message
        job_data["job_id"] = job_id

        try:
            # Send job
            await self.ws.send(json.dumps(job_data))

            # Send video file for upload source
            if job_data.get("input", {}).get("source") == "upload":
                await self.send_video_file(job_id)

            # Wait for ack
            ack = await asyncio.wait_for(self.ws.recv(), timeout=5)
            ack_msg = json.loads(ack)

            if ack_msg.get("type") != "ack":
                raise Exception(f"Expected ack, got {ack_msg.get('type')}")

            print(f"  {YELLOW}Processing...{RESET}")

            # Wait for completion or error
            while True:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=120)
                data = json.loads(msg)

                if data.get("type") == "progress":
                    progress = data.get("percentage", 0)
                    stage = data.get("stage", "")
                    print(f"  {YELLOW}Progress: {progress:.1f}% - {stage}{RESET}")

                elif data.get("type") == "completed":
                    # Receive binary data with header
                    binary_msg = await self.ws.recv()

                    # Parse header
                    header_length = int.from_bytes(binary_msg[:4], "big")
                    header_json = binary_msg[4:4+header_length].decode("utf-8")
                    header = json.loads(header_json)
                    file_data = binary_msg[4+header_length:]

                    size_mb = len(file_data) / (1024 * 1024)
                    metadata = data.get("output_metadata", {})

                    print(f"  {GREEN}✓ Success!{RESET}")
                    print(f"    Output size: {size_mb:.2f} MB")
                    print(f"    Format: {metadata.get('format', 'unknown')}")
                    if metadata.get("duration"):
                        print(f"    Duration: {metadata.get('duration'):.2f}s")

                    # Save output file
                    filename = header.get("filename", "output")
                    output_file = OUTPUT_DIR / f"{name.replace(' ', '_').lower()}_{filename}"
                    output_file.write_bytes(file_data)
                    print(f"    Saved to: {output_file}")

                    self.results.append({"name": name, "status": "PASS", "size_mb": size_mb})
                    return True

                elif data.get("type") == "error":
                    error_msg = data.get("message", "Unknown error")
                    print(f"  {RED}✗ Failed: {error_msg}{RESET}")
                    self.results.append({"name": name, "status": "FAIL", "error": error_msg})
                    return False

        except asyncio.TimeoutError:
            print(f"  {RED}✗ Timeout{RESET}")
            self.results.append({"name": name, "status": "TIMEOUT"})
            return False
        except Exception as e:
            print(f"  {RED}✗ Error: {e}{RESET}")
            self.results.append({"name": name, "status": "ERROR", "error": str(e)})
            return False
        finally:
            print()

    async def test_speed_conversion(self):
        """Test speed conversion (2x speed)"""
        return await self.run_test("Speed Conversion", {
            "type": "start_job",
            "operation": "speed",
            "input": {"source": "upload"},
            "options": {
                "speed_factor": 2.0,
                "maintain_pitch": True
            }
        })

    async def test_compression(self):
        """Test video compression"""
        return await self.run_test("Compression", {
            "type": "start_job",
            "operation": "compress",
            "input": {"source": "upload"},
            "options": {
                "preset": "medium",
                "crf": 28
            }
        })

    async def test_extract_audio(self):
        """Test audio extraction"""
        return await self.run_test("Extract Audio", {
            "type": "start_job",
            "operation": "extract_audio",
            "input": {"source": "upload"},
            "options": {
                "format": "mp3",
                "bitrate_kbps": 192
            }
        })

    async def test_convert_format(self):
        """Test format conversion"""
        return await self.run_test("Convert Format", {
            "type": "start_job",
            "operation": "convert",
            "input": {"source": "upload"},
            "options": {
                "target_format": "webm",
                "stream_copy": False,
                "video_codec": "libvpx-vp9",
                "audio_codec": "libopus"
            }
        })

    async def test_thumbnail(self):
        """Test thumbnail generation"""
        return await self.run_test("Thumbnail", {
            "type": "start_job",
            "operation": "thumbnail",
            "input": {"source": "upload"},
            "options": {
                "timestamp": 1.0,
                "format": "png",
                "width": 640
            }
        })

    async def test_trim(self):
        """Test video trimming"""
        return await self.run_test("Trim", {
            "type": "start_job",
            "operation": "trim",
            "input": {"source": "upload"},
            "options": {
                "start_time": 0.0,
                "end_time": 5.0
            }
        })

    async def test_gif(self):
        """Test GIF creation"""
        return await self.run_test("GIF Creation", {
            "type": "start_job",
            "operation": "gif",
            "input": {"source": "upload"},
            "options": {
                "start_time": 0.0,
                "duration": 3.0,
                "fps": 15,
                "width": 480,
                "optimize": True
            }
        })

    async def test_filters(self):
        """Test video filters"""
        return await self.run_test("Filters", {
            "type": "start_job",
            "operation": "filter",
            "input": {"source": "upload"},
            "options": {
                "filters": [
                    {"type": "scale", "width": 640, "height": 360},
                    {"type": "fps", "fps": 24}
                ]
            }
        })

    async def send_video_file(self, job_id: str):
        """Send test video file with proper binary protocol"""
        with open(TEST_VIDEO, "rb") as f:
            video_data = f.read()

        # Build binary message with header
        header = {"job_id": job_id, "filename": "sample.mp4"}
        header_json = json.dumps(header).encode("utf-8")
        header_length = len(header_json)

        binary_message = (
            header_length.to_bytes(4, "big") + header_json + video_data
        )

        await self.ws.send(binary_message)
        print(f"  {YELLOW}Uploaded {len(video_data) / (1024*1024):.2f} MB{RESET}")

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'=' * 60}")
        print(f"{BLUE}TEST SUMMARY{RESET}")
        print(f"{'=' * 60}\n")

        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] != "PASS")
        total = len(self.results)

        for result in self.results:
            status = result["status"]
            name = result["name"]

            if status == "PASS":
                print(f"{GREEN}✓ PASS{RESET} - {name}")
            else:
                error = result.get("error", "Unknown")
                print(f"{RED}✗ {status}{RESET} - {name}: {error}")

        print(f"\n{'-' * 60}")
        print(f"Total: {total} | Passed: {passed} | Failed: {failed}")

        if failed == 0:
            print(f"{GREEN}All tests passed!{RESET}")
        else:
            print(f"{RED}Some tests failed{RESET}")
        print(f"{'=' * 60}\n")

        return failed == 0


async def main():
    """Main test runner"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}Media Foundry Backend Test Suite{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")

    # Check if test video exists
    if not Path(TEST_VIDEO).exists():
        print(f"{RED}Error: Test video not found at {TEST_VIDEO}{RESET}")
        print(f"{YELLOW}Please update TEST_VIDEO path in the script{RESET}")
        return False

    runner = TestRunner()

    try:
        await runner.connect()

        # Test each feature
        tests = [
            ("Speed Conversion", runner.test_speed_conversion),
            ("Compression", runner.test_compression),
            ("Extract Audio", runner.test_extract_audio),
            ("Convert Format", runner.test_convert_format),
            ("Thumbnail", runner.test_thumbnail),
            ("Trim", runner.test_trim),
            ("GIF Creation", runner.test_gif),
            ("Filters", runner.test_filters),
        ]

        for test_name, test_func in tests:
            # Run test (video will be sent inside run_test)
            await test_func()

            # Small delay between tests
            await asyncio.sleep(1)

        # Print summary
        success = runner.print_summary()
        return success

    except Exception as e:
        print(f"{RED}Fatal error: {e}{RESET}")
        return False
    finally:
        await runner.disconnect()


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted{RESET}")
        sys.exit(1)

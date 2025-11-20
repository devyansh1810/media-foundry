# Quick Start Guide

Get the FFmpeg WebSocket Media Processing Service running in under 5 minutes.

## Prerequisites

- **Python 3.11+**
- **FFmpeg** installed on your system
- **uv** package manager (optional but recommended)

## Installation Steps

### 1. Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Verify installation:**
```bash
ffmpeg -version
```

### 2. Install uv (Fast Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or use pip:
```bash
pip install uv
```

### 3. Clone and Setup Project

```bash
# Navigate to project directory
cd /path/to/ffmpeg-websocket-service

# Install dependencies
uv pip install -e .

# Copy environment configuration
cp .env.example .env
```

### 4. Run the Service

```bash
python -m src.main
```

Or with make:
```bash
make run
```

You should see:
```
timestamp='2025-11-20 12:00:00' level='INFO' logger='__main__' message='Starting FFmpeg WebSocket Media Processing Service'
timestamp='2025-11-20 12:00:00' level='INFO' logger='src.job_manager.manager' message='Starting job manager with 4 workers'
timestamp='2025-11-20 12:00:00' level='INFO' logger='src.utils.health' message='Starting health check server on port 8081'
timestamp='2025-11-20 12:00:00' level='INFO' logger='src.websocket.server' message='Starting WebSocket server on 0.0.0.0:8080'
```

### 5. Test the Service

**Check health:**
```bash
curl http://localhost:8081/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "stats": {
    "total_jobs": 0,
    "active_jobs": 0,
    "queued_jobs": 0,
    "max_concurrent": 4
  }
}
```

**Run example client:**
```bash
# Install websockets for the example
uv pip install websockets

# Run example
python examples/client_example.py
```

## Docker Quick Start

Even faster with Docker:

```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f

# Check health
curl http://localhost:8081/health

# Stop
docker-compose down
```

## Your First Request

Create a simple Python script to test:

```python
import asyncio
import json
import websockets
from uuid import uuid4

async def test_service():
    uri = "ws://localhost:8080"

    async with websockets.connect(uri) as ws:
        # Start a compression job
        message = {
            "type": "start_job",
            "job_id": str(uuid4()),
            "operation": "compress",
            "input": {
                "source": "url",
                "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4"
            },
            "options": {
                "preset": "low",
                "max_width": 640
            }
        }

        await ws.send(json.dumps(message))

        # Wait for completion
        async for msg in ws:
            if isinstance(msg, bytes):
                print(f"Received output file: {len(msg)} bytes")
                break
            else:
                data = json.loads(msg)
                print(f"{data['type']}: {data.get('message', data.get('stage', ''))}")

asyncio.run(test_service())
```

## Troubleshooting

### Port already in use
```bash
# Change ports in .env
WS_PORT=8090
HEALTH_PORT=8091
```

### FFmpeg not found
```bash
# Check FFmpeg installation
which ffmpeg
ffmpeg -version

# Add to PATH if needed
export PATH="/usr/local/bin:$PATH"
```

### Permission errors with temp directory
```bash
# Change temp directory in .env
TEMP_DIR=/tmp/ffmpeg-jobs

# Or create and set permissions
mkdir -p /tmp/ffmpeg-jobs
chmod 777 /tmp/ffmpeg-jobs
```

### Import errors
```bash
# Reinstall dependencies
uv pip install -e . --reinstall
```

## Next Steps

1. Read the [full README](README.md) for detailed documentation
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
3. Check out more examples in `examples/client_example.py`
4. Explore all available operations and options
5. Customize configuration in `.env`

## Support

- GitHub Issues: Report bugs and request features
- Documentation: See README.md for full API documentation
- Examples: Check `examples/` directory for more use cases

Happy media processing! 🎥

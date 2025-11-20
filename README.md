# media-foundry

# FFmpeg WebSocket Media Processing Service

A production-ready, high-performance WebSocket-based media processing service powered by FFmpeg. Built with Python, asyncio, and Pydantic for type safety and efficiency.

## Features

### Core Operations

- **Speed Conversion** - Change playback speed (0.25x - 10x) with optional pitch correction
- **Compression** - Reduce file size with quality presets (low/medium/high) or custom settings
- **Audio Extraction** - Extract audio tracks to various formats (MP3, AAC, WAV, OPUS, M4A, FLAC, OGG)
- **Audio Removal** - Remove audio streams from videos
- **Format Conversion** - Convert between formats (MP4, MKV, WEBM, MOV, AVI, etc.)
- **Thumbnail Generation** - Create thumbnails at specific timestamps or evenly spaced intervals
- **Trimming/Clipping** - Extract clips from videos with precise timing
- **Concatenation** - Merge multiple video files
- **GIF Creation** - Convert video segments to optimized GIFs
- **Filters** - Apply video/audio filters (scale, rotate, crop, FPS change, volume adjust, normalize)
- **Subtitles** - Extract or burn subtitles

### Production Features

- ✅ Fully type-safe with Pydantic models
- ✅ Async I/O with streaming support
- ✅ Worker pool with configurable concurrency
- ✅ Job queue with fair scheduling
- ✅ Progress tracking and real-time updates
- ✅ Graceful cancellation
- ✅ Automatic cleanup of temporary files
- ✅ Health check endpoint
- ✅ Structured logging
- ✅ Docker support
- ✅ Comprehensive test suite

## Quick Start

### Local Development

1. **Install dependencies**:
```bash
# Install FFmpeg (if not already installed)
# Ubuntu/Debian:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg

# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python dependencies
uv pip install -e .

# Or with dev dependencies
uv pip install -e ".[dev]"
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Run the service**:
```bash
python -m src.main
```

The service will start on:
- WebSocket: `ws://localhost:8080`
- Health Check: `http://localhost:8081/health`

### Docker

1. **Build and run with Docker Compose**:
```bash
docker-compose up -d
```

2. **Build manually**:
```bash
docker build -t ffmpeg-websocket-service .
docker run -p 8080:8080 -p 8081:8081 ffmpeg-websocket-service
```

3. **Check health**:
```bash
curl http://localhost:8081/health
```

**For production deployment**, see the comprehensive [Deployment Guide](docs/DEPLOYMENT.md) which covers:
- Production Docker Compose setup
- Systemd service configuration
- Cloud deployments (AWS, GCP, DigitalOcean)
- Kubernetes manifests
- Nginx reverse proxy
- SSL/TLS setup
- Monitoring and scaling

## WebSocket Protocol

### Message Format

All messages are JSON unless explicitly noted as binary.

### Client → Server Messages

#### 1. Start Job

```json
{
  "type": "start_job",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "operation": "speed|compress|extract_audio|remove_audio|convert|thumbnail|trim|concat|gif|filter",
  "input": {
    "source": "upload|url",
    "url": "https://example.com/video.mp4"  // if source=url
  },
  "options": { /* operation-specific options */ }
}
```

#### 2. Cancel Job

```json
{
  "type": "cancel_job",
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 3. Ping

```json
{
  "type": "ping"
}
```

### Server → Client Messages

#### 1. Acknowledgment

```json
{
  "type": "ack",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Job accepted and queued"
}
```

#### 2. Progress Update

```json
{
  "type": "progress",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "percentage": 45.5,
  "stage": "processing",
  "ffmpeg_log": "frame= 123 fps=45 q=28.0 size= 1024kB time=00:00:05.00"
}
```

#### 3. Completion

```json
{
  "type": "completed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "output_metadata": {
    "format": "mp4",
    "duration": 120.5,
    "size_bytes": 5242880,
    "video_codec": "h264",
    "audio_codec": "aac",
    "width": 1920,
    "height": 1080,
    "bitrate": 2500000,
    "fps": 30.0
  },
  "delivery_method": "binary",
  "message": "Job completed successfully"
}
```

#### 4. Error

```json
{
  "type": "error",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "JOB_FAILED",
  "message": "FFmpeg process failed",
  "details": "Error details here"
}
```

#### 5. Pong

```json
{
  "type": "pong"
}
```

### Binary Messages

Binary frames are used for file uploads and downloads.

**Format**: `[4 bytes: header length][header JSON][file data]`

**Upload Example**:
```
Header: {"job_id": "...", "filename": "input.mp4"}
```

**Download Example**:
```
Header: {"job_id": "...", "filename": "output.mp4"}
```

## Operation Examples

### 1. Speed Conversion (2x)

**Request**:
```json
{
  "type": "start_job",
  "job_id": "job-001",
  "operation": "speed",
  "input": {
    "source": "url",
    "url": "https://example.com/video.mp4"
  },
  "options": {
    "speed_factor": 2.0,
    "maintain_pitch": false
  }
}
```

**Options**:
- `speed_factor` (0.25 - 10.0): Speed multiplier
- `maintain_pitch` (bool): Preserve audio pitch

### 2. Compression (Low Quality)

**Request**:
```json
{
  "type": "start_job",
  "job_id": "job-002",
  "operation": "compress",
  "input": {
    "source": "url",
    "url": "https://example.com/video.mp4"
  },
  "options": {
    "preset": "low",
    "max_width": 1280,
    "max_height": 720
  }
}
```

**Options**:
- `preset`: "low" | "medium" | "high" | "custom"
- `video_bitrate_kbps` (int): Video bitrate in kbps
- `audio_bitrate_kbps` (int): Audio bitrate in kbps
- `crf` (0-51): Constant Rate Factor
- `max_width` (int): Maximum width
- `max_height` (int): Maximum height
- `target_format`: "mp4" | "mkv" | "webm"

### 3. Extract Audio to MP3

**Request**:
```json
{
  "type": "start_job",
  "job_id": "job-003",
  "operation": "extract_audio",
  "input": {
    "source": "url",
    "url": "https://example.com/video.mp4"
  },
  "options": {
    "format": "mp3",
    "bitrate_kbps": 192,
    "sample_rate": 44100
  }
}
```

**Options**:
- `format`: "mp3" | "aac" | "wav" | "opus" | "m4a" | "flac" | "ogg"
- `bitrate_kbps` (int): Audio bitrate
- `sample_rate` (8000|16000|22050|44100|48000|96000): Sample rate

### 4. Remove Audio (Mute)

**Request**:
```json
{
  "type": "start_job",
  "job_id": "job-004",
  "operation": "remove_audio",
  "input": {
    "source": "url",
    "url": "https://example.com/video.mp4"
  },
  "options": {
    "keep_video_quality": true
  }
}
```

**Options**:
- `keep_video_quality` (bool): Copy video stream without re-encoding

### 5. Format Conversion

**Request**:
```json
{
  "type": "start_job",
  "job_id": "job-005",
  "operation": "convert",
  "input": {
    "source": "url",
    "url": "https://example.com/video.mp4"
  },
  "options": {
    "target_format": "mkv",
    "stream_copy": true
  }
}
```

**Options**:
- `target_format` (string): Target format
- `stream_copy` (bool): Copy streams without re-encoding
- `video_codec` (string): Video codec (e.g., "h264", "vp9")
- `audio_codec` (string): Audio codec (e.g., "aac", "opus")

### 6. Thumbnail Generation

**Single thumbnail at 5 seconds**:
```json
{
  "type": "start_job",
  "job_id": "job-006",
  "operation": "thumbnail",
  "input": {
    "source": "url",
    "url": "https://example.com/video.mp4"
  },
  "options": {
    "timestamp": 5.0,
    "format": "png",
    "width": 640
  }
}
```

**Multiple evenly-spaced thumbnails**:
```json
{
  "type": "start_job",
  "job_id": "job-007",
  "operation": "thumbnail",
  "input": {
    "source": "url",
    "url": "https://example.com/video.mp4"
  },
  "options": {
    "count": 3,
    "format": "jpeg",
    "width": 320,
    "height": 180
  }
}
```

**Options**:
- `timestamp` (float): Timestamp in seconds (mutually exclusive with `count`)
- `count` (1-20): Number of thumbnails (mutually exclusive with `timestamp`)
- `format`: "png" | "jpeg" | "jpg"
- `width` (int): Thumbnail width
- `height` (int): Thumbnail height

### 7. Trim/Clip Video

**Request**:
```json
{
  "type": "start_job",
  "job_id": "job-008",
  "operation": "trim",
  "input": {
    "source": "url",
    "url": "https://example.com/video.mp4"
  },
  "options": {
    "start_time": 10.0,
    "end_time": 30.0
  }
}
```

**Options**:
- `start_time` (float): Start time in seconds
- `end_time` (float): End time in seconds

### 8. Create GIF

**Request**:
```json
{
  "type": "start_job",
  "job_id": "job-009",
  "operation": "gif",
  "input": {
    "source": "url",
    "url": "https://example.com/video.mp4"
  },
  "options": {
    "start_time": 5.0,
    "duration": 10.0,
    "fps": 15,
    "width": 480,
    "optimize": true
  }
}
```

**Options**:
- `start_time` (float): Start time in seconds
- `duration` (0-30): Duration in seconds
- `fps` (1-30): Frames per second
- `width` (int): GIF width (maintains aspect ratio)
- `optimize` (bool): Optimize for smaller file size

### 9. Apply Filters

**Request**:
```json
{
  "type": "start_job",
  "job_id": "job-010",
  "operation": "filter",
  "input": {
    "source": "url",
    "url": "https://example.com/video.mp4"
  },
  "options": {
    "filters": [
      {"type": "scale", "width": 1280, "height": 720},
      {"type": "volume", "volume": 1.5},
      {"type": "fps", "fps": 30}
    ]
  }
}
```

**Available Filters**:
- `scale`: {"type": "scale", "width": int, "height": int}
- `rotate`: {"type": "rotate", "angle": degrees}
- `crop`: {"type": "crop", "width": int, "height": int, "x": int, "y": int}
- `fps`: {"type": "fps", "fps": int}
- `volume`: {"type": "volume", "volume": float}
- `normalize`: {"type": "normalize"}

## Client Example (Python)

```python
import asyncio
import json
import websockets
from uuid import uuid4

async def process_video():
    uri = "ws://localhost:8080"

    async with websockets.connect(uri) as websocket:
        # Start speed conversion job
        job_id = str(uuid4())
        message = {
            "type": "start_job",
            "job_id": job_id,
            "operation": "speed",
            "input": {
                "source": "url",
                "url": "https://example.com/video.mp4"
            },
            "options": {
                "speed_factor": 2.0,
                "maintain_pitch": False
            }
        }

        await websocket.send(json.dumps(message))

        # Receive messages
        async for msg in websocket:
            if isinstance(msg, bytes):
                # Binary message - output file
                header_len = int.from_bytes(msg[:4], 'big')
                header = json.loads(msg[4:4+header_len])
                file_data = msg[4+header_len:]

                # Save file
                with open(f"output_{header['filename']}", 'wb') as f:
                    f.write(file_data)
                print(f"Saved output file: {len(file_data)} bytes")
                break
            else:
                # JSON message
                data = json.loads(msg)
                msg_type = data.get('type')

                if msg_type == 'ack':
                    print(f"Job accepted: {data['message']}")
                elif msg_type == 'progress':
                    print(f"Progress: {data['percentage']:.1f}% - {data['stage']}")
                elif msg_type == 'completed':
                    print(f"Job completed!")
                    print(f"Metadata: {data['output_metadata']}")
                elif msg_type == 'error':
                    print(f"Error: {data['message']}")
                    break

asyncio.run(process_video())
```

## Configuration

Environment variables (`.env`):

```bash
# Server
WS_HOST=0.0.0.0
WS_PORT=8080
HEALTH_PORT=8081

# FFmpeg
MAX_CONCURRENT_JOBS=4
FFMPEG_TIMEOUT_SECONDS=600
FFMPEG_THREADS=0  # 0=auto

# Files
TEMP_DIR=/tmp/ffmpeg-jobs
MAX_FILE_SIZE_MB=500
CLEANUP_INTERVAL_SECONDS=60

# Logging
LOG_LEVEL=INFO

# WebSocket
WS_MAX_SIZE=524288000  # 500MB
WS_PING_INTERVAL=30
WS_PING_TIMEOUT=10
```

## Testing

Run tests:
```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Type checking
mypy src/

# Code formatting
black src/
ruff check src/

# Or use make commands
make install-dev
make test
make lint
make format
```

## Architecture

```
src/
├── config/          # Configuration with Pydantic settings
├── logging/         # Structured logging
├── ffmpeg/          # FFmpeg command builder and runner
│   ├── command_builder.py  # Build commands for all operations
│   ├── runner.py           # Async FFmpeg process execution
│   └── metadata.py         # Extract media metadata
├── job_manager/     # Job queue and worker pool
│   ├── job.py              # Job model and status
│   └── manager.py          # Queue and worker management
├── websocket/       # WebSocket server and protocol
│   ├── models.py           # Pydantic models for messages
│   └── server.py           # WebSocket server implementation
├── utils/           # Utilities
│   └── health.py           # Health check HTTP server
└── main.py          # Application entry point
```

## Error Codes

- `INVALID_JSON` - Malformed JSON message
- `VALIDATION_ERROR` - Message validation failed
- `UNKNOWN_MESSAGE_TYPE` - Unsupported message type
- `SUBMIT_FAILED` - Failed to submit job
- `JOB_FAILED` - FFmpeg processing failed
- `JOB_CANCELLED` - Job cancelled by user
- `CANCEL_FAILED` - Job not found or already completed
- `INVALID_BINARY` - Invalid binary message format
- `BINARY_ERROR` - Binary message processing error
- `OUTPUT_SEND_FAILED` - Failed to send output file
- `INTERNAL_ERROR` - Internal server error

## Performance Tips

1. **Use stream copy** when possible (format conversion without re-encoding)
2. **Adjust concurrency** based on CPU cores (`MAX_CONCURRENT_JOBS`)
3. **Set FFmpeg threads** appropriately (`FFMPEG_THREADS`)
4. **Use URL input** to avoid binary uploads over WebSocket
5. **Monitor health endpoint** for queue depth and active jobs

## License

MIT

## Documentation

For more detailed documentation, see the [docs/](docs/) directory:

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[Architecture Documentation](docs/ARCHITECTURE.md)** - System design and components
- **[RabbitMQ Integration](docs/RABBITMQ_INTEGRATION.md)** - Production deployment with RabbitMQ
- **[Project Summary](docs/PROJECT_SUMMARY.md)** - High-level overview
- **[Test Results](docs/TEST_RESULTS.md)** - Validation and test coverage
- **[Implementation Checklist](docs/IMPLEMENTATION_CHECKLIST.md)** - Feature completion status

## Examples

Example scripts are in the [examples/](examples/) directory:

```bash
# Complete client example with multiple operations
python examples/client_example.py

# Simple integration test
python examples/test_simple.py

# Test specific operations
python examples/test_speed.py
python examples/test_audio.py
```

## Contributing

Contributions welcome! Please ensure tests pass and code is formatted with `black` and `ruff`.

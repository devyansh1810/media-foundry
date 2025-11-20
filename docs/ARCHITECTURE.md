# Architecture Overview

## System Design

The FFmpeg WebSocket Media Processing Service is built with a modular, production-ready architecture optimized for efficiency and scalability.

### High-Level Architecture

```
┌─────────────┐
│  WebSocket  │
│   Clients   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         WebSocket Server                │
│   - Protocol handling                   │
│   - Message validation (Pydantic)       │
│   - Binary streaming                    │
│   - Connection management               │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         Job Manager                     │
│   - Job queue (asyncio.Queue)           │
│   - Worker pool (concurrent workers)    │
│   - Job lifecycle tracking              │
│   - Progress callbacks                  │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│       FFmpeg Runner                     │
│   - Async process execution             │
│   - Streaming I/O                       │
│   - Progress parsing                    │
│   - Timeout handling                    │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│          FFmpeg CLI                     │
│   - Video/audio processing              │
│   - Format conversion                   │
│   - Filtering & effects                 │
└─────────────────────────────────────────┘
```

### Component Details

#### 1. Configuration (`src/config/`)
- **Pydantic Settings**: Type-safe configuration with validation
- **Environment Variables**: 12-factor app compliant
- **Default Values**: Sensible defaults for all settings
- **Validation**: Automatic validation on startup

#### 2. Logging (`src/logging/`)
- **Structured Logging**: Key-value pairs for easy parsing
- **Contextual Information**: Job ID, operation, duration tracking
- **Configurable Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Sanitized Output**: Redacts sensitive information

#### 3. WebSocket Server (`src/websocket/`)

**Models (`models.py`)**:
- Pydantic models for all message types
- Type-safe operation options
- Input/output validation
- Enum-based operation types

**Server (`server.py`)**:
- Connection lifecycle management
- Message routing and validation
- Binary message handling
- Progress streaming
- Error handling

**Message Flow**:
```
Client                Server
  │                     │
  ├──StartJob──────────>│
  │<─────────────Ack────┤
  │<────────Progress────┤
  │<────────Progress────┤
  │<───────Completed────┤
  │<──────Binary File───┤
  │                     │
```

#### 4. Job Manager (`src/job_manager/`)

**Job Model (`job.py`)**:
- Status tracking (queued → processing → completed/failed/cancelled)
- Progress tracking (0-100%)
- Timing information
- Cancellation support

**Manager (`manager.py`)**:
- **Queue**: `asyncio.Queue` for fair scheduling
- **Worker Pool**: Configurable number of concurrent workers
- **Job Tracking**: Dictionary-based job storage
- **Callbacks**: Progress, completion, error callbacks
- **Cleanup**: Automatic cleanup of old jobs and temp files

**Worker Flow**:
```
┌─────────────┐
│  Get Job    │
│  from Queue │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Download/  │
│  Prepare    │
│  Input      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Build     │
│   FFmpeg    │
│   Command   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Execute   │
│   FFmpeg    │
│   (async)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Extract    │
│  Metadata   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Notify    │
│   Client    │
└─────────────┘
```

#### 5. FFmpeg Module (`src/ffmpeg/`)

**Command Builder (`command_builder.py`)**:
- Operation-specific command generation
- Preset support (low/medium/high quality)
- Filter composition
- Format-specific optimizations

**Runner (`runner.py`)**:
- Async subprocess execution
- Real-time progress tracking
- Stderr/stdout capture
- Timeout handling
- Graceful cancellation

**Metadata Extractor (`metadata.py`)**:
- FFprobe integration
- Stream information extraction
- Format detection
- Duration/bitrate/codec parsing

#### 6. Utilities (`src/utils/`)

**Health Server (`health.py`)**:
- HTTP endpoint on separate port
- JSON status response
- Job statistics
- Version information

**Health Response Example**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "stats": {
    "total_jobs": 42,
    "active_jobs": 3,
    "queued_jobs": 1,
    "max_concurrent": 4
  }
}
```

## Data Flow

### 1. Job Submission
```
1. Client sends StartJobMessage (JSON)
2. WebSocket server validates with Pydantic
3. Job created and added to queue
4. Acknowledgment sent to client
5. Worker picks up job from queue
```

### 2. Input Handling

**URL Source**:
```
1. httpx streams download to temp file
2. Progress tracked during download
3. File validated against size limits
```

**Upload Source**:
```
1. Binary WebSocket message received
2. Header parsed (job_id, filename)
3. Data written to temp file
4. File path stored in job
```

### 3. Processing
```
1. FFmpeg command built based on operation
2. Process spawned with asyncio.create_subprocess_exec
3. Stderr monitored for progress
4. Progress callbacks invoked
5. Output written to temp file
```

### 4. Output Delivery
```
1. Metadata extracted with ffprobe
2. Completion message sent (JSON)
3. Output file streamed as binary
4. Client receives and saves file
```

## Concurrency Model

### Async Architecture
- **Event Loop**: Single asyncio event loop
- **Coroutines**: All I/O operations are async
- **Worker Pool**: N concurrent workers (configurable)
- **No Threads**: Pure async, except HTTP health server

### Resource Management
- **File Descriptors**: Managed by async file operations
- **Memory**: Streaming I/O prevents large file buffering
- **CPU**: Controlled by MAX_CONCURRENT_JOBS
- **Disk**: Automatic cleanup after 1 hour

## Error Handling

### Validation Errors
- Caught at WebSocket layer
- Pydantic ValidationError → ErrorMessage
- Client receives structured error

### Processing Errors
- FFmpeg failures captured from stderr
- Non-zero exit codes handled
- Partial output cleaned up

### Connection Errors
- WebSocket disconnections detected
- In-progress jobs cancelled
- Temp files cleaned up

## Security Considerations

### Input Validation
- File size limits enforced
- URL validation (HTTP/HTTPS only)
- Command injection prevention
- Path traversal prevention

### Resource Limits
- Maximum concurrent jobs
- Per-job timeout
- Maximum file size
- WebSocket message size limits

### Logging
- Sensitive paths redacted
- URLs sanitized
- Command arguments filtered

## Performance Optimizations

### 1. Streaming I/O
- No buffering of large files in memory
- Async file operations with `aiofiles`
- HTTP streaming with `httpx`

### 2. FFmpeg Optimizations
- Stream copy when possible (no re-encoding)
- Fast seek with `-ss` before `-i`
- Efficient concat demuxer
- Optimized presets

### 3. Worker Pool
- Fair scheduling with queue
- Configurable concurrency
- Non-blocking operations

### 4. Temporary Files
- Isolated per-job directories
- Automatic cleanup
- Configurable temp directory

## Scalability

### Horizontal Scaling
The service is designed for horizontal scaling:
- Stateless workers
- Shared storage for temp files (use network mount)
- Load balancer in front of multiple instances

### Vertical Scaling
- Increase MAX_CONCURRENT_JOBS
- Adjust FFMPEG_THREADS
- More CPU cores = more concurrent jobs

### Resource Planning
- CPU: ~100% per concurrent job (during encoding)
- Memory: ~500MB per job (depends on file size)
- Disk: 2x largest file size per job
- Network: Depends on input/output delivery method

## Testing Strategy

### Unit Tests
- Pydantic model validation
- FFmpeg command construction
- Job lifecycle
- Configuration validation

### Integration Tests
- End-to-end message flow
- FFmpeg execution
- File I/O
- Error scenarios

### Manual Testing
- WebSocket client examples
- Docker deployment
- Health endpoint
- Various media formats

## Deployment

### Local Development
```bash
python -m src.main
```

### Docker
```bash
docker-compose up
```

### Production Considerations
- Use environment variables for configuration
- Mount persistent volume for temp files
- Set appropriate resource limits
- Monitor health endpoint
- Set up log aggregation
- Use reverse proxy (nginx) for SSL

## Monitoring

### Health Checks
- HTTP endpoint: `/health`
- Docker HEALTHCHECK
- Response includes job statistics

### Logging
- Structured logs to stdout
- JSON format for log aggregation
- Job lifecycle events
- Error tracking

### Metrics (Future)
- Prometheus endpoint
- Job duration histogram
- Queue depth gauge
- Success/failure counters

## Future Enhancements

1. **Authentication**: Add API key or JWT authentication
2. **Storage Backend**: S3/GCS integration for input/output
3. **Webhooks**: Callback URLs for job completion
4. **Job Persistence**: Redis/Database for job state
5. **Rate Limiting**: Per-client rate limits
6. **Metrics**: Prometheus metrics endpoint
7. **Batching**: Batch processing of multiple files
8. **Caching**: Cache processed files
9. **Priority Queue**: Job prioritization
10. **Distributed Workers**: Multiple worker nodes

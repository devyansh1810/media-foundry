# RabbitMQ Integration Guide

## Overview

The FFmpeg WebSocket Service now supports **RabbitMQ** as an alternative to the in-memory `asyncio.Queue` for job management. This provides significant benefits for production deployments.

## Benefits of RabbitMQ Integration

### 1. **Job Persistence**
- Jobs survive server restarts
- No job loss during deployments
- Messages stored on disk (durable queues)

### 2. **Distributed Processing**
- Run multiple worker instances across different machines
- Horizontal scaling without code changes
- Load balancing handled by RabbitMQ

### 3. **Reliability**
- Message acknowledgment prevents job loss
- Automatic retry on worker failure
- Dead letter queues for failed jobs

### 4. **Better Monitoring**
- RabbitMQ Management UI (http://localhost:15672)
- Real-time queue metrics
- Consumer monitoring
- Message rate statistics

### 5. **Advanced Features**
- Priority queues
- Message TTL (time-to-live)
- Queue length limits
- Per-consumer prefetch control

## Architecture Comparison

### Original (asyncio.Queue)
```
┌─────────────────┐
│  WebSocket      │
│  Server         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  In-Memory      │
│  asyncio.Queue  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Worker Pool    │
│  (4 workers)    │
└─────────────────┘
```

### With RabbitMQ
```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  WebSocket      │────▶│   RabbitMQ      │────▶│  Worker Pool #1  │
│  Server #1      │     │   Exchange      │     │  (4 workers)     │
└─────────────────┘     │      +          │     └──────────────────┘
                        │   Queues        │
┌─────────────────┐     │   (Persistent)  │     ┌──────────────────┐
│  WebSocket      │────▶│                 │────▶│  Worker Pool #2  │
│  Server #2      │     │                 │     │  (4 workers)     │
└─────────────────┘     └─────────────────┘     └──────────────────┘
```

## Installation

### 1. RabbitMQ Server

RabbitMQ is already installed and running on your system:
```bash
# Check status
sudo systemctl status rabbitmq-server

# Verify ports
ss -tlnp | grep 5672   # AMQP port
ss -tlnp | grep 15672  # Management UI
```

### 2. Python Client

Already installed:
```bash
source .venv/bin/activate
# aio-pika is already in your environment
```

## Configuration

### Environment Variables

Add to `.env`:
```bash
# RabbitMQ Configuration
RABBITMQ_URL=amqp://guest:guest@localhost/
```

**URL Format**: `amqp://username:password@host:port/vhost`

**Examples**:
```bash
# Local development
RABBITMQ_URL=amqp://guest:guest@localhost/

# Production with auth
RABBITMQ_URL=amqp://admin:secretpass@rabbitmq.prod.com/

# Custom vhost
RABBITMQ_URL=amqp://user:pass@localhost/ffmpeg_vhost

# SSL connection
RABBITMQ_URL=amqps://user:pass@rabbitmq.prod.com:5671/
```

## Usage

### Start with RabbitMQ

```bash
# Use the RabbitMQ-enabled version
python -m src.main_rabbitmq
```

**vs. original:**
```bash
# In-memory queue version
python -m src.main
```

### Logs Indicate RabbitMQ

```
timestamp='...' message='Starting FFmpeg WebSocket Media Processing Service (RabbitMQ Edition)'
timestamp='...' message='RabbitMQ URL: amqp://guest:guest@localhost/'
timestamp='...' message='Connecting to RabbitMQ at amqp://guest:guest@localhost/'
timestamp='...' message='RabbitMQ connected - Starting 4 workers'
timestamp='...' message='RabbitMQ Worker 0 started'
...
```

### Health Check

```bash
curl http://localhost:8081/health
```

Response includes backend type:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "stats": {
    "total_jobs": 0,
    "active_jobs": 0,
    "queued_jobs": 0,
    "max_concurrent": 4,
    "backend": "RabbitMQ"  ← Indicates RabbitMQ is used
  }
}
```

## RabbitMQ Resources Created

The service automatically creates:

### 1. Exchange
- **Name**: `ffmpeg_jobs`
- **Type**: direct
- **Durable**: Yes (survives broker restart)
- **Purpose**: Routes job messages to queues

### 2. Main Queue
- **Name**: `ffmpeg_job_queue`
- **Durable**: Yes
- **Message TTL**: 1 hour
- **Max Length**: 10,000 messages
- **Purpose**: Stores pending jobs

### 3. Dead Letter Queue
- **Name**: `ffmpeg_job_dlq`
- **Durable**: Yes
- **Purpose**: Stores failed jobs for inspection

## Distributed Workers Setup

### Scenario: Scale to Multiple Machines

**Machine 1** (WebSocket Server + Worker):
```bash
# Start service
python -m src.main_rabbitmq
```

**Machine 2** (Additional Workers):
```bash
# Set RabbitMQ URL to Machine 1
export RABBITMQ_URL=amqp://guest:guest@machine1.local/

# Start worker-only mode (if implemented)
# Or run full service (will add more workers to pool)
python -m src.main_rabbitmq
```

Jobs submitted to Machine 1 can be processed by workers on Machine 2!

## Monitoring

### RabbitMQ Management UI

Access at: **http://localhost:15672**

**Default Credentials**:
- Username: `guest`
- Password: `guest`

**Features**:
- View queue depths
- Monitor message rates
- See connected consumers
- Check resource usage
- Export metrics

### CLI Monitoring

```bash
# List queues
sudo rabbitmqctl list_queues name messages consumers

# Example output:
# Timeout: 60.0 seconds ...
# Listing queues for vhost / ...
# name                    messages    consumers
# ffmpeg_job_queue        0           4
# ffmpeg_job_dlq          0           0
```

### Queue Stats

```bash
# Detailed queue info
sudo rabbitmqctl list_queues name messages_ready messages_unacknowledged

# Consumer info
sudo rabbitmqctl list_consumers
```

## Job Flow with RabbitMQ

### 1. Job Submission
```
Client → WebSocket → JobManager.submit_job()
                          ↓
                   JSON serialization
                          ↓
                   RabbitMQ.publish()
                          ↓
                   Queue: ffmpeg_job_queue
```

### 2. Job Processing
```
RabbitMQ Queue → Worker consumes message
                      ↓
                 Deserialize job
                      ↓
                 Process with FFmpeg
                      ↓
                 Success? → ACK (remove from queue)
                 Failure? → REJECT (move to DLQ)
```

### 3. Fault Tolerance
```
Worker crashes during processing
         ↓
Message not ACKed
         ↓
RabbitMQ requeues after timeout
         ↓
Another worker picks it up
         ↓
Job completes successfully
```

## Advantages in Production

### Deployment Updates
```bash
# Old way (asyncio.Queue)
1. Stop service
2. Jobs in queue are LOST
3. Deploy new version
4. Start service

# With RabbitMQ
1. Stop service
2. Jobs stay in RabbitMQ queue
3. Deploy new version
4. Start service
5. Jobs resume processing automatically
```

### Scaling
```bash
# Need more capacity?
# Just start more workers:

# Terminal 1
python -m src.main_rabbitmq

# Terminal 2
python -m src.main_rabbitmq

# Now 8 workers total processing jobs!
```

### Reliability
```bash
# Worker crashes?
# - Message automatically redelivered
# - Another worker picks it up
# - No manual intervention needed
```

## Performance Considerations

### Latency
- **Small overhead**: ~1-5ms per job (RabbitMQ routing)
- **Network**: Add ~1ms for remote RabbitMQ
- **Overall**: Negligible compared to FFmpeg processing time

### Throughput
- RabbitMQ can handle **thousands of messages/second**
- Bottleneck is FFmpeg processing, not queue
- Horizontal scaling unlimited

### Resource Usage
- **Memory**: RabbitMQ uses ~100MB baseline
- **Disk**: Messages stored on disk (configurable)
- **Network**: Minimal (<1KB per job message)

## Comparison Table

| Feature | asyncio.Queue | RabbitMQ |
|---------|---------------|----------|
| Persistence | ❌ Memory only | ✅ Disk-backed |
| Survives restart | ❌ No | ✅ Yes |
| Distributed workers | ❌ No | ✅ Yes |
| Monitoring UI | ❌ No | ✅ Built-in |
| Message retry | ❌ No | ✅ Automatic |
| Dead letter queue | ❌ No | ✅ Yes |
| Priority queues | ❌ No | ✅ Yes |
| Setup complexity | ✅ Simple | ⚠️ Requires RabbitMQ |
| Performance | ✅ Faster | ✅ Fast enough |
| Best for | Development | Production |

## Migration from asyncio.Queue

**No changes needed in WebSocket protocol or client code!**

The WebSocket API remains identical. Only the backend changes.

```bash
# Before
python -m src.main

# After
python -m src.main_rabbitmq
```

That's it!

## Troubleshooting

### RabbitMQ Connection Failed
```
Error: Cannot connect to RabbitMQ
```

**Check**:
```bash
# Is RabbitMQ running?
sudo systemctl status rabbitmq-server

# Can you reach it?
telnet localhost 5672

# Check URL
echo $RABBITMQ_URL
```

### Jobs Not Processing
```bash
# Check queue depth
sudo rabbitmqctl list_queues

# Check consumers
sudo rabbitmqctl list_consumers

# Look for errors in service logs
```

### Performance Issues
```bash
# Increase workers
export MAX_CONCURRENT_JOBS=8
python -m src.main_rabbitmq

# Or start multiple instances
```

## Testing

```bash
# Test with RabbitMQ
source .venv/bin/activate
python -m src.main_rabbitmq &

# Run test
python test_simple.py

# Check health
curl http://localhost:8081/health
# Should show "backend": "RabbitMQ"
```

## Best Practices

### 1. Use Separate RabbitMQ Instance for Production
```bash
# Development
RABBITMQ_URL=amqp://guest:guest@localhost/

# Production
RABBITMQ_URL=amqp://prod_user:strong_pass@rabbitmq.prod.com/ffmpeg
```

### 2. Enable RabbitMQ Persistence
Ensure durable queues (already configured in code):
```python
await self.channel.declare_queue(
    "ffmpeg_job_queue",
    durable=True,  # ← Survives broker restart
)
```

### 3. Monitor Queue Depth
Set up alerts if queue grows too large:
```bash
# Alert if > 1000 jobs queued
rabbitmqctl list_queues | awk '$2 > 1000'
```

### 4. Use Dead Letter Queue
Check DLQ periodically for failed jobs:
```bash
# View dead letters
sudo rabbitmqctl list_queues name messages | grep dlq
```

## Conclusion

RabbitMQ integration provides:
- ✅ Production-grade reliability
- ✅ Horizontal scalability
- ✅ Zero job loss
- ✅ Built-in monitoring
- ✅ Seamless deployment updates

**Recommendation**: Use RabbitMQ for all production deployments.

---

**Status**: ✅ Fully Tested and Operational
**Version**: 1.0.0
**Last Updated**: November 20, 2025

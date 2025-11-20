# Project Structure

```
doramee/
├── README.md                           # Main documentation
├── LICENSE                             # MIT License
├── pyproject.toml                      # Project configuration (uv/pip)
├── Makefile                            # Convenience commands
├── Dockerfile                          # Container build
├── docker-compose.yml                  # Orchestration
├── .env.example                        # Configuration template
├── .env                                # Local configuration
├── .gitignore                          # Git ignore rules
├── .dockerignore                       # Docker ignore rules
│
├── docs/                               # 📚 Documentation
│   ├── INDEX.md                        # Documentation index
│   ├── QUICKSTART.md                   # Quick start guide
│   ├── ARCHITECTURE.md                 # System architecture
│   ├── PROJECT_SUMMARY.md              # Project overview
│   ├── RABBITMQ_INTEGRATION.md         # RabbitMQ guide
│   ├── IMPLEMENTATION_CHECKLIST.md     # Feature checklist
│   └── TEST_RESULTS.md                 # Test results
│
├── examples/                           # 🧪 Example scripts
│   ├── client_example.py               # Complete client demo
│   ├── test_simple.py                  # Simple integration test
│   ├── test_speed.py                   # Speed conversion test
│   └── test_audio.py                   # Audio extraction test
│
├── src/                                # 🐍 Source code
│   ├── __init__.py
│   ├── main.py                         # Entry point (asyncio.Queue)
│   ├── main_rabbitmq.py                # Entry point (RabbitMQ)
│   │
│   ├── config/                         # ⚙️ Configuration
│   │   ├── __init__.py
│   │   └── settings.py                 # Pydantic settings
│   │
│   ├── logging/                        # 📝 Logging
│   │   ├── __init__.py
│   │   └── logger.py                   # Structured logging
│   │
│   ├── websocket/                      # 🔌 WebSocket server
│   │   ├── __init__.py
│   │   ├── models.py                   # Pydantic models
│   │   └── server.py                   # WebSocket server
│   │
│   ├── job_manager/                    # 📋 Job management
│   │   ├── __init__.py
│   │   ├── job.py                      # Job model
│   │   ├── manager.py                  # asyncio.Queue manager
│   │   └── rabbitmq_manager.py         # RabbitMQ manager
│   │
│   ├── ffmpeg/                         # 🎬 FFmpeg integration
│   │   ├── __init__.py
│   │   ├── command_builder.py          # Command builder
│   │   ├── runner.py                   # Async executor
│   │   └── metadata.py                 # Metadata extraction
│   │
│   └── utils/                          # 🛠️ Utilities
│       ├── __init__.py
│       └── health.py                   # Health endpoint
│
└── tests/                              # ✅ Unit tests
    ├── __init__.py
    ├── test_models.py                  # Model validation tests
    ├── test_ffmpeg_builder.py          # FFmpeg builder tests
    └── test_job_manager.py             # Job manager tests
```

## Directory Purpose

| Directory | Purpose |
|-----------|---------|
| `docs/` | All documentation (guides, architecture, etc.) |
| `examples/` | Example scripts and integration tests |
| `src/` | Main application source code |
| `tests/` | Unit and integration tests |

## Key Files

| File | Purpose |
|------|---------|
| `README.md` | Main documentation and API reference |
| `pyproject.toml` | Python project configuration |
| `Dockerfile` | Container build instructions |
| `.env` | Environment configuration |
| `Makefile` | Convenience commands |

## Entry Points

| Command | Mode | Description |
|---------|------|-------------|
| `python -m src.main` | asyncio.Queue | In-memory queue (development) |
| `python -m src.main_rabbitmq` | RabbitMQ | Persistent queue (production) |

## Port Usage

| Port | Service |
|------|---------|
| 8080 | WebSocket server |
| 8081 | Health check HTTP endpoint |
| 5672 | RabbitMQ (AMQP) |
| 15672 | RabbitMQ Management UI |

## File Counts

- **Source files**: 20 Python files (~2,500 lines)
- **Documentation**: 7 Markdown files
- **Tests**: 3 test files + 4 example scripts
- **Configuration**: 5 files

## Clean Organization

✅ Documentation separated in `docs/`  
✅ Examples separated in `examples/`  
✅ Source code in `src/`  
✅ Tests in `tests/`  
✅ Root directory clean (only essential files)

# Documentation Index

## Getting Started

1. **[README.md](../README.md)** - Main documentation with API reference
2. **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
3. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide

## Architecture & Design

4. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and technical details
5. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - High-level project overview

## Features

6. **[RABBITMQ_INTEGRATION.md](RABBITMQ_INTEGRATION.md)** - RabbitMQ setup and benefits

## Development

6. **[IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)** - Feature completion status
7. **[TEST_RESULTS.md](TEST_RESULTS.md)** - Test results and validation

## Examples

See the [examples/](../examples/) directory for:
- `client_example.py` - Complete WebSocket client with multiple operations
- `test_simple.py` - Simple integration test
- `test_speed.py` - Speed conversion test
- `test_audio.py` - Audio extraction test

## Quick Links

| Document | Purpose | Audience |
|----------|---------|----------|
| [README](../README.md) | Complete API docs | All users |
| [QUICKSTART](QUICKSTART.md) | Quick setup guide | New users |
| [DEPLOYMENT](DEPLOYMENT.md) | Production deployment | DevOps/SysAdmins |
| [ARCHITECTURE](ARCHITECTURE.md) | System internals | Developers |
| [RABBITMQ_INTEGRATION](RABBITMQ_INTEGRATION.md) | RabbitMQ setup | DevOps |
| [PROJECT_SUMMARY](PROJECT_SUMMARY.md) | Project overview | Managers |

## Documentation Structure

```
doramee/
├── README.md                    # Main documentation (keep in root)
├── docs/                        # All other documentation
│   ├── INDEX.md                 # This file
│   ├── QUICKSTART.md
│   ├── ARCHITECTURE.md
│   ├── PROJECT_SUMMARY.md
│   ├── RABBITMQ_INTEGRATION.md
│   ├── IMPLEMENTATION_CHECKLIST.md
│   └── TEST_RESULTS.md
├── examples/                    # Example scripts and tests
│   ├── client_example.py
│   ├── test_simple.py
│   ├── test_speed.py
│   └── test_audio.py
├── src/                         # Source code
└── tests/                       # Unit tests
```

## Contributing

See individual documents for specific topics. Start with the README for an overview.

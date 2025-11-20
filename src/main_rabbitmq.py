"""Main application entry point with RabbitMQ integration"""

import asyncio
import os
import signal
import sys

from src.config import get_settings
from src.job_manager.rabbitmq_manager import RabbitMQJobManager
from src.logging import get_logger, setup_logging
from src.utils import HealthServer
from src.websocket import WebSocketServer


async def main() -> None:
    """Main application with RabbitMQ"""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    settings = get_settings()
    logger.info("Starting FFmpeg WebSocket Media Processing Service (RabbitMQ Edition)")
    logger.info(f"Configuration: max_concurrent_jobs={settings.max_concurrent_jobs}")

    # Get RabbitMQ URL from environment
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    logger.info(f"RabbitMQ URL: {rabbitmq_url}")

    # Create RabbitMQ job manager
    job_manager = RabbitMQJobManager(rabbitmq_url=rabbitmq_url)

    # Create health server
    health_server = HealthServer(stats_callback=job_manager.get_stats)

    # Create WebSocket server
    ws_server = WebSocketServer(job_manager)

    # Graceful shutdown handler
    shutdown_event = asyncio.Event()

    def signal_handler(sig: int, frame: object) -> None:
        logger.info(f"Received signal {sig}, initiating shutdown...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start services
        await job_manager.start()
        health_server.start()

        # Start WebSocket server (blocks until shutdown)
        ws_task = asyncio.create_task(ws_server.start())

        # Wait for shutdown signal
        await shutdown_event.wait()

        # Cancel WebSocket server
        ws_task.cancel()
        try:
            await ws_task
        except asyncio.CancelledError:
            pass

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        logger.info("Shutting down services...")
        await job_manager.stop()
        health_server.stop()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

"""HTTP health check endpoint"""

import asyncio
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any, Callable, Dict

from src import __version__
from src.config import get_settings
from src.logging import get_logger

logger = get_logger(__name__)


class HealthServer:
    """Simple HTTP server for health checks"""

    def __init__(self, stats_callback: Callable[[], Dict[str, Any]]) -> None:
        self.settings = get_settings()
        self.stats_callback = stats_callback
        self.server: HTTPServer | None = None
        self.thread: Thread | None = None

    def start(self) -> None:
        """Start health check server"""
        logger.info(f"Starting health check server on port {self.settings.health_port}")

        # Create request handler with reference to self
        health_server = self

        class HealthRequestHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                """Suppress request logging"""
                pass

            def do_GET(self) -> None:
                if self.path == "/health":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()

                    stats = health_server.stats_callback()
                    response = {
                        "status": "healthy",
                        "version": __version__,
                        "stats": stats,
                    }

                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

        # Create server
        self.server = HTTPServer(
            (self.settings.ws_host, self.settings.health_port),
            HealthRequestHandler,
        )

        # Run in separate thread
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Stop health check server"""
        if self.server:
            logger.info("Stopping health check server")
            self.server.shutdown()
            self.server.server_close()

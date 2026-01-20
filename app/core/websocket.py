"""
WebSocket Connection Manager

Manages real-time event broadcasting to connected frontend clients.
Implements connection pooling and non-blocking message distribution.
"""

import asyncio
import json
from typing import Set, Dict, Any
from datetime import datetime
from fastapi import WebSocket
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts events to all connected clients.
    
    Thread-safe implementation using asyncio locks for concurrent access.
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket instance
        """
        await websocket.accept()
        
        async with self._lock:
            self.active_connections.add(websocket)
        
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send connection confirmation
        await self._send_to_client(websocket, {
            "type": "connection",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"message": "Connected to KeyChaser event stream"}
        })
    
    async def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection from the active pool.
        
        Args:
            websocket: FastAPI WebSocket instance
        """
        async with self._lock:
            self.active_connections.discard(websocket)
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcast an event to all connected clients (non-blocking).
        
        Args:
            event_type: Event type identifier (e.g., "new_beacon", "new_log")
            data: Event payload dictionary
        """
        if not self.active_connections:
            return  # No clients connected
        
        message = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Create broadcast tasks for all connections
        tasks = []
        async with self._lock:
            connections_snapshot = list(self.active_connections)
        
        for connection in connections_snapshot:
            tasks.append(self._send_to_client(connection, message))
        
        # Execute all sends concurrently without blocking
        if tasks:
            asyncio.create_task(self._execute_broadcasts(tasks))
    
    async def _execute_broadcasts(self, tasks):
        """
        Execute broadcast tasks and handle disconnections.
        
        Args:
            tasks: List of send coroutines
        """
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for failed sends (disconnected clients)
        for result in results:
            if isinstance(result, Exception):
                logger.debug(f"Broadcast send failed: {result}")
    
    async def _send_to_client(self, websocket: WebSocket, message: Dict):
        """
        Send a message to a single WebSocket client.
        
        Args:
            websocket: Target WebSocket
            message: Message dictionary
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send to client: {e}")
            # Remove disconnected client
            await self.disconnect(websocket)
            raise
    
    def get_connection_count(self) -> int:
        """Get the number of active WebSocket connections."""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """
    Get the global WebSocket connection manager.
    
    Returns:
        ConnectionManager instance
    """
    return manager

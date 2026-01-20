"""
KeyChaser - Main Entry Point

This module initializes the FastAPI application, loads protocol handlers,
and starts concurrent asyncio tasks for both the web dashboard and
malware protocol listeners.
"""

import asyncio
import importlib
import inspect
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.database import close_db, get_session_factory, init_db
from app.core.logging import get_logger
from app.core.websocket import get_connection_manager
from app.protocols.base import ProtocolHandler

logger = get_logger(__name__)


def load_protocol_handlers() -> List[ProtocolHandler]:
    """
    Dynamically load protocol handlers from the protocols directory.
    
    Scans for Python modules in app/protocols/ and instantiates any
    classes that inherit from ProtocolHandler.
    
    Returns:
        List of instantiated protocol handler objects
    """
    handlers = []
    db_factory = get_session_factory()
    
    protocols_path = Path(__file__).parent / "protocols"
    
    logger.info(f"Loading protocol handlers from {protocols_path}")
    
    for protocol_file in protocols_path.glob("*.py"):
        # Skip base class and utilities
        if protocol_file.stem in ["__init__", "base", "utils"]:
            continue
        
        # Check if this protocol is enabled
        if protocol_file.stem not in settings.enabled_protocols:
            logger.info(f"Skipping disabled protocol: {protocol_file.stem}")
            continue
        
        try:
            # Import the module
            module_name = f"app.protocols.{protocol_file.stem}"
            module = importlib.import_module(module_name)
            
            # Find ProtocolHandler subclasses
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, ProtocolHandler) and 
                    obj is not ProtocolHandler and
                    obj.__module__ == module_name):
                    
                    # Instantiate handler
                    handler = obj(db_factory)
                    handlers.append(handler)
                    logger.info(f"Loaded protocol handler: {handler.name} on port {handler.port}")
            
        except Exception as e:
            logger.error(f"Failed to load protocol handler {protocol_file.stem}: {e}", exc_info=True)
    
    return handlers


async def start_protocol_listener(handler: ProtocolHandler) -> None:
    """
    Start an asyncio TCP server for a protocol handler.
    
    Args:
        handler: Protocol handler instance
    """
    try:
        server = await asyncio.start_server(
            handler.handle_connection,
            host=settings.host,
            port=handler.port,
            reuse_address=True,
            reuse_port=True if sys.platform != "win32" else False,
        )
        
        addr = server.sockets[0].getsockname()
        logger.info(f"[{handler.name}] Listening on {addr[0]}:{addr[1]}")
        
        async with server:
            await server.serve_forever()
            
    except Exception as e:
        logger.error(f"[{handler.name}] Failed to start listener: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize database, load handlers, start listeners
    - Shutdown: Close database connections, cleanup resources
    """
    # Startup
    logger.info("=" * 60)
    logger.info("KeyChaser - Malware C2 Sinkhole Starting...")
    logger.info("=" * 60)
    
    # Initialize database
    await init_db()
    
    # Load protocol handlers
    handlers = load_protocol_handlers()
    
    if not handlers:
        logger.warning("No protocol handlers loaded! Sinkhole will only serve dashboard.")
    else:
        logger.info(f"Loaded {len(handlers)} protocol handler(s)")
    
    # Start protocol listeners as background tasks
    listener_tasks = []
    for handler in handlers:
        task = asyncio.create_task(start_protocol_listener(handler))
        listener_tasks.append(task)
        logger.info(f"Started listener for {handler.name} on port {handler.port}")
    
    # Store tasks in app state for cleanup
    app.state.listener_tasks = listener_tasks
    app.state.handlers = handlers
    
    logger.info("=" * 60)
    logger.info(f"Dashboard available at http://{settings.host}:{settings.api_port}")
    logger.info("KeyChaser is ready to intercept malware traffic!")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down KeyChaser...")
    
    # Cancel listener tasks
    for task in listener_tasks:
        task.cancel()
    
    # Wait for tasks to complete
    await asyncio.gather(*listener_tasks, return_exceptions=True)
    
    # Close database
    await close_db()
    
    logger.info("KeyChaser shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="KeyChaser",
    description="Advanced Malware C2 Sinkhole and Traffic Emulation Framework",
    version=settings.app_version,
    lifespan=lifespan,
)

# Mount static files (CSS, JS)
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Setup Jinja2 templates
templates_path = Path(__file__).parent / "templates"
templates_path.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_path))

# Register API routers
from app.api import bots, logs, stats, auth

app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(bots.router, prefix="/api", tags=["bots"])
app.include_router(logs.router, prefix="/api", tags=["logs"])
app.include_router(stats.router, prefix="/api", tags=["stats"])


@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming to frontend.
    
    Clients connect to receive live updates about:
    - New bot connections (new_beacon)
    - New log entries (new_log)
    - New credentials (new_credential)
    """
    manager = get_connection_manager()
    await manager.connect(websocket)
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            # Wait for messages from client (ping/pong, etc.)
            data = await websocket.receive_text()
            # Echo back (optional)
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


@app.get("/")
async def dashboard(request):
    """Render main dashboard."""
    from fastapi import Request
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "settings": settings}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "handlers": len(getattr(app.state, "handlers", [])),
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info",
    )

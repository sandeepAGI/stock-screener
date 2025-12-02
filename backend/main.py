"""
StockAnalyzer Pro - FastAPI Backend
Main application entry point
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Set
import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import get_database_connection
from backend.models.schemas import HealthResponse
from backend.api import (
    stocks_router,
    rankings_router,
    data_router,
    sentiment_router,
    calculate_router,
)

# Create FastAPI app
app = FastAPI(
    title="StockAnalyzer Pro API",
    description="REST API for stock analysis with composite scoring",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS for Electron frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for desktop app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stocks_router)
app.include_router(rankings_router)
app.include_router(data_router)
app.include_router(sentiment_router)
app.include_router(calculate_router)


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)


manager = ConnectionManager()


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_connected = False
    try:
        db = get_database_connection()
        db_connected = db.connection is not None
        db.close()
    except Exception:
        pass

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        database_connected=db_connected,
        version="1.0.0",
        timestamp=datetime.now()
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "StockAnalyzer Pro API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health",
    }


@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                # Handle ping/pong for keepalive
                if data == "ping":
                    await websocket.send_text("pong")

                # Handle status requests
                elif data == "status":
                    # Import status from other modules
                    from backend.api.data import _refresh_status
                    from backend.api.sentiment import _sentiment_status
                    from backend.api.calculate import _calculation_status

                    await websocket.send_json({
                        "type": "status",
                        "data_refresh": _refresh_status,
                        "sentiment": _sentiment_status,
                        "calculation": _calculation_status,
                    })

            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_text("ping")

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Helper function to broadcast progress updates (can be imported by other modules)
async def broadcast_progress(progress_type: str, data: dict):
    """Broadcast progress update to all WebSocket clients"""
    await manager.broadcast({
        "type": progress_type,
        "timestamp": datetime.now().isoformat(),
        **data
    })


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("StockAnalyzer Pro API starting...")

    # Verify database connection
    try:
        db = get_database_connection()
        stocks_count = len(db.get_all_stocks())
        db.close()
        print(f"Database connected. {stocks_count} active stocks found.")
    except Exception as e:
        print(f"Warning: Database connection issue: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("StockAnalyzer Pro API shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

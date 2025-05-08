import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create the FastAPI application"""
    app = FastAPI(
        title="BlockPlain RAG API",
        description="API for querying BlockPlain blockchain data using RAG",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(router)
    
    return app

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server"""
    app = create_app()
    logger.info(f"Starting API server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
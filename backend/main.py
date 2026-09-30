"""
FastAPI Server Entrypoint for AI Discovery Engine ("Retrieval Lens")
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import router as api_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("RetrievalLensServer")

app = FastAPI(
    title="Retrieval Lens API",
    description="Backend REST API powering the Google Photos Retrieval Discovery Engine",
    version="2.0.0"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)


@app.get("/")
def health_check():
    return {
        "product": "Retrieval Lens - AI Discovery Engine",
        "status": "online",
        "version": "2.0.0",
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting Retrieval Lens FastAPI server on {host}:{port}...")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)

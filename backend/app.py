"""
FastAPI main application.
Entry point for the exam submission backend.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
import logging

from backend.routes import submit, success
from backend.utils.logger import setup_logging, get_logger

# Setup logging
log_file = setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Exam Submission API",
    description="API for submitting exam answers",
    version="1.0.0"
)

# CORS middleware - allow all origins for development
# In production, configure specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(submit.router)
app.include_router(success.router)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An internal server error occurred",
            "error_code": "internal_error"
        }
    )


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("=" * 80)
    logger.info("Starting Exam Submission API")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 80)
    
    # Ensure logs directory exists
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    logger.info(f"Logs directory: {logs_dir}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Exam Submission API")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Exam Submission API",
        "version": "1.0.0",
        "endpoints": {
            "submit": "/submit_exam",
            "success": "/success"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server with uvicorn...")
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


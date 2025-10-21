"""
FastAPI Service for Data Pipeline
Provides REST API for pipeline control and monitoring
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from .config import settings
from .pipeline import DataPipeline

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global pipeline instance
pipeline: Optional[DataPipeline] = None
pipeline_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    global pipeline
    logger.info("Starting Data Pipeline Service...")

    # Initialize pipeline
    pipeline = DataPipeline()

    # Start pipeline in background (optional auto-start)
    # Uncomment to auto-start on service launch:
    # asyncio.create_task(run_pipeline_async())

    yield

    # Cleanup on shutdown
    logger.info("Shutting down Data Pipeline Service...")
    if pipeline:
        pipeline.stop()


app = FastAPI(
    title="Bioprocess Data Pipeline API",
    description="Real-time data cleaning, feature engineering, and monitoring",
    version="0.1.0",
    lifespan=lifespan,
)


# Pydantic models for API
class PipelineStatus(BaseModel):
    is_running: bool
    cycle_count: int
    quality_stats: Dict[str, int]
    uptime_seconds: Optional[float] = None


class FeatureResponse(BaseModel):
    timestamp: str
    features: Dict[str, float]
    feature_count: int


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    version: str


# API Endpoints

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        service="data-pipeline",
        version="0.1.0",
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check"""
    return HealthResponse(
        status="healthy" if pipeline is not None else "initializing",
        timestamp=datetime.utcnow().isoformat(),
        service="data-pipeline",
        version="0.1.0",
    )


@app.get("/status", response_model=PipelineStatus)
async def get_status():
    """Get current pipeline status"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    return PipelineStatus(
        is_running=pipeline.is_running,
        cycle_count=pipeline.cycle_count,
        quality_stats=pipeline.cleaner.get_quality_stats(),
    )


@app.post("/start")
async def start_pipeline(background_tasks: BackgroundTasks):
    """Start the data pipeline"""
    global pipeline_task

    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    if pipeline.is_running:
        return {"message": "Pipeline is already running", "cycle_count": pipeline.cycle_count}

    # Run pipeline in background
    pipeline_task = asyncio.create_task(run_pipeline_async())

    return {
        "message": "Pipeline started",
        "interval_seconds": settings.processing_interval_seconds,
    }


@app.post("/stop")
async def stop_pipeline():
    """Stop the data pipeline"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    if not pipeline.is_running:
        return {"message": "Pipeline is not running"}

    pipeline.stop()

    return {
        "message": "Pipeline stopped",
        "total_cycles": pipeline.cycle_count,
        "quality_stats": pipeline.cleaner.get_quality_stats(),
    }


@app.post("/process-window")
async def process_single_window():
    """Process a single 30-second window (manual trigger)"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    features = pipeline.process_window()

    if features is None:
        raise HTTPException(status_code=500, detail="Window processing failed")

    return FeatureResponse(
        timestamp=datetime.utcnow().isoformat(),
        features=features,
        feature_count=len(features),
    )


@app.post("/reset")
async def reset_pipeline():
    """Reset pipeline state for a new batch"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    pipeline.reset_batch()

    return {
        "message": "Pipeline reset for new batch",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/quality-stats")
async def get_quality_stats():
    """Get cumulative data quality statistics"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    stats = pipeline.cleaner.get_quality_stats()

    return {
        "stats": stats,
        "total_cycles": pipeline.cycle_count,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/config")
async def get_config():
    """Get current pipeline configuration"""
    return {
        "window_size_seconds": settings.window_size_seconds,
        "processing_interval_seconds": settings.processing_interval_seconds,
        "vessel_id": settings.vessel_id,
        "influx_bucket_raw": settings.influx_bucket_raw,
        "influx_bucket_30s": settings.influx_bucket_30s,
        "influx_bucket_pred": settings.influx_bucket_pred,
        "physical_bounds": settings.physical_bounds,
    }


# Async helper functions

async def run_pipeline_async():
    """Run pipeline in async context"""
    try:
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, pipeline.run_continuous)
    except Exception as e:
        logger.error(f"Pipeline async error: {e}", exc_info=True)


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level=settings.log_level.lower(),
    )

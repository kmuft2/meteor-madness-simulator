"""
Main FastAPI application for Meteor Madness Simulator
NASA Space Apps Challenge 2025
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api.routes import simulation, nasa_data, usgs_data, real_asteroids, gee_routes, earthquake_comparison

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Meteor Madness Simulator API",
    description="Interactive asteroid impact visualization and simulation tool using NASA and USGS data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(simulation.router, prefix="/api")
app.include_router(nasa_data.router, prefix="/api")
app.include_router(usgs_data.router, prefix="/api")
app.include_router(gee_routes.router, prefix="/api")
app.include_router(real_asteroids.router, prefix="/api")
app.include_router(earthquake_comparison.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Meteor Madness Simulator API",
        "version": "1.0.0",
        "description": "NASA Space Apps Challenge 2025",
        "endpoints": {
            "docs": "/docs",
            "simulation": "/api/simulation",
            "nasa_data": "/api/nasa",
            "usgs_data": "/api/usgs",
            "gee_data": "/api/gee"
        },
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "cuda_available": False,  # Will be updated by physics engine
        "apis": {
            "nasa_neo": "configured",
            "nasa_sbdb": "configured",
            "usgs_earthquake": "configured"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("=" * 60)
    logger.info("Meteor Madness Simulator API Starting")
    logger.info("=" * 60)
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"NASA API configured: {bool(settings.nasa_api_key)}")
    logger.info(f"USGS API configured: {bool(settings.usgs_earthquake_api_url)}")
    
    # Check CUDA availability
    try:
        from app.physics.impact_physics import EnhancedPhysicsEngine
        engine = EnhancedPhysicsEngine()
        if engine.device_available:
            logger.info("✅ CUDA GPU available for physics calculations")
        else:
            logger.info("ℹ️ Using CPU for physics calculations")
    except Exception as e:
        logger.warning(f"Physics engine check failed: {e}")
    
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("Meteor Madness Simulator API shutting down")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )

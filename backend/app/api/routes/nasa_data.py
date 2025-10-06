"""
NASA data API routes for asteroid information
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta

from app.services.nasa.official_apis import OfficialNASAAPIService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nasa", tags=["nasa-data"])


@router.get("/neo/recent")
async def get_recent_neos(days: int = Query(default=3, ge=1, le=7)) -> Dict:
    """
    Get recent Near-Earth Objects from NASA NEO API
    
    Args:
        days: Number of days to look back (1-7)
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        async with OfficialNASAAPIService(
            settings.nasa_api_key,
            settings.nasa_neo_api_url,
            settings.nasa_sbdb_api_url
        ) as nasa:
            data = await nasa.get_neo_feed_official(start_date, end_date)
            
        return {
            "status": "success",
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "data": data
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch recent NEOs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch NEO data: {str(e)}")


@router.get("/neo/stats")
async def get_neo_stats() -> Dict:
    """
    Get overall NEO statistics from NASA
    """
    try:
        # Use urllib directly for simple GET
        import urllib.request as request
        import json
        
        url = f"https://api.nasa.gov/neo/rest/v1/stats?api_key={settings.nasa_api_key}"
        
        with request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        return {
            "status": "success",
            "data": data
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch NEO stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


@router.get("/neo/hazardous")
async def get_hazardous_asteroids(limit: int = Query(default=20, ge=1, le=100)) -> Dict:
    """
    Get potentially hazardous asteroids from NASA
    
    Args:
        limit: Maximum number of asteroids to return
    """
    try:
        async with OfficialNASAAPIService(
            settings.nasa_api_key,
            settings.nasa_neo_api_url,
            settings.nasa_sbdb_api_url
        ) as nasa:
            phas = await nasa.get_potentially_hazardous_asteroids(limit)
        
        return {
            "status": "success",
            "count": len(phas),
            "asteroids": phas
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch hazardous asteroids: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


@router.get("/sbdb/{asteroid_id}")
async def get_asteroid_details(asteroid_id: str) -> Dict:
    """
    Get detailed orbital and physical parameters for a specific asteroid
    from NASA Small-Body Database
    
    Args:
        asteroid_id: NASA asteroid ID or designation
    """
    try:
        async with OfficialNASAAPIService(
            settings.nasa_api_key,
            settings.nasa_neo_api_url,
            settings.nasa_sbdb_api_url
        ) as nasa:
            details = await nasa.get_sbdb_asteroid_details(asteroid_id)
        
        if not details:
            raise HTTPException(status_code=404, detail=f"Asteroid {asteroid_id} not found")
        
        return {
            "status": "success",
            "asteroid_id": asteroid_id,
            "data": details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch asteroid details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch details: {str(e)}")

"""
USGS data API routes for earthquake correlation
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
import logging

from app.services.usgs.earthquake_service import USGSEarthquakeService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/usgs", tags=["usgs-data"])


@router.get("/earthquakes/recent")
async def get_recent_earthquakes(
    min_magnitude: float = Query(default=6.0, ge=0, le=10),
    limit: int = Query(default=20, ge=1, le=100)
) -> Dict:
    """
    Get recent major earthquakes from USGS
    
    Args:
        min_magnitude: Minimum earthquake magnitude
        limit: Maximum number of results
    """
    try:
        async with USGSEarthquakeService(settings.usgs_earthquake_api_url) as usgs:
            earthquakes = await usgs.get_reference_earthquakes(
                min_magnitude=min_magnitude,
                max_magnitude=9.5,
                limit=limit
            )
        
        return {
            "status": "success",
            "count": len(earthquakes),
            "earthquakes": earthquakes
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch earthquakes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


@router.get("/seismic/magnitude/{energy_joules}")
async def convert_energy_to_magnitude(energy_joules: float) -> Dict:
    """
    Convert impact energy to equivalent seismic magnitude
    
    Args:
        energy_joules: Impact energy in joules
    """
    try:
        usgs = USGSEarthquakeService(settings.usgs_earthquake_api_url)
        
        magnitude_data = usgs.impact_energy_to_seismic_magnitude(energy_joules)
        damage_scale = usgs.get_earthquake_damage_description(
            magnitude_data['equivalent_magnitude']
        )
        
        return {
            "status": "success",
            "input_energy_joules": energy_joules,
            "magnitude_data": magnitude_data,
            "damage_scale": damage_scale
        }
        
    except Exception as e:
        logger.error(f"Failed to convert energy: {e}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.get("/seismic/similar/{magnitude}")
async def find_similar_earthquakes(
    magnitude: float,
    tolerance: float = Query(default=0.5, ge=0.1, le=2.0)
) -> Dict:
    """
    Find historical earthquakes with similar magnitude
    
    Args:
        magnitude: Target earthquake magnitude
        tolerance: Magnitude tolerance for matching
    """
    try:
        async with USGSEarthquakeService(settings.usgs_earthquake_api_url) as usgs:
            similar = await usgs.find_similar_magnitude_earthquakes(magnitude, tolerance)
        
        return {
            "status": "success",
            "target_magnitude": magnitude,
            "tolerance": tolerance,
            "count": len(similar),
            "earthquakes": similar
        }
        
    except Exception as e:
        logger.error(f"Failed to find similar earthquakes: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

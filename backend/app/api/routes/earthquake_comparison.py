"""
API endpoints for earthquake comparison with asteroid impacts
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.usgs.earthquake_cache import get_earthquake_cache

router = APIRouter()


class EarthquakeComparison(BaseModel):
    """Response model for earthquake comparisons"""
    similar_earthquakes: List[Dict]
    famous_earthquakes: List[Dict]
    magnitude_range_stats: Dict
    interpretation: str


@router.get("/compare-to-earthquakes", response_model=EarthquakeComparison)
async def compare_to_earthquakes(
    magnitude: float,
    tolerance: float = 0.5
):
    """
    Compare an asteroid impact to historical earthquakes by seismic magnitude
    
    Args:
        magnitude: Seismic magnitude (Richter scale equivalent) of asteroid impact
        tolerance: +/- tolerance for finding similar earthquakes (default 0.5)
    
    Returns:
        Similar historical earthquakes and context
    """
    try:
        cache = get_earthquake_cache()
        
        # Find similar earthquakes
        similar = cache.find_similar_magnitude(magnitude, tolerance)
        
        # Get famous earthquakes for context
        famous = cache.get_famous_earthquakes()
        
        # Get statistics for the magnitude range
        stats = cache.get_magnitude_range_stats(
            magnitude - tolerance,
            magnitude + tolerance
        )
        
        # Generate human-readable interpretation
        interpretation = _generate_interpretation(magnitude, similar, famous)
        
        return EarthquakeComparison(
            similar_earthquakes=similar,
            famous_earthquakes=famous,
            magnitude_range_stats=stats,
            interpretation=interpretation
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/famous-earthquakes")
async def get_famous_earthquakes():
    """
    Get list of famous historical earthquakes for comparison
    
    Returns:
        List of historically significant earthquakes
    """
    try:
        cache = get_earthquake_cache()
        return {
            "famous_earthquakes": cache.get_famous_earthquakes()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/magnitude-range-stats")
async def get_magnitude_range_stats(min_mag: float, max_mag: float):
    """
    Get statistics for earthquakes in a magnitude range
    
    Args:
        min_mag: Minimum magnitude
        max_mag: Maximum magnitude
    
    Returns:
        Statistics about earthquakes in that range
    """
    try:
        cache = get_earthquake_cache()
        return cache.get_magnitude_range_stats(min_mag, max_mag)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _generate_interpretation(
    magnitude: float,
    similar: List[Dict],
    famous: List[Dict]
) -> str:
    """Generate human-readable interpretation of the comparison"""
    
    if magnitude < 5.0:
        comparison = "This impact would be comparable to a minor earthquake, likely not felt by most people."
    elif magnitude < 6.0:
        comparison = "This impact would be comparable to a moderate earthquake, potentially causing local damage."
    elif magnitude < 7.0:
        comparison = "This impact would be comparable to a strong earthquake, causing significant regional damage."
    elif magnitude < 8.0:
        comparison = "This impact would be comparable to a major earthquake, causing widespread severe damage."
    elif magnitude < 9.0:
        comparison = "This impact would be comparable to a great earthquake, one of the most destructive events possible."
    else:
        comparison = "This impact would exceed the strongest earthquakes ever recorded, causing catastrophic global effects."
    
    # Add specific comparison if we found similar earthquakes
    if similar:
        top_eq = similar[0]
        comparison += f"\n\nSimilar to the {top_eq['location']} earthquake ({top_eq['year']})"
        if top_eq.get('historical_context'):
            comparison += f": {top_eq['historical_context']}"
        
        if top_eq.get('tsunami'):
            comparison += "\n⚠️ WARNING: This magnitude could trigger tsunamis in coastal impacts."
    
    # Reference famous earthquakes for context
    if magnitude >= 8.0:
        relevant_famous = [eq for eq in famous if abs(eq['magnitude'] - magnitude) < 1.0]
        if relevant_famous:
            comparison += f"\n\nThis is comparable in magnitude to devastating events like:"
            for eq in relevant_famous[:3]:
                comparison += f"\n  • {eq['context']}"
    
    return comparison


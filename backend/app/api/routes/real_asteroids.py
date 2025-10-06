"""
Real asteroid data from official NASA APIs
Implements requirements from NASA Space Apps Challenge 2025
"""

from fastapi import APIRouter, HTTPException, Query
import aiohttp
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nasa", tags=["nasa-real-data"])

# NASA API Configuration
NASA_SBDB_URL = "https://ssd-api.jpl.nasa.gov/sbdb.api"
NASA_NEO_URL = "https://api.nasa.gov/neo/rest/v1"
NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")

# Common asteroid name to designation mapping
ASTEROID_MAP = {
    "apophis": "99942",
    "bennu": "101955",
    "eros": "433",
    "itokawa": "25143",
    "ryugu": "162173",
    "didymos": "65803"
}


@router.get("/asteroid/{name}")
async def get_real_asteroid_data(name: str) -> Dict:
    """
    Fetch real asteroid data from official NASA SBDB
    
    Args:
        name: Asteroid name or designation (e.g., "apophis", "99942")
    
    Returns:
        Complete orbital elements and physical parameters from NASA
    """
    try:
        # Convert name to designation if needed
        designation = ASTEROID_MAP.get(name.lower(), name)
        
        params = {
            "sstr": designation,
            "full-prec": "true",  # Full precision orbital elements
            "phys-par": "true",   # Physical parameters
            "cov": "mat"          # Request covariance matrix in full form
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(NASA_SBDB_URL, params=params, timeout=10) as response:
                if response.status != 200:
                    logger.error(f"NASA SBDB API returned {response.status}")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"NASA SBDB API error: {response.status}"
                    )
                
                data = await response.json()
        
        # Process and structure the data
        result = _process_sbdb_response(data)
        
        logger.info(f"Successfully fetched data for asteroid: {result['name']}")
        return result
        
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching asteroid data: {e}")
        raise HTTPException(status_code=503, detail="NASA API unavailable")
    except Exception as e:
        logger.error(f"Error processing asteroid data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/potentially-hazardous")
async def get_potentially_hazardous_asteroids(
    limit: int = Query(default=50, ge=1, le=100)
) -> Dict:
    """
    Fetch list of Potentially Hazardous Asteroids from NASA NEO API
    
    Args:
        limit: Maximum number of PHAs to return
    
    Returns:
        List of PHAs with orbital and physical data
    """
    try:
        params = {
            "is_potentially_hazardous_asteroid": "true",
            "api_key": NASA_API_KEY
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{NASA_NEO_URL}/neo/browse",
                params=params,
                timeout=15
            ) as response:
                if response.status != 200:
                    logger.error(f"NASA NEO API returned {response.status}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"NASA NEO API error: {response.status}"
                    )
                
                data = await response.json()
        
        # Process PHA data
        phas = []
        for neo in data.get("near_earth_objects", [])[:limit]:
            pha_data = {
                "id": neo.get("id"),
                "name": neo.get("name", "Unknown"),
                "nasa_jpl_url": neo.get("nasa_jpl_url"),
                "absolute_magnitude_h": float(neo.get("absolute_magnitude_h", 0)),
                "diameter_min_m": float(
                    neo.get("estimated_diameter", {})
                    .get("meters", {})
                    .get("estimated_diameter_min", 0)
                ),
                "diameter_max_m": float(
                    neo.get("estimated_diameter", {})
                    .get("meters", {})
                    .get("estimated_diameter_max", 0)
                ),
                "is_potentially_hazardous": True,
                "close_approaches": [],
                "data_source": "NASA_NEO_API_Official"
            }
            
            # Extract close approach data
            for approach in neo.get("close_approach_data", [])[:3]:  # Last 3 approaches
                pha_data["close_approaches"].append({
                    "date": approach.get("close_approach_date_full"),
                    "velocity_km_s": float(
                        approach.get("relative_velocity", {})
                        .get("kilometers_per_second", 0)
                    ),
                    "miss_distance_km": float(
                        approach.get("miss_distance", {})
                        .get("kilometers", 0)
                    ),
                    "miss_distance_lunar": float(
                        approach.get("miss_distance", {})
                        .get("lunar", 0)
                    )
                })
            
            phas.append(pha_data)
        
        logger.info(f"Retrieved {len(phas)} potentially hazardous asteroids")
        
        return {
            "count": len(phas),
            "phas": phas,
            "data_source": "NASA_NEO_API_Official",
            "api_credit": "NASA/JPL Near-Earth Object Program"
        }
        
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching PHAs: {e}")
        raise HTTPException(status_code=503, detail="NASA API unavailable")
    except Exception as e:
        logger.error(f"Error processing PHA data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/asteroid/{name}/orbital-elements")
async def get_orbital_elements(name: str) -> Dict:
    """
    Get just the Keplerian orbital elements for an asteroid
    
    Args:
        name: Asteroid name or designation
    
    Returns:
        Keplerian orbital elements for trajectory calculation
    """
    full_data = await get_real_asteroid_data(name)
    
    return {
        "name": full_data["name"],
        "orbital_elements": full_data["orbital_elements"],
        "data_source": "NASA_SBDB_Official"
    }


def _process_sbdb_response(data: Dict) -> Dict:
    """
    Extract and format data from NASA SBDB response
    
    Args:
        data: Raw response from NASA SBDB API
    
    Returns:
        Structured asteroid data
    """
    # Extract object info
    obj = data.get("object", {})
    
    # Extract orbital elements
    orbit = data.get("orbit", {})
    elements_raw = {elem["name"]: elem["value"] 
                   for elem in orbit.get("elements", [])}
    
    orbital_elements = {
        "semi_major_axis_au": float(elements_raw.get("a", 0)),
        "eccentricity": float(elements_raw.get("e", 0)),
        "inclination_deg": float(elements_raw.get("i", 0)),
        "longitude_ascending_node_deg": float(elements_raw.get("om", 0)),
        "argument_periapsis_deg": float(elements_raw.get("w", 0)),
        "mean_anomaly_deg": float(elements_raw.get("ma", 0)),
        "orbital_period_days": float(elements_raw.get("per", 0)),
        "perihelion_distance_au": float(elements_raw.get("q", 0)),
        "aphelion_distance_au": float(elements_raw.get("ad", 0))
    }
    
    # Extract physical parameters
    phys_params = {param["name"]: param.get("value", 0) 
                  for param in data.get("phys_par", [])}
    
    physical_parameters = {
        "absolute_magnitude_H": float(phys_params.get("H", 0)),
        "diameter_km": float(phys_params.get("diameter", 0)),
        "albedo": float(phys_params.get("albedo", 0.14)),  # Default 0.14 for C-type
        "rotation_period_hours": float(phys_params.get("rot_per", 0)) if "rot_per" in phys_params else None
    }
    
    # Extract close approach data
    close_approaches = []
    for ca in data.get("close_approach_data", [])[:5]:  # Last 5 approaches
        close_approaches.append({
            "date": ca.get("cd", ""),
            "distance_au": float(ca.get("dist", 0)),
            "distance_km": float(ca.get("dist", 0)) * 149597870.7,  # AU to km
            "velocity_km_s": float(ca.get("v_rel", 0))
        })
    
    covariance = _extract_covariance(orbit)

    return {
        "object_id": obj.get("des", ""),
        "name": obj.get("fullname", "Unknown"),
        "is_potentially_hazardous": obj.get("pha", False),
        "orbital_elements": orbital_elements,
        "physical_parameters": physical_parameters,
        "close_approaches": close_approaches,
        "orbit_class": orbit.get("orbit_class", {}).get("name", "Unknown"),
        "orbit_class_code": orbit.get("orbit_class", {}).get("code", ""),
        "covariance": covariance,
        "data_source": "NASA_SBDB_Official",
        "jpl_url": f"https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={obj.get('des', '')}"
    }


def _extract_covariance(orbit: Dict) -> Optional[Dict]:
    """Extract covariance matrix information from SBDB orbit section."""
    cov = orbit.get("covariance")
    if not cov:
        return None

    return {
        "matrix": cov.get("data"),
        "labels": cov.get("labels", []),
        "epoch_jd": cov.get("epoch"),
        "elements": cov.get("elements")
    }


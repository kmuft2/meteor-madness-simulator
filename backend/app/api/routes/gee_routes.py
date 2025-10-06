"""
Google Earth Engine API Routes
FastAPI endpoints for GEE data access
NASA Space Apps Challenge 2025 - Meteor Madness
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.services.gee_service import GoogleEarthEngineService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gee", tags=["Google Earth Engine"])

# Initialize GEE service
gee_service = GoogleEarthEngineService()


# Request/Response Models

class LocationRequest(BaseModel):
    """Base location request model"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    radius_km: float = Field(5.0, gt=0, le=100, description="Radius in kilometers")


class ElevationRequest(LocationRequest):
    """Request model for elevation data"""
    dataset: str = Field("USGS/SRTMGL1_003", description="GEE dataset ID")


class PopulationRequest(LocationRequest):
    """Request model for population data"""
    dataset: str = Field("WorldPop/GP/100m/pop", description="GEE dataset ID")


class LandCoverRequest(LocationRequest):
    """Request model for land cover data"""
    dataset: str = Field("ESRI_Global_LULC_10m", description="GEE dataset ID")


class UrbanRequest(LocationRequest):
    """Request model for urban data"""
    dataset: str = Field("JRC/GHSL/P2023A/GHS_BUILT", description="GEE dataset ID")


class WaterRequest(LocationRequest):
    """Request model for water data"""
    dataset: str = Field("JRC/GSW1_4/GlobalSurfaceWater", description="GEE dataset ID")


class AffectedPopulationRequest(BaseModel):
    """Request model for affected population calculation"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    damage_radii_km: List[float] = Field(..., description="List of damage radii in km")


# Routes

@router.post("/elevation")
async def get_elevation_data(request: ElevationRequest):
    """
    Get SRTM elevation data for a region
    
    - **latitude**: Center latitude (-90 to 90)
    - **longitude**: Center longitude (-180 to 180)
    - **radius_km**: Radius in kilometers (default: 5km, max: 100km)
    - **dataset**: GEE dataset ID (default: USGS/SRTMGL1_003)
    
    Returns elevation data including values, min/max, and mean elevation.
    """
    try:
        logger.info(f"Fetching elevation data for ({request.latitude}, {request.longitude}), radius: {request.radius_km}km")
        
        data = await gee_service.get_elevation_data(
            request.latitude,
            request.longitude,
            request.radius_km
        )
        
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching elevation data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch elevation data: {str(e)}")


@router.post("/population")
async def get_population_data(request: PopulationRequest):
    """
    Get population density data from WorldPop
    
    - **latitude**: Center latitude
    - **longitude**: Center longitude
    - **radius_km**: Radius in kilometers
    - **dataset**: GEE dataset ID (default: WorldPop/GP/100m/pop)
    
    Returns population density data including total population and density.
    """
    try:
        logger.info(f"Fetching population data for ({request.latitude}, {request.longitude}), radius: {request.radius_km}km")
        
        data = await gee_service.get_population_data(
            request.latitude,
            request.longitude,
            request.radius_km
        )
        
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching population data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch population data: {str(e)}")


@router.post("/landcover")
async def get_landcover_data(request: LandCoverRequest):
    """
    Get land cover data from ESRI 10m dataset
    
    - **latitude**: Center latitude
    - **longitude**: Center longitude
    - **radius_km**: Radius in kilometers
    - **dataset**: GEE dataset ID
    
    Returns land cover classification data.
    """
    try:
        logger.info(f"Fetching land cover data for ({request.latitude}, {request.longitude}), radius: {request.radius_km}km")
        
        data = await gee_service.get_landcover_data(
            request.latitude,
            request.longitude,
            request.radius_km
        )
        
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching land cover data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch land cover data: {str(e)}")


@router.post("/urban")
async def get_urban_data(request: UrbanRequest):
    """
    Get urban built-up areas from GHSL dataset
    
    - **latitude**: Center latitude
    - **longitude**: Center longitude
    - **radius_km**: Radius in kilometers
    - **dataset**: GEE dataset ID
    
    Returns urban built-up area data.
    """
    try:
        logger.info(f"Fetching urban data for ({request.latitude}, {request.longitude}), radius: {request.radius_km}km")
        
        data = await gee_service.get_urban_data(
            request.latitude,
            request.longitude,
            request.radius_km
        )
        
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching urban data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch urban data: {str(e)}")


@router.post("/water")
async def get_water_data(request: WaterRequest):
    """
    Get surface water data from JRC Global Surface Water
    
    - **latitude**: Center latitude
    - **longitude**: Center longitude
    - **radius_km**: Radius in kilometers
    - **dataset**: GEE dataset ID
    
    Returns surface water occurrence data.
    """
    try:
        logger.info(f"Fetching water data for ({request.latitude}, {request.longitude}), radius: {request.radius_km}km")
        
        data = await gee_service.get_water_data(
            request.latitude,
            request.longitude,
            request.radius_km
        )
        
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching water data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch water data: {str(e)}")


@router.post("/affected-population")
async def calculate_affected_population(request: AffectedPopulationRequest):
    """
    Calculate affected population in multiple damage zones
    
    - **latitude**: Impact latitude
    - **longitude**: Impact longitude
    - **damage_radii_km**: List of damage radii in kilometers
    
    Returns population affected in each zone.
    """
    try:
        logger.info(f"Calculating affected population for impact at ({request.latitude}, {request.longitude})")
        
        data = await gee_service.calculate_affected_population(
            request.latitude,
            request.longitude,
            request.damage_radii_km
        )
        
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        logger.error(f"Error calculating affected population: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate affected population: {str(e)}")


@router.get("/datasets")
async def list_available_datasets():
    """
    List all available GEE datasets
    
    Returns a list of supported datasets with descriptions.
    """
    datasets = {
        "elevation": [
            {
                "id": "USGS/SRTMGL1_003",
                "name": "SRTM Digital Elevation Data 30m",
                "resolution": "30m",
                "description": "Global 30m digital elevation model"
            },
            {
                "id": "ASTER/ASTGTM",
                "name": "ASTER Global DEM",
                "resolution": "30m",
                "description": "Alternative global DEM"
            },
            {
                "id": "USGS/GMTED2010",
                "name": "Global Multi-resolution Terrain Elevation Data",
                "resolution": "variable",
                "description": "Global elevation data for QA"
            }
        ],
        "land_cover": [
            {
                "id": "ESRI_Global_LULC_10m",
                "name": "ESRI 10m Annual Land Cover",
                "resolution": "10m",
                "description": "Annual global land cover maps (2017-2024)"
            },
            {
                "id": "MODIS/006/MCD12Q1",
                "name": "MODIS Land Cover",
                "resolution": "500m",
                "description": "Global land cover classification"
            },
            {
                "id": "GLC_FCS30D",
                "name": "Global 30m Land Cover",
                "resolution": "30m",
                "description": "Annual land cover 1985-2022"
            }
        ],
        "population": [
            {
                "id": "WorldPop/GP/100m/pop",
                "name": "WorldPop",
                "resolution": "100m",
                "description": "Global gridded population data"
            },
            {
                "id": "CIESIN/GPWv411/GPW_Population_Density",
                "name": "NASA SEDAC GPW",
                "resolution": "1km",
                "description": "Gridded Population of the World"
            }
        ],
        "water": [
            {
                "id": "JRC/GSW1_4/GlobalSurfaceWater",
                "name": "JRC Global Surface Water",
                "resolution": "30m",
                "description": "Global surface water mapping"
            },
            {
                "id": "GLOBAL_FLOOD_DB/MODIS",
                "name": "Global Flood Database",
                "resolution": "250m",
                "description": "Flood extent data"
            }
        ],
        "urban": [
            {
                "id": "JRC/GHSL/P2023A/GHS_BUILT",
                "name": "Global Human Settlement Layer",
                "resolution": "100m",
                "description": "Urban footprint and population"
            },
            {
                "id": "DLR/GUF_v1/GlobalUrbanFootprint",
                "name": "Global Urban Footprint",
                "resolution": "12m",
                "description": "Urban settlement extent"
            }
        ]
    }
    
    return {
        "success": True,
        "datasets": datasets
    }


@router.get("/health")
async def gee_health_check():
    """
    Check GEE service health and authentication status
    
    Returns service status and initialization state.
    """
    return {
        "status": "healthy",
        "gee_initialized": gee_service.initialized,
        "service": "Google Earth Engine Data Service",
        "version": "1.0.0"
    }


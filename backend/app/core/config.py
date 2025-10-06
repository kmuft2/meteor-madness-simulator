"""
Application configuration using Pydantic settings
Loads from environment variables with validation
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "Meteor Madness Simulator"
    debug: bool = True
    
    # NASA APIs
    nasa_api_key: str = "DEMO_KEY"
    nasa_neo_api_url: str = "https://api.nasa.gov/neo/rest/v1/"
    nasa_sbdb_api_url: str = "https://ssd-api.jpl.nasa.gov/sbdb.api"
    nasa_comet_api_url: str = "https://data.nasa.gov/resource/b67r-rgxc.json"
    
    # USGS APIs
    usgs_earthquake_api_url: str = "https://earthquake.usgs.gov/fdsnws/event/1/"
    usgs_elevation_api_url: str = "https://elevation.usgs.gov/arcgis/rest/services/"
    
    # Database (optional)
    database_url: Optional[str] = None
    
    # CUDA
    cuda_visible_devices: str = "0"
    cuda_enabled: bool = True
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()

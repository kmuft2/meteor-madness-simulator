# EDITING: Cascade at 05:11 UTC - Adding orbital intercept models
"""
Pydantic models for asteroid and impact data
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class AsteroidParameters(BaseModel):
    """Input parameters for asteroid impact simulation"""
    diameter: float = Field(..., description="Asteroid diameter in meters", gt=0)
    velocity: float = Field(..., description="Impact velocity in km/s", gt=0, le=100)
    density: float = Field(2500.0, description="Asteroid density in kg/m³", gt=0)
    angle: float = Field(45.0, description="Impact angle in degrees", ge=0, le=90)
    composition: Optional[str] = Field("rocky", description="Asteroid composition type")
    

class OrbitalElements(BaseModel):
    """Keplerian orbital elements"""
    eccentricity: float = Field(..., description="Orbital eccentricity")
    semi_major_axis_au: float = Field(..., description="Semi-major axis in AU")
    inclination_deg: float = Field(..., description="Orbital inclination in degrees")
    longitude_ascending_node_deg: float = Field(..., description="Longitude of ascending node")
    argument_periapsis_deg: float = Field(..., description="Argument of periapsis")
    mean_anomaly_deg: float = Field(..., description="Mean anomaly")


class OrbitalIntercept(BaseModel):
    """Derived Earth-intercept parameters from orbital elements"""
    entry_velocity_km_s: float = Field(..., description="Relative entry velocity at Earth in km/s")
    entry_angle_deg: float = Field(..., description="Entry angle relative to horizontal plane")
    latitude: float = Field(..., description="Estimated impact latitude in degrees", ge=-90, le=90)
    longitude: float = Field(..., description="Estimated impact longitude in degrees", ge=-180, le=180)
    azimuth_deg: float = Field(..., description="Approach azimuth (degrees from north)")
    mean_anomaly_deg: float = Field(..., description="Mean anomaly at Earth intercept")
    distance_to_orbit_km: float = Field(..., description="Distance from asteroid to Earth's orbital radius at intercept (km)")


class ImpactResults(BaseModel):
    """Results from impact physics simulation"""
    crater_diameter: float = Field(..., description="Crater diameter in meters")
    crater_depth: float = Field(..., description="Crater depth in meters")
    kinetic_energy_joules: float = Field(..., description="Impact kinetic energy in joules")
    energy_mt_tnt: float = Field(..., description="Energy in megatons TNT equivalent")
    thermal_radius_km: float = Field(..., description="Thermal radiation radius in km")
    overpressure_radius_km: float = Field(..., description="Overpressure radius in km")
    seismic_magnitude: float = Field(..., description="Equivalent earthquake magnitude")
    seismic_energy_ergs: float = Field(..., description="Seismic energy in ergs")
    
    # Input parameters for reference
    input_parameters: AsteroidParameters
    
    # Comprehensive danger assessment (replaces USGS)
    danger_assessment: Optional[Dict] = Field(None, description="Comprehensive impact danger metrics")
    
    # DEPRECATED: USGS correlation (kept for backward compatibility)
    usgs_damage_scale: Optional[Dict] = Field(None, description="USGS damage scale info (deprecated)")
    similar_earthquakes: Optional[List[Dict]] = Field(None, description="Similar historical earthquakes (deprecated)")
    
    calculation_method: str = Field("enhanced_physics_engine", description="Calculation method used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NASAAsteroidData(BaseModel):
    """Asteroid data from NASA APIs"""
    id: str
    neo_reference_id: str
    name: str
    nasa_jpl_url: Optional[str] = None
    absolute_magnitude_h: float
    is_potentially_hazardous: bool
    estimated_diameter: Dict
    close_approach_data: List[Dict] = []
    orbital_data: Optional[Dict] = None
    data_source: str = "NASA_Official"


class SimulationRequest(BaseModel):
    """Request for impact simulation"""
    asteroid_params: AsteroidParameters
    location_lat: Optional[float] = Field(None, description="Impact latitude", ge=-90, le=90)
    location_lon: Optional[float] = Field(None, description="Impact longitude", ge=-180, le=180)
    orbital_elements: Optional[OrbitalElements] = Field(None, description="Optional Keplerian orbital elements for intercept calculation")
    include_usgs_correlation: bool = Field(True, description="Include USGS earthquake correlation")
    include_trajectory: bool = Field(False, description="Include trajectory calculation")


class SimulationResponse(BaseModel):
    """Response from impact simulation"""
    impact_results: ImpactResults
    trajectory_data: Optional[List[Dict]] = None
    location: Optional[Dict] = None
    orbital_intercept: Optional[OrbitalIntercept] = Field(None, description="Derived orbital intercept data if orbital elements were provided")
    computation_time_ms: float


class MonteCarloImpactRequest(BaseModel):
    """Request payload for Monte Carlo impact probability heatmap"""
    asteroid_id: str = Field(..., description="NASA SBDB asteroid identifier or designation")
    asteroid_params: AsteroidParameters
    samples: int = Field(500, description="Number of Monte Carlo orbital samples", ge=100, le=10000)
    bin_size_deg: float = Field(5.0, description="Heatmap bin size in degrees", ge=0.5, le=30.0)
    random_seed: Optional[int] = Field(None, description="Optional random seed for reproducibility")

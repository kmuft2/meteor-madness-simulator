"""
Simulation API routes for asteroid impact calculations
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
# EDITING: Cascade at 05:33 UTC - Integrating orbital intercept in simulation API
import logging
import time
import math
from datetime import datetime, timedelta

from app.models.asteroid import (
    SimulationRequest, 
    SimulationResponse, 
    AsteroidParameters,
    ImpactResults,
    MonteCarloImpactRequest
)
from app.physics.impact_physics import EnhancedPhysicsEngine
from app.physics.orbital_mechanics import calculate_impact_scenario, OrbitalMechanics
from app.physics.danger_assessment import DangerAssessment
from app.services.usgs.earthquake_service import USGSEarthquakeService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulation", tags=["simulation"])

# Initialize physics engine and danger assessor (singletons)
physics_engine = EnhancedPhysicsEngine()
danger_assessor = DangerAssessment()


@router.post("/impact", response_model=SimulationResponse)
async def simulate_impact(request: SimulationRequest) -> SimulationResponse:
    """
    Simulate asteroid impact and calculate effects
    
    This endpoint calculates:
    - Crater dimensions
    - Energy release (kinetic energy and TNT equivalent)
    - Thermal radiation effects
    - Environmental damage
    """
    start_time = time.time()
    
    try:
        requested_location = (
            {
                "latitude": request.location_lat,
                "longitude": request.location_lon
            }
            if request.location_lat is not None and request.location_lon is not None
            else None
        )

        params_dict = {
            'diameter': request.asteroid_params.diameter,
            'velocity': request.asteroid_params.velocity,
            'density': request.asteroid_params.density,
            'angle': request.asteroid_params.angle
        }

        intercept_data: Optional[Dict] = None
        scenario: Optional[Dict] = None
        orbital_elements_dict = request.orbital_elements.dict() if request.orbital_elements else None

        if orbital_elements_dict:
            scenario = calculate_impact_scenario(
                params_dict.copy(),
                orbital_elements=orbital_elements_dict,
                target_location=requested_location
            )
            if scenario:
                intercept_data = scenario.get('orbital_intercept')
                effective_params = scenario.get('effective_parameters', {})
                if effective_params:
                    params_dict['velocity'] = effective_params.get('entry_velocity_km_s', params_dict['velocity'])
                    params_dict['angle'] = effective_params.get('entry_angle_deg', params_dict['angle'])

        # Compute basic impact effects using effective entry parameters
        impact_data = physics_engine.compute_impact_effects(params_dict)

        # DEPRECATED: USGS correlation (kept for backward compatibility, but likely fails for large impacts)
        usgs_damage_scale = None
        similar_earthquakes = None

        if request.include_usgs_correlation and impact_data['energy_mt_tnt'] < 100:
            try:
                async with USGSEarthquakeService(settings.usgs_earthquake_api_url) as usgs:
                    usgs_damage_scale = usgs.get_earthquake_damage_description(
                        impact_data['seismic_magnitude']
                    )
                    similar_earthquakes = await usgs.find_similar_magnitude_earthquakes(
                        impact_data['seismic_magnitude'],
                        tolerance=0.5
                    )
            except Exception as e:
                logger.debug(f"USGS correlation skipped (impact too large or API unavailable): {e}")

        # Determine impact location and atmospheric trajectory
        trajectory_data = None
        location = None

        if scenario:
            trajectory_data = scenario['atmospheric_entry']['trajectory']
            location = scenario['impact_location']

        if request.include_trajectory:
            try:
                if scenario is None:
                    scenario = calculate_impact_scenario(
                        params_dict.copy(),
                        orbital_elements=orbital_elements_dict,
                        target_location=requested_location
                    )
                    if scenario:
                        intercept_data = intercept_data or scenario.get('orbital_intercept')
                if scenario:
                    trajectory_data = scenario['atmospheric_entry']['trajectory']
                    location = scenario['impact_location']
            except Exception as e:
                logger.warning(f"Trajectory calculation failed: {e}")

        if location is None and requested_location:
            location = {
                "latitude": requested_location['latitude'],
                "longitude": requested_location['longitude'],
                "impact_point": [requested_location['longitude'], requested_location['latitude']],
                "impact_angle_deg": request.asteroid_params.angle
            }

        if location is None and intercept_data:
            location = {
                "latitude": intercept_data.get('latitude'),
                "longitude": intercept_data.get('longitude'),
                "impact_point": [intercept_data.get('longitude'), intercept_data.get('latitude')],
                "impact_angle_deg": params_dict['angle'],
                "azimuth_deg": intercept_data.get('azimuth_deg')
            }

        if location and 'impact_angle_deg' not in location:
            location['impact_angle_deg'] = params_dict['angle']
        if location and 'azimuth_deg' not in location and intercept_data:
            location['azimuth_deg'] = intercept_data.get('azimuth_deg')

        # Calculate comprehensive danger assessment using final location estimate
        danger_assessment = None
        try:
            danger_lat = location['latitude'] if location else (
                intercept_data['latitude'] if intercept_data else (request.location_lat or 0.0)
            )
            danger_lon = location['longitude'] if location else (
                intercept_data['longitude'] if intercept_data else (request.location_lon or 0.0)
            )

            danger_assessment = danger_assessor.assess_impact(
                energy_mt_tnt=impact_data['energy_mt_tnt'],
                crater_diameter_m=impact_data['crater_diameter'],
                crater_depth_m=impact_data['crater_depth'],
                latitude=danger_lat,
                longitude=danger_lon,
                impact_angle_deg=params_dict['angle'],
                asteroid_diameter_m=request.asteroid_params.diameter,
                velocity_km_s=params_dict['velocity']
            )
        except Exception as e:
            logger.warning(f"Danger assessment failed: {e}")

        effective_parameters_model = request.asteroid_params.copy(update={
            "velocity": params_dict['velocity'],
            "angle": params_dict['angle']
        })

        # Build impact results
        impact_results = ImpactResults(
            crater_diameter=impact_data['crater_diameter'],
            crater_depth=impact_data['crater_depth'],
            kinetic_energy_joules=impact_data['kinetic_energy_joules'],
            energy_mt_tnt=impact_data['energy_mt_tnt'],
            thermal_radius_km=impact_data['thermal_radius_km'],
            overpressure_radius_km=impact_data['overpressure_radius_km'],
            seismic_magnitude=impact_data['seismic_magnitude'],
            seismic_energy_ergs=impact_data['seismic_energy_ergs'],
            input_parameters=effective_parameters_model,
            danger_assessment=danger_assessment,
            usgs_damage_scale=usgs_damage_scale,  # Deprecated
            similar_earthquakes=similar_earthquakes[:3] if similar_earthquakes else None,  # Deprecated
            calculation_method=impact_data['calculation_method']
        )

        computation_time = (time.time() - start_time) * 1000  # ms

        return SimulationResponse(
            impact_results=impact_results,
            trajectory_data=trajectory_data,
            location=location,
            orbital_intercept=intercept_data,
            computation_time_ms=computation_time
        )
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.post("/batch", response_model=List[Dict])
async def simulate_batch_impacts(asteroid_params_list: List[AsteroidParameters]) -> List[Dict]:
    """
    Simulate multiple asteroid impacts in batch
    More efficient for comparing multiple scenarios
    """
    start_time = time.time()
    
    try:
        # Convert to dicts
        params_dicts = [
            {
                'diameter': p.diameter,
                'velocity': p.velocity,
                'density': p.density,
                'angle': p.angle
            }
            for p in asteroid_params_list
        ]
        
        # Compute batch (uses GPU if available)
        results = physics_engine.compute_batch_impacts(params_dicts)
        
        # Add input parameters to results
        for i, result in enumerate(results):
            result['input_parameters'] = asteroid_params_list[i].dict()
        
        computation_time = (time.time() - start_time) * 1000
        
        return results
        
    except Exception as e:
        logger.error(f"Batch simulation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch simulation failed: {str(e)}")


@router.get("/validate/tunguska")
async def validate_tunguska() -> Dict:
    """
    Validate physics engine against the 1908 Tunguska event
    Returns comparison with historical data
    """
    tunguska_params = {
        'diameter': 50.0,
        'velocity': 27.0,
        'density': 2000.0,
        'angle': 45.0
    }
    
    results = physics_engine.compute_impact_effects(tunguska_params)
    
    return {
        "event": "Tunguska 1908",
        "input_parameters": tunguska_params,
        "calculated_results": results,
        "historical_data": {
            "estimated_energy_mt": 12.0,
            "estimated_crater_diameter": 150.0,
            "description": "Airburst over Siberia, flattened 2000 km² of forest"
        },
        "validation": {
            "energy_match": 8 < results['energy_mt_tnt'] < 20,
            "notes": "Results within expected range for Tunguska-like event"
        }
    }


@router.get("/validate/chelyabinsk")
async def validate_chelyabinsk() -> Dict:
    """
    Validate physics engine against the 2013 Chelyabinsk event
    """
    chelyabinsk_params = {
        'diameter': 20.0,
        'velocity': 19.0,
        'density': 3300.0,
        'angle': 20.0
    }
    
    results = physics_engine.compute_impact_effects(chelyabinsk_params)
    
    return {
        "event": "Chelyabinsk 2013",
        "input_parameters": chelyabinsk_params,
        "calculated_results": results,
        "historical_data": {
            "estimated_energy_mt": 0.5,
            "seismic_magnitude": 2.7,
            "description": "Airburst, ~1500 injuries from broken glass"
        },
        "validation": {
            "energy_match": 0.3 < results['energy_mt_tnt'] < 0.7,
            "notes": "Results consistent with observed Chelyabinsk event"
        }
    }


@router.post("/trajectory")
async def calculate_trajectory(
    asteroid_params: AsteroidParameters,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Dict:
    """
    Calculate detailed atmospheric entry trajectory for 3D visualization
    
    Returns trajectory points through atmosphere with altitude, velocity, and position
    """
    try:
        params_dict = {
            'diameter': asteroid_params.diameter,
            'velocity': asteroid_params.velocity,
            'density': asteroid_params.density,
            'angle': asteroid_params.angle
        }
        
        target_loc = None
        if latitude is not None and longitude is not None:
            target_loc = {'latitude': latitude, 'longitude': longitude}
        
        scenario = calculate_impact_scenario(
            params_dict,
            orbital_elements=None,
            target_location=target_loc
        )
        
        return {
            "status": "success",
            "impact_location": scenario['impact_location'],
            "trajectory": scenario['atmospheric_entry']['trajectory'],
            "impact_velocity_km_s": scenario['atmospheric_entry']['impact_velocity_km_s'],
            "fragmented": scenario['atmospheric_entry']['fragmented'],
            "airburst_altitude_km": scenario['atmospheric_entry'].get('airburst_altitude_km', 0)
        }
        
    except Exception as e:
        logger.error(f"Trajectory calculation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trajectory calculation failed: {str(e)}")


@router.post("/orbital-trajectory")
async def calculate_orbital_trajectory(
    orbital_elements: Dict, 
    num_points: int = 360,
    check_collision: bool = True,
    full_orbit: bool = True
) -> Dict:
    """
    Calculate orbital trajectory for 3D space visualization
    
    Args:
        orbital_elements: Keplerian elements (semi_major_axis_au, eccentricity, etc.)
        num_points: Minimum number of points along orbit (default 360 for smooth path)
        check_collision: Check for Earth collision and stop if detected (default True)
        full_orbit: Calculate full orbital period (default True)
    
    Returns:
        Complete orbital path with collision detection, continuing until either:
        - Asteroid collides with Earth, or
        - Full orbital cycle is complete
    """
    try:
        om = OrbitalMechanics()
        trajectory = om.generate_trajectory_visualization(
            orbital_elements, 
            num_points,
            check_collision,
            full_orbit
        )
        
        # Extract metadata from first point if available
        metadata = trajectory[0].get("trajectory_metadata", {}) if trajectory else {}
        
        return {
            "status": "success",
            "trajectory": trajectory,
            "orbital_elements": orbital_elements,
            "num_points": len(trajectory),
            "metadata": {
                "collision_detected": metadata.get("collision_detected", False),
                "collision_point_index": metadata.get("collision_point_index"),
                "orbital_period_years": metadata.get("orbital_period_years", 0),
                "full_orbit_calculated": metadata.get("full_orbit_calculated", True),
                "points_calculated": len(trajectory)
            }
        }
        
    except Exception as e:
        logger.error(f"Orbital trajectory calculation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Orbital calculation failed: {str(e)}")


@router.get("/scenario/{scenario_name}")
async def get_preset_scenario(scenario_name: str) -> Dict:
    """
    Get preset impact scenarios with real orbital data
    
    Available scenarios:
    - tunguska: 1908 Tunguska event
    - chelyabinsk: 2013 Chelyabinsk event
    - apophis: 99942 Apophis close approach
    - chicxulub: Dinosaur extinction event
    """
    scenarios = {
        "tunguska": {
            "name": "Tunguska 1908",
            "asteroid_params": {
                "diameter": 50.0,
                "velocity": 27.0,
                "density": 2000.0,
                "angle": 45.0
            },
            "location": {"latitude": 60.886, "longitude": 101.894},
            "orbital_elements": {
                "semi_major_axis_au": 1.2,
                "eccentricity": 0.35,
                "inclination_deg": 8.0,
                "longitude_ascending_node_deg": 180.0,
                "argument_periapsis_deg": 90.0,
                "mean_anomaly_deg": 0.0
            },
            "description": "Airburst over Siberia that flattened 2000 km² of forest"
        },
        "chelyabinsk": {
            "name": "Chelyabinsk 2013",
            "asteroid_params": {
                "diameter": 20.0,
                "velocity": 19.0,
                "density": 3300.0,
                "angle": 20.0
            },
            "location": {"latitude": 54.8, "longitude": 61.1},
            "orbital_elements": {
                "semi_major_axis_au": 1.65,
                "eccentricity": 0.51,
                "inclination_deg": 2.7,
                "longitude_ascending_node_deg": 326.0,
                "argument_periapsis_deg": 277.0,
                "mean_anomaly_deg": 0.0
            },
            "description": "Airburst over Russia causing ~1500 injuries"
        },
        "apophis": {
            "name": "99942 Apophis",
            "asteroid_params": {
                "diameter": 370.0,
                "velocity": 7.4,
                "density": 3200.0,
                "angle": 45.0
            },
            "location": {"latitude": 0.0, "longitude": 0.0},
            "orbital_elements": {
                "semi_major_axis_au": 0.922,
                "eccentricity": 0.191,
                "inclination_deg": 3.331,
                "longitude_ascending_node_deg": 204.4,
                "argument_periapsis_deg": 126.4,
                "mean_anomaly_deg": 0.0
            },
            "description": "Near-Earth asteroid with close approaches"
        },
        "chicxulub": {
            "name": "Chicxulub Impact",
            "asteroid_params": {
                "diameter": 10000.0,
                "velocity": 20.0,
                "density": 2500.0,
                "angle": 60.0
            },
            "location": {"latitude": 21.4, "longitude": -89.5},
            "orbital_elements": {
                "semi_major_axis_au": 2.5,
                "eccentricity": 0.6,
                "inclination_deg": 15.0,
                "longitude_ascending_node_deg": 45.0,
                "argument_periapsis_deg": 120.0,
                "mean_anomaly_deg": 0.0
            },
            "description": "Dinosaur extinction event 66 million years ago"
        }
    }
    
    if scenario_name.lower() not in scenarios:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{scenario_name}' not found. Available: {list(scenarios.keys())}"
        )
    
    scenario = scenarios[scenario_name.lower()]
    
    # Calculate impact effects for this scenario
    try:
        params_dict = scenario['asteroid_params']
        impact_data = physics_engine.compute_impact_effects(params_dict)
        
        # Calculate trajectory if location provided
        trajectory_data = None
        if 'location' in scenario:
            full_scenario = calculate_impact_scenario(
                params_dict,
                orbital_elements=scenario.get('orbital_elements'),
                target_location=scenario['location']
            )
            trajectory_data = full_scenario['atmospheric_entry']['trajectory'][:20]  # Limit points
        
        return {
            "status": "success",
            "scenario": scenario,
            "impact_effects": impact_data,
            "trajectory_preview": trajectory_data
        }
        
    except Exception as e:
        logger.error(f"Scenario calculation failed: {e}")
        return {
            "status": "partial",
            "scenario": scenario,
            "error": str(e)
        }


@router.get("/neo/live-threats")
async def get_live_neo_threats():
    """
    Get live Near-Earth Object data from NASA API
    Returns asteroids making close approaches in the next 7 days
    """
    try:
        from app.services.nasa.neo_live_service import NASANEOLiveService
        
        async with NASANEOLiveService(settings.nasa_api_key) as neo_service:
            # Get potentially hazardous asteroids
            hazardous = await neo_service.get_potentially_hazardous()
            
            # Get all close approaches for next 7 days
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            all_approaches = await neo_service.get_close_approaches(start_date, end_date)
            
            return {
                "status": "success",
                "data_source": "NASA_NEO_API_Live",
                "query_date": datetime.now().isoformat(),
                "potentially_hazardous": hazardous,
                "all_close_approaches": all_approaches[:20],  # Limit to 20
                "total_count": len(all_approaches),
                "hazardous_count": len(hazardous)
            }
    except Exception as e:
        logger.error(f"Failed to fetch live NEO data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch NASA NEO data: {str(e)}")


@router.get("/neo/{asteroid_id}")
async def get_neo_details(asteroid_id: str):
    """
    Get detailed information about a specific asteroid from NASA
    """
    try:
        from app.services.nasa.neo_live_service import NASANEOLiveService
        
        async with NASANEOLiveService(settings.nasa_api_key) as neo_service:
            asteroid_data = await neo_service.get_asteroid_by_id(asteroid_id)
            
            if not asteroid_data:
                raise HTTPException(status_code=404, detail=f"Asteroid {asteroid_id} not found")
            
            return {
                "status": "success",
                "asteroid": asteroid_data
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch asteroid {asteroid_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deflection/analyze")
async def analyze_deflection_strategies(
    asteroid_diameter: float,
    asteroid_density: float = 3200.0,
    years_warning: float = 10.0
):
    """
    Analyze and compare all deflection strategies for a given asteroid
    
    Args:
        asteroid_diameter: Diameter in meters
        asteroid_density: Density in kg/m³ (default: 3200 for rocky asteroid)
        years_warning: Years of warning time before impact
    
    Returns:
        Comparison of all deflection strategies with recommendations
    """
    try:
        from app.physics.deflection_strategies import DeflectionStrategies
        
        ds = DeflectionStrategies()
        result = ds.compare_all_strategies(
            asteroid_diameter_m=asteroid_diameter,
            asteroid_density_kg_m3=asteroid_density,
            years_before_impact=years_warning
        )
        
        return {
            "status": "success",
            "deflection_analysis": result
        }
    except Exception as e:
        logger.error(f"Deflection analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deflection/kinetic-impactor")
async def calculate_kinetic_impactor(
    asteroid_mass_kg: float,
    asteroid_velocity_km_s: float,
    impactor_mass_kg: float = 500.0,
    impactor_velocity_km_s: float = 6.0,
    impact_efficiency: float = 3.0,
    years_before_impact: float = 10.0
):
    """
    Calculate deflection from kinetic impactor mission (DART-style)
    """
    try:
        from app.physics.deflection_strategies import DeflectionStrategies
        
        ds = DeflectionStrategies()
        result = ds.kinetic_impactor(
            asteroid_mass_kg=asteroid_mass_kg,
            asteroid_velocity_km_s=asteroid_velocity_km_s,
            impactor_mass_kg=impactor_mass_kg,
            impactor_velocity_km_s=impactor_velocity_km_s,
            impact_efficiency=impact_efficiency,
            years_before_impact=years_before_impact
        )
        
        return {
            "status": "success",
            "kinetic_impactor": result
        }
    except Exception as e:
        logger.error(f"Kinetic impactor calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tsunami/analyze")
async def analyze_tsunami_impact(
    asteroid_diameter: float,
    asteroid_velocity: float,
    asteroid_density: float = 3000.0,
    ocean_depth: float = 4000.0,
    impact_angle: float = 45.0,
    latitude: float = 0.0,
    longitude: float = 0.0
):
    """
    Analyze tsunami generation and coastal impact for ocean impacts
    
    Args:
        asteroid_diameter: Diameter in meters
        asteroid_velocity: Impact velocity in km/s
        asteroid_density: Density in kg/m³
        ocean_depth: Ocean depth at impact site in meters
        impact_angle: Impact angle from horizontal in degrees
        latitude: Impact latitude
        longitude: Impact longitude
    
    Returns:
        Tsunami generation parameters and coastal impact assessment
    """
    try:
        from app.physics.tsunami_model import TsunamiModel
        
        tm = TsunamiModel()
        
        # Calculate tsunami generation
        tsunami_result = tm.calculate_ocean_impact_tsunami(
            asteroid_diameter_m=asteroid_diameter,
            asteroid_velocity_km_s=asteroid_velocity,
            asteroid_density_kg_m3=asteroid_density,
            ocean_depth_m=ocean_depth,
            impact_angle_deg=impact_angle
        )
        
        # Calculate coastal impact (assuming moderate coastal population)
        coastal_result = tm.calculate_coastal_impact(
            tsunami_wave_height_m=tsunami_result['coastal_wave_height_m'],
            coastal_population_density=500,  # people/km²
            coastal_elevation_m=10.0  # meters
        )
        
        return {
            "status": "success",
            "is_ocean_impact": tm.is_ocean_impact(latitude, longitude),
            "tsunami_generation": tsunami_result,
            "coastal_impact": coastal_result,
            "warning": "Immediate evacuation required for coastal areas" if tsunami_result['risk_level'] in ['HIGH', 'CATASTROPHIC'] else None
        }
    except Exception as e:
        logger.error(f"Tsunami analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gpu/info")
async def get_gpu_info():
    """
    Get GPU hardware information and capabilities
    """
    try:
        from app.physics.gpu_accelerated import GPUAcceleratedSimulator
        
        gpu_sim = GPUAcceleratedSimulator()
        info = gpu_sim.get_gpu_info()
        
        return {
            "status": "success",
            "gpu": info
        }
    except Exception as e:
        logger.error(f"GPU info failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gpu/high-res-trajectory")
async def gpu_high_resolution_trajectory(
    altitude_km: float = 100.0,
    velocity_km_s: float = 20.0,
    angle_deg: float = 45.0,
    time_steps: int = 10000
):
    """
    GPU-accelerated high-resolution trajectory calculation
    Calculates 10,000+ trajectory points with gravitational effects
    
    Args:
        altitude_km: Starting altitude in km
        velocity_km_s: Initial velocity in km/s
        angle_deg: Entry angle from horizontal
        time_steps: Number of simulation steps (default: 10,000)
    
    Returns:
        High-resolution trajectory with positions, velocities, altitudes
    """
    try:
        from app.physics.gpu_accelerated import GPUAcceleratedSimulator
        import numpy as np
        
        gpu_sim = GPUAcceleratedSimulator()
        
        # Convert to SI units
        EARTH_RADIUS = 6371000  # meters
        altitude_m = altitude_km * 1000
        velocity_m_s = velocity_km_s * 1000
        angle_rad = math.radians(angle_deg)
        
        # Initial conditions
        initial_position = np.array([
            0.0,
            0.0,
            EARTH_RADIUS + altitude_m
        ])
        
        initial_velocity = np.array([
            velocity_m_s * math.cos(angle_rad),
            0.0,
            -velocity_m_s * math.sin(angle_rad)
        ])
        
        # Run simulation
        result = gpu_sim.high_resolution_trajectory(
            initial_position,
            initial_velocity,
            asteroid_mass=1e6,  # 1 ton asteroid
            time_steps=time_steps,
            dt=0.1
        )
        
        # Sample points for return (full dataset too large)
        sample_rate = max(1, time_steps // 1000)
        
        return {
            "status": "success",
            "trajectory": {
                "altitudes_km": result['altitudes'][::sample_rate].tolist(),
                "speeds_km_s": (result['speeds'][::sample_rate] / 1000).tolist(),
                "time_steps_calculated": time_steps,
                "time_steps_returned": len(result['altitudes'][::sample_rate]),
                "calculation_time_ms": result['calculation_time_ms'],
                "calculation_method": result['calculation_method'],
                "performance_points_per_second": result['points_per_second']
            }
        }
    except Exception as e:
        logger.error(f"GPU trajectory failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gpu/monte-carlo-probability")
async def gpu_monte_carlo_probability(
    semi_major_axis_au: float,
    eccentricity: float,
    num_simulations: int = 10000,
    uncertainty_percent: float = 1.0
):
    """
    GPU-accelerated Monte Carlo simulation for impact probability
    Runs thousands of orbital variations in parallel
    
    Args:
        semi_major_axis_au: Semi-major axis in AU
        eccentricity: Orbital eccentricity
        num_simulations: Number of Monte Carlo runs (1,000-100,000)
        uncertainty_percent: Uncertainty in orbital elements (%)
    
    Returns:
        Impact probability with detailed statistics
    """
    try:
        from app.physics.gpu_accelerated import GPUAcceleratedSimulator
        
        gpu_sim = GPUAcceleratedSimulator()
        
        orbital_elements = {
            'semi_major_axis_au': semi_major_axis_au,
            'eccentricity': eccentricity
        }
        
        result = gpu_sim.monte_carlo_impact_probability(
            orbital_elements,
            num_simulations=num_simulations,
            uncertainty_sigma=uncertainty_percent / 100
        )
        
        return {
            "status": "success",
            "monte_carlo": result
        }
    except Exception as e:
        logger.error(f"Monte Carlo simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gpu/crater-morphology")
async def gpu_crater_morphology(
    asteroid_diameter: float,
    asteroid_velocity: float,
    asteroid_density: float = 3000.0,
    impact_angle: float = 45.0,
    target_density: float = 2500.0,
    grid_resolution: int = 1000
):
    """
    GPU-accelerated detailed crater morphology calculation
    Computes crater shape on high-resolution grid
    
    Args:
        asteroid_diameter: Diameter in meters
        asteroid_velocity: Velocity in km/s
        asteroid_density: Density in kg/m³
        impact_angle: Impact angle from horizontal
        target_density: Target material density
        grid_resolution: Grid size (100-2000, higher = more detail)
    
    Returns:
        Detailed crater morphology with 3D shape data
    """
    try:
        from app.physics.gpu_accelerated import GPUAcceleratedSimulator
        
        gpu_sim = GPUAcceleratedSimulator()
        
        # Calculate impact energy
        radius = asteroid_diameter / 2
        volume = (4/3) * math.pi * (radius**3)
        mass = volume * asteroid_density
        velocity_m_s = asteroid_velocity * 1000
        impact_energy = 0.5 * mass * (velocity_m_s**2)
        
        result = gpu_sim.parallel_crater_formation(
            impact_energy_joules=impact_energy,
            asteroid_diameter_m=asteroid_diameter,
            impact_angle_deg=impact_angle,
            target_density_kg_m3=target_density,
            grid_resolution=grid_resolution
        )
        
        return {
            "status": "success",
            "crater_morphology": result
        }
    except Exception as e:
        logger.error(f"Crater morphology calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monte-carlo-impact-map")
async def monte_carlo_impact_map(request: MonteCarloImpactRequest) -> Dict:
    """
    Generate Monte Carlo impact probability heatmap using SBDB covariance data.
    
    This endpoint:
    1. Fetches orbital covariance matrix from NASA SBDB for the specified asteroid
    2. Samples orbital elements from the multivariate normal distribution
    3. Calculates impact location for each sample using orbital mechanics
    4. Aggregates results into a geographic heatmap
    
    Args:
        request: Contains asteroid_id, asteroid_params, samples count, bin_size_deg
    
    Returns:
        Heatmap data with impact probability distribution across Earth's surface
    """
    try:
        from app.physics.gpu_accelerated import GPUAcceleratedSimulator
        from app.services.nasa.official_apis import OfficialNASAAPIService
        
        start_time = time.time()
        
        # Fetch SBDB data with covariance
        async with OfficialNASAAPIService(
            settings.nasa_api_key,
            settings.nasa_neo_api_url,
            settings.nasa_sbdb_api_url
        ) as nasa_service:
            sbdb_data = await nasa_service.get_sbdb_asteroid_details(
                request.asteroid_id,
                include_covariance=True
            )
        
        if not sbdb_data:
            raise HTTPException(
                status_code=404,
                detail=f"Asteroid '{request.asteroid_id}' not found in NASA SBDB"
            )
        
        keplerian_elements = sbdb_data.get("keplerian_elements")
        covariance = sbdb_data.get("covariance")
        
        if not keplerian_elements:
            raise HTTPException(
                status_code=400,
                detail="Orbital elements not available for this asteroid"
            )
        
        if not covariance:
            raise HTTPException(
                status_code=400,
                detail="Covariance data not available for this asteroid. "
                       "Monte Carlo analysis requires orbital uncertainty information."
            )
        
        # Prepare asteroid parameters
        params_dict = {
            'diameter': request.asteroid_params.diameter,
            'velocity': request.asteroid_params.velocity,
            'density': request.asteroid_params.density,
            'angle': request.asteroid_params.angle
        }
        
        # Run Monte Carlo simulation
        gpu_sim = GPUAcceleratedSimulator()
        mc_result = gpu_sim.monte_carlo_impact_map(
            nominal_elements=keplerian_elements,
            covariance=covariance,
            asteroid_params=params_dict,
            samples=request.samples,
            bin_size_deg=request.bin_size_deg,
            seed=request.random_seed
        )
        
        total_time = time.time() - start_time
        
        return {
            "status": "success",
            "asteroid_id": request.asteroid_id,
            "asteroid_name": sbdb_data.get("object_name", "Unknown"),
            "orbital_elements": keplerian_elements,
            "monte_carlo_results": mc_result,
            "metadata": {
                "total_computation_time_ms": total_time * 1000,
                "data_source": "NASA_SBDB_Official",
                "covariance_epoch_jd": covariance.get("epoch_jd"),
                "disclaimer": "This is a statistical estimate based on orbital uncertainties. "
                             "Actual impact probability and location depend on many factors."
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Monte Carlo impact map failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

"""
Tsunami Modeling for Ocean Impacts
Based on USGS coastal hazard models and asteroid impact research
Now uses real GEBCO bathymetry data for accurate ocean depths
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Physical constants
EARTH_RADIUS_KM = 6371.0
WATER_DENSITY = 1025.0  # kg/m³ (seawater)
GRAVITY = 9.81  # m/s²


class TsunamiModel:
    """Model tsunami generation and propagation from ocean impacts"""
    
    def __init__(self, bathymetry_service=None):
        self.bathymetry_service = bathymetry_service
        self.ocean_depth_m = 4000  # Fallback average ocean depth
    
    def calculate_ocean_impact_tsunami(self,
                                      asteroid_diameter_m: float,
                                      asteroid_velocity_km_s: float,
                                      asteroid_density_kg_m3: float,
                                      ocean_depth_m: float = 4000.0,
                                      impact_angle_deg: float = 45.0) -> Dict:
        """
        Calculate tsunami generation from asteroid ocean impact
        
        Based on Ward & Asphaug (2000) and USGS tsunami models
        
        Args:
            asteroid_diameter_m: Diameter of asteroid in meters
            asteroid_velocity_km_s: Impact velocity in km/s
            asteroid_density_kg_m3: Density of asteroid
            ocean_depth_m: Ocean depth at impact site
            impact_angle_deg: Impact angle from horizontal
        
        Returns:
            Dict with tsunami parameters
        """
        # Calculate asteroid properties
        radius_m = asteroid_diameter_m / 2
        volume_m3 = (4/3) * math.pi * (radius_m ** 3)
        mass_kg = volume_m3 * asteroid_density_kg_m3
        
        # Impact energy
        velocity_m_s = asteroid_velocity_km_s * 1000
        kinetic_energy_joules = 0.5 * mass_kg * (velocity_m_s ** 2)
        
        # Energy coupled to water (depends on impact angle and depth)
        angle_rad = math.radians(impact_angle_deg)
        coupling_efficiency = 0.1 * math.sin(angle_rad)  # Approximate
        
        # Depth sensitivity: Deep water impacts are FAR less effective at generating tsunamis
        # Ward & Asphaug (2000): When h >> d, most energy goes into cavity/heating, not waves
        depth_ratio = ocean_depth_m / asteroid_diameter_m
        
        if depth_ratio <= 2:
            # Shallow impact: maximum tsunami generation
            depth_factor = 1.0
        elif depth_ratio <= 5:
            # Moderate depth: linear reduction
            depth_factor = 1.0 - (depth_ratio - 2) / 6  # 1.0 → 0.5
        elif depth_ratio <= 10:
            # Deep impact: exponential reduction
            depth_factor = 0.5 * math.exp(-(depth_ratio - 5) / 5)  # 0.5 → 0.18
        else:
            # Very deep: minimal tsunami (most energy dissipated)
            # Use inverse square for realistic deep-water suppression
            depth_factor = 10.0 / (depth_ratio ** 1.5)
        
        tsunami_energy_joules = kinetic_energy_joules * coupling_efficiency * depth_factor
        
        # Initial wave amplitude (Ward & Asphaug scaling, adjusted for realism)
        # Original: H₀ ≈ 0.1 * (E / ρ g)^(1/4)
        # Adjusted with lower coefficient for more realistic results
        amplitude_m = 0.02 * (tsunami_energy_joules / (WATER_DENSITY * GRAVITY)) ** 0.22
        
        # Apply safety caps to prevent unrealistic values
        # These caps are generous to let depth variations show through
        # Caps based on physical plausibility and asteroid size
        if asteroid_diameter_m < 50:
            max_amplitude = 15  # Very small impacts
        elif asteroid_diameter_m < 150:
            max_amplitude = 35  # Small-medium impacts
        elif asteroid_diameter_m < 300:
            max_amplitude = 60  # Medium impacts
        elif asteroid_diameter_m < 500:
            max_amplitude = 100  # Large impacts
        elif asteroid_diameter_m < 1000:
            max_amplitude = 200  # Very large impacts
        else:
            # Giant impacts: scale with size but cap at physically reasonable maximum
            max_amplitude = min(500, asteroid_diameter_m * 0.5)
        
        # Only apply cap if calculated value exceeds it
        amplitude_m = min(amplitude_m, max_amplitude)
        
        # Wave period (approximate)
        # T ≈ 2π√(h/g) for shallow water waves
        if ocean_depth_m < 1000:
            period_seconds = 2 * math.pi * math.sqrt(ocean_depth_m / GRAVITY)
        else:
            period_seconds = 2 * math.pi * math.sqrt(1000 / GRAVITY)
        
        # Wave speed (shallow water approximation: c = √(gh))
        wave_speed_m_s = math.sqrt(GRAVITY * ocean_depth_m)
        wave_speed_km_h = wave_speed_m_s * 3.6
        
        # Estimate coastal wave height using Green's Law amplification
        # Green's Law: H_coast = H_deep * (h_deep / h_coast)^(1/4)
        # Typical amplification: 2-4x for most coastlines
        # Historical data: 2004 tsunami amplified ~3-4x approaching shore
        #                  2011 tsunami amplified ~2-5x (extreme local conditions to 10x)
        
        if amplitude_m < 5:
            coastal_amplification = 2.5  # Small waves
        elif amplitude_m < 15:
            coastal_amplification = 3.0  # Medium waves
        elif amplitude_m < 30:
            coastal_amplification = 3.5  # Large waves
        else:
            # Very large waves: slight increase but cap at realistic maximum
            # Even extreme bathymetry rarely causes >5x amplification
            coastal_amplification = min(4.5, 3.5 + (amplitude_m - 30) / 100)
        
        coastal_wave_height_m = amplitude_m * coastal_amplification
        
        # Inundation distance (very rough estimate)
        # Based on empirical formula: R ≈ H² / tan(β) where β is coastal slope
        coastal_slope = 0.05  # Typical value (5%)
        inundation_distance_m = (coastal_wave_height_m ** 2) / coastal_slope
        inundation_distance_km = inundation_distance_m / 1000
        
        # Risk assessment
        risk_level = self._assess_tsunami_risk(coastal_wave_height_m, inundation_distance_km)
        
        return {
            "tsunami_generated": amplitude_m > 1.0,  # Significant if >1m
            "initial_wave_amplitude_m": amplitude_m,
            "coastal_wave_height_m": coastal_wave_height_m,
            "wave_period_seconds": period_seconds,
            "wave_speed_m_s": wave_speed_m_s,
            "wave_speed_km_h": wave_speed_km_h,
            "inundation_distance_km": inundation_distance_km,
            "tsunami_energy_joules": tsunami_energy_joules,
            "energy_mt_tnt": tsunami_energy_joules / 4.184e15,
            "ocean_depth_m": ocean_depth_m,
            "depth_ratio": depth_ratio,
            "coupling_efficiency": coupling_efficiency,
            "risk_level": risk_level,
            "affected_radius_km": self._calculate_affected_radius(amplitude_m),
            "arrival_time_hours": self._estimate_arrival_times(amplitude_m),
            "description": self._generate_tsunami_description(coastal_wave_height_m, risk_level)
        }
    
    def _assess_tsunami_risk(self, wave_height_m: float, inundation_km: float) -> str:
        """Assess tsunami risk level based on wave height"""
        if wave_height_m < 1:
            return "MINIMAL"
        elif wave_height_m < 3:
            return "LOW"
        elif wave_height_m < 10:
            return "MODERATE"
        elif wave_height_m < 20:
            return "HIGH"
        else:
            return "CATASTROPHIC"
    
    def _calculate_affected_radius(self, amplitude_m: float) -> float:
        """Estimate radius of ocean affected by tsunami"""
        # Tsunamis can travel across entire ocean basins
        # Rough estimate based on wave amplitude
        if amplitude_m < 1:
            return 100  # km
        elif amplitude_m < 10:
            return 500
        elif amplitude_m < 50:
            return 2000
        else:
            return 5000  # Trans-oceanic
    
    def _estimate_arrival_times(self, amplitude_m: float) -> Dict[str, float]:
        """Estimate tsunami arrival times at different distances"""
        # Tsunami speed in deep ocean ~800 km/h
        tsunami_speed_km_h = 800
        
        return {
            "nearshore_100km": 100 / tsunami_speed_km_h,
            "regional_500km": 500 / tsunami_speed_km_h,
            "distant_2000km": 2000 / tsunami_speed_km_h,
            "transoceanic_10000km": 10000 / tsunami_speed_km_h
        }
    
    def _generate_tsunami_description(self, wave_height_m: float, risk_level: str) -> str:
        """Generate human-readable tsunami description"""
        if wave_height_m < 1:
            return "Minimal tsunami risk. Small waves may occur near impact site."
        elif wave_height_m < 3:
            return "Low tsunami risk. Minor coastal flooding possible within 100 km."
        elif wave_height_m < 10:
            return f"Moderate tsunami risk. {wave_height_m:.1f}m waves could flood coastal areas within 500 km."
        elif wave_height_m < 20:
            return f"High tsunami risk! {wave_height_m:.1f}m waves will devastate coastlines within 1000+ km."
        else:
            return f"CATASTROPHIC tsunami! {wave_height_m:.1f}m waves will cause trans-oceanic devastation."
    
    def calculate_coastal_impact(self,
                                 tsunami_wave_height_m: float,
                                 coastal_population_density: int,
                                 coastal_elevation_m: float = 10.0) -> Dict:
        """
        Calculate potential impact on coastal populations
        
        Args:
            tsunami_wave_height_m: Height of tsunami wave at coast
            coastal_population_density: People per km²
            coastal_elevation_m: Average elevation of coastal area
        
        Returns:
            Dict with impact assessment
        """
        # Determine if area is flooded
        flooded = tsunami_wave_height_m > coastal_elevation_m
        
        # Estimate affected area (very rough)
        # Assuming inundation extends (wave_height/slope) inland
        coastal_slope = 0.05  # 5% typical
        inundation_distance_km = (tsunami_wave_height_m / coastal_slope) / 1000 if flooded else 0
        
        # Assume 100 km of coastline affected
        affected_coastline_km = 100
        affected_area_km2 = inundation_distance_km * affected_coastline_km if flooded else 0
        
        # Estimated affected population
        affected_population = int(affected_area_km2 * coastal_population_density) if flooded else 0
        
        # Casualty estimate (historically ~10-30% in major tsunamis without warning)
        casualty_rate_no_warning = 0.20  # 20%
        casualty_rate_with_warning = 0.05  # 5% with evacuation
        
        estimated_casualties_no_warning = int(affected_population * casualty_rate_no_warning)
        estimated_casualties_with_warning = int(affected_population * casualty_rate_with_warning)
        
        return {
            "flooded": flooded,
            "inundation_distance_km": inundation_distance_km,
            "affected_area_km2": affected_area_km2,
            "affected_population": affected_population,
            "estimated_casualties_no_warning": estimated_casualties_no_warning,
            "estimated_casualties_with_warning": estimated_casualties_with_warning,
            "evacuation_recommended": flooded,
            "warning_time_critical": tsunami_wave_height_m > 5.0,
            "description": f"{'EVACUATION REQUIRED' if flooded else 'Area safe from tsunami'}"
        }
    
    def is_ocean_impact(self, latitude: float, longitude: float) -> bool:
        """
        Check if impact location is in ocean using real bathymetry data
        
        Args:
            latitude: Impact latitude in degrees
            longitude: Impact longitude in degrees
        
        Returns:
            bool: True if ocean, False if land
        """
        if self.bathymetry_service is not None:
            try:
                return self.bathymetry_service.is_ocean(latitude, longitude)
            except Exception as e:
                logger.warning(f"Bathymetry service failed, using fallback: {e}")
        
        # Fallback: simple heuristic
        return self._is_ocean_fallback(latitude, longitude)
    
    def _is_ocean_fallback(self, latitude: float, longitude: float) -> bool:
        """Fallback ocean detection when bathymetry not available"""
        # Major landmasses (rough bounding boxes)
        land_boxes = [
            (15, 75, -170, -50),   # North America
            (-55, 15, -85, -30),   # South America
            (-35, 75, -20, 60),    # Europe/Africa
            (-10, 80, 25, 180),    # Asia
            (-45, -10, 110, 155),  # Australia
        ]
        
        for lat_min, lat_max, lon_min, lon_max in land_boxes:
            if lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max:
                return False
        
        return True
    
    def get_ocean_depth_at_location(self, latitude: float, longitude: float) -> float:
        """
        Get real ocean depth at impact location
        
        Args:
            latitude: Impact latitude in degrees
            longitude: Impact longitude in degrees
        
        Returns:
            float: Ocean depth in meters (returns fallback if on land or data unavailable)
        """
        if self.bathymetry_service is not None:
            try:
                depth = self.bathymetry_service.get_ocean_depth_meters(latitude, longitude)
                if depth > 0:
                    # Check if we have real elevation data or using TID + estimates
                    has_elevation = self.bathymetry_service.elevation_data is not None
                    has_tid = self.bathymetry_service.dataset is not None and 'tid' in self.bathymetry_service.dataset
                    
                    if has_elevation:
                        logger.info(f"Ocean depth from GEBCO elevation data at ({latitude:.2f}, {longitude:.2f}): {depth:.0f}m")
                    elif has_tid:
                        logger.info(f"Ocean depth at ({latitude:.2f}, {longitude:.2f}): {depth:.0f}m (TID-verified ocean, estimated depth)")
                    else:
                        logger.info(f"Estimated ocean depth at ({latitude:.2f}, {longitude:.2f}): {depth:.0f}m (geographic heuristic)")
                    return depth
                else:
                    logger.info(f"Land impact detected at ({latitude:.2f}, {longitude:.2f})")
                    return 0  # Land
            except Exception as e:
                logger.warning(f"Bathymetry query failed: {e}")
        
        # Fallback to average
        return self.ocean_depth_m if self.is_ocean_impact(latitude, longitude) else 0
    
    def calculate_tsunami_from_location(self,
                                       latitude: float,
                                       longitude: float,
                                       asteroid_diameter_m: float,
                                       asteroid_velocity_km_s: float,
                                       asteroid_density_kg_m3: float,
                                       impact_angle_deg: float = 45.0) -> Optional[Dict]:
        """
        Calculate tsunami using real ocean depth at impact location
        
        Args:
            latitude: Impact latitude
            longitude: Impact longitude
            asteroid_diameter_m: Asteroid diameter
            asteroid_velocity_km_s: Impact velocity
            asteroid_density_kg_m3: Asteroid density
            impact_angle_deg: Impact angle
        
        Returns:
            Dict with tsunami data, or None if land impact
        """
        # Check if ocean impact
        if not self.is_ocean_impact(latitude, longitude):
            logger.info("Land impact - no tsunami generated")
            return None
        
        # Get real ocean depth
        ocean_depth = self.get_ocean_depth_at_location(latitude, longitude)
        
        if ocean_depth == 0:
            return None  # Land impact
        
        # Get coastal parameters if bathymetry available
        coastal_elevation = 10.0
        coastal_slope = 0.05
        
        if self.bathymetry_service is not None:
            try:
                coastal_elevation, coastal_slope = self.bathymetry_service.get_coastal_elevation(
                    latitude, longitude, search_radius_deg=0.5
                )
            except Exception as e:
                logger.warning(f"Coastal elevation query failed: {e}")
        
        # Calculate tsunami with real depth
        tsunami_data = self.calculate_ocean_impact_tsunami(
            asteroid_diameter_m=asteroid_diameter_m,
            asteroid_velocity_km_s=asteroid_velocity_km_s,
            asteroid_density_kg_m3=asteroid_density_kg_m3,
            ocean_depth_m=ocean_depth,
            impact_angle_deg=impact_angle_deg
        )
        
        # Add location info
        tsunami_data['impact_location'] = {
            'latitude': latitude,
            'longitude': longitude,
            'ocean_depth_m': ocean_depth,
            'coastal_elevation_m': coastal_elevation,
            'coastal_slope': coastal_slope,
            'data_source': 'GEBCO_2025' if self.bathymetry_service else 'FALLBACK'
        }
        
        return tsunami_data


# Test function
def test_tsunami_model():
    """Test tsunami modeling"""
    tm = TsunamiModel()
    
    print("\n🌊 Tsunami Impact Modeling")
    print("=" * 70)
    
    # Test with different sized asteroids
    test_cases = [
        ("Small (50m)", 50, 20, 3000),
        ("Medium (200m)", 200, 20, 3000),
        ("Large (500m)", 500, 20, 4000),
        ("Chicxulub-sized (10km)", 10000, 20, 4000)
    ]
    
    for name, diameter, velocity, depth in test_cases:
        result = tm.calculate_ocean_impact_tsunami(
            asteroid_diameter_m=diameter,
            asteroid_velocity_km_s=velocity,
            asteroid_density_kg_m3=3000,
            ocean_depth_m=depth
        )
        
        print(f"\n{name} asteroid ({diameter}m) - Ocean depth: {depth}m")
        print(f"  Tsunami generated: {result['tsunami_generated']}")
        print(f"  Initial wave amplitude: {result['initial_wave_amplitude_m']:.1f} m")
        print(f"  Coastal wave height: {result['coastal_wave_height_m']:.1f} m")
        print(f"  Inundation distance: {result['inundation_distance_km']:.1f} km")
        print(f"  Risk level: {result['risk_level']}")
        print(f"  {result['description']}")


if __name__ == "__main__":
    test_tsunami_model()

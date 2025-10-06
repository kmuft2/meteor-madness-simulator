"""
Comprehensive danger assessment for asteroid impacts
Replaces USGS earthquake comparison with actual impact effects:
- Tsunami wave heights and coastal inundation
- Atmospheric dust and climate effects
- Population casualty estimates (using WorldPop 2020 real data)
- Infrastructure damage zones
- Global vs regional impact classification
"""

import math
import logging
from typing import Dict, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

# Import population service
try:
    from app.services.population_service import get_population_service
    POPULATION_DATA_AVAILABLE = True
except ImportError:
    logger.warning("Population service not available, using estimates")
    POPULATION_DATA_AVAILABLE = False

# Import bathymetry service for tsunami modeling
try:
    from app.services.bathymetry_service import get_bathymetry_service
    BATHYMETRY_AVAILABLE = True
except ImportError:
    logger.warning("Bathymetry service not available, using fallback depths")
    BATHYMETRY_AVAILABLE = False

# Import tsunami model
try:
    from app.physics.tsunami_model import TsunamiModel
    TSUNAMI_MODEL_AVAILABLE = True
except ImportError:
    logger.warning("Tsunami model not available")
    TSUNAMI_MODEL_AVAILABLE = False


class ImpactSeverity(str, Enum):
    """Impact severity classification based on energy"""
    NEGLIGIBLE = "negligible"  # < 1 KT (burns up in atmosphere)
    LOCAL = "local"  # 1 KT - 1 MT (city block to small city)
    REGIONAL = "regional"  # 1-100 MT (major city to small country)
    CONTINENTAL = "continental"  # 100-10,000 MT (continent-wide effects)
    GLOBAL = "global"  # > 10,000 MT (mass extinction potential)


class DangerAssessment:
    """
    Calculate comprehensive impact dangers using established scientific models
    """
    
    # Constants
    EARTH_RADIUS_KM = 6371.0
    OCEAN_COVERAGE = 0.71  # 71% of Earth is water
    
    def __init__(self):
        pass
    
    def assess_impact(
        self,
        energy_mt_tnt: float,
        crater_diameter_m: float,
        crater_depth_m: float,
        latitude: float,
        longitude: float,
        impact_angle_deg: float = 45.0,
        asteroid_diameter_m: float = 100.0,
        velocity_km_s: float = 20.0
    ) -> Dict:
        """
        Complete danger assessment for an asteroid impact
        
        Args:
            energy_mt_tnt: Impact energy in megatons TNT
            crater_diameter_m: Crater diameter in meters
            crater_depth_m: Crater depth in meters
            latitude: Impact latitude
            longitude: Impact longitude
            impact_angle_deg: Impact angle (degrees from horizontal)
            asteroid_diameter_m: Asteroid diameter in meters
            velocity_km_s: Impact velocity in km/s
            
        Returns:
            Dictionary with comprehensive danger metrics
        """
        # Classify impact severity
        severity = self._classify_severity(energy_mt_tnt)
        
        # Check if ocean or land impact
        is_ocean_impact = self._is_ocean_impact(latitude, longitude)
        
        # Calculate damage zones
        damage_zones = self._calculate_damage_zones(energy_mt_tnt, crater_diameter_m)
        
        # Calculate casualties (rough estimate)
        casualties = self._estimate_casualties(damage_zones, latitude, longitude)
        
        # Calculate tsunami if ocean impact
        tsunami_data = None
        if is_ocean_impact:
            tsunami_data = self._calculate_tsunami(
                energy_mt_tnt,
                crater_diameter_m,
                latitude,
                longitude,
                asteroid_diameter_m,
                velocity_km_s,
                impact_angle_deg
            )
        
        # Calculate atmospheric effects
        atmospheric_effects = self._calculate_atmospheric_effects(
            energy_mt_tnt,
            asteroid_diameter_m,
            is_ocean_impact
        )
        
        # Calculate ejecta curtain
        ejecta = self._calculate_ejecta(crater_diameter_m, energy_mt_tnt)
        
        # Global effects threshold
        global_effects = self._assess_global_effects(energy_mt_tnt, atmospheric_effects)
        
        return {
            "severity": severity,
            "impact_type": "ocean" if is_ocean_impact else "land",
            "damage_zones": damage_zones,
            "casualties": casualties,
            "tsunami": tsunami_data,
            "atmospheric_effects": atmospheric_effects,
            "ejecta": ejecta,
            "global_effects": global_effects,
            "comparable_to": self._get_comparison(energy_mt_tnt)
        }
    
    def _classify_severity(self, energy_mt: float) -> str:
        """Classify impact severity based on energy"""
        if energy_mt < 0.001:
            return ImpactSeverity.NEGLIGIBLE
        elif energy_mt < 1.0:
            return ImpactSeverity.LOCAL
        elif energy_mt < 100.0:
            return ImpactSeverity.REGIONAL
        elif energy_mt < 10000.0:
            return ImpactSeverity.CONTINENTAL
        else:
            return ImpactSeverity.GLOBAL
    
    def _is_ocean_impact(self, lat: float, lon: float) -> bool:
        """
        Check if impact is in ocean using real bathymetry data
        NO FALLBACK - will raise error if data not available
        """
        # Use real bathymetry data - NO FALLBACK
        if BATHYMETRY_AVAILABLE:
            bathymetry_service = get_bathymetry_service()
            is_ocean = bathymetry_service.is_ocean(lat, lon)
            logger.info(f"Bathymetry check: ({lat:.2f}, {lon:.2f}) -> {'ocean' if is_ocean else 'land'}")
            return is_ocean
        
        raise ImportError("Bathymetry service not available - check h5py installation")
    
    def _calculate_damage_zones(self, energy_mt: float, crater_diameter_m: float) -> Dict:
        """
        Calculate concentric damage zones based on overpressure
        Uses Glasstone & Dolan (1977) nuclear weapons effects scaling
        """
        # Zone radii in km
        zones = {}
        
        # Total destruction (>20 psi overpressure)
        # Everything destroyed, 100% fatalities
        zones["total_destruction_km"] = 0.5 * (energy_mt ** (1/3))
        
        # Severe damage (5-20 psi)
        # Buildings collapse, ~50% fatalities
        zones["severe_damage_km"] = 1.5 * (energy_mt ** (1/3))
        
        # Moderate damage (1-5 psi)
        # Windows shatter, some building damage, ~5% fatalities
        zones["moderate_damage_km"] = 3.0 * (energy_mt ** (1/3))
        
        # Light damage (0.5-1 psi)
        # Windows break, minor injuries
        zones["light_damage_km"] = 5.0 * (energy_mt ** (1/3))
        
        # Thermal burns (3rd degree)
        thermal_energy = 0.3 * energy_mt  # 30% thermal radiation
        zones["thermal_burns_km"] = 1.2 * (thermal_energy ** 0.4)
        
        # Fireball radius (vaporization zone)
        zones["fireball_km"] = 0.09 * (energy_mt ** 0.4)
        
        return zones
    
    def _estimate_casualties(self, damage_zones: Dict, lat: float, lon: float) -> Dict:
        """
        Calculate accurate casualties using WorldPop 2020 real population data
        Queries all damage zones and applies appropriate fatality/injury rates
        """
        if not POPULATION_DATA_AVAILABLE:
            return self._estimate_casualties_fallback(damage_zones, lat, lon)
        
        try:
            pop_service = get_population_service()
            
            # Define zone radii to query (sorted smallest to largest)
            zone_radii = [
                damage_zones["fireball_km"],
                damage_zones["total_destruction_km"],
                damage_zones["severe_damage_km"],
                damage_zones["moderate_damage_km"],
                damage_zones["light_damage_km"]
            ]
            
            # Get real population data for all zones
            pop_data = pop_service.get_population_in_zones(
                latitude=lat,
                longitude=lon,
                zone_radii_km=zone_radii
            )
            
            # Extract populations per zone
            zones = pop_data['zones']
            
            # Fatality rates per zone based on overpressure
            # Fireball: 100% (vaporized)
            # Total destruction (>20 psi): 100%
            # Severe damage (5-20 psi): 50%
            # Moderate damage (1-5 psi): 5%
            # Light damage (0.5-1 psi): 0.1%
            
            fireball_pop = zones[0]['annular_population']
            total_dest_pop = zones[1]['annular_population']
            severe_pop = zones[2]['annular_population']
            moderate_pop = zones[3]['annular_population']
            light_pop = zones[4]['annular_population']
            
            # Calculate deaths
            immediate_deaths = (
                fireball_pop * 1.0 +       # 100% vaporized
                total_dest_pop * 1.0 +     # 100% killed
                severe_pop * 0.5 +         # 50% killed
                moderate_pop * 0.05 +      # 5% killed
                light_pop * 0.001          # 0.1% killed
            )
            
            # Calculate injured (survivors with injuries)
            injured = (
                total_dest_pop * 0.0 +     # No survivors to injure
                severe_pop * 0.4 +         # 40% of survivors injured
                moderate_pop * 0.3 +       # 30% injured
                light_pop * 0.1            # 10% injured
            )
            
            total_affected = pop_data['total_affected']
            
            # Add thermal burns casualties (overlapping but additional)
            thermal_radius = damage_zones["thermal_burns_km"]
            thermal_pop_data = pop_service.get_population_in_zones(
                latitude=lat,
                longitude=lon,
                zone_radii_km=[thermal_radius]
            )
            thermal_casualties = int(thermal_pop_data['total_affected'] * 0.1)  # 10% burn injuries
            
            casualties_dict = {
                "immediate_deaths_estimate": int(immediate_deaths),
                "injured_estimate": int(injured + thermal_casualties),
                "affected_population": total_affected,
                "data_source": pop_data['data_source'],
                "country_code": pop_data.get('country_code', 'UNKNOWN'),
                "zone_breakdown": {
                    "fireball": {"population": fireball_pop, "fatality_rate": 1.0},
                    "total_destruction": {"population": total_dest_pop, "fatality_rate": 1.0},
                    "severe_damage": {"population": severe_pop, "fatality_rate": 0.5},
                    "moderate_damage": {"population": moderate_pop, "fatality_rate": 0.05},
                    "light_damage": {"population": light_pop, "fatality_rate": 0.001}
                },
                "note": "Using WorldPop 2020 real population data for accurate estimates"
            }
            
            # Add detailed location info (city, state, country name, etc.)
            if 'location_info' in pop_data:
                casualties_dict['location_info'] = pop_data['location_info']
            
            return casualties_dict
        
        except Exception as e:
            logger.error(f"Error calculating casualties with real data: {e}")
            return self._estimate_casualties_fallback(damage_zones, lat, lon)
    
    def _estimate_casualties_fallback(self, damage_zones: Dict, lat: float, lon: float) -> Dict:
        """Fallback casualty estimate using average density"""
        avg_density = 60  # Global average people per km²
        
        fireball_area = math.pi * (damage_zones["fireball_km"] ** 2)
        total_dest_area = math.pi * (damage_zones["total_destruction_km"] ** 2) - fireball_area
        severe_area = math.pi * (damage_zones["severe_damage_km"] ** 2) - total_dest_area - fireball_area
        moderate_area = math.pi * (damage_zones["moderate_damage_km"] ** 2) - severe_area - total_dest_area - fireball_area
        
        immediate_deaths = (
            fireball_area * avg_density * 1.0 +
            total_dest_area * avg_density * 1.0 +
            severe_area * avg_density * 0.5 +
            moderate_area * avg_density * 0.05
        )
        
        injured = (
            severe_area * avg_density * 0.4 +
            moderate_area * avg_density * 0.3
        )
        
        total_affected = (fireball_area + total_dest_area + severe_area + moderate_area) * avg_density
        
        return {
            "immediate_deaths_estimate": int(immediate_deaths),
            "injured_estimate": int(injured),
            "affected_population": int(total_affected),
            "data_source": "FALLBACK_GLOBAL_AVERAGE",
            "note": "Using global average density - real population data not available"
        }
    
    def _calculate_tsunami(
        self, 
        energy_mt: float, 
        crater_diameter_m: float,
        latitude: float,
        longitude: float,
        asteroid_diameter_m: float,
        velocity_km_s: float,
        impact_angle_deg: float
    ) -> Dict:
        """
        Calculate tsunami using real bathymetry data from GEBCO
        NO FALLBACK - will raise error if data not available
        """
        # Use advanced tsunami model with real bathymetry - NO FALLBACK
        if not TSUNAMI_MODEL_AVAILABLE:
            raise ImportError("Tsunami model not available")
        if not BATHYMETRY_AVAILABLE:
            raise ImportError("Bathymetry service not available")
        
        bathymetry_service = get_bathymetry_service()
        tsunami_model = TsunamiModel(bathymetry_service=bathymetry_service)
        
        tsunami_data = tsunami_model.calculate_tsunami_from_location(
            latitude=latitude,
            longitude=longitude,
            asteroid_diameter_m=asteroid_diameter_m,
            asteroid_velocity_km_s=velocity_km_s,
            asteroid_density_kg_m3=3000,  # Typical asteroid density
            impact_angle_deg=impact_angle_deg
        )
        
        if tsunami_data:
            logger.info("✓ Using GEBCO bathymetry for tsunami calculation")
            return tsunami_data
        
        raise ValueError("Tsunami calculation returned None (likely land impact)")
    
    def _calculate_tsunami_fallback(self, energy_mt: float, crater_diameter_m: float, water_depth_m: float) -> Dict:
        """
        Fallback tsunami calculation when bathymetry not available
        Based on Ward & Asphaug (2000) - asteroid tsunami scaling
        """
        # Energy in joules
        energy_j = energy_mt * 4.184e15
        
        # Tsunami wave height at source (meters)
        # H0 = (E / (ρ * g * d²))^(1/2) where:
        # E = energy, ρ = water density, g = gravity, d = water depth
        rho_water = 1025  # kg/m³
        g = 9.81  # m/s²
        
        # Wave height at crater
        h0 = math.sqrt(energy_j / (rho_water * g * (water_depth_m ** 2)))
        
        # Deep water tsunami velocity (km/h)
        tsunami_velocity_kmh = 3.6 * math.sqrt(g * water_depth_m)
        
        # Wave heights at various distances (using geometric spreading and energy dissipation)
        distances_km = [10, 50, 100, 500, 1000, 5000]
        wave_heights = {}
        
        for dist_km in distances_km:
            dist_m = dist_km * 1000
            # Simplified geometric spreading: H ~ H0 * sqrt(r0/r)
            # Where r0 is source radius (crater diameter/2)
            r0_m = crater_diameter_m / 2
            if dist_m > r0_m:
                height_m = h0 * math.sqrt(r0_m / dist_m) * math.exp(-dist_m / 1e6)  # Exponential decay
                wave_heights[f"{dist_km}_km"] = max(0.1, height_m)
            else:
                wave_heights[f"{dist_km}_km"] = h0
        
        # Coastal inundation distance (rough estimate)
        # Runup = 2-4x wave height, inundation ~ 100m per meter of runup
        coastal_inundation_m = wave_heights.get("100_km", 1.0) * 3 * 100
        
        return {
            "wave_height_at_source_m": round(h0, 1),
            "tsunami_velocity_kmh": round(tsunami_velocity_kmh, 1),
            "wave_heights_at_distance": {k: round(v, 2) for k, v in wave_heights.items()},
            "coastal_inundation_distance_m": round(coastal_inundation_m, 0),
            "arrival_time_hours": {
                "100_km": round(100 / tsunami_velocity_kmh, 2),
                "500_km": round(500 / tsunami_velocity_kmh, 2),
                "1000_km": round(1000 / tsunami_velocity_kmh, 2),
            },
            "warning": "Ocean impact - tsunami will affect all coastlines within 5000 km"
        }
    
    def _calculate_atmospheric_effects(self, energy_mt: float, diameter_m: float, is_ocean: bool) -> Dict:
        """
        Calculate atmospheric dust, soot, and climate effects
        Based on Toon et al. (1997) - impact winter scaling
        """
        # Dust injected into stratosphere (kg)
        # Scales with crater volume and ejecta velocity
        crater_volume_m3 = (math.pi / 3) * ((diameter_m * 10) ** 2) * (diameter_m * 10 * 0.1)
        ejecta_mass_kg = crater_volume_m3 * 2500  # crustal density
        
        # Fraction that reaches stratosphere (> 20km altitude)
        stratospheric_fraction = 0.001 if energy_mt < 100 else 0.01 if energy_mt < 10000 else 0.1
        stratospheric_dust_kg = ejecta_mass_kg * stratospheric_fraction
        
        # Global dust loading (kg/m² of Earth surface)
        earth_surface_m2 = 4 * math.pi * (self.EARTH_RADIUS_KM * 1000) ** 2
        dust_loading = stratospheric_dust_kg / earth_surface_m2
        
        # Temperature drop (rough estimate)
        # From impact winter studies: ~0.01°C per 1 mg/m² of stratospheric dust
        temp_drop_c = dust_loading * 1000 * 0.01  # Convert kg to mg
        
        # Duration of effects
        if temp_drop_c < 1:
            duration = "days to weeks"
        elif temp_drop_c < 10:
            duration = "months to years"
        else:
            duration = "years to decades"
        
        # Soot from fires (land impacts)
        soot_mass_kg = 0
        if not is_ocean and energy_mt > 1:
            # Wildfires ignited by thermal radiation
            fire_area_km2 = math.pi * (1.2 * (energy_mt ** 0.4)) ** 2
            soot_mass_kg = fire_area_km2 * 1e6 * 0.01  # ~0.01 kg/m² soot
        
        return {
            "stratospheric_dust_kg": round(stratospheric_dust_kg, 0),
            "global_dust_loading_mg_m2": round(dust_loading * 1e6, 3),
            "temperature_drop_celsius": round(temp_drop_c, 2),
            "effect_duration": duration,
            "soot_from_fires_kg": round(soot_mass_kg, 0) if soot_mass_kg > 0 else None,
            "sunlight_reduction_percent": min(90, round(dust_loading * 1e6 * 2, 1)),
            "note": "Large impacts cause 'impact winter' - global cooling from stratospheric dust"
        }
    
    def _calculate_ejecta(self, crater_diameter_m: float, energy_mt: float) -> Dict:
        """
        Calculate ejecta blanket and ballistic debris
        """
        # Ejecta blanket extends 2-3x crater radius
        ejecta_radius_km = (crater_diameter_m / 1000) * 2.5
        
        # Ballistic ejecta can travel 1000s of km for large impacts
        if energy_mt > 1000:
            max_range_km = min(5000, 100 * (energy_mt ** 0.25))
        else:
            max_range_km = min(1000, 50 * (energy_mt ** 0.3))
        
        # Re-entry heating of ejecta can cause global fires
        global_fires = energy_mt > 100000  # Chicxulub-scale
        
        return {
            "ejecta_blanket_radius_km": round(ejecta_radius_km, 2),
            "ballistic_range_km": round(max_range_km, 1),
            "ejecta_thickness_at_crater_m": round(crater_diameter_m * 0.02, 1),
            "global_fires_from_reentry": global_fires,
            "note": "Ejecta blanket buries everything; ballistic debris causes fires from re-entry heating"
        }
    
    def _assess_global_effects(self, energy_mt: float, atmospheric: Dict) -> Dict:
        """
        Determine if impact has global consequences
        """
        is_global = energy_mt > 10000  # > 10,000 MT = global effects
        
        effects = {
            "is_global_catastrophe": is_global,
            "mass_extinction_risk": energy_mt > 100000,  # Chicxulub was ~100 million MT
            "crop_failure_risk": atmospheric["temperature_drop_celsius"] > 2,
            "global_famine_risk": atmospheric["temperature_drop_celsius"] > 5,
            "civilization_threat": energy_mt > 50000,
        }
        
        if is_global:
            effects["description"] = "Global catastrophe - worldwide climate disruption and mass casualties"
        elif energy_mt > 100:
            effects["description"] = "Continental disaster - regional devastation with global economic impact"
        else:
            effects["description"] = "Regional disaster - localized destruction"
        
        return effects
    
    def _get_comparison(self, energy_mt: float) -> str:
        """
        Human-understandable comparison
        """
        if energy_mt < 0.001:
            return "Large firework"
        elif energy_mt < 0.015:
            return "Small tactical nuclear weapon (Hiroshima was ~0.015 MT)"
        elif energy_mt < 1:
            return f"{int(energy_mt * 1000)} Kilotons - Large nuclear weapon"
        elif energy_mt < 15:
            return "Tunguska event (1908) - Leveled 2,000 km² of forest"
        elif energy_mt < 100:
            return f"~{int(energy_mt)} times Hiroshima - Major city destroyer"
        elif energy_mt < 1000:
            return "Tsar Bomba scale - Largest nuclear weapon ever tested (50 MT)"
        elif energy_mt < 100000:
            return "Continental devastation - Multi-state destruction"
        else:
            return "Chicxulub scale - Mass extinction event (killed the dinosaurs)"


def format_danger_report(assessment: Dict, energy_mt: float) -> str:
    """
    Format danger assessment into human-readable report
    """
    report = []
    report.append(f"=" * 70)
    report.append(f"ASTEROID IMPACT DANGER ASSESSMENT")
    report.append(f"=" * 70)
    report.append(f"Severity: {assessment['severity'].upper()}")
    report.append(f"Impact Type: {assessment['impact_type'].upper()}")
    report.append(f"Energy: {energy_mt:.2f} Megatons TNT")
    report.append(f"Comparable to: {assessment['comparable_to']}")
    report.append("")
    
    # Damage zones
    report.append("DAMAGE ZONES:")
    zones = assessment['damage_zones']
    report.append(f"  Fireball (vaporization): {zones['fireball_km']:.1f} km radius")
    report.append(f"  Total destruction: {zones['total_destruction_km']:.1f} km radius")
    report.append(f"  Severe damage: {zones['severe_damage_km']:.1f} km radius")
    report.append(f"  Moderate damage: {zones['moderate_damage_km']:.1f} km radius")
    report.append(f"  Thermal burns: {zones['thermal_burns_km']:.1f} km radius")
    report.append("")
    
    # Casualties
    cas = assessment['casualties']
    report.append("CASUALTY ESTIMATES:")
    report.append(f"  Immediate deaths: ~{cas['immediate_deaths_estimate']:,}")
    report.append(f"  Injured: ~{cas['injured_estimate']:,}")
    report.append(f"  Affected population: ~{cas['affected_population']:,}")
    report.append("")
    
    # Tsunami
    if assessment['tsunami']:
        tsunami = assessment['tsunami']
        report.append("TSUNAMI EFFECTS:")
        report.append(f"  Wave height at source: {tsunami['wave_height_at_source_m']:.1f} meters")
        report.append(f"  Tsunami velocity: {tsunami['tsunami_velocity_kmh']:.0f} km/h")
        report.append(f"  Coastal inundation: {tsunami['coastal_inundation_distance_m']:.0f} meters inland")
        report.append(f"  Wave heights:")
        for dist, height in tsunami['wave_heights_at_distance'].items():
            report.append(f"    At {dist}: {height:.1f} meters")
        report.append("")
    
    # Atmospheric
    atm = assessment['atmospheric_effects']
    report.append("ATMOSPHERIC EFFECTS:")
    report.append(f"  Temperature drop: {atm['temperature_drop_celsius']:.1f}°C")
    report.append(f"  Sunlight reduction: {atm['sunlight_reduction_percent']:.0f}%")
    report.append(f"  Duration: {atm['effect_duration']}")
    report.append("")
    
    # Global effects
    global_fx = assessment['global_effects']
    report.append("GLOBAL IMPACT:")
    report.append(f"  {global_fx['description']}")
    if global_fx['mass_extinction_risk']:
        report.append(f"  ⚠️  MASS EXTINCTION RISK")
    report.append(f"=" * 70)
    
    return "\n".join(report)


if __name__ == "__main__":
    # Test with Tunguska
    assessor = DangerAssessment()
    
    result = assessor.assess_impact(
        energy_mt_tnt=15.0,
        crater_diameter_m=150,
        crater_depth_m=15,
        latitude=60.886,
        longitude=101.894,
        asteroid_diameter_m=50,
        velocity_km_s=27
    )
    
    print(format_danger_report(result, 15.0))

"""
Asteroid Deflection and Mitigation Strategies
Models different approaches to preventing asteroid impacts
"""

import math
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

# Physical constants
AU_TO_KM = 149597870.7
EARTH_MASS = 5.972e24  # kg
G = 6.67430e-11  # Gravitational constant m^3 kg^-1 s^-2


class DeflectionStrategies:
    """Model various asteroid deflection strategies"""
    
    def __init__(self):
        pass
    
    def kinetic_impactor(self,
                        asteroid_mass_kg: float,
                        asteroid_velocity_km_s: float,
                        impactor_mass_kg: float,
                        impactor_velocity_km_s: float,
                        impact_efficiency: float = 1.0,
                        years_before_impact: float = 10.0) -> Dict:
        """
        Calculate deflection from kinetic impactor (DART-style mission)
        
        Args:
            asteroid_mass_kg: Mass of asteroid
            asteroid_velocity_km_s: Orbital velocity of asteroid
            impactor_mass_kg: Mass of spacecraft impactor
            impactor_velocity_km_s: Relative impact velocity
            impact_efficiency: Momentum enhancement factor (1-5, typically ~3-4)
            years_before_impact: Time before potential Earth impact
        
        Returns:
            Dict with deflection results and success probability
        """
        # Convert to m/s
        v_asteroid = asteroid_velocity_km_s * 1000
        v_impactor = impactor_velocity_km_s * 1000
        
        # Momentum transfer (with enhancement from ejecta)
        momentum_change = impactor_mass_kg * v_impactor * impact_efficiency
        
        # Velocity change of asteroid (Δv)
        delta_v = momentum_change / asteroid_mass_kg  # m/s
        
        # Distance deflection after given time
        time_seconds = years_before_impact * 365.25 * 24 * 3600
        deflection_distance_km = (delta_v * time_seconds) / 1000
        
        # Earth's radius for comparison
        earth_radius_km = 6371
        
        # Success if deflection > Earth radius
        success = deflection_distance_km > earth_radius_km
        success_margin = deflection_distance_km / earth_radius_km
        
        return {
            "strategy": "Kinetic Impactor",
            "delta_v_m_s": delta_v,
            "delta_v_cm_s": delta_v * 100,  # More readable unit
            "momentum_transfer_kg_m_s": momentum_change,
            "deflection_distance_km": deflection_distance_km,
            "years_before_impact": years_before_impact,
            "success": success,
            "success_margin": success_margin,
            "impactor_mass_kg": impactor_mass_kg,
            "impact_efficiency": impact_efficiency,
            "description": f"Spacecraft impact delivering {momentum_change/1e6:.1f} MN·s of momentum",
            "example_mission": "NASA DART (Double Asteroid Redirection Test)",
            "feasibility": "HIGH" if success else "LOW"
        }
    
    def gravity_tractor(self,
                       asteroid_mass_kg: float,
                       asteroid_diameter_m: float,
                       spacecraft_mass_kg: float,
                       operation_time_years: float = 10.0,
                       standoff_distance_m: float = 100.0) -> Dict:
        """
        Calculate deflection from gravity tractor
        
        A spacecraft hovers near asteroid and uses mutual gravity to tug it off course
        
        Args:
            asteroid_mass_kg: Mass of asteroid
            asteroid_diameter_m: Diameter for calculating approach distance
            spacecraft_mass_kg: Mass of tractor spacecraft
            operation_time_years: Time spacecraft operates
            standoff_distance_m: Distance spacecraft maintains from asteroid
        
        Returns:
            Dict with deflection results
        """
        # Gravitational force between spacecraft and asteroid
        distance_m = asteroid_diameter_m / 2 + standoff_distance_m
        force = G * asteroid_mass_kg * spacecraft_mass_kg / (distance_m ** 2)
        
        # Acceleration of asteroid
        acceleration = force / asteroid_mass_kg  # m/s²
        
        # Time in seconds
        time_seconds = operation_time_years * 365.25 * 24 * 3600
        
        # Velocity change (assuming constant acceleration)
        delta_v = acceleration * time_seconds  # m/s
        
        # Distance deflection
        deflection_distance_km = (delta_v * time_seconds) / (2 * 1000)  # km
        
        # Success criteria
        earth_radius_km = 6371
        success = deflection_distance_km > earth_radius_km
        success_margin = deflection_distance_km / earth_radius_km
        
        return {
            "strategy": "Gravity Tractor",
            "delta_v_m_s": delta_v,
            "delta_v_cm_s": delta_v * 100,
            "gravitational_force_N": force,
            "acceleration_m_s2": acceleration,
            "deflection_distance_km": deflection_distance_km,
            "operation_time_years": operation_time_years,
            "spacecraft_mass_kg": spacecraft_mass_kg,
            "standoff_distance_m": standoff_distance_m,
            "success": success,
            "success_margin": success_margin,
            "description": f"Continuous {force*1e9:.2f} nN gravitational tug over {operation_time_years:.1f} years",
            "advantages": "Precise, no impact, works on any composition",
            "disadvantages": "Very slow, requires long warning time",
            "feasibility": "MEDIUM" if success else "LOW"
        }
    
    def nuclear_standoff(self,
                        asteroid_mass_kg: float,
                        asteroid_diameter_m: float,
                        nuclear_yield_megatons: float = 1.0,
                        standoff_distance_m: float = 100.0,
                        ablation_efficiency: float = 0.1,
                        years_before_impact: float = 10.0) -> Dict:
        """
        Calculate deflection from nuclear standoff burst
        
        Nuclear device detonated near (not on) asteroid, ablating surface material
        
        Args:
            asteroid_mass_kg: Mass of asteroid
            asteroid_diameter_m: Diameter of asteroid  
            nuclear_yield_megatons: Yield of nuclear device (MT)
            standoff_distance_m: Detonation distance from surface
            ablation_efficiency: Fraction of energy that causes ablation (0-1)
            years_before_impact: Time before potential impact
        
        Returns:
            Dict with deflection results
        """
        # Convert yield to joules
        yield_joules = nuclear_yield_megatons * 4.184e15  # 1 MT = 4.184e15 J
        
        # Energy absorbed by asteroid (inverse square law + efficiency)
        asteroid_surface_area = math.pi * (asteroid_diameter_m / 2) ** 2
        solid_angle_fraction = asteroid_surface_area / (4 * math.pi * standoff_distance_m ** 2)
        
        absorbed_energy = yield_joules * solid_angle_fraction * ablation_efficiency
        
        # Estimate ablated mass (assuming ~5 MJ/kg to ablate rock)
        ablation_energy = 5e6  # J/kg
        ablated_mass_kg = absorbed_energy / ablation_energy
        
        # Rocket equation: Δv = v_exhaust * ln(m_initial / m_final)
        # Approximate exhaust velocity for ablated rock: ~5-10 km/s
        v_exhaust = 7000  # m/s (middle estimate)
        
        mass_ratio = asteroid_mass_kg / (asteroid_mass_kg - ablated_mass_kg)
        delta_v = v_exhaust * math.log(mass_ratio)  # m/s
        
        # Distance deflection
        time_seconds = years_before_impact * 365.25 * 24 * 3600
        deflection_distance_km = (delta_v * time_seconds) / 1000
        
        # Success criteria
        earth_radius_km = 6371
        success = deflection_distance_km > earth_radius_km
        success_margin = deflection_distance_km / earth_radius_km
        
        return {
            "strategy": "Nuclear Standoff Burst",
            "delta_v_m_s": delta_v,
            "delta_v_cm_s": delta_v * 100,
            "nuclear_yield_mt": nuclear_yield_megatons,
            "absorbed_energy_joules": absorbed_energy,
            "ablated_mass_kg": ablated_mass_kg,
            "ablated_mass_fraction": ablated_mass_kg / asteroid_mass_kg,
            "deflection_distance_km": deflection_distance_km,
            "years_before_impact": years_before_impact,
            "success": success,
            "success_margin": success_margin,
            "description": f"{nuclear_yield_megatons} MT standoff burst ablating {ablated_mass_kg:.0f} kg of surface material",
            "advantages": "Very powerful, works on large asteroids",
            "disadvantages": "Political/legal challenges, radioactive contamination risk",
            "feasibility": "MEDIUM" if success else "LOW",
            "warning": "Last resort option - requires international approval"
        }
    
    def ion_beam_shepherd(self,
                         asteroid_mass_kg: float,
                         ion_thrust_newtons: float = 1.0,
                         operation_time_years: float = 15.0) -> Dict:
        """
        Calculate deflection from ion beam shepherd
        
        Spacecraft uses ion thruster to push against asteroid
        
        Args:
            asteroid_mass_kg: Mass of asteroid
            ion_thrust_newtons: Thrust of ion engine
            operation_time_years: Time of operation
        
        Returns:
            Dict with deflection results
        """
        # Acceleration
        acceleration = ion_thrust_newtons / asteroid_mass_kg  # m/s²
        
        # Time in seconds
        time_seconds = operation_time_years * 365.25 * 24 * 3600
        
        # Velocity change
        delta_v = acceleration * time_seconds  # m/s
        
        # Distance deflection
        deflection_distance_km = (delta_v * time_seconds) / (2 * 1000)
        
        # Success criteria
        earth_radius_km = 6371
        success = deflection_distance_km > earth_radius_km
        success_margin = deflection_distance_km / earth_radius_km
        
        return {
            "strategy": "Ion Beam Shepherd",
            "delta_v_m_s": delta_v,
            "delta_v_cm_s": delta_v * 100,
            "ion_thrust_N": ion_thrust_newtons,
            "acceleration_m_s2": acceleration,
            "deflection_distance_km": deflection_distance_km,
            "operation_time_years": operation_time_years,
            "success": success,
            "success_margin": success_margin,
            "description": f"Continuous {ion_thrust_newtons} N ion thrust over {operation_time_years:.1f} years",
            "advantages": "Continuous thrust, very efficient propulsion",
            "disadvantages": "Requires spacecraft to maintain position",
            "feasibility": "MEDIUM" if success else "LOW"
        }
    
    def compare_all_strategies(self,
                              asteroid_diameter_m: float,
                              asteroid_density_kg_m3: float,
                              years_before_impact: float) -> Dict:
        """
        Compare all deflection strategies for a given asteroid and warning time
        
        Args:
            asteroid_diameter_m: Diameter of asteroid in meters
            asteroid_density_kg_m3: Density of asteroid
            years_before_impact: Warning time in years
        
        Returns:
            Dict comparing all strategies
        """
        # Calculate asteroid mass
        radius_m = asteroid_diameter_m / 2
        volume_m3 = (4/3) * math.pi * (radius_m ** 3)
        asteroid_mass_kg = volume_m3 * asteroid_density_kg_m3
        
        # Calculate each strategy
        strategies = {
            "kinetic_impactor": self.kinetic_impactor(
                asteroid_mass_kg, 30.0, 500, 6.0, 3.0, years_before_impact
            ),
            "gravity_tractor": self.gravity_tractor(
                asteroid_mass_kg, asteroid_diameter_m, 20000, years_before_impact
            ),
            "nuclear_standoff": self.nuclear_standoff(
                asteroid_mass_kg, asteroid_diameter_m, 1.0, 100, 0.1, years_before_impact
            ),
            "ion_beam": self.ion_beam_shepherd(
                asteroid_mass_kg, 1.0, years_before_impact
            )
        }
        
        # Sort by success and deflection distance
        sorted_strategies = sorted(
            strategies.items(),
            key=lambda x: (x[1]['success'], x[1]['deflection_distance_km']),
            reverse=True
        )
        
        return {
            "asteroid_diameter_m": asteroid_diameter_m,
            "asteroid_mass_kg": asteroid_mass_kg,
            "years_before_impact": years_before_impact,
            "strategies": strategies,
            "recommended": sorted_strategies[0][0] if sorted_strategies else None,
            "all_successful": all(s['success'] for s in strategies.values()),
            "comparison_summary": {
                name: {
                    "success": data['success'],
                    "deflection_km": data['deflection_distance_km'],
                    "delta_v_cm_s": data['delta_v_cm_s'],
                    "feasibility": data.get('feasibility', 'UNKNOWN')
                }
                for name, data in strategies.items()
            }
        }


# Test function
def test_deflection_strategies():
    """Test deflection strategy calculations"""
    ds = DeflectionStrategies()
    
    print("\n🚀 Asteroid Deflection Strategy Comparison")
    print("=" * 70)
    
    # Test with Apophis-sized asteroid (370m diameter)
    result = ds.compare_all_strategies(
        asteroid_diameter_m=370,
        asteroid_density_kg_m3=3200,
        years_before_impact=10
    )
    
    print(f"\nAsteroid: {result['asteroid_diameter_m']}m diameter")
    print(f"Mass: {result['asteroid_mass_kg']/1e9:.2f} billion kg")
    print(f"Warning time: {result['years_before_impact']} years")
    print(f"\nRecommended strategy: {result['recommended'].upper()}")
    print("\nStrategy Comparison:")
    
    for name, summary in result['comparison_summary'].items():
        status = "✅" if summary['success'] else "❌"
        print(f"\n{status} {name.replace('_', ' ').title()}:")
        print(f"   Deflection: {summary['deflection_km']:.1f} km")
        print(f"   Δv: {summary['delta_v_cm_s']:.2f} cm/s")
        print(f"   Feasibility: {summary['feasibility']}")


if __name__ == "__main__":
    test_deflection_strategies()

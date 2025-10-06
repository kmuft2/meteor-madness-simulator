"""
Enhanced physics engine for asteroid impact calculations
Includes CUDA support with CPU fallback for scientific accuracy
"""

import math
import logging
from typing import List, Dict, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Try to import CUDA libraries
try:
    import cupy as cp
    from numba import cuda
    CUDA_AVAILABLE = True
    logger.info("CUDA libraries available")
except ImportError:
    CUDA_AVAILABLE = False
    logger.warning("CUDA not available, using CPU fallback")


class EnhancedPhysicsEngine:
    """
    Enhanced physics engine for asteroid impact simulation
    Based on NASA orbital mechanics standards and USGS seismic scaling
    """
    
    def __init__(self):
        self.device_available = self._check_cuda_availability()
        
        if self.device_available:
            logger.info("✅ CUDA GPU enabled for physics calculations")
        else:
            logger.info("ℹ️ Using CPU fallback for physics calculations")
    
    def _check_cuda_availability(self) -> bool:
        """Check if CUDA is available and functional"""
        if not CUDA_AVAILABLE:
            return False
        
        try:
            cp.cuda.runtime.getDeviceCount()
            # Try a simple operation
            test = cp.array([1, 2, 3])
            test = test * 2
            return True
        except Exception:
            # CUDA not functional - silently fall back to CPU
            # This is normal if CUDA toolkit isn't installed
            return False
    
    def compute_impact_effects(self, asteroid_params: Dict) -> Dict:
        """
        Compute impact effects for a single asteroid
        
        Args:
            asteroid_params: Dictionary with diameter, velocity, density, angle
            
        Returns:
            Dictionary with impact results including crater size, energy, seismic effects
        """
        # Extract parameters
        diameter = asteroid_params.get('diameter', 100.0)  # meters
        velocity = asteroid_params.get('velocity', 20.0)  # km/s
        density = asteroid_params.get('density', 2500.0)  # kg/m³
        angle = asteroid_params.get('angle', 45.0)  # degrees
        
        # Convert units
        velocity_ms = velocity * 1000.0  # m/s
        angle_rad = math.radians(angle)
        radius = diameter / 2.0
        
        # Mass calculation (spherical assumption)
        volume = (4.0/3.0) * math.pi * (radius ** 3)
        mass = density * volume
        
        # Kinetic energy
        kinetic_energy = 0.5 * mass * (velocity_ms ** 2)
        
        # Crater scaling using π-group dimensional analysis
        # Based on Holsapple & Housen (1987) - NASA recommended approach
        target_density = 2500.0  # Average crustal density kg/m³
        gravity = 9.81  # m/s²
        
        # Scaling law constants for gravity regime
        K = 1.88
        alpha = 0.22
        
        # π-groups calculation
        pi_2 = (gravity * radius * math.sin(angle_rad)) / (velocity_ms ** 2)
        pi_R = K * (pi_2 ** (-alpha))
        
        # Crater radius and diameter
        crater_radius = pi_R * radius * ((density / target_density) ** (1.0/3.0))
        crater_diameter = 2.0 * crater_radius
        crater_depth = crater_diameter * 0.1  # Empirical depth/diameter ratio
        
        # Energy conversion to TNT equivalent
        # 1 megaton TNT = 4.184 × 10^15 joules
        energy_mt_tnt = kinetic_energy / 4.184e15
        
        # Seismic magnitude calculation (USGS-based)
        # Convert to ergs for seismic calculation
        energy_ergs = kinetic_energy * 1e7
        if energy_ergs > 0:
            seismic_magnitude = (2.0/3.0) * math.log10(energy_ergs) - 10.7
            seismic_magnitude = max(0.0, min(seismic_magnitude, 12.0))
        else:
            seismic_magnitude = 0.0
        
        # Environmental effects
        # Thermal radiation radius (Glasstone & Dolan scaling)
        thermal_energy = 0.3 * kinetic_energy  # ~30% goes to thermal radiation
        thermal_flux_threshold = 6300.0  # J/m² for 1st degree burns
        if thermal_energy > 0:
            thermal_radius = math.sqrt(thermal_energy / (4.0 * math.pi * thermal_flux_threshold))
            thermal_radius_km = thermal_radius / 1000.0
        else:
            thermal_radius_km = 0.0
        
        # Overpressure radius (Glasstone scaling for 1 psi)
        if energy_mt_tnt > 0:
            overpressure_radius_km = 2.15 * (energy_mt_tnt ** (1.0/3.0))
        else:
            overpressure_radius_km = 0.0
        
        return {
            "crater_diameter": crater_diameter,
            "crater_depth": crater_depth,
            "kinetic_energy_joules": kinetic_energy,
            "energy_mt_tnt": energy_mt_tnt,
            "thermal_radius_km": thermal_radius_km,
            "overpressure_radius_km": overpressure_radius_km,
            "seismic_magnitude": seismic_magnitude,
            "seismic_energy_ergs": energy_ergs,
            "mass_kg": mass,
            "calculation_method": "cpu_enhanced_physics" if not self.device_available else "gpu_enhanced_physics"
        }
    
    def compute_batch_impacts(self, asteroid_params_list: List[Dict]) -> List[Dict]:
        """
        Compute impact effects for multiple asteroids
        Uses GPU if available, otherwise CPU
        """
        if self.device_available and len(asteroid_params_list) > 10:
            return self._compute_batch_gpu(asteroid_params_list)
        else:
            return self._compute_batch_cpu(asteroid_params_list)
    
    def _compute_batch_cpu(self, asteroid_params_list: List[Dict]) -> List[Dict]:
        """CPU implementation for batch processing"""
        results = []
        for params in asteroid_params_list:
            results.append(self.compute_impact_effects(params))
        return results
    
    def _compute_batch_gpu(self, asteroid_params_list: List[Dict]) -> List[Dict]:
        """GPU implementation for batch processing (if CUDA available)"""
        # Fallback to CPU if GPU not available
        if not self.device_available:
            return self._compute_batch_cpu(asteroid_params_list)
        
        try:
            # Prepare input arrays
            n = len(asteroid_params_list)
            input_data = np.zeros((n, 4), dtype=np.float32)
            
            for i, params in enumerate(asteroid_params_list):
                input_data[i] = [
                    params.get('diameter', 100.0),
                    params.get('velocity', 20.0),
                    params.get('density', 2500.0),
                    params.get('angle', 45.0)
                ]
            
            # Transfer to GPU
            d_input = cp.asarray(input_data)
            
            # Allocate output arrays
            d_output = cp.zeros((n, 8), dtype=np.float32)
            
            # Process on GPU (vectorized operations)
            self._gpu_compute_impacts(d_input, d_output)
            
            # Transfer back to CPU
            output_data = cp.asnumpy(d_output)
            
            # Format results
            results = []
            for i in range(n):
                results.append({
                    "crater_diameter": float(output_data[i, 0]),
                    "crater_depth": float(output_data[i, 1]),
                    "kinetic_energy_joules": float(output_data[i, 2]),
                    "energy_mt_tnt": float(output_data[i, 3]),
                    "thermal_radius_km": float(output_data[i, 4]),
                    "overpressure_radius_km": float(output_data[i, 5]),
                    "seismic_magnitude": float(output_data[i, 6]),
                    "seismic_energy_ergs": float(output_data[i, 7]),
                    "calculation_method": "gpu_enhanced_physics"
                })
            
            return results
        except Exception as e:
            logger.error(f"GPU computation failed: {e}, falling back to CPU")
            return self._compute_batch_cpu(asteroid_params_list)
    
    def _gpu_compute_impacts(self, d_input, d_output):
        """GPU computation using CuPy vectorized operations"""
        # Extract parameters
        diameter = d_input[:, 0]
        velocity = d_input[:, 1] * 1000.0  # km/s to m/s
        density = d_input[:, 2]
        angle = d_input[:, 3] * (np.pi / 180.0)  # degrees to radians
        
        # Constants
        PI = np.pi
        
        # Mass calculation
        radius = diameter / 2.0
        volume = (4.0/3.0) * PI * (radius ** 3)
        mass = density * volume
        
        # Kinetic energy
        kinetic_energy = 0.5 * mass * (velocity ** 2)
        
        # Crater scaling
        target_density = 2500.0
        gravity = 9.81
        K = 1.88
        alpha = 0.22
        
        pi_2 = (gravity * radius * cp.sin(angle)) / (velocity ** 2)
        pi_R = K * (pi_2 ** (-alpha))
        
        crater_radius = pi_R * radius * ((density / target_density) ** (1.0/3.0))
        crater_diameter = 2.0 * crater_radius
        crater_depth = crater_diameter * 0.1
        
        # Energy conversions
        energy_mt_tnt = kinetic_energy / 4.184e15
        energy_ergs = kinetic_energy * 1e7
        seismic_magnitude = (2.0/3.0) * cp.log10(energy_ergs + 1e-10) - 10.7
        seismic_magnitude = cp.clip(seismic_magnitude, 0.0, 12.0)
        
        # Environmental effects
        thermal_energy = 0.3 * kinetic_energy
        thermal_radius = cp.sqrt(thermal_energy / (4.0 * PI * 6300.0))
        thermal_radius_km = thermal_radius / 1000.0
        
        overpressure_radius_km = 2.15 * (energy_mt_tnt ** (1.0/3.0))
        
        # Store results
        d_output[:, 0] = crater_diameter
        d_output[:, 1] = crater_depth
        d_output[:, 2] = kinetic_energy
        d_output[:, 3] = energy_mt_tnt
        d_output[:, 4] = thermal_radius_km
        d_output[:, 5] = overpressure_radius_km
        d_output[:, 6] = seismic_magnitude
        d_output[:, 7] = energy_ergs


def validate_tunguska_event():
    """
    Validate physics engine against the 1908 Tunguska event
    Expected: ~50m diameter, ~150m crater, ~10-15 MT TNT
    """
    engine = EnhancedPhysicsEngine()
    
    # Tunguska parameters (estimated)
    tunguska_params = {
        'diameter': 50.0,  # meters
        'velocity': 27.0,  # km/s
        'density': 2000.0,  # kg/m³ (icy composition)
        'angle': 45.0  # degrees
    }
    
    results = engine.compute_impact_effects(tunguska_params)
    
    print("=" * 60)
    print("Tunguska Event Validation (1908)")
    print("=" * 60)
    print(f"Input diameter: {tunguska_params['diameter']} m")
    print(f"Input velocity: {tunguska_params['velocity']} km/s")
    print(f"Calculated crater: {results['crater_diameter']:.1f} m")
    print(f"Calculated energy: {results['energy_mt_tnt']:.2f} MT TNT")
    print(f"Seismic magnitude: {results['seismic_magnitude']:.1f}")
    print(f"Thermal radius: {results['thermal_radius_km']:.1f} km")
    print(f"Overpressure radius: {results['overpressure_radius_km']:.1f} km")
    print("=" * 60)
    
    # Expected: ~10-15 MT TNT, crater ~150m
    if 8 < results['energy_mt_tnt'] < 20:
        print("✅ Energy estimate matches historical data")
    else:
        print(f"⚠️ Energy estimate off: expected 10-15 MT, got {results['energy_mt_tnt']:.2f} MT")
    
    return results


if __name__ == "__main__":
    # Run validation
    validate_tunguska_event()
    
    # Test batch processing
    print("\nTesting batch processing...")
    engine = EnhancedPhysicsEngine()
    
    test_params = [
        {'diameter': 10.0, 'velocity': 15.0, 'density': 2500.0, 'angle': 45.0},
        {'diameter': 50.0, 'velocity': 20.0, 'density': 2500.0, 'angle': 45.0},
        {'diameter': 100.0, 'velocity': 25.0, 'density': 2500.0, 'angle': 45.0},
    ]
    
    results = engine.compute_batch_impacts(test_params)
    print(f"✅ Processed {len(results)} impacts")
    for i, result in enumerate(results):
        print(f"  Impact {i+1}: {result['energy_mt_tnt']:.3f} MT TNT, Magnitude {result['seismic_magnitude']:.1f}")

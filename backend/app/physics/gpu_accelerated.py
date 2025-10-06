"""
GPU-Accelerated Physics Simulations
Uses CUDA for high-resolution, complex calculations that would be too slow on CPU
"""

import math
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from numba import cuda
import time

logger = logging.getLogger(__name__)

# Try to import CUDA libraries
try:
    import cupy as cp
    CUDA_AVAILABLE = True
    logger.info("🚀 GPU acceleration available")
except ImportError:
    CUDA_AVAILABLE = False
    cp = np  # Fallback to numpy
    logger.warning("⚠️ GPU not available, using CPU")

# Physical constants
G = 6.67430e-11  # Gravitational constant
EARTH_MASS = 5.972e24  # kg
EARTH_RADIUS = 6371000  # meters
AU_TO_M = 1.496e11  # Astronomical unit to meters


class GPUAcceleratedSimulator:
    """GPU-accelerated physics simulations for complex calculations"""
    
    def __init__(self):
        self.cuda_available = CUDA_AVAILABLE
        if self.cuda_available:
            try:
                self.device_count = cp.cuda.runtime.getDeviceCount()
                self.device_props = cp.cuda.runtime.getDeviceProperties(0)
                logger.info(f"✅ Using GPU: {self.device_props['name'].decode()}")
                logger.info(f"   CUDA Cores: {self.device_props['multiProcessorCount']}")
                logger.info(f"   Memory: {self.device_props['totalGlobalMem'] / 1e9:.1f} GB")
            except Exception as e:
                logger.warning(f"GPU detection failed: {e}")
                self.cuda_available = False
        else:
            logger.info("ℹ️ Running on CPU (slower but functional)")
    
    def high_resolution_trajectory(self,
                                  initial_position: np.ndarray,
                                  initial_velocity: np.ndarray,
                                  asteroid_mass: float,
                                  time_steps: int = 10000,
                                  dt: float = 0.1) -> Dict:
        """
        GPU-accelerated high-resolution trajectory calculation
        Calculates 10,000+ trajectory points with gravitational effects
        
        Args:
            initial_position: [x, y, z] in meters
            initial_velocity: [vx, vy, vz] in m/s
            asteroid_mass: Mass in kg
            time_steps: Number of simulation steps (default: 10,000)
            dt: Time step in seconds
        
        Returns:
            Dict with high-resolution trajectory data
        """
        start_time = time.time()
        
        if self.cuda_available:
            result = self._gpu_trajectory(initial_position, initial_velocity, 
                                         asteroid_mass, time_steps, dt)
        else:
            result = self._cpu_trajectory(initial_position, initial_velocity,
                                         asteroid_mass, time_steps, dt)
        
        calc_time = time.time() - start_time
        result['calculation_time_ms'] = calc_time * 1000
        result['calculation_method'] = 'GPU' if self.cuda_available else 'CPU'
        result['points_per_second'] = time_steps / calc_time if calc_time > 0 else 0
        
        logger.info(f"✅ Trajectory calculated: {time_steps} points in {calc_time:.3f}s "
                   f"({result['points_per_second']:.0f} points/sec)")
        
        return result
    
    def _gpu_trajectory(self, pos: np.ndarray, vel: np.ndarray, 
                       mass: float, steps: int, dt: float) -> Dict:
        """GPU-accelerated trajectory calculation using CuPy"""
        # Transfer to GPU
        position = cp.array(pos, dtype=cp.float64)
        velocity = cp.array(vel, dtype=cp.float64)
        
        # Preallocate arrays on GPU
        positions = cp.zeros((steps, 3), dtype=cp.float64)
        velocities = cp.zeros((steps, 3), dtype=cp.float64)
        altitudes = cp.zeros(steps, dtype=cp.float64)
        speeds = cp.zeros(steps, dtype=cp.float64)
        
        # Earth center
        earth_center = cp.array([0.0, 0.0, 0.0], dtype=cp.float64)
        
        # Runge-Kutta 4th order integration on GPU
        for i in range(steps):
            positions[i] = position
            velocities[i] = velocity
            
            # Calculate altitude
            r = cp.linalg.norm(position - earth_center)
            altitudes[i] = r - EARTH_RADIUS
            speeds[i] = cp.linalg.norm(velocity)
            
            # RK4 integration
            k1_v = self._acceleration_gpu(position, mass)
            k1_p = velocity
            
            k2_v = self._acceleration_gpu(position + k1_p * dt/2, mass)
            k2_p = velocity + k1_v * dt/2
            
            k3_v = self._acceleration_gpu(position + k2_p * dt/2, mass)
            k3_p = velocity + k2_v * dt/2
            
            k4_v = self._acceleration_gpu(position + k3_p * dt, mass)
            k4_p = velocity + k3_v * dt
            
            # Update position and velocity
            velocity = velocity + (k1_v + 2*k2_v + 2*k3_v + k4_v) * dt / 6
            position = position + (k1_p + 2*k2_p + 2*k3_p + k4_p) * dt / 6
        
        # Transfer back to CPU
        return {
            'positions': cp.asnumpy(positions),
            'velocities': cp.asnumpy(velocities),
            'altitudes': cp.asnumpy(altitudes),
            'speeds': cp.asnumpy(speeds),
            'time_steps': steps,
            'dt': dt
        }
    
    def _acceleration_gpu(self, position: cp.ndarray, mass: float) -> cp.ndarray:
        """Calculate gravitational acceleration on GPU"""
        r_vec = position - cp.array([0.0, 0.0, 0.0])
        r = cp.linalg.norm(r_vec)
        
        # Gravitational acceleration from Earth
        a_grav = -G * EARTH_MASS * r_vec / (r**3)
        
        return a_grav
    
    def _cpu_trajectory(self, pos: np.ndarray, vel: np.ndarray,
                       mass: float, steps: int, dt: float) -> Dict:
        """CPU fallback for trajectory calculation"""
        position = pos.copy()
        velocity = vel.copy()
        
        positions = np.zeros((steps, 3))
        velocities = np.zeros((steps, 3))
        altitudes = np.zeros(steps)
        speeds = np.zeros(steps)
        
        for i in range(steps):
            positions[i] = position
            velocities[i] = velocity
            
            r = np.linalg.norm(position)
            altitudes[i] = r - EARTH_RADIUS
            speeds[i] = np.linalg.norm(velocity)
            
            # Simple Euler integration (faster for CPU)
            acceleration = self._acceleration_cpu(position, mass)
            velocity = velocity + acceleration * dt
            position = position + velocity * dt
        
        return {
            'positions': positions,
            'velocities': velocities,
            'altitudes': altitudes,
            'speeds': speeds,
            'time_steps': steps,
            'dt': dt
        }
    
    def _acceleration_cpu(self, position: np.ndarray, mass: float) -> np.ndarray:
        """Calculate gravitational acceleration on CPU"""
        r_vec = position
        r = np.linalg.norm(r_vec)
        a_grav = -G * EARTH_MASS * r_vec / (r**3)
        return a_grav
    
    def monte_carlo_impact_probability(self,
                                      orbital_elements: Dict,
                                      num_simulations: int = 10000,
                                      uncertainty_sigma: float = 0.01) -> Dict:
        """
        GPU-accelerated Monte Carlo simulation for impact probability
        Runs thousands of orbital variations in parallel
        
        Args:
            orbital_elements: Nominal orbital elements
            num_simulations: Number of Monte Carlo runs (default: 10,000)
            uncertainty_sigma: Uncertainty in orbital elements (fraction)
        
        Returns:
            Dict with impact probability and statistics
        """
        start_time = time.time()
        
        if self.cuda_available:
            result = self._gpu_monte_carlo(orbital_elements, num_simulations, uncertainty_sigma)
        else:
            result = self._cpu_monte_carlo(orbital_elements, num_simulations, uncertainty_sigma)
        
        calc_time = time.time() - start_time
        result['calculation_time_ms'] = calc_time * 1000
        result['simulations_per_second'] = num_simulations / calc_time if calc_time > 0 else 0
        
        logger.info(
            f"✅ Monte Carlo: {num_simulations} simulations in {calc_time:.3f}s "
            f"({result['simulations_per_second']:.0f} sim/sec)"
        )
        return result
    
    def _gpu_monte_carlo(self, elements: Dict, n_sim: int, sigma: float) -> Dict:
        """GPU-accelerated Monte Carlo on orbital elements"""
        a = elements.get('semi_major_axis_au', 1.0) * AU_TO_M
        e = elements.get('eccentricity', 0.1)
        
        # Generate variations on GPU
        rng = cp.random.default_rng()
        a_samples = rng.normal(a, a * sigma, n_sim)
        e_samples = rng.normal(e, e * sigma, n_sim)
        
        # Calculate perihelion distances
        q = a_samples * (1 - e_samples)  # Perihelion distance
        
        # Count impacts (perihelion < Earth orbit ~ 1 AU)
        impacts = cp.sum(q < (1.0 * AU_TO_M))
        impact_probability = float(impacts) / n_sim
        
        # Calculate statistics
        mean_perihelion_au = float(cp.mean(q)) / AU_TO_M
        std_perihelion_au = float(cp.std(q)) / AU_TO_M
        min_perihelion_au = float(cp.min(q)) / AU_TO_M
        
        return {
            'impact_probability': impact_probability,
            'impact_count': int(impacts),
            'total_simulations': n_sim,
            'mean_perihelion_au': mean_perihelion_au,
            'std_perihelion_au': std_perihelion_au,
            'min_perihelion_au': min_perihelion_au,
            'method': 'GPU Monte Carlo'
        }
    
    def _cpu_monte_carlo(self, elements: Dict, n_sim: int, sigma: float) -> Dict:
        """CPU fallback for Monte Carlo"""
        a = elements.get('semi_major_axis_au', 1.0) * AU_TO_M
        e = elements.get('eccentricity', 0.1)
        
        a_samples = np.random.normal(a, a * sigma, n_sim)
        e_samples = np.random.normal(e, e * sigma, n_sim)
        
        q = a_samples * (1 - e_samples)
        impacts = np.sum(q < (1.0 * AU_TO_M))
        impact_probability = float(impacts) / n_sim
        
        return {
            'impact_probability': impact_probability,
            'impact_count': int(impacts),
            'total_simulations': n_sim,
            'mean_perihelion_au': float(np.mean(q)) / AU_TO_M,
            'std_perihelion_au': float(np.std(q)) / AU_TO_M,
            'min_perihelion_au': float(np.min(q)) / AU_TO_M,
            'method': 'CPU Monte Carlo'
        }

    def monte_carlo_impact_map(
        self,
        nominal_elements: Dict,
        covariance: Dict,
        asteroid_params: Dict,
        samples: int,
        bin_size_deg: float,
        seed: Optional[int] = None,
    ) -> Dict:
        """Generate Monte Carlo impact heatmap using SBDB covariance data."""

        from app.physics.orbital_mechanics import calculate_impact_scenario

        start_time = time.time()

        required_labels = ["a", "e", "i", "om", "w", "ma"]
        covariance_labels = covariance.get("labels", [])
        matrix_raw = covariance.get("matrix")

        if not matrix_raw:
            raise ValueError("Covariance matrix data missing")

        matrix_np = np.array(matrix_raw, dtype=float)
        if matrix_np.ndim == 1:
            size = int(math.sqrt(matrix_np.size))
            matrix_np = matrix_np.reshape((size, size))
        elif matrix_np.ndim != 2:
            raise ValueError("Unexpected covariance matrix shape")

        label_to_index = {label: idx for idx, label in enumerate(covariance_labels)}
        if not all(label in label_to_index for label in required_labels):
            raise ValueError("Covariance matrix missing required orbital element labels")

        indices = [label_to_index[label] for label in required_labels]
        cov_submatrix = matrix_np[np.ix_(indices, indices)]

        mean_vector = np.array([
            nominal_elements.get('semi_major_axis_au', 1.0),
            nominal_elements.get('eccentricity', 0.1),
            nominal_elements.get('inclination_deg', 0.0),
            nominal_elements.get('longitude_ascending_node_deg', 0.0),
            nominal_elements.get('argument_periapsis_deg', 0.0),
            nominal_elements.get('mean_anomaly_deg', 0.0),
        ], dtype=float)

        rng = np.random.default_rng(seed)

        # Ensure covariance is positive semi-definite
        try:
            np.linalg.cholesky(cov_submatrix)
        except np.linalg.LinAlgError:
            jitter = np.eye(cov_submatrix.shape[0]) * 1e-10
            cov_submatrix = cov_submatrix + jitter
            np.linalg.cholesky(cov_submatrix)

        samples_matrix = rng.multivariate_normal(mean_vector, cov_submatrix, size=samples)

        bin_counts: Dict[Tuple[int, int], int] = {}
        sample_locations: List[Tuple[float, float]] = []

        for sample in samples_matrix:
            sampled_elements = {
                'semi_major_axis_au': max(sample[0], 0.1),
                'eccentricity': min(max(sample[1], 0.0), 0.999),
                'inclination_deg': float(sample[2] % 180.0),
                'longitude_ascending_node_deg': float(sample[3] % 360.0),
                'argument_periapsis_deg': float(sample[4] % 360.0),
                'mean_anomaly_deg': float(sample[5] % 360.0),
            }

            scenario = calculate_impact_scenario(asteroid_params, sampled_elements)
            intercept = scenario.get("orbital_intercept")

            if not intercept:
                continue

            impact_location = scenario.get("impact_location")
            if not impact_location:
                continue

            lat = float(impact_location.get("latitude"))
            lon = float(impact_location.get("longitude"))

            if math.isnan(lat) or math.isnan(lon):
                continue

            sample_locations.append((lat, lon))

            lat_bin = math.floor((lat + 90.0) / bin_size_deg)
            lon_bin = math.floor((lon + 180.0) / bin_size_deg)
            key = (lat_bin, lon_bin)
            bin_counts[key] = bin_counts.get(key, 0) + 1

        valid_samples = len(sample_locations)
        heatmap = []

        for (lat_bin, lon_bin), count in bin_counts.items():
            lat_center = -90.0 + (lat_bin + 0.5) * bin_size_deg
            lon_center = -180.0 + (lon_bin + 0.5) * bin_size_deg
            probability = count / valid_samples if valid_samples else 0.0
            heatmap.append({
                "lat_center_deg": lat_center,
                "lon_center_deg": lon_center,
                "count": count,
                "probability": probability
            })

        calc_time = time.time() - start_time

        result = {
            "total_samples": samples,
            "valid_samples": valid_samples,
            "invalid_samples": samples - valid_samples,
            "bin_size_deg": bin_size_deg,
            "heatmap": heatmap,
            "calculation_time_ms": calc_time * 1000,
            "method": "CPU Monte Carlo",
        }

        if sample_locations:
            latitudes = [lat for lat, _ in sample_locations]
            longitudes = [lon for _, lon in sample_locations]
            result["mean_latitude"] = float(np.mean(latitudes))
            result["mean_longitude"] = float(np.mean(longitudes))

        return result
    
    def parallel_crater_formation(self,
                                 impact_energy_joules: float,
                                 asteroid_diameter_m: float,
                                 impact_angle_deg: float,
                                 target_density_kg_m3: float = 2500.0,
                                 grid_resolution: int = 1000) -> Dict:
        """
        GPU-accelerated crater formation modeling
        Calculates detailed crater morphology on fine grid
        
        Args:
            impact_energy_joules: Impact energy
            asteroid_diameter_m: Asteroid diameter
            impact_angle_deg: Impact angle from horizontal
            target_density_kg_m3: Target material density
            grid_resolution: Grid size (1000x1000 default)
        
        Returns:
            Dict with detailed crater morphology
        """
        start_time = time.time()
        
        if self.cuda_available:
            result = self._gpu_crater_formation(
                impact_energy_joules, asteroid_diameter_m,
                impact_angle_deg, target_density_kg_m3, grid_resolution
            )
        else:
            result = self._cpu_crater_formation(
                impact_energy_joules, asteroid_diameter_m,
                impact_angle_deg, target_density_kg_m3, grid_resolution
            )
        
        calc_time = time.time() - start_time
        result['calculation_time_ms'] = calc_time * 1000
        result['grid_points'] = grid_resolution * grid_resolution
        result['points_per_second'] = result['grid_points'] / calc_time if calc_time > 0 else 0
        
        logger.info(f"✅ Crater model: {grid_resolution}x{grid_resolution} grid in {calc_time:.3f}s")
        
        return result
    
    def _gpu_crater_formation(self, energy: float, diameter: float,
                             angle: float, density: float, res: int) -> Dict:
        """GPU-accelerated crater formation"""
        # Crater scaling (Schmidt-Housen)
        crater_diameter = 1.8 * (energy / 1e9) ** 0.22 * (diameter ** 0.13)
        crater_depth = crater_diameter / 10  # Depth-to-diameter ratio ~0.1
        
        # Create grid on GPU
        x = cp.linspace(-crater_diameter, crater_diameter, res)
        y = cp.linspace(-crater_diameter, crater_diameter, res)
        X, Y = cp.meshgrid(x, y)
        
        # Distance from center
        R = cp.sqrt(X**2 + Y**2)
        
        # Crater profile (power-law)
        Z = cp.where(
            R < crater_diameter/2,
            -crater_depth * (1 - (2*R/crater_diameter)**2),
            0
        )
        
        # Calculate ejecta distribution
        ejecta = cp.where(
            (R >= crater_diameter/2) & (R < crater_diameter*2),
            crater_depth/10 * cp.exp(-(R - crater_diameter/2)**2 / (crater_diameter/2)**2),
            0
        )
        
        # Total elevation change
        elevation = Z + ejecta
        
        # Statistics
        excavated_volume = float(cp.sum(cp.abs(Z[Z < 0])) * (2*crater_diameter/res)**2)
        ejecta_volume = float(cp.sum(ejecta[ejecta > 0]) * (2*crater_diameter/res)**2)
        
        return {
            'crater_diameter_m': crater_diameter,
            'crater_depth_m': crater_depth,
            'excavated_volume_m3': excavated_volume,
            'ejecta_volume_m3': ejecta_volume,
            'grid_resolution': res,
            'rim_height_m': float(cp.max(ejecta)),
            'max_depth_m': float(cp.min(Z)),
            'method': 'GPU Parallel'
        }
    
    def _cpu_crater_formation(self, energy: float, diameter: float,
                             angle: float, density: float, res: int) -> Dict:
        """CPU fallback for crater formation"""
        # Simple calculation (no grid)
        crater_diameter = 1.8 * (energy / 1e9) ** 0.22 * (diameter ** 0.13)
        crater_depth = crater_diameter / 10
        
        excavated_volume = math.pi * (crater_diameter/2)**2 * crater_depth
        ejecta_volume = excavated_volume * 1.5
        
        return {
            'crater_diameter_m': crater_diameter,
            'crater_depth_m': crater_depth,
            'excavated_volume_m3': excavated_volume,
            'ejecta_volume_m3': ejecta_volume,
            'grid_resolution': res,
            'rim_height_m': crater_depth / 20,
            'max_depth_m': crater_depth,
            'method': 'CPU Simplified'
        }
    
    def get_gpu_info(self) -> Dict:
        """Get information about GPU hardware"""
        if not self.cuda_available:
            return {
                'available': False,
                'message': 'CUDA not available - install cupy and numba'
            }
        
        try:
            props = cp.cuda.runtime.getDeviceProperties(0)
            return {
                'available': True,
                'device_name': props['name'].decode(),
                'cuda_cores': props['multiProcessorCount'],
                'total_memory_gb': props['totalGlobalMem'] / 1e9,
                'compute_capability': f"{props['major']}.{props['minor']}",
                'max_threads_per_block': props['maxThreadsPerBlock'],
                'max_grid_size': props['maxGridSize'],
                'clock_rate_mhz': props['clockRate'] / 1000
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }


# Test functions
def test_gpu_acceleration():
    """Test GPU acceleration features"""
    gpu_sim = GPUAcceleratedSimulator()
    
    print("\n🚀 GPU Acceleration Test")
    print("=" * 70)
    
    # GPU info
    info = gpu_sim.get_gpu_info()
    if info['available']:
        print(f"\n✅ GPU: {info['device_name']}")
        print(f"   CUDA Cores: {info['cuda_cores']}")
        print(f"   Memory: {info['total_memory_gb']:.1f} GB")
    else:
        print("\n⚠️ GPU not available - using CPU")
    
    # Test high-resolution trajectory
    print("\n1️⃣ High-Resolution Trajectory (10,000 points)")
    initial_pos = np.array([0.0, 0.0, EARTH_RADIUS + 100000])  # 100km altitude
    initial_vel = np.array([7000.0, 0.0, 0.0])  # 7 km/s horizontal
    
    result = gpu_sim.high_resolution_trajectory(
        initial_pos, initial_vel, 1e6, time_steps=10000, dt=0.1
    )
    print(f"   Calculation time: {result['calculation_time_ms']:.1f} ms")
    print(f"   Performance: {result['points_per_second']:.0f} points/second")
    print(f"   Method: {result['calculation_method']}")
    
    # Test Monte Carlo
    print("\n2️⃣ Monte Carlo Impact Probability (10,000 simulations)")
    orbital_elements = {
        'semi_major_axis_au': 0.922,
        'eccentricity': 0.191
    }
    
    result = gpu_sim.monte_carlo_impact_probability(
        orbital_elements, num_simulations=10000, uncertainty_sigma=0.01
    )
    print(f"   Impact probability: {result['impact_probability']*100:.2f}%")
    print(f"   Calculation time: {result['calculation_time_ms']:.1f} ms")
    print(f"   Performance: {result['simulations_per_second']:.0f} sim/second")
    
    # Test crater formation
    print("\n3️⃣ Parallel Crater Formation (1000x1000 grid)")
    result = gpu_sim.parallel_crater_formation(
        impact_energy_joules=1e18,
        asteroid_diameter_m=100,
        impact_angle_deg=45,
        grid_resolution=1000
    )
    print(f"   Crater diameter: {result['crater_diameter_m']:.1f} m")
    print(f"   Calculation time: {result['calculation_time_ms']:.1f} ms")
    print(f"   Performance: {result['points_per_second']:.0f} points/second")
    print(f"   Method: {result['method']}")


if __name__ == "__main__":
    test_gpu_acceleration()

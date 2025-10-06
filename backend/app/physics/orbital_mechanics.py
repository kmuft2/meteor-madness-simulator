# EDITING: Cascade at 05:12 UTC - Integrating orbital intercept physics
"""
Orbital mechanics and trajectory calculations for asteroid impacts
Based on NASA JPL orbital mechanics standards
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Physical constants
AU_TO_KM = 149597870.7  # Astronomical Unit in km
EARTH_RADIUS = 6371.0  # km
EARTH_MASS = 5.972e24  # kg
G = 6.67430e-11  # Gravitational constant m^3 kg^-1 s^-2
EARTH_MU = 3.986004418e14  # Earth's gravitational parameter m^3/s^2
SUN_MU = 1.32712440018e20  # Sun's gravitational parameter m^3/s^2
EARTH_ROTATION_RATE = 7.2921159e-5  # rad/s


class OrbitalMechanics:
    """
    Calculate asteroid trajectories, impact locations, and flight paths
    """
    
    def __init__(self):
        self.earth_radius_m = EARTH_RADIUS * 1000  # Convert to meters
    
    def keplerian_to_cartesian(self, orbital_elements: Dict) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert Keplerian orbital elements to Cartesian position and velocity
        
        Args:
            orbital_elements: Dict with:
                - semi_major_axis_au: Semi-major axis in AU
                - eccentricity: Orbital eccentricity
                - inclination_deg: Inclination in degrees
                - longitude_ascending_node_deg: RAAN in degrees
                - argument_periapsis_deg: Argument of periapsis in degrees
                - mean_anomaly_deg: Mean anomaly in degrees
        
        Returns:
            position, velocity in heliocentric coordinates (km, km/s)
        """
        # Extract elements
        a = orbital_elements.get('semi_major_axis_au', 1.5) * AU_TO_KM
        e = orbital_elements.get('eccentricity', 0.1)
        i = math.radians(orbital_elements.get('inclination_deg', 5.0))
        omega = math.radians(orbital_elements.get('longitude_ascending_node_deg', 0.0))
        w = math.radians(orbital_elements.get('argument_periapsis_deg', 0.0))
        M = math.radians(orbital_elements.get('mean_anomaly_deg', 0.0))
        
        # Solve Kepler's equation for eccentric anomaly
        E = self._solve_keplers_equation(M, e)
        
        # True anomaly
        nu = 2 * math.atan2(
            math.sqrt(1 + e) * math.sin(E / 2),
            math.sqrt(1 - e) * math.cos(E / 2)
        )
        
        # Distance from focus
        r = a * (1 - e * math.cos(E))
        
        # Position in orbital plane
        x_orb = r * math.cos(nu)
        y_orb = r * math.sin(nu)
        z_orb = 0.0
        
        # Velocity in orbital plane (using Sun's gravitational parameter for heliocentric orbit)
        # Convert a from km to m for calculation
        a_m = a * 1000
        h = math.sqrt(SUN_MU * a_m * (1 - e**2))  # Angular momentum in m^2/s
        r_m = r * 1000  # Convert r to meters
        vx_orb = -(h / r_m) * math.sin(nu) / 1000  # Convert back to km/s
        vy_orb = (h / r_m) * (e + math.cos(nu)) / 1000  # Convert back to km/s
        vz_orb = 0.0
        
        # Rotation matrices to transform to inertial frame
        # Rotate by argument of periapsis
        cos_w, sin_w = math.cos(w), math.sin(w)
        # Rotate by inclination
        cos_i, sin_i = math.cos(i), math.sin(i)
        # Rotate by longitude of ascending node
        cos_o, sin_o = math.cos(omega), math.sin(omega)
        
        # Combined rotation matrix
        R11 = cos_o * cos_w - sin_o * sin_w * cos_i
        R12 = -cos_o * sin_w - sin_o * cos_w * cos_i
        R13 = sin_o * sin_i
        
        R21 = sin_o * cos_w + cos_o * sin_w * cos_i
        R22 = -sin_o * sin_w + cos_o * cos_w * cos_i
        R23 = -cos_o * sin_i
        
        R31 = sin_w * sin_i
        R32 = cos_w * sin_i
        R33 = cos_i
        
        # Transform position
        position = np.array([
            R11 * x_orb + R12 * y_orb + R13 * z_orb,
            R21 * x_orb + R22 * y_orb + R23 * z_orb,
            R31 * x_orb + R32 * y_orb + R33 * z_orb
        ])
        
        # Transform velocity
        velocity = np.array([
            R11 * vx_orb + R12 * vy_orb + R13 * vz_orb,
            R21 * vx_orb + R22 * vy_orb + R23 * vz_orb,
            R31 * vx_orb + R32 * vy_orb + R33 * vz_orb
        ])
        
        return position, velocity
    
    def _solve_keplers_equation(self, M: float, e: float, tolerance: float = 1e-8) -> float:
        """
        Solve Kepler's equation M = E - e*sin(E) for eccentric anomaly E
        Using Newton-Raphson iteration
        """
        E = M  # Initial guess
        
        for _ in range(100):  # Max iterations
            f = E - e * math.sin(E) - M
            f_prime = 1 - e * math.cos(E)
            
            E_new = E - f / f_prime
            
            if abs(E_new - E) < tolerance:
                return E_new
            
            E = E_new
        
        return E
    
    def calculate_impact_location(self, 
                                  velocity_vector: np.ndarray,
                                  impact_angle_deg: float = 45.0,
                                  target_lat: Optional[float] = None,
                                  target_lon: Optional[float] = None) -> Dict:
        """
        Calculate impact location on Earth's surface
        
        Args:
            velocity_vector: Velocity vector in Earth-centered frame (km/s)
            impact_angle_deg: Impact angle from horizontal
            target_lat: Optional target latitude (if specific location desired)
            target_lon: Optional target longitude
        
        Returns:
            Dict with latitude, longitude, impact azimuth
        """
        if target_lat is not None and target_lon is not None:
            # Use specified location
            latitude = target_lat
            longitude = target_lon
        else:
            # Calculate from velocity vector
            # Convert velocity to impact direction
            v_norm = velocity_vector / np.linalg.norm(velocity_vector)
            
            # Impact latitude from z-component
            latitude = math.degrees(math.asin(v_norm[2]))
            
            # Impact longitude from x,y components
            longitude = math.degrees(math.atan2(v_norm[1], v_norm[0]))
        
        # Calculate impact azimuth (direction of arrival)
        azimuth = self._calculate_azimuth(velocity_vector)
        
        return {
            "latitude": latitude,
            "longitude": longitude,
            "impact_angle_deg": impact_angle_deg,
            "azimuth_deg": azimuth,
            "impact_point": [longitude, latitude]
        }

    def find_earth_intercept(self, orbital_elements: Dict) -> Optional[Dict]:
        """Find the point where the asteroid's heliocentric orbit intersects Earth's orbital radius.

        Returns None if no viable intercept is found within tolerance.
        """
        # Earth's orbital radius (assumed circular 1 AU)
        target_radius = 1.0 * AU_TO_KM
        tolerance_km = 5000  # within 5,000 km of Earth's orbital radius

        closest = None
        closest_diff = float('inf')

        # Sweep mean anomaly 0-360 deg for intercept candidates
        for step in range(0, 361, 2):
            test_elements = orbital_elements.copy()
            test_elements['mean_anomaly_deg'] = step
            position, velocity = self.keplerian_to_cartesian(test_elements)

            distance = np.linalg.norm(position)
            diff = abs(distance - target_radius)

            if diff < closest_diff:
                closest_diff = diff
                closest = (step, position, velocity, distance)

        if closest is None or closest_diff > tolerance_km:
            return None

        mean_anomaly_deg, pos_vec, vel_vec, distance = closest

        # Estimate Earth's heliocentric position along same direction
        if distance == 0:
            return None
        direction = pos_vec / distance
        earth_pos = direction * target_radius
        relative_position = pos_vec - earth_pos
        rel_pos_norm = np.linalg.norm(relative_position)
        if rel_pos_norm < 1.0:
            rel_pos_norm = 1.0

        # Compute relative velocity vs Earth
        # Earth velocity ~29.78 km/s; approximate vector in orbital plane
        earth_speed = 29.78
        # Earth direction at intercept assumed to align with pos_vec projection
        earth_dir = np.cross([0, 0, 1], pos_vec)
        if np.linalg.norm(earth_dir) == 0:
            earth_dir = np.array([0, 30.0, 0])
        else:
            earth_dir = earth_dir / np.linalg.norm(earth_dir) * earth_speed

        relative_vel = vel_vec - earth_dir
        rel_speed = np.linalg.norm(relative_vel)
        if rel_speed < 1e-6:
            return None

        # Convert to geographic entry parameters
        v_norm = relative_vel / rel_speed
        lat_from_position = math.degrees(math.asin(relative_position[2] / rel_pos_norm))
        lon_from_position = math.degrees(math.atan2(relative_position[1], relative_position[0]))

        azimuth = self._calculate_azimuth(relative_vel)

        # Entry angle relative to horizontal plane at impact point
        entry_angle_deg = math.degrees(math.asin(min(1.0, max(0.0, abs(v_norm[2])))))

        return {
            "entry_velocity_km_s": rel_speed,
            "entry_angle_deg": entry_angle_deg,
            "latitude": lat_from_position,
            "longitude": lon_from_position,
            "azimuth_deg": azimuth,
            "mean_anomaly_deg": mean_anomaly_deg,
            "distance_to_orbit_km": closest_diff,
            "relative_velocity_vector": relative_vel.tolist(),
            "position_vector": pos_vec.tolist(),
            "relative_position_vector": relative_position.tolist(),
        }
    
    def _calculate_azimuth(self, velocity_vector: np.ndarray) -> float:
        """Calculate impact azimuth from velocity vector"""
        vx, vy = velocity_vector[0], velocity_vector[1]
        azimuth = math.degrees(math.atan2(vx, vy))
        return azimuth % 360
    
    def calculate_atmospheric_entry(self,
                                    initial_velocity_km_s: float,
                                    entry_angle_deg: float,
                                    asteroid_diameter_m: float,
                                    asteroid_density_kg_m3: float,
                                    entry_altitude_km: float = 100.0,
                                    start_altitude_km: float = 10000.0) -> Dict:
        """
        Calculate complete trajectory from space to impact
        
        Args:
            initial_velocity_km_s: Entry velocity in km/s
            entry_angle_deg: Entry angle from horizontal
            asteroid_diameter_m: Asteroid diameter in meters
            asteroid_density_kg_m3: Asteroid density
            entry_altitude_km: Atmospheric entry altitude (100 km)
            start_altitude_km: Starting altitude for visualization (default 10000 km)
        
        Returns:
            Dict with trajectory points from space to impact, including ablation and fragmentation
        """
        # Convert units
        v0 = initial_velocity_km_s * 1000  # m/s
        angle_rad = math.radians(entry_angle_deg)
        
        # Asteroid properties
        radius = asteroid_diameter_m / 2.0
        mass = (4.0/3.0) * math.pi * (radius**3) * asteroid_density_kg_m3
        cross_section = math.pi * radius**2
        
        trajectory = []
        
        # PHASE 1: Orbital approach (start_altitude → entry_altitude)
        # No atmosphere, just gravity and initial velocity
        h = start_altitude_km * 1000  # meters
        v = v0
        x = 0.0
        time = 0.0
        dt_space = 1.0  # 1 second timestep in space (less precision needed)
        
        while h > entry_altitude_km * 1000 and time < 600:  # Max 10 minutes
            trajectory.append({
                "time": time,
                "altitude_km": h / 1000.0,
                "velocity_km_s": v / 1000.0,
                "horizontal_distance_km": x / 1000.0,
                "dynamic_pressure_pa": 0.0,  # No atmosphere yet
                "atmospheric_density": 0.0
            })
            
            # Simple ballistic motion (no drag in space)
            dx = v * math.cos(angle_rad) * dt_space
            dh = -v * math.sin(angle_rad) * dt_space
            
            x += dx
            h += dh
            time += dt_space
            
            # Velocity stays constant in space (ignoring Earth's gravity for simplicity)
            # In reality it would increase slightly due to gravity
        
        # PHASE 2: Atmospheric entry (entry_altitude → 0)
        # Atmospheric model (exponential)
        h_scale = 8500  # Scale height in meters
        rho0 = 1.225  # Sea level density kg/m^3
        Cd = 1.0  # Drag coefficient
        dt = 0.1  # seconds - finer timestep for atmosphere
        
        max_time = time + 120.0  # Maximum 2 more minutes in atmosphere
        
        while h > 0 and time < max_time and v > 0:
            # Atmospheric density at altitude
            rho = rho0 * math.exp(-h / h_scale)
            
            # Drag force
            drag = 0.5 * Cd * cross_section * rho * v**2
            
            # Acceleration (drag only, simplified)
            a_drag = -drag / mass
            a_gravity = -9.81 * math.sin(angle_rad)
            a_total = a_drag + a_gravity
            
            # Update velocity
            v += a_total * dt
            
            # Update position
            dx = v * math.cos(angle_rad) * dt
            dh = -v * math.sin(angle_rad) * dt  # Negative: asteroid falling DOWN
            
            x += dx
            h += dh
            
            # Dynamic pressure
            q = 0.5 * rho * v**2
            
            # Store trajectory point
            trajectory.append({
                "time": time,
                "altitude_km": h / 1000.0,
                "velocity_km_s": v / 1000.0,
                "horizontal_distance_km": x / 1000.0,
                "dynamic_pressure_pa": q,
                "atmospheric_density": rho
            })
            
            time += dt
            
            # Check for fragmentation (simple threshold)
            if q > 1e6 and asteroid_diameter_m < 100:  # 1 MPa threshold
                logger.info(f"Asteroid fragmentation at {h/1000:.1f} km altitude")
                break
        
        # Calculate impact velocity if it reached surface
        impact_velocity_km_s = v / 1000.0 if h <= 0 else 0.0
        impact_distance_km = x / 1000.0
        
        # CRITICAL FIX: Invert horizontal_distance_km so it counts DOWN to 0 at impact
        # Currently: starts at 0, ends at max (WRONG for visualization)
        # After fix: starts at max, ends at 0 (CORRECT - asteroid approaches impact point)
        max_horizontal_dist = impact_distance_km
        for point in trajectory:
            point["horizontal_distance_km"] = max_horizontal_dist - point["horizontal_distance_km"]
        
        return {
            "trajectory": trajectory,
            "impact_velocity_km_s": impact_velocity_km_s,
            "impact_distance_km": impact_distance_km,
            "entry_angle_deg": entry_angle_deg,
            "fragmented": len(trajectory) < 100 and h > 0,
            "airburst_altitude_km": h / 1000.0 if h > 0 else 0.0
        }
    
    def generate_trajectory_visualization(self,
                                         orbital_elements: Dict,
                                         num_points: int = 100,
                                         check_collision: bool = True,
                                         full_orbit: bool = True) -> List[Dict]:
        """
        Generate trajectory points for 3D visualization
        
        Args:
            orbital_elements: Keplerian elements
            num_points: Minimum number of points along orbit (used as resolution)
            check_collision: Check for Earth collision
            full_orbit: Calculate full orbital period (overrides num_points)
        
        Returns:
            List of position dicts with x, y, z in AU, collision status
        """
        trajectory_points = []
        
        # Calculate orbital period for full orbit visualization
        a = orbital_elements.get('semi_major_axis_au', 1.0)
        orbital_period_years = a ** 1.5  # Kepler's third law (simplified)
        
        # If full_orbit is True, calculate enough points for complete orbit
        # Use at least 360 points for smooth visualization
        if full_orbit:
            total_points = max(360, num_points)
        else:
            total_points = num_points
        
        # Earth position (simplified: assume circular orbit at 1 AU)
        # In reality, would need to calculate Earth's actual position
        earth_radius_au = EARTH_RADIUS / AU_TO_KM
        collision_threshold_au = earth_radius_au + (100.0 / AU_TO_KM)  # Earth radius + 100km buffer
        
        collision_detected = False
        collision_point = None
        
        for i in range(total_points):
            # Vary mean anomaly around orbit
            elements = orbital_elements.copy()
            mean_anomaly = (360.0 * i / total_points) % 360
            elements['mean_anomaly_deg'] = mean_anomaly
            
            position, velocity = self.keplerian_to_cartesian(elements)
            
            # Convert to AU
            pos_au = position / AU_TO_KM
            
            # Check distance from Earth (at origin for heliocentric frame)
            # For a more accurate check, calculate Earth's actual position
            # For now, check distance from Sun-Earth L1 point approximation
            # Simplified: check if asteroid crosses Earth's orbital zone
            distance_from_sun = np.linalg.norm(pos_au)
            
            # Check if asteroid is in Earth's orbital vicinity (within ~0.01 AU)
            # and at similar orbital phase
            earth_orbit_radius = 1.0  # AU
            radial_distance_from_earth_orbit = abs(distance_from_sun - earth_orbit_radius)
            
            # For collision detection, check if asteroid comes within collision threshold
            # of Earth's orbit at the same orbital phase
            if check_collision and radial_distance_from_earth_orbit < collision_threshold_au:
                # Potential collision - check 3D distance
                # Assume Earth is at (1, 0, 0) for this phase (simplified)
                # In reality, would calculate Earth's actual position at this time
                earth_pos_estimate = np.array([earth_orbit_radius, 0, 0])
                distance_to_earth_estimate = np.linalg.norm(pos_au - earth_pos_estimate)
                
                if distance_to_earth_estimate < collision_threshold_au:
                    collision_detected = True
                    collision_point = i
            
            trajectory_points.append({
                "x": float(pos_au[0]),
                "y": float(pos_au[1]),
                "z": float(pos_au[2]),
                "index": i,
                "mean_anomaly_deg": float(mean_anomaly),
                "distance_from_sun_au": float(distance_from_sun),
                "is_collision_zone": bool(radial_distance_from_earth_orbit < collision_threshold_au) if check_collision else False
            })
            
            # If collision detected and we want to stop there
            if collision_detected and check_collision:
                logger.info(f"Collision detected at point {i} (mean anomaly: {mean_anomaly:.1f}°)")
                break
        
        # Add metadata
        result_meta = {
            "collision_detected": bool(collision_detected),
            "collision_point_index": int(collision_point) if collision_point is not None else None,
            "total_points": int(len(trajectory_points)),
            "orbital_period_years": float(orbital_period_years),
            "full_orbit_calculated": bool(not collision_detected or not check_collision)
        }
        
        # Attach metadata to first point for easy access
        if trajectory_points:
            trajectory_points[0]["trajectory_metadata"] = result_meta
        
        return trajectory_points
    
    def calculate_close_approach(self,
                                 orbital_elements: Dict,
                                 earth_position: np.ndarray) -> Dict:
        """
        Calculate closest approach to Earth
        
        Args:
            orbital_elements: Keplerian elements
            earth_position: Earth position vector in heliocentric coords (AU)
        
        Returns:
            Dict with closest approach distance, time, relative velocity
        """
        # Current asteroid position
        ast_pos, ast_vel = self.keplerian_to_cartesian(orbital_elements)
        
        # Convert to same units (km)
        earth_pos_km = earth_position * AU_TO_KM
        
        # Distance to Earth
        rel_pos = ast_pos - earth_pos_km
        distance_km = np.linalg.norm(rel_pos)
        distance_au = distance_km / AU_TO_KM
        
        # Relative velocity
        # Assuming Earth velocity ~30 km/s circular orbit
        earth_vel = np.array([0, 30.0, 0])  # Simplified
        rel_vel = ast_vel - earth_vel
        relative_velocity_km_s = np.linalg.norm(rel_vel)
        
        return {
            "distance_km": distance_km,
            "distance_au": distance_au,
            "distance_earth_radii": distance_km / EARTH_RADIUS,
            "relative_velocity_km_s": relative_velocity_km_s,
            "is_collision": distance_km < EARTH_RADIUS + 100,  # Within 100 km of surface
            "collision_probability": self._estimate_collision_probability(distance_au, relative_velocity_km_s)
        }
    
    def _estimate_collision_probability(self, distance_au: float, velocity_km_s: float) -> float:
        """
        Estimate collision probability based on distance and velocity
        Very simplified model for demonstration
        """
        # Collision cross-section
        earth_cross_section = math.pi * (EARTH_RADIUS / AU_TO_KM)**2
        
        # Gravitational focusing factor
        v_inf = velocity_km_s
        v_esc = 11.2  # Earth escape velocity
        focusing_factor = 1 + (v_esc / v_inf)**2
        
        # Effective cross-section
        sigma_eff = earth_cross_section * focusing_factor
        
        # Probability (very simplified)
        if distance_au < 0.01:  # Very close approach
            prob = sigma_eff / (4 * math.pi * distance_au**2)
            return min(prob, 1.0)
        else:
            return 0.0


def calculate_impact_scenario(asteroid_params: Dict, 
                              orbital_elements: Optional[Dict] = None,
                              target_location: Optional[Dict] = None) -> Dict:
    """
    Calculate complete impact scenario with trajectory and location
    
    Args:
        asteroid_params: Diameter, velocity, density, angle
        orbital_elements: Optional Keplerian elements
        target_location: Optional specific lat/lon
    
    Returns:
        Complete impact scenario with trajectory, location, atmospheric entry
    """
    om = OrbitalMechanics()

    # Extract baseline parameters from request
    base_velocity_km_s = asteroid_params.get('velocity', 20.0)
    diameter_m = asteroid_params.get('diameter', 100.0)
    density = asteroid_params.get('density', 2500.0)
    base_angle = asteroid_params.get('angle', 45.0)

    intercept = None
    if orbital_elements:
        intercept = om.find_earth_intercept(orbital_elements)

    # Determine effective entry parameters
    effective_velocity = base_velocity_km_s
    effective_angle = base_angle
    impact_vector = np.array([effective_velocity, 0.0, 0.0])
    impact_lat = None
    impact_lon = None
    impact_azimuth = None

    if intercept:
        effective_velocity = intercept['entry_velocity_km_s']
        effective_angle = intercept['entry_angle_deg']
        impact_lat = intercept['latitude']
        impact_lon = intercept['longitude']
        impact_azimuth = intercept['azimuth_deg']
        impact_vector = np.array(intercept['relative_velocity_vector'])

    # Fallback or user-specified target overrides
    if target_location and impact_lat is None:
        impact_lat = target_location.get('latitude')
        impact_lon = target_location.get('longitude')
    if impact_lat is None or impact_lon is None:
        import random
        impact_lat = random.uniform(-60, 60)
        impact_lon = random.uniform(-180, 180)

    if impact_azimuth is None:
        impact_azimuth = om._calculate_azimuth(impact_vector)

    impact_location = om.calculate_impact_location(
        impact_vector,
        effective_angle,
        impact_lat,
        impact_lon
    )
    impact_location['impact_angle_deg'] = effective_angle
    impact_location['azimuth_deg'] = impact_azimuth

    # Calculate atmospheric entry using effective parameters
    entry_data = om.calculate_atmospheric_entry(
        effective_velocity,
        effective_angle,
        diameter_m,
        density,
        entry_altitude_km=100.0
    )

    # Generate orbital trajectory if elements provided
    orbital_trajectory = None
    if orbital_elements:
        orbital_trajectory = om.generate_trajectory_visualization(orbital_elements, 50)

    return {
        "impact_location": impact_location,
        "atmospheric_entry": entry_data,
        "orbital_trajectory": orbital_trajectory,
        "orbital_intercept": intercept,
        "effective_parameters": {
            "entry_velocity_km_s": effective_velocity,
            "entry_angle_deg": effective_angle
        },
        "asteroid_params": asteroid_params
    }


if __name__ == "__main__":
    # Test orbital mechanics
    print("Testing Orbital Mechanics...")
    
    om = OrbitalMechanics()
    
    # Test Keplerian to Cartesian
    elements = {
        'semi_major_axis_au': 1.5,
        'eccentricity': 0.2,
        'inclination_deg': 10.0,
        'longitude_ascending_node_deg': 45.0,
        'argument_periapsis_deg': 30.0,
        'mean_anomaly_deg': 0.0
    }
    
    pos, vel = om.keplerian_to_cartesian(elements)
    print(f"Position: {pos} km")
    print(f"Velocity: {vel} km/s")
    
    # Test atmospheric entry
    print("\nTesting Atmospheric Entry...")
    entry = om.calculate_atmospheric_entry(
        initial_velocity_km_s=20.0,
        entry_angle_deg=45.0,
        asteroid_diameter_m=50.0,
        asteroid_density_kg_m3=2500.0
    )
    
    print(f"Trajectory points: {len(entry['trajectory'])}")
    print(f"Impact velocity: {entry['impact_velocity_km_s']:.2f} km/s")
    print(f"Fragmented: {entry['fragmented']}")
    
    # Test complete scenario
    print("\nTesting Complete Impact Scenario...")
    scenario = calculate_impact_scenario(
        asteroid_params={'diameter': 100, 'velocity': 20, 'density': 2500, 'angle': 45},
        target_location={'latitude': 40.7, 'longitude': -74.0}  # New York
    )
    
    print(f"Impact location: {scenario['impact_location']['latitude']:.2f}°, "
          f"{scenario['impact_location']['longitude']:.2f}°")
    print(f"Impact velocity: {scenario['atmospheric_entry']['impact_velocity_km_s']:.2f} km/s")

/**
 * API Service for backend integration
 * Provides real trajectory data and impact simulations
 */

const API_BASE_URL = '/api';

export interface AsteroidParams {
  diameter: number;      // meters
  velocity: number;      // km/s
  density: number;       // kg/m³
  angle: number;         // degrees from horizontal
}

export interface TrajectoryPoint {
  time: number;
  altitude_km: number;
  velocity_km_s: number;
  horizontal_distance_km: number;
  dynamic_pressure_pa: number;
  atmospheric_density: number;
}

export interface ImpactLocation {
  latitude: number;
  longitude: number;
  impact_angle_deg: number;
  azimuth_deg: number;
  impact_point: [number, number];  // [lon, lat]
}

export interface ImpactResults {
  crater_diameter: number;
  crater_depth: number;
  kinetic_energy_joules: number;
  energy_mt_tnt: number;
  thermal_radius_km: number;
  overpressure_radius_km: number;
  seismic_magnitude: number;
  
  // Comprehensive danger assessment
  danger_assessment?: {
    severity: string;
    impact_type: string;
    damage_zones: {
      fireball_km: number;
      total_destruction_km: number;
      severe_damage_km: number;
      moderate_damage_km: number;
      light_damage_km: number;
      thermal_burns_km: number;
    };
    casualties: {
      immediate_deaths_estimate: number;
      injured_estimate: number;
      affected_population: number;
      data_source?: string;
      country_code?: string;
      zone_breakdown?: {
        fireball: { population: number; fatality_rate: number };
        total_destruction: { population: number; fatality_rate: number };
        severe_damage: { population: number; fatality_rate: number };
        moderate_damage: { population: number; fatality_rate: number };
        light_damage: { population: number; fatality_rate: number };
      };
      location_info?: {
        country_code: string;  // ISO-3 (e.g., USA)
        country_code_iso2?: string;  // ISO-2 (e.g., US)
        country_name: string;
        city?: string;
        state?: string;
        continent?: string;
        ocean?: string;
        is_ocean: boolean;
        latitude: number;
        longitude: number;
      };
      note: string;
    };
    tsunami?: {
      // New enhanced tsunami model fields
      tsunami_generated?: boolean;
      initial_wave_amplitude_m?: number;
      coastal_wave_height_m?: number;
      wave_period_seconds?: number;
      wave_speed_m_s?: number;
      wave_speed_km_h?: number;
      inundation_distance_km?: number;
      tsunami_energy_joules?: number;
      energy_mt_tnt?: number;
      ocean_depth_m?: number;
      depth_ratio?: number;
      coupling_efficiency?: number;
      risk_level?: string;
      affected_radius_km?: number;
      description?: string;
      impact_location?: {
        latitude: number;
        longitude: number;
        ocean_depth_m: number;
        coastal_elevation_m: number;
        coastal_slope: number;
        data_source: string;
      };
      // Legacy fields (for backward compatibility)
      wave_height_at_source_m?: number;
      tsunami_velocity_kmh?: number;
      wave_heights_at_distance?: Record<string, number>;
      coastal_inundation_distance_m?: number;
      arrival_time_hours?: Record<string, number>;
      warning?: string;
    };
    atmospheric_effects: {
      stratospheric_dust_kg: number;
      global_dust_loading_mg_m2: number;
      temperature_drop_celsius: number;
      effect_duration: string;
      soot_from_fires_kg?: number;
      sunlight_reduction_percent: number;
      note: string;
    };
    ejecta: {
      ejecta_blanket_radius_km: number;
      ballistic_range_km: number;
      ejecta_thickness_at_crater_m: number;
      global_fires_from_reentry: boolean;
      note: string;
    };
    global_effects: {
      is_global_catastrophe: boolean;
      mass_extinction_risk: boolean;
      crop_failure_risk: boolean;
      global_famine_risk: boolean;
      civilization_threat: boolean;
      description: string;
    };
    comparable_to: string;
  };
  
  // DEPRECATED: USGS data (kept for backward compatibility)
  usgs_damage_scale?: {
    mercalli_intensity: string;
    description: string;
  };
  similar_earthquakes?: Array<{
    location: string;
    magnitude: number;
    year: number;
  }>;
}

export interface OrbitalIntercept {
  entry_velocity_km_s: number;
  entry_angle_deg: number;
  latitude?: number;
  longitude?: number;
  azimuth_deg?: number;
  mean_anomaly_deg?: number;
  distance_to_orbit_km?: number;
  relative_velocity_vector?: number[];
  position_vector?: number[];
  relative_position_vector?: number[];
}

export interface SimulationResponse {
  impact_results: ImpactResults;
  location: ImpactLocation;
  trajectory_data: TrajectoryPoint[];
  orbital_intercept?: OrbitalIntercept | null;
  computation_time_ms: number;
}

export interface OrbitalElements {
  semi_major_axis_au: number;
  eccentricity: number;
  inclination_deg: number;
  longitude_ascending_node_deg: number;
  argument_periapsis_deg: number;
  mean_anomaly_deg: number;
}

export interface OrbitalPoint {
  x: number;  // AU
  y: number;  // AU
  z: number;  // AU
  index: number;
}

export interface Scenario {
  name: string;
  asteroid_params: AsteroidParams;
  location: { latitude: number; longitude: number };
  description: string;
  orbital_elements?: OrbitalElements;
}

/**
 * Run full impact simulation with trajectory
 */
export async function simulateImpact(
  asteroidParams: AsteroidParams,
  latitude: number,
  longitude: number,
  orbitalElements?: OrbitalElements | null
): Promise<SimulationResponse> {
  const response = await fetch(`${API_BASE_URL}/simulation/impact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      asteroid_params: asteroidParams,
      location_lat: latitude,
      location_lon: longitude,
      orbital_elements: orbitalElements ?? null,
      include_trajectory: true,
      include_usgs_correlation: true,
    }),
  });

  if (!response.ok) {
    throw new Error(`Simulation failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get atmospheric entry trajectory only
 */
export async function getTrajectory(
  asteroidParams: AsteroidParams,
  latitude: number,
  longitude: number
): Promise<{ trajectory: TrajectoryPoint[]; impact_location: ImpactLocation }> {
  const response = await fetch(`${API_BASE_URL}/simulation/trajectory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      asteroid_params: asteroidParams,
      latitude,
      longitude,
    }),
  });

  if (!response.ok) {
    throw new Error(`Trajectory calculation failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get preset scenario
 */
export async function getScenario(scenarioName: string): Promise<{
  scenario: Scenario;
  impact_effects: ImpactResults;
  trajectory_preview: TrajectoryPoint[];
}> {
  const response = await fetch(`${API_BASE_URL}/simulation/scenario/${scenarioName}`);

  if (!response.ok) {
    throw new Error(`Failed to load scenario: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get orbital trajectory for 3D space visualization
 * Now calculates complete orbital path until collision or full cycle
 */
export async function getOrbitalTrajectory(
  orbitalElements: OrbitalElements,
  numPoints: number = 360,
  checkCollision: boolean = true,
  fullOrbit: boolean = true
): Promise<{ 
  trajectory: OrbitalPoint[]; 
  orbital_elements: OrbitalElements;
  metadata: {
    collision_detected: boolean;
    collision_point_index: number | null;
    orbital_period_years: number;
    full_orbit_calculated: boolean;
    points_calculated: number;
  }
}> {
  const params = new URLSearchParams({
    num_points: numPoints.toString(),
    check_collision: checkCollision.toString(),
    full_orbit: fullOrbit.toString()
  });

  const response = await fetch(`${API_BASE_URL}/simulation/orbital-trajectory?${params}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orbitalElements),
  });

  if (!response.ok) {
    throw new Error(`Orbital trajectory calculation failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Real asteroid data interfaces
 */
export interface RealAsteroid {
  id: string;
  name: string;
  nasa_jpl_url: string;
  absolute_magnitude_h: number;
  diameter_min_m: number;
  diameter_max_m: number;
  is_potentially_hazardous: boolean;
  close_approaches: {
    date: string;
    velocity_km_s: number;
    miss_distance_km: number;
    miss_distance_lunar: number;
  }[];
}

export interface NASAAsteroidData {
  object_id: string;
  name: string;
  is_potentially_hazardous: boolean;
  orbital_elements: OrbitalElements;
  physical_parameters: {
    absolute_magnitude_H: number;
    diameter_km: number;
    albedo: number;
    rotation_period_hours: number | null;
  };
  close_approaches: any[];
  orbit_class: string;
  jpl_url: string;
}

/**
 * Fetch potentially hazardous asteroids from NASA
 */
export async function getPotentiallyHazardousAsteroids(limit: number = 20): Promise<RealAsteroid[]> {
  const response = await fetch(`${API_BASE_URL}/nasa/potentially-hazardous?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch asteroids: ${response.statusText}`);
  }
  const data = await response.json();
  return data.phas;
}

/**
 * Fetch detailed asteroid data from NASA SBDB
 */
export async function getNASAAsteroidData(nameOrId: string): Promise<NASAAsteroidData> {
  const response = await fetch(`${API_BASE_URL}/nasa/asteroid/${encodeURIComponent(nameOrId)}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch asteroid data: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Available preset scenarios (kept as example only - Tunguska)
 */
export const SCENARIOS = [
  { id: 'tunguska', name: 'Tunguska (1908)', icon: '🌲', description: 'Example historical impact' },
] as const;

export type ScenarioId = typeof SCENARIOS[number]['id'];

/**
 * Monte Carlo impact probability heatmap interfaces
 */


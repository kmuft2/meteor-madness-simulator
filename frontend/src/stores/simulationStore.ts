import { create } from 'zustand';
import type {
  AsteroidParams,
  TrajectoryPoint,
  ImpactLocation,
  ImpactResults,
  ScenarioId,
  OrbitalElements,
  OrbitalPoint,
  OrbitalIntercept,
} from '../services/simulationApi';
import {
  simulateImpact,
  getScenario,
  getOrbitalTrajectory,
  SCENARIOS,
} from '../services/simulationApi';

interface SimulationState {
  time: number;
  maxTime: number;
  impactTime: number;
  playing: boolean;
  speed: number;
  asteroidParams: AsteroidParams;
  impactLocation: ImpactLocation;
  trajectoryData: TrajectoryPoint[];
  impactResults: ImpactResults | null;
  orbitalIntercept: OrbitalIntercept | null;
  orbitalElements: OrbitalElements | null;
  orbitalTrajectory: OrbitalPoint[];
  orbitalMetadata: {
    collision_detected: boolean;
    collision_point_index: number | null;
    orbital_period_years: number;
    full_orbit_calculated: boolean;
    points_calculated: number;
  } | null;
  orbitalTrajectoryLoading: boolean;
  orbitalTrajectoryError: string | null;
  showOrbitalPath: boolean;
  currentScenario: ScenarioId | 'custom';
  loading: boolean;
  error: string | null;

  setTime: (time: number) => void;
  setPlaying: (playing: boolean) => void;
  setSpeed: (speed: number) => void;
  reset: () => void;
  updateTime: (deltaSeconds: number) => void;
  setAsteroidParams: (params: Partial<AsteroidParams>) => void;
  setImpactLocation: (lat: number, lon: number) => void;
  setOrbitalElements: (elements: OrbitalElements | null) => void;
  placeAsteroidAt: (latitude: number, longitude: number) => Promise<void>;
  runSimulation: (
    params: AsteroidParams,
    lat: number,
    lon: number,
    orbitalElements?: OrbitalElements | null
  ) => Promise<void>;
  loadScenario: (scenarioId: ScenarioId) => Promise<void>;
  loadOrbitalTrajectory: (elements: OrbitalElements) => Promise<void>;
  toggleOrbitalPath: () => void;
}

const orbitalElementsEqual = (
  current: OrbitalElements | null,
  next: OrbitalElements | null
): boolean => {
  if (!current || !next) {
    return current === next;
  }

  return (
    current.semi_major_axis_au === next.semi_major_axis_au &&
    current.eccentricity === next.eccentricity &&
    current.inclination_deg === next.inclination_deg &&
    current.longitude_ascending_node_deg === next.longitude_ascending_node_deg &&
    current.argument_periapsis_deg === next.argument_periapsis_deg &&
    current.mean_anomaly_deg === next.mean_anomaly_deg
  );
};

const DEFAULT_ASTEROID_PARAMS: AsteroidParams = {
  diameter: 100,
  velocity: 20,
  density: 2500,
  angle: 45,
};

const DEFAULT_IMPACT_LOCATION: ImpactLocation = {
  latitude: 40.7128,
  longitude: -74.006,
  impact_angle_deg: DEFAULT_ASTEROID_PARAMS.angle,
  azimuth_deg: 90,
  impact_point: [-74.006, 40.7128],
};

export const useSimulationStore = create<SimulationState>((set, get) => ({
  time: 0,
  maxTime: 5400,
  impactTime: 2700,
  playing: false,
  speed: 1,
  asteroidParams: DEFAULT_ASTEROID_PARAMS,
  impactLocation: DEFAULT_IMPACT_LOCATION,
  trajectoryData: [],
  impactResults: null,
  orbitalIntercept: null,
  orbitalElements: null,
  orbitalTrajectory: [],
  orbitalMetadata: null,
  orbitalTrajectoryLoading: false,
  orbitalTrajectoryError: null,
  showOrbitalPath: false,
  currentScenario: 'custom',
  loading: false,
  error: null,

  setTime: (time: number) => {
    const clamped = Math.max(0, Math.min(time, get().maxTime));
    set({ time: clamped });
  },

  setPlaying: (playing: boolean) => set({ playing }),

  setSpeed: (speed: number) => set({ speed }),

  reset: () =>
    set({
      time: 0,
      playing: false,
    }),

  updateTime: (deltaSeconds: number) => {
    const { playing, speed, time, maxTime } = get();
    if (!playing) {
      return;
    }

    const newTime = time + deltaSeconds * speed * 60;
    const clamped = Math.max(0, Math.min(newTime, maxTime));
    set({ time: clamped });

    if (clamped <= 0 || clamped >= maxTime) {
      set({ playing: false });
    }
  },

  setAsteroidParams: (params: Partial<AsteroidParams>) => {
    set({
      asteroidParams: { ...get().asteroidParams, ...params },
      currentScenario: 'custom',
    });
  },

  setImpactLocation: (lat: number, lon: number) => {
    const { asteroidParams, impactLocation } = get();
    set({
      impactLocation: {
        latitude: lat,
        longitude: lon,
        impact_angle_deg: asteroidParams.angle,
        azimuth_deg: impactLocation?.azimuth_deg ?? 90,
        impact_point: [lon, lat],
      },
      currentScenario: 'custom',
    });
  },

  setOrbitalElements: (elements: OrbitalElements | null) => {
    const currentElements = get().orbitalElements;

    set({
      orbitalElements: elements,
    });

    if (orbitalElementsEqual(currentElements, elements)) {
      return;
    }

    if (elements) {
      void get().loadOrbitalTrajectory(elements);
    } else {
      set({
        orbitalTrajectory: [],
        orbitalMetadata: null,
        orbitalTrajectoryLoading: false,
        orbitalTrajectoryError: null,
        showOrbitalPath: false,
      });
    }
  },

  placeAsteroidAt: async (latitude: number, longitude: number) => {
    const { asteroidParams, orbitalElements } = get();
    await get().runSimulation(asteroidParams, latitude, longitude, orbitalElements);
    set({ currentScenario: 'custom' });
  },

  runSimulation: async (
    params: AsteroidParams,
    lat: number,
    lon: number,
    orbitalElements: OrbitalElements | null = null
  ) => {
    set({ loading: true, error: null });

    try {
      const data = await simulateImpact(params, lat, lon, orbitalElements);
      const fallbackLocation = get().impactLocation ?? DEFAULT_IMPACT_LOCATION;
      const rawLocation = data.location ?? fallbackLocation;

      const normalizedLocation: ImpactLocation = {
        latitude: rawLocation.latitude,
        longitude: rawLocation.longitude,
        impact_angle_deg: rawLocation.impact_angle_deg ?? params.angle,
        azimuth_deg: rawLocation.azimuth_deg ?? fallbackLocation.azimuth_deg,
        impact_point: rawLocation.impact_point ?? [rawLocation.longitude, rawLocation.latitude],
      };

      const intercept = data.orbital_intercept ?? null;

      set({
        asteroidParams: params,
        impactLocation: normalizedLocation,
        trajectoryData: data.trajectory_data ?? [],
        impactResults: data.impact_results ?? null,
        orbitalIntercept: intercept,
        orbitalElements: orbitalElements ?? get().orbitalElements,
        loading: false,
        time: 0,
        playing: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Simulation failed',
        loading: false,
      });
      console.error('Simulation error:', error);
    }
  },

  loadScenario: async (scenarioId: ScenarioId) => {
    set({ loading: true, error: null });

    try {
      const { scenario, impact_effects, trajectory_preview } = await getScenario(scenarioId);

      const scenarioLocation: ImpactLocation = {
        latitude: scenario.location.latitude,
        longitude: scenario.location.longitude,
        impact_angle_deg: scenario.asteroid_params.angle,
        azimuth_deg: scenario.orbital_elements ? get().impactLocation?.azimuth_deg ?? 90 : 90,
        impact_point: [scenario.location.longitude, scenario.location.latitude],
      };

      set({
        currentScenario: scenarioId,
        asteroidParams: scenario.asteroid_params,
        impactLocation: scenarioLocation,
        trajectoryData: trajectory_preview ?? [],
        impactResults: impact_effects ?? null,
        loading: false,
        time: 0,
        playing: false,
      });

      if (scenario.orbital_elements) {
        get().setOrbitalElements(scenario.orbital_elements);
      }

      void get().runSimulation(
        scenario.asteroid_params,
        scenario.location.latitude,
        scenario.location.longitude,
        scenario.orbital_elements ?? null
      );
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load scenario',
        loading: false,
      });
      console.error('Scenario load error:', error);
    }
  },

  loadOrbitalTrajectory: async (elements: OrbitalElements) => {
    set({
      orbitalTrajectoryLoading: true,
      orbitalTrajectoryError: null,
      orbitalTrajectory: [],
      orbitalMetadata: null,
      showOrbitalPath: false,
    });

    try {
      const { trajectory, metadata } = await getOrbitalTrajectory(elements);

      set({
        orbitalTrajectory: trajectory,
        orbitalMetadata: metadata,
        orbitalTrajectoryLoading: false,
        orbitalTrajectoryError: null,
        showOrbitalPath: true,
      });

      if (metadata.collision_detected) {
        console.warn(`⚠️ Collision detected at point ${metadata.collision_point_index}`);
      }
    } catch (error) {
      console.error('Failed to load orbital trajectory:', error);
      set({
        orbitalTrajectory: [],
        orbitalMetadata: null,
        orbitalTrajectoryLoading: false,
        orbitalTrajectoryError:
          error instanceof Error ? error.message : 'Failed to load orbital trajectory',
        showOrbitalPath: false,
      });
    }
  },

  toggleOrbitalPath: () => set({ showOrbitalPath: !get().showOrbitalPath }),
}));

export { SCENARIOS };

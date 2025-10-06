import { useMemo } from 'react';
import * as THREE from 'three';
import { useSimulationStore } from '../../stores/simulationStore';
import { Line } from '@react-three/drei';

const EARTH_RADIUS = 6371;

/**
 * Convert lat/lon/altitude to 3D Cartesian coordinates
 */
function latLonAltToCartesian(lat: number, lon: number, altitudeKm: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  const radius = EARTH_RADIUS + altitudeKm;
  
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

export function TrajectoryLine() {
  const { trajectoryData, impactLocation, time, impactTime, asteroidParams } = useSimulationStore();
  
  // Calculate if impact has occurred
  const hasImpacted = useMemo(() => {
    if (trajectoryData.length === 0) return false;
    
    const asteroidRadiusKm = (asteroidParams.diameter / 2) / 1000;
    const progress = Math.min(1.0, Math.max(0, time / impactTime));
    const index = Math.floor(progress * (trajectoryData.length - 1));
    const point = trajectoryData[Math.min(index, trajectoryData.length - 1)];
    
    return point.altitude_km <= asteroidRadiusKm;
  }, [trajectoryData, time, impactTime, asteroidParams.diameter]);
  
  const points = useMemo(() => {
    if (!impactLocation || trajectoryData.length === 0) {
      // No trajectory data yet - return empty or simple fallback line
      return [];
    }
    
    // Use real trajectory data with HORIZONTAL movement along azimuth
    // The asteroid approaches from a direction (azimuth) and descends
    const azimuth = (impactLocation.azimuth_deg || 90) * (Math.PI / 180);
    const earthCircumference = 2 * Math.PI * EARTH_RADIUS;
    
    const pts: THREE.Vector3[] = trajectoryData.map(point => {
      // Calculate how far back from impact point based on horizontal distance
      const horizontalDist = point.horizontal_distance_km || 0;
      
      // Convert horizontal distance to angular displacement
      // Project backward from impact point along approach azimuth
      const latOffset = -(horizontalDist / earthCircumference) * 360 * Math.cos(azimuth);
      const lonOffset = -(horizontalDist / earthCircumference) * 360 * Math.sin(azimuth) / 
                        Math.cos(impactLocation.latitude * Math.PI / 180);
      
      const currentLat = impactLocation.latitude + latOffset;
      const currentLon = impactLocation.longitude + lonOffset;
      
      return latLonAltToCartesian(
        currentLat,
        currentLon,
        point.altitude_km
      );
    });
    
    return pts;
  }, [trajectoryData, impactLocation]);
  
  // Hide trajectory line after impact
  if (points.length === 0 || hasImpacted) {
    return null;
  }
  
  return (
    <Line
      points={points}
      color="#ff6600"
      lineWidth={2}
      dashed
      dashScale={0.01}
      dashSize={0.5}
      gapSize={0.3}
      transparent
      opacity={0.6}
    />
  );
}



import { useRef, useMemo } from 'react';
import * as THREE from 'three';
import { useSimulationStore } from '../../stores/simulationStore';

const EARTH_RADIUS = 6371;

// Visibility scale for craters (makes them visible while keeping physics accurate)
const CRATER_VISIBILITY_SCALE = 1; // Makes craters 200x larger for visibility

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

/**
 * ImpactCrater component
 * Displays a realistic 3D crater on Earth surface after impact
 * 
 * DYNAMIC SIZING: Crater size is calculated from real physics (impact energy, angle, etc.)
 * and scales proportionally with impact parameters. Larger/faster asteroids = bigger craters.
 * 
 * VISIBILITY: Applied 50x scale for visualization (real craters too small to see at Earth scale)
 * Physics calculations remain accurate - only visual representation is scaled.
 */
export function ImpactCrater() {
  const craterMeshRef = useRef<THREE.Mesh>(null);
  const craterRimRef = useRef<THREE.Mesh>(null);
  const ejectaRef = useRef<THREE.Mesh>(null);
  
  const { 
    time, 
    impactTime,
    impactLocation,
    impactResults,
    trajectoryData,
    asteroidParams
  } = useSimulationStore();

  const impactData = useMemo(() => {
    const asteroidRadiusKm = (asteroidParams.diameter / 2) / 1000;

    let trajectoryPoint: (typeof trajectoryData)[number] | null = null;
    if (trajectoryData.length > 0) {
      for (let i = 0; i < trajectoryData.length; i += 1) {
        if (trajectoryData[i].altitude_km <= asteroidRadiusKm) {
          trajectoryPoint = trajectoryData[i];
          break;
        }
      }

      if (!trajectoryPoint) {
        trajectoryPoint = trajectoryData[trajectoryData.length - 1];
      }
    }

    let actualImpactTimeSeconds: number | null = null;
    if (trajectoryPoint?.time !== undefined) {
      actualImpactTimeSeconds = trajectoryPoint.time;
    } else if (trajectoryData.length > 0) {
      if (trajectoryData.length === 1) {
        actualImpactTimeSeconds = impactTime;
      } else {
        for (let i = 0; i < trajectoryData.length; i += 1) {
          if (trajectoryData[i].altitude_km <= asteroidRadiusKm) {
            const progress = i / (trajectoryData.length - 1);
            actualImpactTimeSeconds = progress * impactTime;
            break;
          }
        }
      }
    }

    const azimuthRad = ((impactLocation?.azimuth_deg ?? 90) * Math.PI) / 180;
    const horizontalDistanceKm = trajectoryPoint?.horizontal_distance_km ?? 0;

    let impactLatLon: { latitude: number; longitude: number } | null = null;
    if (impactLocation) {
      const earthCircumference = 2 * Math.PI * EARTH_RADIUS;
      const latOffset = -(horizontalDistanceKm / earthCircumference) * 360 * Math.cos(azimuthRad);

      const latRad = (impactLocation.latitude * Math.PI) / 180;
      const cosLat = Math.cos(latRad);
      const lonOffset = cosLat !== 0
        ? -(horizontalDistanceKm / earthCircumference) * 360 * Math.sin(azimuthRad) / cosLat
        : 0;

      impactLatLon = {
        latitude: impactLocation.latitude + latOffset,
        longitude: impactLocation.longitude + lonOffset,
      };
    }

    const earthRotationAtImpact = actualImpactTimeSeconds !== null
      ? (actualImpactTimeSeconds / 86400) * Math.PI * 2
      : 0;

    const surfacePosition = impactLatLon
      ? latLonAltToCartesian(impactLatLon.latitude, impactLatLon.longitude, 0)
      : new THREE.Vector3(0, 0, 0);

    const impactPositionAtImpact = surfacePosition.clone().applyAxisAngle(
      new THREE.Vector3(0, 1, 0),
      earthRotationAtImpact
    );

    const impactNormalAtImpact = impactPositionAtImpact.lengthSq() > 0
      ? impactPositionAtImpact.clone().normalize()
      : new THREE.Vector3(0, 1, 0);

    return {
      actualImpactTimeSeconds,
      impactLatLon,
      surfacePosition,
      impactPositionAtImpact,
      impactNormalAtImpact,
      earthRotationAtImpact,
    };
  }, [asteroidParams.diameter, impactLocation, impactTime, trajectoryData]);

  const actualImpactTime = impactData.actualImpactTimeSeconds;
  const showCrater = actualImpactTime !== null && time >= actualImpactTime;
  const timeSinceImpact = showCrater && actualImpactTime !== null ? time - actualImpactTime : 0;

  const currentEarthRotation = (time / 86400) * Math.PI * 2;
  const rotationSinceImpact = currentEarthRotation - impactData.earthRotationAtImpact;

  const { impactPosition, impactNormal } = useMemo(() => {
    const rotatedPosition = impactData.impactPositionAtImpact.clone().applyAxisAngle(
      new THREE.Vector3(0, 1, 0),
      rotationSinceImpact
    );

    const rotatedNormal = impactData.impactNormalAtImpact.clone().applyAxisAngle(
      new THREE.Vector3(0, 1, 0),
      rotationSinceImpact
    );

    return {
      impactPosition: rotatedPosition,
      impactNormal: rotatedNormal,
    };
  }, [impactData.impactPositionAtImpact, impactData.impactNormalAtImpact, rotationSinceImpact]);

  const craterGeometry = useMemo(() => {
    if (!impactResults) {
      return null;
    }

    const craterDiameterMeters = impactResults.crater_diameter;
    const craterDepthMeters = impactResults.crater_depth;

    const craterRadiusKm = ((craterDiameterMeters / 2) / 1000) * CRATER_VISIBILITY_SCALE;
    const craterDepthKm = (craterDepthMeters / 1000) * CRATER_VISIBILITY_SCALE;

    const segments = 64;
    const geometry = new THREE.CircleGeometry(craterRadiusKm, segments);

    const positions = geometry.attributes.position;
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const y = positions.getY(i);
      const distFromCenter = Math.sqrt(x * x + y * y);
      const normalizedDist = craterRadiusKm !== 0 ? distFromCenter / craterRadiusKm : 0;

      const depth = -craterDepthKm * (1 - normalizedDist * normalizedDist);
      positions.setZ(i, depth);
    }

    geometry.computeVertexNormals();
    return geometry;
  }, [impactResults]);

  const rimGeometry = useMemo(() => {
    if (!impactResults) {
      return null;
    }

    const craterDiameterMeters = impactResults.crater_diameter;
    const craterRadiusKm = ((craterDiameterMeters / 2) / 1000) * CRATER_VISIBILITY_SCALE;
    const rimHeightKm = craterRadiusKm * 0.05;

    const segments = 64;
    const geometry = new THREE.RingGeometry(
      craterRadiusKm * 0.95,
      craterRadiusKm * 1.15,
      segments
    );

    const positions = geometry.attributes.position;
    for (let i = 0; i < positions.count; i++) {
      positions.setZ(i, rimHeightKm);
    }

    geometry.computeVertexNormals();
    return geometry;
  }, [impactResults]);

  const ejectaGeometry = useMemo(() => {
    if (!impactResults) {
      return null;
    }

    const craterDiameterMeters = impactResults.crater_diameter;
    const craterRadiusKm = ((craterDiameterMeters / 2) / 1000) * CRATER_VISIBILITY_SCALE;
    const ejectaRadiusKm = craterRadiusKm * 2.5;
    const segments = 64;

    const geometry = new THREE.RingGeometry(
      craterRadiusKm * 1.15,
      ejectaRadiusKm,
      segments
    );

    const positions = geometry.attributes.position;
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const y = positions.getY(i);
      const distFromCenter = Math.sqrt(x * x + y * y);
      const normalizedDist = ejectaRadiusKm !== craterRadiusKm
        ? (distFromCenter - craterRadiusKm) / (ejectaRadiusKm - craterRadiusKm)
        : 0;

      const thickness = 0.02 * Math.exp(-normalizedDist * 3);
      positions.setZ(i, thickness);
    }

    geometry.computeVertexNormals();
    return geometry;
  }, [impactResults]);

  const quaternion = useMemo(() => {
    const q = new THREE.Quaternion();
    const up = new THREE.Vector3(0, 0, 1);
    q.setFromUnitVectors(up, impactNormal);
    return q;
  }, [impactNormal]);
  
  // Debug: Log when conditions change
  if (typeof window !== 'undefined') {
    const debugInfo = {
      showCrater,
      hasGeometry: !!craterGeometry && !!rimGeometry && !!ejectaGeometry,
      actualImpactTime,
      currentTime: time,
      craterDiameter: impactResults?.crater_diameter
    };
    
    // Only log when showCrater changes
    const prev = (window as any).__prevShowCrater;
    if (prev !== showCrater) {
      console.log('🌑 Crater visibility changed:', debugInfo);
      (window as any).__prevShowCrater = showCrater;
    }
  }
  
  if (!showCrater || !craterGeometry || !rimGeometry || !ejectaGeometry) {
    return null;
  }
  
  console.log('✅ Rendering crater! Diameter:', impactResults?.crater_diameter, 'm');
  
  return (
    <group>
      <group position={impactPosition} quaternion={quaternion}>
      {/* Crater bowl - dark, shadowed */}
      <mesh ref={craterMeshRef} visible={true} scale={timeSinceImpact >= 5 ? 1 : Math.min(1, timeSinceImpact / 5)}>
        <primitive object={craterGeometry} />
        <meshStandardMaterial
          color="#2c1810"
          roughness={0.95}
          metalness={0.05}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* Crater rim - raised edge */}
      <mesh ref={craterRimRef} visible={true} scale={timeSinceImpact >= 5 ? 1 : Math.min(1, timeSinceImpact / 5)}>
        <primitive object={rimGeometry} />
        <meshStandardMaterial
          color="#4a3528"
          roughness={0.9}
          metalness={0.1}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* Ejecta blanket - debris field */}
      <mesh 
        ref={ejectaRef} 
        visible={timeSinceImpact >= 1}
        scale={timeSinceImpact >= 5 ? 1 : Math.max(0, (timeSinceImpact - 1) / 4)}
      >
        <primitive object={ejectaGeometry} />
        <meshStandardMaterial
          color="#6b5544"
          roughness={0.85}
          metalness={0.15}
          transparent
          opacity={0.7}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* Hot glowing crater center (fades over time) */}
      <mesh position={[0, 0, impactResults ? -((impactResults.crater_depth / 2 / 1000) * CRATER_VISIBILITY_SCALE) : 0]}>
        <circleGeometry args={[
          impactResults ? ((impactResults.crater_diameter / 4 / 1000) * CRATER_VISIBILITY_SCALE) : 1,
          32
        ]} />
        <meshBasicMaterial
          color="#ff3300"
          transparent
          opacity={Math.max(0, 1 - timeSinceImpact / 30)}
          side={THREE.DoubleSide}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
      </group>
    </group>
  );
}
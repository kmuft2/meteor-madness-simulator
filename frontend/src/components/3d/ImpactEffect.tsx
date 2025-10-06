import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useSimulationStore } from '../../stores/simulationStore';

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

/**
 * ImpactEffect component
 * Displays transient visual effects after asteroid impact including:
 * - Explosion flash (first 2 seconds)
 * - Expanding shockwave ring (0-30 seconds)
 * Note: Persistent crater glow handled by ImpactCrater component
 */
export function ImpactEffect() {
  const explosionRef = useRef<THREE.Mesh>(null);
  const shockwaveRef = useRef<THREE.Mesh>(null);
  // craterGlowRef removed - ImpactCrater component handles the glowing crater center
  
  const { 
    time, 
    impactTime,
    impactLocation,
    impactResults,
    trajectoryData,
    asteroidParams
  } = useSimulationStore();
  
  // Calculate actual impact time based on when asteroid surface touches Earth
  const getActualImpactTime = (): number | null => {
    if (trajectoryData.length === 0) return null;
    
    const asteroidRadiusKm = (asteroidParams.diameter / 2) / 1000; // meters to km
    
    // Find the first trajectory point where altitude <= asteroid radius
    for (let i = 0; i < trajectoryData.length; i++) {
      if (trajectoryData[i].altitude_km <= asteroidRadiusKm) {
        // Calculate the time at this point
        const progress = i / (trajectoryData.length - 1);
        return progress * impactTime;
      }
    }
    return null;
  };
  
  // Determine if impact has actually occurred
  const actualImpactTime = getActualImpactTime();
  const showImpact = actualImpactTime !== null && time >= actualImpactTime;
  const timeSinceImpact = showImpact && actualImpactTime !== null ? time - actualImpactTime : 0;
  
  // Store the Earth rotation at impact time (same as ImpactCrater)
  const impactRotationRef = useRef<number | null>(null);
  
  // Calculate and store Earth's rotation at impact (once)
  if (showImpact && impactRotationRef.current === null && actualImpactTime !== null) {
    // Earth rotates once per day (86400 seconds)
    impactRotationRef.current = (actualImpactTime / 86400) * Math.PI * 2;
  }
  
  // Reset rotation ref when impact disappears (for new impacts)
  if (!showImpact && impactRotationRef.current !== null) {
    impactRotationRef.current = null;
  }
  
  // Impact position
  const impactPosition = useMemo(() => {
    if (!impactLocation) return new THREE.Vector3(0, 0, 0);
    
    return latLonAltToCartesian(
      impactLocation.latitude,
      impactLocation.longitude,
      0 // At surface
    );
  }, [impactLocation]);
  
  // Calculate normal vector at impact point for proper orientation (for future use)
  // const impactNormal = useMemo(() => {
  //   return impactPosition.clone().normalize();
  // }, [impactPosition]);
  
  useFrame(() => {
    if (!showImpact) return;
    
    const t = timeSinceImpact; // Time in seconds since impact
    const impactEnergy = impactResults?.energy_mt_tnt || 1.0; // MT TNT
    
    // Scale effects based on impact energy (logarithmic scale)
    const energyScale = Math.log10(Math.max(0.1, impactEnergy)) + 1;
    
    // === Initial Flash (0-2 seconds) ===
    if (explosionRef.current) {
      if (t < 2) {
        explosionRef.current.visible = true;
        // Bright initial flash that fades quickly
        const flashIntensity = Math.max(0, 1 - (t / 2));
        const flashScale = 20 * energyScale * (1 + t * 2);
        
        explosionRef.current.scale.setScalar(flashScale);
        (explosionRef.current.material as THREE.MeshBasicMaterial).opacity = flashIntensity * 0.9;
      } else {
        explosionRef.current.visible = false;
      }
    }
    
    // === Expanding Shockwave (0-30 seconds) ===
    if (shockwaveRef.current) {
      const shockwaveDuration = 30; // seconds
      if (t < shockwaveDuration) {
        shockwaveRef.current.visible = true;
        
        // Shockwave expands from impact point
        // Speed based on physics: roughly 300-500 m/s for atmospheric blast wave
        const shockwaveSpeed = 0.4 * energyScale; // km/s
        const shockwaveRadius = 10 + shockwaveSpeed * t * 10;
        
        // Fade out as it expands
        const shockwaveOpacity = Math.max(0, 1 - (t / shockwaveDuration));
        
        shockwaveRef.current.scale.setScalar(shockwaveRadius);
        (shockwaveRef.current.material as THREE.MeshBasicMaterial).opacity = shockwaveOpacity * 0.4;
      } else {
        shockwaveRef.current.visible = false;
      }
    }
  });
  
  if (!showImpact || !impactLocation) return null;
  
  // Use the stored Earth rotation at impact time (matches ImpactCrater)
  const effectRotation = impactRotationRef.current ?? 0;
  
  return (
    <group rotation={[0, effectRotation, 0]}>
      <group position={impactPosition}>
      {/* Initial Explosion Flash */}
      <mesh ref={explosionRef} visible={false}>
        <sphereGeometry args={[1, 32, 32]} />
        <meshBasicMaterial
          color="#ff6600"
          transparent
          opacity={0.9}
          depthWrite={false}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* Expanding Shockwave Ring */}
      <mesh 
        ref={shockwaveRef} 
        visible={false}
        rotation={[Math.PI / 2, 0, 0]} // Orient to surface
      >
        <ringGeometry args={[0.8, 1.0, 64]} />
        <meshBasicMaterial
          color="#ff9944"
          transparent
          opacity={0.4}
          depthWrite={false}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* Crater Glow removed - ImpactCrater component handles persistent crater glow */}
      {/* Particles/Debris could be added here */}
      </group>
    </group>
  );
}


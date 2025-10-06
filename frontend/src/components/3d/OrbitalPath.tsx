import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useSimulationStore } from '../../stores/simulationStore';

// Visualization scale - makes orbit visible alongside Earth
// Orbital distances are in AU (1 AU = ~150 million km)
// This scale brings them into a reasonable 3D view range
const ORBIT_SCALE = 100000; // Scale factor: 1 AU → 100,000 units in 3D space

/**
 * Visualizes the asteroid's orbital path in 3D space
 * Shows the elliptical orbit around the sun
 * Uses scaled coordinates so orbit is visible with Earth
 */
export function OrbitalPath() {
  const orbitalTrajectory = useSimulationStore((state) => state.orbitalTrajectory);
  const showOrbitalPath = useSimulationStore((state) => state.showOrbitalPath);
  const orbitalMetadata = useSimulationStore((state) => state.orbitalMetadata);
  const lineRef = useRef<THREE.Line | null>(null);
  
  // Create orbital path line object
  const orbitLine = useMemo(() => {
    if (orbitalTrajectory.length === 0) {
      return null;
    }
    
    console.log(`Rendering orbital path with ${orbitalTrajectory.length} points`);
    if (orbitalMetadata) {
      console.log(`Orbit: ${orbitalMetadata.orbital_period_years.toFixed(2)} years, collision: ${orbitalMetadata.collision_detected}`);
    }
    
    // Convert AU to scaled coordinates for visualization
    const points = orbitalTrajectory.map(point => {
      const x = point.x * ORBIT_SCALE;
      const y = point.y * ORBIT_SCALE;
      const z = point.z * ORBIT_SCALE;
      
      return new THREE.Vector3(x, z, y); // Swap Y/Z for Three.js coords
    });
    
    // Close the loop by adding first point at the end for complete ellipse
    if (points.length > 0) {
      points.push(points[0].clone());
    }
    
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    
    console.log(`✅ Created closed orbital path: ${points.length} points (${orbitalTrajectory.length} + 1 to close)`);
    
    // Bright orbital path material
    const material = new THREE.LineBasicMaterial({
      color: 0xff3300,  // Bright orange/red for visibility
      linewidth: 3,
      transparent: true,
      opacity: 0.85,
    });
    
    return new THREE.Line(geometry, material);
  }, [orbitalTrajectory, orbitalMetadata]);
  
  // Animate the orbital path (subtle glow pulse)
  useFrame(({ clock }) => {
    if (lineRef.current && lineRef.current.material instanceof THREE.LineBasicMaterial) {
      const pulse = Math.sin(clock.getElapsedTime() * 0.5) * 0.15 + 0.7;
      lineRef.current.material.opacity = pulse;
    }
  });
  
  if (!showOrbitalPath || !orbitLine || orbitalTrajectory.length === 0) {
    return null;
  }
  
  return (
    <group>
      {/* Orbital path line - complete closed ellipse */}
      <primitive ref={lineRef} object={orbitLine} />
      
      {/* Asteroid position markers at key points */}
      {orbitalTrajectory.filter((_, i) => i % 30 === 0).map((point, index) => {
        const x = point.x * ORBIT_SCALE;
        const y = point.y * ORBIT_SCALE;
        const z = point.z * ORBIT_SCALE;
        
        return (
          <mesh
            key={index}
            position={[x, z, y]}
          >
            <sphereGeometry args={[500, 8, 8]} /> {/* Scaled marker size */}
            <meshBasicMaterial
              color={0xff6600}
              transparent
              opacity={0.6}
            />
          </mesh>
        );
      })}
      
      {/* Sun representation at origin */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[5000, 32, 32]} /> {/* Scaled Sun */}
        <meshBasicMaterial
          color={0xffaa00}
          transparent
          opacity={0.9}
        />
      </mesh>
      
      {/* Orbit plane helper (subtle disc) */}
      <mesh rotation-x={Math.PI / 2} position={[0, 0, 0]}>
        <ringGeometry args={[
          0.5 * ORBIT_SCALE,  // Inner radius (0.5 AU scaled)
          1.5 * ORBIT_SCALE,  // Outer radius (1.5 AU scaled)
          64
        ]} />
        <meshBasicMaterial
          color={0x3498db}
          transparent
          opacity={0.05}
          side={THREE.DoubleSide}
        />
      </mesh>
    </group>
  );
}

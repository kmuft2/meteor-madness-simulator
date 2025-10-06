import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { Earth3D } from './Earth3D';
import { Atmosphere } from './Atmosphere';
import { Clouds } from './Clouds';
import { Starfield } from './Starfield';
import { Sun } from './Sun';
import { Asteroid } from './Asteroid';
import { TrajectoryLine } from './TrajectoryLine';
import { ImpactEffect } from './ImpactEffect';
import { ImpactCrater } from './ImpactCrater';
import { OrbitalPath } from './OrbitalPath';
import { PostProcessing } from './PostProcessing';
import * as THREE from 'three';

/**
 * Advanced 3D scene with:
 * - Multi-layer Earth rendering (day/night/specular/clouds)
 * - Realistic atmosphere with scattering
 * - HDR starfield with nebulas and twinkling
 * - Dynamic sun with lens flares
 * - Procedural asteroids with particle trails
 * - Orbital mechanics visualization (Keplerian orbits)
 * - Real trajectory data from backend simulation
 * - Post-processing effects (Bloom, DoF, Vignette)
 * - Optimized rendering with LOD
 */
export function Scene3D() {
  return (
    <Canvas
      camera={{
        position: [20000, 10000, 20000],
        fov: 50,
        near: 1,
        far: 200000,
      }}
      shadows
      dpr={[1, 2]} // Adaptive pixel ratio for performance
      gl={{
        antialias: true,
        alpha: false,
        powerPreference: 'high-performance',
        toneMapping: THREE.ACESFilmicToneMapping,
        toneMappingExposure: 1.2,
      }}
      style={{ width: '100vw', height: '100vh' }}
    >
      {/* Enhanced Lighting Setup */}
      <ambientLight intensity={0.15} color="#1a1a2e" />
      
      {/* Fill light from opposite sun */}
      <directionalLight
        position={[-30000, 0, -30000]}
        intensity={0.2}
        color="#6699ff"
      />
      
      {/* Subtle point light at Earth's core for atmosphere rim */}
      <pointLight 
        position={[0, 0, 0]} 
        intensity={0.1} 
        color="#4488ff" 
        distance={15000}
        decay={2}
      />
      
      {/* Background and Environment */}
      <color attach="background" args={['#000005']} />
      <fog attach="fog" args={['#000005', 50000, 150000]} />
      
      {/* Scene Objects - Ordered by render priority */}
      <Starfield />
      <Sun />
      <OrbitalPath />
      <Earth3D />
      <Atmosphere />
      <Clouds />
      <Asteroid />
      <TrajectoryLine />
      <ImpactEffect />
      <ImpactCrater />
      
      {/* Enhanced Camera Controls with inertia */}
      <OrbitControls
        enableDamping
        dampingFactor={0.08}
        rotateSpeed={0.5}
        zoomSpeed={0.8}
        minDistance={7000}
        maxDistance={100000}
        enablePan
        panSpeed={0.5}
        maxPolarAngle={Math.PI}
        minPolarAngle={0}
        target={[0, 0, 0]}
      />
      
      {/* Post-Processing Effects */}
      <PostProcessing />
    </Canvas>
  );
}



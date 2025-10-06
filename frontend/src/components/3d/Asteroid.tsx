import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useSimulationStore } from '../../stores/simulationStore';
import { createNoise3D } from 'simplex-noise';

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
 * Generate procedural jagged asteroid geometry
 */
function createAsteroidGeometry(baseRadius: number): THREE.BufferGeometry {
  const geometry = new THREE.IcosahedronGeometry(baseRadius, 3);
  const positions = geometry.attributes.position;
  const noise3D = createNoise3D();
  
  // Deform vertices to create rocky, irregular shape
  for (let i = 0; i < positions.count; i++) {
    const x = positions.getX(i);
    const y = positions.getY(i);
    const z = positions.getZ(i);
    
    // Multiple octaves of noise for detailed surface
    let displacement = 0;
    let amplitude = 1;
    let frequency = 0.5;
    
    for (let j = 0; j < 4; j++) {
      displacement += noise3D(
        x * frequency,
        y * frequency,
        z * frequency
      ) * amplitude;
      amplitude *= 0.5;
      frequency *= 2;
    }
    
    // Apply displacement (creates craters and bumps)
    const length = Math.sqrt(x * x + y * y + z * z);
    const scale = 1 + displacement * 0.3;
    
    positions.setXYZ(
      i,
      (x / length) * baseRadius * scale,
      (y / length) * baseRadius * scale,
      (z / length) * baseRadius * scale
    );
  }
  
  geometry.computeVertexNormals();
  return geometry;
}

/**
 * Advanced asteroid with:
 * - Procedural jagged geometry (no perfect spheres)
 * - High-res rocky textures with normal and AO maps
 * - Animated rotation and orbital motion
 * - Particle trail system for atmospheric entry
 * - Dynamic glow based on altitude/heat
 */
export function Asteroid() {
  const meshRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const trailRef = useRef<THREE.Points>(null);
  
  const { 
    time, 
    impactTime,
    asteroidParams, 
    trajectoryData, 
    impactLocation 
  } = useSimulationStore();
  
  // Generate unique asteroid geometry with ACCURATE scale
  // asteroidParams.diameter is in METERS
  // EARTH_RADIUS is in KILOMETERS (6371 km)
  // So we need to convert: diameter_meters / 1000 = diameter_km
  // Then radius = diameter / 2
  const asteroidGeometry = useMemo(() => {
    // Convert diameter from meters to km, then get radius
    const radiusKm = (asteroidParams.diameter / 1000) / 2;
    
    // For very small asteroids (< 10m), use a minimum scale for visibility
    // Otherwise they'd be invisible compared to Earth
    const scale = Math.max(0.01, radiusKm);
    
    return createAsteroidGeometry(scale);
  }, [asteroidParams.diameter]);
  
  // Create high-quality rocky texture with normal map details
  const [asteroidTexture, normalMap, aoMap] = useMemo(() => {
    // Base color texture
    const colorCanvas = document.createElement('canvas');
    colorCanvas.width = 1024;
    colorCanvas.height = 1024;
    const colorCtx = colorCanvas.getContext('2d')!;
    
    const noise3D = createNoise3D();
    
    // Generate rocky surface color
    for (let y = 0; y < 1024; y++) {
      for (let x = 0; x < 1024; x++) {
        let value = 0;
        let amplitude = 1;
        let frequency = 0.005;
        
        for (let i = 0; i < 5; i++) {
          value += noise3D(x * frequency, y * frequency, 0) * amplitude;
          amplitude *= 0.5;
          frequency *= 2;
        }
        
        value = (value + 1) / 2;
        
        // Rocky color palette (grays and browns)
        const baseColor = 40 + value * 60;
        const r = baseColor + Math.random() * 20;
        const g = baseColor + Math.random() * 15;
        const b = baseColor * 0.8 + Math.random() * 10;
        
        colorCtx.fillStyle = `rgb(${r}, ${g}, ${b})`;
        colorCtx.fillRect(x, y, 1, 1);
      }
    }
    
    // Add craters
    for (let i = 0; i < 50; i++) {
      const x = Math.random() * 1024;
      const y = Math.random() * 1024;
      const size = Math.random() * 80 + 20;
      
      const gradient = colorCtx.createRadialGradient(x, y, size * 0.3, x, y, size);
      gradient.addColorStop(0, 'rgba(20, 20, 20, 0.6)');
      gradient.addColorStop(1, 'rgba(30, 30, 30, 0)');
      
      colorCtx.fillStyle = gradient;
      colorCtx.beginPath();
      colorCtx.arc(x, y, size, 0, Math.PI * 2);
      colorCtx.fill();
    }
    
    const colorTexture = new THREE.CanvasTexture(colorCanvas);
    
    // Normal map (for lighting detail)
    const normalCanvas = document.createElement('canvas');
    normalCanvas.width = 1024;
    normalCanvas.height = 1024;
    const normalCtx = normalCanvas.getContext('2d')!;
    
    for (let y = 0; y < 1024; y++) {
      for (let x = 0; x < 1024; x++) {
        const nx = noise3D(x * 0.01, y * 0.01, 0);
        const ny = noise3D(x * 0.01, y * 0.01, 100);
        
        const r = ((nx + 1) / 2) * 255;
        const g = ((ny + 1) / 2) * 255;
        const b = 200; // Z component (pointing out)
        
        normalCtx.fillStyle = `rgb(${r}, ${g}, ${b})`;
        normalCtx.fillRect(x, y, 1, 1);
      }
    }
    
    const normalTexture = new THREE.CanvasTexture(normalCanvas);
    
    // AO map (ambient occlusion - adds depth to crevices)
    const aoCanvas = document.createElement('canvas');
    aoCanvas.width = 512;
    aoCanvas.height = 512;
    const aoCtx = aoCanvas.getContext('2d')!;
    
    for (let y = 0; y < 512; y++) {
      for (let x = 0; x < 512; x++) {
        const ao = (noise3D(x * 0.02, y * 0.02, 50) + 1) / 2;
        const brightness = 100 + ao * 155;
        
        aoCtx.fillStyle = `rgb(${brightness}, ${brightness}, ${brightness})`;
        aoCtx.fillRect(x, y, 1, 1);
      }
    }
    
    const aoTexture = new THREE.CanvasTexture(aoCanvas);
    
    return [colorTexture, normalTexture, aoTexture];
  }, []);
  
  // Particle trail system
  const trailParticles = useMemo(() => {
    const particleCount = 200;
    const positions = new Float32Array(particleCount * 3);
    const velocities = new Float32Array(particleCount * 3);
    const lifetimes = new Float32Array(particleCount);
    
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = 0;
      positions[i * 3 + 1] = 0;
      positions[i * 3 + 2] = 0;
      
      velocities[i * 3] = (Math.random() - 0.5) * 50;
      velocities[i * 3 + 1] = (Math.random() - 0.5) * 50;
      velocities[i * 3 + 2] = (Math.random() - 0.5) * 50;
      
      lifetimes[i] = Math.random();
    }
    
    return { positions, velocities, lifetimes };
  }, []);
  
  // Calculate current position and animate asteroid + particles
  useFrame((_state, delta) => {
    if (!meshRef.current || !glowRef.current || !trailRef.current || !impactLocation) return;
    
    if (trajectoryData.length > 0) {
      // Use real trajectory data from backend physics
      const progress = Math.min(1.0, Math.max(0, time / impactTime));
      const index = Math.floor(progress * (trajectoryData.length - 1));
      const point = trajectoryData[Math.min(index, trajectoryData.length - 1)];
      
      const asteroidRadiusKm = (asteroidParams.diameter / 2) / 1000;
      const hasImpacted = point.altitude_km <= asteroidRadiusKm;
      
      if (hasImpacted) {
        // Stop rotation on impact
        meshRef.current.visible = false;
        glowRef.current.visible = false;
        trailRef.current.visible = false;
        // Don't update rotation or position after impact
        return;
      }
      
      meshRef.current.visible = true;
      glowRef.current.visible = true;
      
      // Calculate position along trajectory using horizontal distance and azimuth
      const azimuth = (impactLocation.azimuth_deg || 90) * (Math.PI / 180);
      const horizontalDist = point.horizontal_distance_km || 0;
      
      // Project backward from impact point along approach azimuth
      // Convert horizontal distance to angular displacement
      const earthCircumference = 2 * Math.PI * EARTH_RADIUS;
      const latOffset = -(horizontalDist / earthCircumference) * 360 * Math.cos(azimuth);
      const lonOffset = -(horizontalDist / earthCircumference) * 360 * Math.sin(azimuth) / 
                        Math.cos(impactLocation.latitude * Math.PI / 180);
      
      const currentLat = impactLocation.latitude + latOffset;
      const currentLon = impactLocation.longitude + lonOffset;
      
      const position = latLonAltToCartesian(
        currentLat,        // Moves horizontally based on trajectory!
        currentLon,        // Moves horizontally based on trajectory!
        point.altitude_km  // AND descends vertically
      );
      
      meshRef.current.position.copy(position);
      glowRef.current.position.copy(position);
      
      // Scale glow and emissive based on atmospheric heating
      const maxAltitude = trajectoryData[0]?.altitude_km || 100;
      const altitudeFactor = 1 - point.altitude_km / maxAltitude;
      const glowIntensity = 1 + (3 * altitudeFactor);
      glowRef.current.scale.setScalar(glowIntensity);
      
      // Update emissive intensity (hotter as it descends)
      if (meshRef.current.material instanceof THREE.MeshStandardMaterial) {
        meshRef.current.material.emissiveIntensity = 0.2 + altitudeFactor * 0.8;
      }
      
      // Show particle trail when entering atmosphere (below 100km)
      if (point.altitude_km < 100) {
        trailRef.current.visible = true;
        
        // Update particle trail
        const geometry = trailRef.current.geometry;
        const positions = geometry.attributes.position.array as Float32Array;
        
        for (let i = 0; i < trailParticles.positions.length / 3; i++) {
          const i3 = i * 3;
          
          // Age particles
          trailParticles.lifetimes[i] -= delta * 2;
          
          // Reset dead particles at asteroid position
          if (trailParticles.lifetimes[i] <= 0) {
            positions[i3] = position.x + (Math.random() - 0.5) * 10;
            positions[i3 + 1] = position.y + (Math.random() - 0.5) * 10;
            positions[i3 + 2] = position.z + (Math.random() - 0.5) * 10;
            
            trailParticles.velocities[i3] = (Math.random() - 0.5) * 100;
            trailParticles.velocities[i3 + 1] = (Math.random() - 0.5) * 100;
            trailParticles.velocities[i3 + 2] = (Math.random() - 0.5) * 100;
            
            trailParticles.lifetimes[i] = 1;
          } else {
            // Update particle positions
            positions[i3] += trailParticles.velocities[i3] * delta;
            positions[i3 + 1] += trailParticles.velocities[i3 + 1] * delta;
            positions[i3 + 2] += trailParticles.velocities[i3 + 2] * delta;
          }
        }
        
        geometry.attributes.position.needsUpdate = true;
      } else {
        trailRef.current.visible = false;
      }
      
      // Chaotic rotation (tumbling through space) - only before impact
      meshRef.current.rotation.x += 0.015;
      meshRef.current.rotation.y += 0.023;
      meshRef.current.rotation.z += 0.007;
    } else {
      // Fallback animation
      const progress = Math.min(1.0, Math.max(0, time / impactTime));
      const distance = 50000 * (1 - progress);
      const altitude = Math.max(0, distance - EARTH_RADIUS);
      
      // Check if impacted in fallback mode too
      const asteroidRadiusKm = (asteroidParams.diameter / 2) / 1000;
      const fallbackImpacted = altitude / 1000 <= asteroidRadiusKm;
      
      if (fallbackImpacted) {
        meshRef.current.visible = false;
        glowRef.current.visible = false;
        return;
      }
      
      const position = latLonAltToCartesian(
        impactLocation.latitude,
        impactLocation.longitude,
        altitude
      );
      
      meshRef.current.position.copy(position);
      glowRef.current.position.copy(position);
      
      // Only rotate before impact
      meshRef.current.rotation.x += 0.015;
      meshRef.current.rotation.y += 0.023;
      meshRef.current.rotation.z += 0.007;
    }
  });
  
  // Calculate accurate scale for glow/effects (same as geometry calculation)
  const radiusKm = (asteroidParams.diameter / 1000) / 2;
  const scale = Math.max(0.01, radiusKm);
  
  return (
    <group>
      {/* Particle trail (plasma/fire) */}
      <points ref={trailRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={trailParticles.positions.length / 3}
            array={trailParticles.positions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={30}
          color="#ff6600"
          transparent
          opacity={0.6}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>
      
      {/* Atmospheric heating glow */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[scale * 1.8, 16, 16]} />
        <meshBasicMaterial
          color="#ff4400"
          transparent
          opacity={0.4}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>
      
      {/* Main asteroid with procedural geometry */}
      <mesh ref={meshRef} castShadow geometry={asteroidGeometry}>
        <meshStandardMaterial
          map={asteroidTexture}
          normalMap={normalMap}
          aoMap={aoMap}
          aoMapIntensity={1.5}
          roughness={0.95}
          metalness={0.05}
          emissive="#ff3300"
          emissiveIntensity={0.2}
        />
      </mesh>
    </group>
  );
}

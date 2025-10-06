import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { createNoise2D } from 'simplex-noise';
import { useSimulationStore } from '../../stores/simulationStore';

const EARTH_RADIUS = 6371;
const CLOUD_RADIUS = EARTH_RADIUS * 1.008;

/**
 * Advanced cloud layer with:
 * - Procedural noise-based cloud texture
 * - Transparent rendering with proper blending
 * - Animated rotation slightly faster than Earth (for visual effect)
 * - Synced to simulation time (pauses when simulation pauses)
 * - Realistic opacity and coverage patterns
 */
export function Clouds() {
  const cloudsRef = useRef<THREE.Mesh>(null);
  const { time } = useSimulationStore();
  
  // Generate procedural cloud texture using simplex noise
  const cloudTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 2048;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d')!;
    
    const noise2D = createNoise2D();
    const imageData = ctx.createImageData(canvas.width, canvas.height);
    
    for (let y = 0; y < canvas.height; y++) {
      for (let x = 0; x < canvas.width; x++) {
        const nx = x / canvas.width;
        const ny = y / canvas.height;
        
        // Layer multiple octaves of noise for realistic clouds
        let value = 0;
        let amplitude = 1;
        let frequency = 2;
        let maxValue = 0;
        
        // 5 octaves of noise
        for (let i = 0; i < 5; i++) {
          value += noise2D(nx * frequency, ny * frequency) * amplitude;
          maxValue += amplitude;
          amplitude *= 0.5;
          frequency *= 2;
        }
        
        // Normalize to 0-1 range
        value = (value / maxValue + 1) / 2;
        
        // Apply threshold and curve to create cloud-like patterns
        value = Math.pow(Math.max(0, value - 0.4), 2) * 4;
        value = Math.min(1, value);
        
        // Reduce clouds near poles (they're less common there)
        const latitudeFactor = 1 - Math.pow(Math.abs(ny - 0.5) * 2, 2) * 0.3;
        value *= latitudeFactor;
        
        const idx = (y * canvas.width + x) * 4;
        imageData.data[idx] = 255;     // R
        imageData.data[idx + 1] = 255; // G
        imageData.data[idx + 2] = 255; // B
        imageData.data[idx + 3] = value * 255; // Alpha
      }
    }
    
    ctx.putImageData(imageData, 0, 0);
    
    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    return texture;
  }, []);
  
  // Rotate clouds slightly faster than Earth for dynamic effect
  // Clouds rotate ~10% faster than Earth (86400s per rotation -> ~78000s)
  // Synced to simulation time so it pauses when simulation pauses
  useFrame(() => {
    if (cloudsRef.current) {
      // Clouds rotate slightly faster than Earth (1.1x speed)
      cloudsRef.current.rotation.y = (time / 78545) * Math.PI * 2; // ~21.8 hour rotation
    }
  });
  
  return (
    <mesh ref={cloudsRef}>
      <sphereGeometry args={[CLOUD_RADIUS, 128, 128]} />
      <meshPhongMaterial
        map={cloudTexture}
        transparent
        opacity={0.35}
        depthWrite={false}
        side={THREE.DoubleSide}
        blending={THREE.NormalBlending}
      />
    </mesh>
  );
}

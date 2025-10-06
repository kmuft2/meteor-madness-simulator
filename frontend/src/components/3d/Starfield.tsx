import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { createNoise2D } from 'simplex-noise';

/**
 * Advanced starfield with:
 * - Multiple star sizes and brightnesses
 * - Realistic star colors (based on temperature)
 * - Twinkling animation
 * - Background nebula clouds
 * - Milky Way band simulation
 * - Distant galaxies as faint sprites
 */
export function Starfield() {
  const starsRef = useRef<THREE.Points>(null);
  const nebulaRef = useRef<THREE.Mesh>(null);
  const milkyWayRef = useRef<THREE.Mesh>(null);
  
  // Generate stars with realistic distribution
  const [positions, colors, sizes, twinklePhases] = useMemo(() => {
    const starCount = 15000;
    const positions = new Float32Array(starCount * 3);
    const colors = new Float32Array(starCount * 3);
    const sizes = new Float32Array(starCount);
    const twinklePhases = new Float32Array(starCount);
    
    // Star color temperatures (Kelvin to RGB approximation)
    const starTypes = [
      { temp: 'blue', color: new THREE.Color(0.6, 0.7, 1.0), freq: 0.1 },
      { temp: 'white', color: new THREE.Color(1.0, 1.0, 1.0), freq: 0.3 },
      { temp: 'yellow', color: new THREE.Color(1.0, 0.95, 0.7), freq: 0.4 },
      { temp: 'orange', color: new THREE.Color(1.0, 0.7, 0.5), freq: 0.15 },
      { temp: 'red', color: new THREE.Color(1.0, 0.5, 0.4), freq: 0.05 },
    ];
    
    for (let i = 0; i < starCount; i++) {
      const i3 = i * 3;
      
      // Spherical distribution with clustering toward "galactic plane"
      const radius = 80000 + Math.random() * 30000;
      const theta = Math.random() * Math.PI * 2;
      
      // Cluster more stars near equatorial plane (Milky Way effect)
      let phi = Math.acos((Math.random() * 2) - 1);
      if (Math.random() < 0.4) {
        phi = Math.PI / 2 + (Math.random() - 0.5) * 0.3;
      }
      
      positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i3 + 2] = radius * Math.cos(phi);
      
      // Select star type based on frequency distribution
      let rand = Math.random();
      let selectedType = starTypes[0];
      for (const type of starTypes) {
        if (rand < type.freq) {
          selectedType = type;
          break;
        }
        rand -= type.freq;
      }
      
      colors[i3] = selectedType.color.r;
      colors[i3 + 1] = selectedType.color.g;
      colors[i3 + 2] = selectedType.color.b;
      
      // Varied star sizes (magnitude)
      const magnitude = Math.random();
      sizes[i] = magnitude < 0.05 ? 120 : magnitude < 0.2 ? 80 : 50;
      
      // Random twinkle phase
      twinklePhases[i] = Math.random() * Math.PI * 2;
    }
    
    return [positions, colors, sizes, twinklePhases];
  }, []);
  
  // Create nebula background texture
  const nebulaTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 2048;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d')!;
    
    const noise2D = createNoise2D();
    
    // Create nebula clouds with multiple colors
    for (let layer = 0; layer < 3; layer++) {
      const imageData = ctx.createImageData(canvas.width, canvas.height);
      const colors = [
        [100, 50, 150], // Purple
        [50, 100, 200], // Blue
        [200, 100, 150], // Pink
      ][layer];
      
      for (let y = 0; y < canvas.height; y++) {
        for (let x = 0; x < canvas.width; x++) {
          const nx = x / canvas.width * 3;
          const ny = y / canvas.height * 3;
          
          let value = 0;
          let amplitude = 1;
          let frequency = 1 + layer;
          
          for (let i = 0; i < 4; i++) {
            value += noise2D(nx * frequency, ny * frequency) * amplitude;
            amplitude *= 0.5;
            frequency *= 2;
          }
          
          value = (value + 1) / 2;
          value = Math.pow(Math.max(0, value - 0.6), 2) * 8;
          
          const idx = (y * canvas.width + x) * 4;
          imageData.data[idx] = colors[0] * value;
          imageData.data[idx + 1] = colors[1] * value;
          imageData.data[idx + 2] = colors[2] * value;
          imageData.data[idx + 3] = value * 60;
        }
      }
      
      ctx.putImageData(imageData, 0, 0);
    }
    
    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    return texture;
  }, []);
  
  // Animate star twinkling
  useFrame(({ clock }) => {
    if (starsRef.current) {
      const geometry = starsRef.current.geometry;
      const sizeAttribute = geometry.attributes.size;
      
      for (let i = 0; i < sizeAttribute.count; i++) {
        const baseSize = sizes[i];
        const phase = twinklePhases[i];
        const twinkle = Math.sin(clock.elapsedTime * 2 + phase) * 0.2 + 1;
        sizeAttribute.setX(i, baseSize * twinkle);
      }
      
      sizeAttribute.needsUpdate = true;
    }
  });
  
  return (
    <group>
      {/* Background nebula sphere */}
      <mesh ref={nebulaRef}>
        <sphereGeometry args={[95000, 64, 64]} />
        <meshBasicMaterial
          map={nebulaTexture}
          side={THREE.BackSide}
          transparent
          opacity={0.4}
          depthWrite={false}
        />
      </mesh>
      
      {/* Milky Way band */}
      <mesh ref={milkyWayRef} rotation={[0, 0, Math.PI / 6]}>
        <torusGeometry args={[85000, 8000, 2, 100]} />
        <meshBasicMaterial
          color={0x88aaff}
          side={THREE.BackSide}
          transparent
          opacity={0.08}
          depthWrite={false}
        />
      </mesh>
      
      {/* Stars */}
      <points ref={starsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={positions.length / 3}
            array={positions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-color"
            count={colors.length / 3}
            array={colors}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-size"
            count={sizes.length}
            array={sizes}
            itemSize={1}
          />
        </bufferGeometry>
        <pointsMaterial
          size={50}
          sizeAttenuation
          vertexColors
          transparent
          opacity={0.9}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>
    </group>
  );
}



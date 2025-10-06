import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

/**
 * Sun component with:
 * - Bright glowing sphere
 * - Lens flare sprite system
 * - Dynamic directional light
 * - Corona/atmosphere effect
 * - Pulsing animation
 */
export function Sun() {
  const sunRef = useRef<THREE.Mesh>(null);
  const coronaRef = useRef<THREE.Mesh>(null);
  const lensFlareRef = useRef<THREE.Group>(null);
  
  // Create sun surface texture with noise
  const sunTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 512;
    const ctx = canvas.getContext('2d')!;
    
    // Radial gradient for sun glow
    const gradient = ctx.createRadialGradient(256, 256, 0, 256, 256, 256);
    gradient.addColorStop(0, '#fff5e6');
    gradient.addColorStop(0.4, '#ffd966');
    gradient.addColorStop(0.8, '#ff9933');
    gradient.addColorStop(1, '#ff6600');
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 512, 512);
    
    // Add solar flare details
    for (let i = 0; i < 100; i++) {
      const angle = Math.random() * Math.PI * 2;
      const dist = Math.random() * 256;
      const x = 256 + Math.cos(angle) * dist;
      const y = 256 + Math.sin(angle) * dist;
      const size = Math.random() * 20 + 5;
      
      const flareGradient = ctx.createRadialGradient(x, y, 0, x, y, size);
      flareGradient.addColorStop(0, 'rgba(255, 255, 200, 0.3)');
      flareGradient.addColorStop(1, 'rgba(255, 200, 0, 0)');
      
      ctx.fillStyle = flareGradient;
      ctx.beginPath();
      ctx.arc(x, y, size, 0, Math.PI * 2);
      ctx.fill();
    }
    
    return new THREE.CanvasTexture(canvas);
  }, []);
  
  // Create lens flare elements
  const lensFlareElements = useMemo(() => {
    const elements: { position: THREE.Vector3; size: number; color: THREE.Color; opacity: number }[] = [];
    
    // Main bright spot
    elements.push({
      position: new THREE.Vector3(50000, 0, 50000),
      size: 2000,
      color: new THREE.Color(1, 1, 0.9),
      opacity: 0.8,
    });
    
    // Hexagonal artifacts (lens internal reflections)
    for (let i = 1; i <= 5; i++) {
      const t = i / 6;
      elements.push({
        position: new THREE.Vector3(50000 * (1 - t * 0.5), 0, 50000 * (1 - t * 0.5)),
        size: 500 + i * 200,
        color: new THREE.Color().setHSL(0.1 + i * 0.05, 0.8, 0.7),
        opacity: 0.3 - i * 0.04,
      });
    }
    
    return elements;
  }, []);
  
  // Animate sun pulsing and rotation
  useFrame(({ clock }) => {
    if (sunRef.current) {
      const pulse = Math.sin(clock.elapsedTime * 0.5) * 0.03 + 1;
      sunRef.current.scale.setScalar(pulse);
      sunRef.current.rotation.y = clock.elapsedTime * 0.01;
    }
    
    if (coronaRef.current) {
      coronaRef.current.rotation.z = clock.elapsedTime * 0.02;
    }
  });
  
  return (
    <group>
      {/* Main sun sphere */}
      <mesh ref={sunRef} position={[50000, 0, 50000]}>
        <sphereGeometry args={[1392, 64, 64]} />
        <meshStandardMaterial
          map={sunTexture}
          emissive={new THREE.Color(1, 0.8, 0.4)}
          emissiveIntensity={2}
          toneMapped={false}
        />
      </mesh>
      
      {/* Sun corona/atmosphere */}
      <mesh ref={coronaRef} position={[50000, 0, 50000]}>
        <sphereGeometry args={[1600, 64, 64]} />
        <shaderMaterial
          uniforms={{
            glowColor: { value: new THREE.Color(1, 0.7, 0.3) },
          }}
          vertexShader={`
            varying vec3 vNormal;
            varying vec3 vPosition;
            
            void main() {
              vNormal = normalize(normalMatrix * normal);
              vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
              gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
          `}
          fragmentShader={`
            uniform vec3 glowColor;
            varying vec3 vNormal;
            varying vec3 vPosition;
            
            void main() {
              vec3 viewDir = normalize(-vPosition);
              float intensity = pow(1.0 - abs(dot(viewDir, vNormal)), 4.0);
              gl_FragColor = vec4(glowColor, intensity * 0.7);
            }
          `}
          transparent
          blending={THREE.AdditiveBlending}
          side={THREE.BackSide}
          depthWrite={false}
        />
      </mesh>
      
      {/* Lens flare sprites */}
      <group ref={lensFlareRef}>
        {lensFlareElements.map((element, i) => (
          <sprite key={i} position={element.position} scale={[element.size, element.size, 1]}>
            <spriteMaterial
              color={element.color}
              transparent
              opacity={element.opacity}
              blending={THREE.AdditiveBlending}
              depthWrite={false}
            />
          </sprite>
        ))}
      </group>
      
      {/* Directional light from sun */}
      <directionalLight
        position={[50000, 0, 50000]}
        intensity={2}
        color="#fff5e6"
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-far={150000}
        shadow-camera-left={-20000}
        shadow-camera-right={20000}
        shadow-camera-top={20000}
        shadow-camera-bottom={-20000}
      />
    </group>
  );
}

import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const EARTH_RADIUS = 6371;

/**
 * Advanced atmospheric scattering shader with:
 * - Rayleigh scattering simulation
 * - View-angle dependent glow
 * - Sun direction awareness
 * - Realistic color gradient (blue at edge, fading to transparent)
 * - Both outer glow and inner rim lighting
 */
export function Atmosphere() {
  const atmosphereRef = useRef<THREE.Mesh>(null);
  const innerAtmosphereRef = useRef<THREE.Mesh>(null);
  
  // Outer atmosphere shader (space-facing glow)
  const outerAtmosphereShader = useMemo(() => ({
    uniforms: {
      sunDirection: { value: new THREE.Vector3(1, 0, 0).normalize() },
      glowColor: { value: new THREE.Color(0.3, 0.6, 1.0) },
    },
    vertexShader: `
      varying vec3 vNormal;
      varying vec3 vPosition;
      
      void main() {
        vNormal = normalize(normalMatrix * normal);
        vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform vec3 sunDirection;
      uniform vec3 glowColor;
      
      varying vec3 vNormal;
      varying vec3 vPosition;
      
      void main() {
        vec3 viewDir = normalize(-vPosition);
        vec3 normal = normalize(vNormal);
        
        // Fresnel effect - stronger glow at edges
        float fresnel = pow(1.0 - abs(dot(viewDir, normal)), 3.5);
        
        // Sun influence on atmosphere color
        vec3 sunDir = normalize(mat3(viewMatrix) * sunDirection);
        float sunAlignment = max(0.0, dot(normal, sunDir));
        
        // Atmosphere color shifts from blue to orange near sun
        vec3 atmosphereColor = mix(
          glowColor,
          vec3(1.0, 0.7, 0.4),
          sunAlignment * 0.3
        );
        
        // Combine effects
        float intensity = fresnel * (0.7 + sunAlignment * 0.3);
        
        gl_FragColor = vec4(atmosphereColor, intensity * 0.6);
      }
    `,
  }), []);
  
  // Inner atmosphere shader (surface-facing rim light)
  const innerAtmosphereShader = useMemo(() => ({
    uniforms: {
      sunDirection: { value: new THREE.Vector3(1, 0, 0).normalize() },
    },
    vertexShader: `
      varying vec3 vNormal;
      varying vec3 vPosition;
      
      void main() {
        vNormal = normalize(normalMatrix * normal);
        vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform vec3 sunDirection;
      
      varying vec3 vNormal;
      varying vec3 vPosition;
      
      void main() {
        vec3 viewDir = normalize(-vPosition);
        vec3 normal = normalize(vNormal);
        
        // Inner rim lighting
        float rim = 1.0 - abs(dot(viewDir, normal));
        rim = pow(rim, 2.0);
        
        // Sun direction influence
        vec3 sunDir = normalize(mat3(viewMatrix) * sunDirection);
        float sunDot = max(0.0, dot(normal, sunDir));
        
        // Create atmospheric scattering effect
        vec3 scatterColor = vec3(0.4, 0.7, 1.0);
        float intensity = rim * (0.3 + sunDot * 0.2);
        
        gl_FragColor = vec4(scatterColor, intensity);
      }
    `,
  }), []);
  
  // Update sun direction in shaders
  useFrame(({ clock }) => {
    const sunDir = new THREE.Vector3(
      Math.cos(clock.getElapsedTime() * 0.01) * 50000,
      0,
      Math.sin(clock.getElapsedTime() * 0.01) * 50000
    ).normalize();
    
    if (atmosphereRef.current?.material instanceof THREE.ShaderMaterial) {
      atmosphereRef.current.material.uniforms.sunDirection.value.copy(sunDir);
    }
    if (innerAtmosphereRef.current?.material instanceof THREE.ShaderMaterial) {
      innerAtmosphereRef.current.material.uniforms.sunDirection.value.copy(sunDir);
    }
  });
  
  return (
    <group>
      {/* Outer atmosphere glow (viewed from space) */}
      <mesh ref={atmosphereRef}>
        <sphereGeometry args={[EARTH_RADIUS * 1.12, 128, 128]} />
        <shaderMaterial
          args={[outerAtmosphereShader]}
          blending={THREE.AdditiveBlending}
          side={THREE.BackSide}
          transparent
          depthWrite={false}
        />
      </mesh>
      
      {/* Inner atmosphere rim (surface lighting) */}
      <mesh ref={innerAtmosphereRef}>
        <sphereGeometry args={[EARTH_RADIUS * 1.025, 128, 128]} />
        <shaderMaterial
          args={[innerAtmosphereShader]}
          blending={THREE.AdditiveBlending}
          side={THREE.FrontSide}
          transparent
          depthWrite={false}
        />
      </mesh>
    </group>
  );
}



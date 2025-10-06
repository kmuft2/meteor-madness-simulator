import { useRef, useMemo } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import { TextureLoader } from 'three';
import * as THREE from 'three';
import { useSimulationStore } from '../../stores/simulationStore';

const EARTH_RADIUS = 6371;

/**
 * Advanced multi-layer Earth rendering with:
 * - Day texture (diffuse)
 * - Normal/bump map for terrain relief
 * - Specular map for water reflection
 * - Ambient lighting for night side visibility
 * - Physically-based shading with atmospheric effects
 */
export function Earth3D() {
  const earthRef = useRef<THREE.Mesh>(null);
  const { time } = useSimulationStore();
  
  // Load high-quality Earth textures
  const [colorMap, bumpMap, specularMap] = useLoader(TextureLoader, [
    'https://unpkg.com/three-globe@2.27.2/example/img/earth-blue-marble.jpg',
    'https://unpkg.com/three-globe@2.27.2/example/img/earth-topology.png',
    'https://unpkg.com/three-globe@2.27.2/example/img/earth-water.png',
  ]);
  
  // Configure textures for sharper appearance at distance
  useMemo(() => {
    [colorMap, bumpMap, specularMap].forEach(texture => {
      texture.anisotropy = 16; // Max anisotropic filtering for sharpness
      texture.minFilter = THREE.LinearMipmapLinearFilter; // Smooth minification
      texture.magFilter = THREE.LinearFilter; // Smooth magnification
      texture.generateMipmaps = true;
    });
  }, [colorMap, bumpMap, specularMap]);
  
  
  // Custom shader for day/night blending
  const earthShader = useMemo(() => {
    return {
      uniforms: {
        dayTexture: { value: colorMap },
        specularMap: { value: specularMap },
        bumpMap: { value: bumpMap },
        sunDirection: { value: new THREE.Vector3(1, 0, 0).normalize() },
        bumpScale: { value: 100.0 },
      },
      vertexShader: `
        varying vec2 vUv;
        varying vec3 vNormal;
        varying vec3 vPosition;
        varying vec3 vSunDirection;
        
        uniform vec3 sunDirection;
        uniform sampler2D bumpMap;
        uniform float bumpScale;
        
        void main() {
          vUv = uv;
          vNormal = normalize(normalMatrix * normal);
          vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
          vSunDirection = normalize(mat3(viewMatrix) * sunDirection);
          
          // Apply bump mapping to vertex position
          vec3 objectNormal = normalize(normal);
          float height = texture2D(bumpMap, uv).r;
          vec3 newPosition = position + objectNormal * height * bumpScale * 0.01;
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
        }
      `,
      fragmentShader: `
        uniform sampler2D dayTexture;
        uniform sampler2D specularMap;
        uniform vec3 sunDirection;
        
        varying vec2 vUv;
        varying vec3 vNormal;
        varying vec3 vPosition;
        varying vec3 vSunDirection;
        
        void main() {
          // Sample textures
          vec4 dayColor = texture2D(dayTexture, vUv);
          vec4 specular = texture2D(specularMap, vUv);
          
          // Calculate lighting
          vec3 normal = normalize(vNormal);
          float sunDot = dot(normal, vSunDirection);
          
          // Smooth day/night transition
          float lightIntensity = smoothstep(-0.2, 0.2, sunDot);
          
          // Add ambient light to prevent complete darkness on night side
          vec3 ambientLight = dayColor.rgb * 0.2; // Ambient illumination
          
          // Apply lighting with ambient on dark side
          vec3 baseColor = mix(ambientLight, dayColor.rgb, lightIntensity);
          
          // Add specular highlights for water (ocean reflections)
          vec3 viewDir = normalize(-vPosition);
          vec3 halfDir = normalize(vSunDirection + viewDir);
          float specAngle = max(dot(halfDir, normal), 0.0);
          float specularIntensity = pow(specAngle, 32.0) * specular.r * lightIntensity;
          
          // Add atmospheric scattering at edges
          float fresnel = pow(1.0 - max(dot(viewDir, normal), 0.0), 3.0);
          vec3 atmosphereColor = vec3(0.3, 0.6, 1.0) * fresnel * 0.3;
          
          // Combine all lighting
          vec3 finalColor = baseColor + specularIntensity * vec3(1.0, 1.0, 0.9) + atmosphereColor;
          
          gl_FragColor = vec4(finalColor, 1.0);
        }
      `,
    };
  }, [colorMap, specularMap, bumpMap]);
  
  // Rotate Earth based on simulation time (NOT clock time)
  // Earth rotates once every 24 hours = 86400 seconds
  // This ensures Earth rotation is synced to simulation and pauses when simulation pauses
  useFrame(() => {
    if (earthRef.current) {
      // Accurate rotation based on simulation time
      // time is in seconds, one rotation per day
      earthRef.current.rotation.y = (time / 86400) * Math.PI * 2;
      
      // Sun direction - keep sun relatively fixed in space
      // Sun at approximately (1, 0, 0) direction (shining from +X axis)
      const sunDir = new THREE.Vector3(1, 0, 0).normalize();
      
      if (earthRef.current.material instanceof THREE.ShaderMaterial) {
        earthRef.current.material.uniforms.sunDirection.value.copy(sunDir);
      }
    }
  });
  
  return (
    <mesh ref={earthRef} receiveShadow castShadow>
      <sphereGeometry args={[EARTH_RADIUS, 256, 256]} />
      <shaderMaterial
        attach="material"
        args={[earthShader]}
        side={THREE.FrontSide}
      />
    </mesh>
  );
}



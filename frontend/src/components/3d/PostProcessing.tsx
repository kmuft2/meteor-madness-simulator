import { EffectComposer, Bloom, DepthOfField, Vignette, ChromaticAberration } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';
import * as THREE from 'three';

/**
 * Advanced post-processing effects:
 * - Bloom: Makes bright objects glow (sun, asteroids, stars)
 * - Depth of Field: Cinematic focus effect
 * - Vignette: Darkens edges for dramatic framing
 * - Chromatic Aberration: Subtle color fringing for realism
 */
export function PostProcessing() {
  return (
    <EffectComposer multisampling={8}>
      {/* Bloom effect for glowing objects */}
      <Bloom
        intensity={0.8}
        luminanceThreshold={0.3}
        luminanceSmoothing={0.9}
        height={512}
        mipmapBlur
      />
      
      {/* Depth of field for cinematic feel - reduced for less blur */}
      <DepthOfField
        focusDistance={0.01}
        focalLength={0.02}
        bokehScale={1.5}
        height={480}
      />
      
      {/* Vignette darkens edges */}
      <Vignette
        offset={0.3}
        darkness={0.5}
        eskil={false}
        blendFunction={BlendFunction.NORMAL}
      />
      
      {/* Subtle chromatic aberration */}
      <ChromaticAberration
        offset={new THREE.Vector2(0.001, 0.001)}
        radialModulation={false}
        modulationOffset={0}
      />
    </EffectComposer>
  );
}

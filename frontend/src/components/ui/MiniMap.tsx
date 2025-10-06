import { Paper, Box, Typography, IconButton, Collapse } from '@mui/material';
import { ExpandLess, ExpandMore } from '@mui/icons-material';
import { useSimulationStore } from '../../stores/simulationStore';
import { useEffect, useRef, useState, useCallback } from 'react';
import { useDraggable } from '../../hooks/useDraggable';

export function MiniMap() {
  const [expanded, setExpanded] = useState(true);
  const { position, handleMouseDown, isDragging } = useDraggable(window.innerWidth - 232, window.innerHeight - 210);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { impactLocation, impactResults, placeAsteroidAt } = useSimulationStore();
  const [placementError, setPlacementError] = useState<string | null>(null);
  const [mapImage, setMapImage] = useState<HTMLImageElement | null>(null);
  const [animationTick, setAnimationTick] = useState(0);

  useEffect(() => {
    let mounted = true;
    const img = new Image();
    img.src = '/world_map_simple.png';
    img.onload = () => {
      if (mounted) {
        setMapImage(img);
      }
    };
    img.onerror = () => {
      if (mounted) {
        console.warn('Failed to load mini-map texture from /world_map_simple.png');
        setMapImage(null);
      }
    };

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width, height } = canvas;

    ctx.clearRect(0, 0, width, height);

    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, '#041830');
    gradient.addColorStop(1, '#020912');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    if (mapImage) {
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(mapImage, 0, 0, mapImage.width, mapImage.height, 0, 0, width, height);
    } else {
      ctx.fillStyle = '#11263c';
      ctx.fillRect(0, 0, width, height);
    }

    ctx.strokeStyle = 'rgba(52, 152, 219, 0.25)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 3]);

    for (let lat = -60; lat <= 60; lat += 15) {
      const y = ((90 - lat) / 180) * height;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    for (let lon = -180; lon <= 180; lon += 30) {
      const x = ((lon + 180) / 360) * width;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }

    ctx.setLineDash([]);

    if (!impactLocation) {
      return;
    }

    const { latitude, longitude } = impactLocation;
    const x = ((longitude + 180) / 360) * width;
    const y = ((90 - latitude) / 180) * height;

    let color = '#e74c3c';
    if (impactResults) {
      const energy = impactResults.energy_mt_tnt;
      if (energy >= 100000) color = '#8B0000';
      else if (energy >= 10000) color = '#e74c3c';
      else if (energy >= 1000) color = '#e67e22';
      else if (energy >= 100) color = '#f39c12';
      else if (energy >= 10) color = '#f1c40f';
      else color = '#2ecc71';
    }

    const pulseSize = 8 + Math.sin(Date.now() / 200) * 2;
    const highlight = ctx.createRadialGradient(x, y, 0, x, y, pulseSize * 2);
    highlight.addColorStop(0, color);
    highlight.addColorStop(0.55, `${color}80`);
    highlight.addColorStop(1, `${color}00`);

    ctx.fillStyle = highlight;
    ctx.beginPath();
    ctx.arc(x, y, pulseSize * 2, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, pulseSize * 0.65, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x - 15, y);
    ctx.lineTo(x + 15, y);
    ctx.moveTo(x, y - 15);
    ctx.lineTo(x, y + 15);
    ctx.stroke();

    if (impactResults) {
      const kmToPixels = (km: number) => (km / 111) * (width / 360);

      ctx.strokeStyle = 'rgba(231, 76, 60, 0.6)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(x, y, kmToPixels(impactResults.thermal_radius_km), 0, Math.PI * 2);
      ctx.stroke();

      ctx.strokeStyle = 'rgba(243, 156, 18, 0.5)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(x, y, kmToPixels(impactResults.overpressure_radius_km), 0, Math.PI * 2);
      ctx.stroke();
    }
  }, [impactLocation, impactResults, mapImage, animationTick]);
  
  // Animation loop for pulsing effect
  useEffect(() => {
    let frameId: number;

    const animate = () => {
      setAnimationTick((tick) => tick + 1);
      frameId = requestAnimationFrame(animate);
    };

    if (impactLocation) {
      frameId = requestAnimationFrame(animate);
    }

    return () => {
      if (frameId) {
        cancelAnimationFrame(frameId);
      }
    };
  }, [impactLocation]);
  
  const handleCanvasClick = useCallback(async (event: MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const width = canvas.width;
    const height = canvas.height;

    const longitude = (x / width) * 360 - 180;
    const latitude = 90 - (y / height) * 180;

    try {
      setPlacementError(null);
      await placeAsteroidAt(latitude, longitude);
    } catch (error) {
      setPlacementError(error instanceof Error ? error.message : 'Failed to reposition asteroid');
    }
  }, [placeAsteroidAt]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.addEventListener('click', handleCanvasClick);
    return () => {
      canvas.removeEventListener('click', handleCanvasClick);
    };
  }, [handleCanvasClick]);

  if (!impactLocation) return null;
  
  return (
    <Paper
      elevation={3}
      onMouseDown={handleMouseDown}
      sx={{
        position: 'absolute',
        top: `${position.y}px`,
        left: `${position.x}px`,
        cursor: isDragging ? 'grabbing' : 'grab',
        userSelect: 'none',
        p: 1,
        bgcolor: 'rgba(10, 10, 20, 0.85)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(52, 152, 219, 0.3)',
        borderRadius: 1.5,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
        zIndex: 1000,
      }}
    >
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={0.5}>
        <Typography 
          variant="caption" 
          sx={{ 
            color: '#3498db', 
            fontWeight: 600, 
            fontSize: '0.7rem',
          }}
        >
          🗺️ Impact Location
        </Typography>
        <IconButton
          size="small"
          onClick={() => setExpanded((prev) => !prev)}
          sx={{ color: '#7f8c8d', p: 0.25 }}
        >
          {expanded ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
        </IconButton>
      </Box>

      <Collapse in={expanded}>
        <canvas
          ref={canvasRef}
          width={240}
          height={130}
          style={{
            width: '240px',
            height: '130px',
            borderRadius: '6px',
            border: '1px solid rgba(52, 152, 219, 0.25)',
            cursor: 'crosshair',
            background: 'radial-gradient(circle at 50% 50%, rgba(15, 23, 42, 0.85), rgba(2, 6, 23, 0.95))',
          }}
        />

        <Box sx={{ mt: 0.75, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem' }}>
            {impactLocation.latitude.toFixed(2)}°, {impactLocation.longitude.toFixed(2)}°
          </Typography>
          {impactResults && (
            <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
              <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: '#e74c3c' }} />
              <Typography variant="caption" sx={{ color: '#e74c3c', fontSize: '0.6rem' }}>
                Thermal
              </Typography>
              <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: '#f39c12', ml: 0.5 }} />
              <Typography variant="caption" sx={{ color: '#f39c12', fontSize: '0.6rem' }}>
                Blast
              </Typography>
            </Box>
          )}
        </Box>

        <Typography variant="caption" sx={{ color: '#95a5a6', fontSize: '0.6rem', mt: 0.5 }}>
          Click anywhere on the map to reposition the impact location.
        </Typography>
        {placementError && (
          <Typography variant="caption" sx={{ color: '#ff7675', fontSize: '0.6rem', mt: 0.5 }}>
            ⚠️ {placementError}
          </Typography>
        )}
      </Collapse>
    </Paper>
  );
}

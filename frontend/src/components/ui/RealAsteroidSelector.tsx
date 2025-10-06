import { Box, Button, Paper, Typography, CircularProgress, IconButton, Collapse, Chip, Tooltip } from '@mui/material';
import { ExpandLess, ExpandMore, Refresh, Warning, Map as MapIcon } from '@mui/icons-material';
import { useState, useEffect } from 'react';
import {
  getPotentiallyHazardousAsteroids,
  getNASAAsteroidData,
  type RealAsteroid,
} from '../../services/simulationApi';
import { useSimulationStore } from '../../stores/simulationStore';
import { AsteroidPlacementPanel } from './AsteroidPlacementPanel';
import { useDraggable } from '../../hooks/useDraggable';

export function RealAsteroidSelector() {
  const [expanded, setExpanded] = useState(true);
  const { position, handleMouseDown, isDragging } = useDraggable(window.innerWidth - 292, 180);
  const [asteroids, setAsteroids] = useState<RealAsteroid[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAsteroid, setSelectedAsteroid] = useState<string | null>(null);
  const [showPlacementPanel, setShowPlacementPanel] = useState(false);
  
  const {
    runSimulation,
    setAsteroidParams,
    setOrbitalElements,
    loadOrbitalTrajectory,
    impactLocation,
  } = useSimulationStore();

  // Fetch asteroids on mount
  useEffect(() => {
    fetchAsteroids();
  }, []);

  const fetchAsteroids = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPotentiallyHazardousAsteroids(15);
      setAsteroids(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load asteroids');
      console.error('Error fetching asteroids:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectAsteroid = async (asteroid: RealAsteroid) => {
    setSelectedAsteroid(asteroid.id);
    setLoading(true);
    setError(null);

    try {
      // Use average diameter and first close-approach velocity when available
      const diameter = (asteroid.diameter_min_m + asteroid.diameter_max_m) / 2;
      const velocity = asteroid.close_approaches.length > 0
        ? asteroid.close_approaches[0].velocity_km_s
        : 20;

      const params = {
        diameter,
        velocity,
        density: 2500,
        angle: 45,
      };
      setAsteroidParams(params);

      // Fetch SBDB orbital elements for orbital tracking
      let orbitalElements = null;
      try {
        const nasaData = await getNASAAsteroidData(asteroid.id);
        orbitalElements = nasaData?.orbital_elements ?? null;

        if (orbitalElements) {
          setOrbitalElements(orbitalElements);
          await loadOrbitalTrajectory(orbitalElements);
        } else {
          console.warn(`No orbital elements returned from NASA SBDB for ${asteroid.id}`);
          setOrbitalElements(null);
        }
      } catch (sbdbError) {
        console.error('Failed to fetch NASA SBDB data:', sbdbError);
        setOrbitalElements(null);
        throw new Error('Unable to retrieve orbital elements from NASA SBDB for this asteroid.');
      }

      const latitude = impactLocation?.latitude ?? 0;
      const longitude = impactLocation?.longitude ?? 0;
      await runSimulation(params, latitude, longitude, orbitalElements);
      setShowPlacementPanel(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to simulate asteroid');
      console.error('Asteroid selection error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Paper
        elevation={3}
        onMouseDown={handleMouseDown}
        sx={{
          position: 'absolute',
          top: `${position.y}px`,
          left: `${position.x}px`,
          cursor: isDragging ? 'grabbing' : 'grab',
          userSelect: 'none',
          p: 1.5,
          bgcolor: 'rgba(10, 10, 20, 0.75)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(231, 76, 60, 0.3)',
          borderRadius: 1.5,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
          minWidth: 280,
          maxWidth: 280,
          maxHeight: 'calc(80vh - 190px)',
          overflowY: 'auto',
          zIndex: 1000,
          '&::-webkit-scrollbar': {
            width: '6px',
          },
          '&::-webkit-scrollbar-track': {
            background: 'rgba(255, 255, 255, 0.05)',
            borderRadius: '10px',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'rgba(231, 76, 60, 0.3)',
            borderRadius: '10px',
            '&:hover': {
              background: 'rgba(231, 76, 60, 0.5)',
            },
          },
        }}
      >
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
          <Box>
            <Typography variant="subtitle2" sx={{ color: '#e74c3c', fontWeight: 600, fontSize: '0.875rem' }}>
              ☄️ Real NASA Asteroids
            </Typography>
            <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem' }}>
              Potentially Hazardous Objects
            </Typography>
          </Box>
          <Box display="flex" gap={0.5} alignItems="center">
          <Tooltip title="Refresh asteroid list">
            <IconButton 
              size="small" 
              onClick={fetchAsteroids}
              disabled={loading}
              sx={{ color: '#7f8c8d', p: 0.5 }}
            >
              <Refresh fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Open asteroid placement controls">
            <span>
              <IconButton
                size="small"
                onClick={() => setShowPlacementPanel((prev) => !prev)}
                disabled={loading}
                sx={{ color: '#00bcd4', p: 0.5 }}
              >
                <MapIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
          <IconButton 
            size="small" 
            onClick={() => setExpanded(!expanded)}
            sx={{ color: '#7f8c8d', p: 0.5 }}
          >
            {expanded ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
          </IconButton>
        </Box>
      </Box>

      <Collapse in={expanded}>
        {error && (
          <Box sx={{ 
            mb: 1, 
            p: 0.75, 
            bgcolor: 'rgba(231, 76, 60, 0.1)', 
            borderRadius: 0.5,
            border: '1px solid rgba(231, 76, 60, 0.3)'
          }}>
            <Typography variant="caption" sx={{ color: '#e74c3c', fontSize: '0.7rem' }}>
              ⚠️ {error}
            </Typography>
          </Box>
        )}

        {loading && asteroids.length === 0 ? (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, py: 2 }}>
            <CircularProgress size={16} sx={{ color: '#e74c3c' }} />
            <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.75rem' }}>
              Loading NASA data...
            </Typography>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
            {asteroids.map((asteroid) => {
              const avgDiameter = (asteroid.diameter_min_m + asteroid.diameter_max_m) / 2;
              const isSelected = selectedAsteroid === asteroid.id;

              return (
                <Button
                  key={asteroid.id}
                  variant={isSelected ? 'contained' : 'outlined'}
                  onClick={() => selectAsteroid(asteroid)}
                  disabled={loading}
                  size="small"
                  sx={{
                    justifyContent: 'flex-start',
                    textTransform: 'none',
                    color: isSelected ? '#fff' : '#e74c3c',
                    borderColor: isSelected ? 'rgba(231, 76, 60, 0.8)' : 'rgba(231, 76, 60, 0.3)',
                    bgcolor: isSelected ? 'rgba(231, 76, 60, 0.3)' : 'transparent',
                    py: 0.75,
                    px: 1,
                    fontSize: '0.7rem',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    gap: 0.5,
                    '&:hover': {
                      bgcolor: isSelected ? 'rgba(231, 76, 60, 0.4)' : 'rgba(231, 76, 60, 0.15)',
                      borderColor: 'rgba(231, 76, 60, 0.6)',
                    },
                  }}
                >
                  <Box display="flex" alignItems="center" width="100%" gap={0.5}>
                    {asteroid.is_potentially_hazardous && (
                      <Warning sx={{ fontSize: '0.9rem', color: '#f39c12' }} />
                    )}
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        fontWeight: 600, 
                        fontSize: '0.7rem',
                        flex: 1,
                        textAlign: 'left',
                        lineHeight: 1.2
                      }}
                    >
                      {asteroid.name.length > 35 
                        ? asteroid.name.substring(0, 35) + '...' 
                        : asteroid.name}
                    </Typography>
                  </Box>
                  
                  <Box display="flex" gap={0.5} width="100%" flexWrap="wrap">
                    <Chip
                      label={`${(avgDiameter).toFixed(0)}m`}
                      size="small"
                      sx={{
                        height: 16,
                        fontSize: '0.6rem',
                        bgcolor: 'rgba(52, 152, 219, 0.2)',
                        color: '#3498db',
                        '& .MuiChip-label': { px: 0.75, py: 0 }
                      }}
                    />
                    {asteroid.close_approaches.length > 0 && (
                      <Chip
                        label={`${asteroid.close_approaches[0].velocity_km_s.toFixed(1)} km/s`}
                        size="small"
                        sx={{
                          height: 16,
                          fontSize: '0.6rem',
                          bgcolor: 'rgba(46, 204, 113, 0.2)',
                          color: '#2ecc71',
                          '& .MuiChip-label': { px: 0.75, py: 0 }
                        }}
                      />
                    )}
                    {asteroid.close_approaches.length > 0 && (
                      <Chip
                        label={`${asteroid.close_approaches[0].miss_distance_lunar.toFixed(1)} LD`}
                        size="small"
                        sx={{
                          height: 16,
                          fontSize: '0.6rem',
                          bgcolor: 'rgba(155, 89, 182, 0.2)',
                          color: '#9b59b6',
                          '& .MuiChip-label': { px: 0.75, py: 0 }
                        }}
                      />
                    )}
                  </Box>
                </Button>
              );
            })}
          </Box>
        )}

        <Box sx={{ mt: 1, p: 0.75, bgcolor: 'rgba(52, 152, 219, 0.05)', borderRadius: 0.5 }}>
          <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block' }}>
            💡 Data from NASA/JPL NEO Program
          </Typography>
          <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.6rem', display: 'block', mt: 0.25 }}>
            LD = Lunar Distance (384,400 km)
          </Typography>
        </Box>
      </Collapse>
      </Paper>

      {showPlacementPanel && (
        <Box
          sx={{
            position: 'absolute',
            top: 80,
            right: 310,
            maxHeight: 'calc(100vh - 160px)',
            overflowY: 'auto',
            zIndex: 1200,
          }}
        >
          <AsteroidPlacementPanel onClose={() => setShowPlacementPanel(false)} />
        </Box>
      )}
    </>
  );
}


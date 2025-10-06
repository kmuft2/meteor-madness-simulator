import { Box, Paper, Typography, Switch, FormControlLabel, Chip, IconButton, Collapse } from '@mui/material';
import { ExpandLess, ExpandMore } from '@mui/icons-material';
import { useState } from 'react';
import { useSimulationStore } from '../../stores/simulationStore';
import { useDraggable } from '../../hooks/useDraggable';

export function OrbitalControls() {
  const [expanded, setExpanded] = useState(true);
  const { position, handleMouseDown, isDragging } = useDraggable(window.innerWidth - 292, window.innerHeight - 250);
  const orbitalElements = useSimulationStore((state) => state.orbitalElements);
  const showOrbitalPath = useSimulationStore((state) => state.showOrbitalPath);
  const toggleOrbitalPath = useSimulationStore((state) => state.toggleOrbitalPath);
  const orbitalMetadata = useSimulationStore((state) => state.orbitalMetadata);
  const orbitalTrajectoryLoading = useSimulationStore((state) => state.orbitalTrajectoryLoading);
  const orbitalTrajectoryError = useSimulationStore((state) => state.orbitalTrajectoryError);

  // Only show if orbital elements are available
  if (!orbitalElements) {
    return null;
  }

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
        p: 1.5,
        bgcolor: 'rgba(10, 10, 20, 0.75)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(52, 152, 219, 0.3)',
        borderRadius: 1.5,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
        minWidth: 280,
        maxWidth: 280,
        zIndex: 1000,
      }}
    >
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
        <Box>
          <Typography variant="subtitle2" sx={{ color: '#3498db', fontWeight: 600, fontSize: '0.875rem', mb: 0.5 }}>
            🌌 Orbital Mechanics
          </Typography>
          <Chip
            label="Real Orbit"
            size="small"
            sx={{
              bgcolor: 'rgba(52, 152, 219, 0.2)',
              color: '#3498db',
              fontSize: '0.7rem',
              height: 18,
            }}
          />
        </Box>

        <IconButton
          size="small"
          onClick={() => setExpanded(!expanded)}
          sx={{ color: '#7f8c8d', p: 0.5 }}
        >
          {expanded ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
        </IconButton>
      </Box>

      <Collapse in={expanded}>
        <FormControlLabel
          control={
            <Switch
              checked={showOrbitalPath && !orbitalTrajectoryLoading}
              onChange={() => toggleOrbitalPath()}
              disabled={orbitalTrajectoryLoading}
              sx={{
                '& .MuiSwitch-switchBase.Mui-checked': {
                  color: '#3498db',
                },
                '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                  backgroundColor: '#3498db',
                },
              }}
            />
          }
          label={
            <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.75rem' }}>
              {orbitalTrajectoryLoading ? 'Loading orbit…' : 'Show Orbital Path'}
            </Typography>
          }
        />

        {orbitalTrajectoryError && (
          <Typography
            variant="caption"
            sx={{
              color: '#e74c3c',
              fontSize: '0.65rem',
              display: 'block',
              mt: 0.5,
            }}
          >
            Failed to load orbit: {orbitalTrajectoryError}
          </Typography>
        )}

        <Box
          sx={{
            mt: 1,
            p: 1,
            bgcolor: 'rgba(52, 152, 219, 0.1)',
            borderRadius: 0.5,
            border: '1px solid rgba(52, 152, 219, 0.2)',
          }}
        >
          <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block', mb: 0.5 }}>
            Orbital Elements
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0.5, fontSize: '0.7rem' }}>
            <Box>
              <Typography variant="caption" sx={{ color: '#95a5a6', fontSize: '0.65rem' }}>
                Semi-major axis
              </Typography>
              <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.7rem', fontWeight: 500, display: 'block' }}>
                {orbitalElements.semi_major_axis_au.toFixed(3)} AU
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" sx={{ color: '#95a5a6', fontSize: '0.65rem' }}>
                Eccentricity
              </Typography>
              <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.7rem', fontWeight: 500, display: 'block' }}>
                {orbitalElements.eccentricity.toFixed(3)}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" sx={{ color: '#95a5a6', fontSize: '0.65rem' }}>
                Inclination
              </Typography>
              <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.7rem', fontWeight: 500, display: 'block' }}>
                {orbitalElements.inclination_deg.toFixed(2)}°
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" sx={{ color: '#95a5a6', fontSize: '0.65rem' }}>
                Periapsis arg.
              </Typography>
              <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.7rem', fontWeight: 500, display: 'block' }}>
                {orbitalElements.argument_periapsis_deg.toFixed(1)}°
              </Typography>
            </Box>
          </Box>
        </Box>

      {orbitalMetadata && (
        <Box
          sx={{
            mt: 1,
            p: 1,
            bgcolor: 'rgba(231, 76, 60, 0.08)',
            borderRadius: 0.5,
            border: '1px solid rgba(231, 76, 60, 0.2)',
          }}
        >
          <Typography variant="caption" sx={{ color: '#e74c3c', fontSize: '0.65rem', fontWeight: 600, display: 'block', mb: 0.5 }}>
            Orbit Metadata
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0.5 }}>
            <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.68rem' }}>
              Period: {orbitalMetadata.orbital_period_years.toFixed(2)} yr
            </Typography>
            <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.68rem' }}>
              Points: {orbitalMetadata.points_calculated}
            </Typography>
            <Typography variant="caption" sx={{ color: orbitalMetadata.collision_detected ? '#e74c3c' : '#2ecc71', fontSize: '0.68rem', gridColumn: 'span 2' }}>
              {orbitalMetadata.collision_detected
                ? `Collision predicted at index ${orbitalMetadata.collision_point_index ?? 'N/A'}`
                : 'No collision detected'}
            </Typography>
          </Box>
        </Box>
      )}

        <Typography
          variant="caption"
          sx={{
            color: '#7f8c8d',
            fontSize: '0.65rem',
            display: 'block',
            mt: 1,
            fontStyle: 'italic',
          }}
        >
          Keplerian orbital elements from NASA JPL data
        </Typography>
      </Collapse>
    </Paper>
  );
}

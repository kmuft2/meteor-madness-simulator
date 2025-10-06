import { Box, Typography, Paper, Divider, IconButton, Collapse } from '@mui/material';
import { ExpandLess, ExpandMore } from '@mui/icons-material';
import { useState } from 'react';
import { useSimulationStore } from '../../stores/simulationStore';
import { useDraggable } from '../../hooks/useDraggable';

export function InfoPanel() {
  const [expanded, setExpanded] = useState(true);
  const { position, handleMouseDown, isDragging } = useDraggable(12, 12);
  
  const {
    time,
    impactTime,
    asteroidParams,
    trajectoryData,
    impactLocation,
    impactResults,
  } = useSimulationStore();
  
  // Get current trajectory point based on time
  const getCurrentTrajectoryPoint = () => {
    if (trajectoryData.length === 0) return null;
    
    const progress = time / impactTime;
    const index = Math.floor(progress * (trajectoryData.length - 1));
    return trajectoryData[Math.min(index, trajectoryData.length - 1)];
  };
  
  const currentPoint = getCurrentTrajectoryPoint();
  const distance = currentPoint ? currentPoint.altitude_km + 6371 : 50000; // Add Earth radius
  const velocity = currentPoint ? currentPoint.velocity_km_s : asteroidParams.velocity;
  const timeToImpact = Math.max(0, impactTime - time);
  
  const isCloseApproach = distance < 10000;
  const isVeryClose = distance < 1000;
  
  // Determine danger level based on impact results
  const getDangerLevel = () => {
    if (!impactResults) return { level: 'Unknown', color: '#7f8c8d', bgColor: 'rgba(127, 140, 141, 0.1)' };
    
    const energy = impactResults.energy_mt_tnt;
    const severity = impactResults.danger_assessment?.severity?.toLowerCase();
    
    // Use backend danger assessment if available
    if (severity) {
      if (severity.includes('extinction') || severity.includes('global')) {
        return { level: 'EXTINCTION', color: '#8B0000', bgColor: 'rgba(139, 0, 0, 0.2)' };
      } else if (severity.includes('regional') || severity.includes('catastrophic')) {
        return { level: 'CATASTROPHIC', color: '#e74c3c', bgColor: 'rgba(231, 76, 60, 0.2)' };
      } else if (severity.includes('major') || severity.includes('city')) {
        return { level: 'MAJOR', color: '#e67e22', bgColor: 'rgba(230, 126, 34, 0.2)' };
      } else if (severity.includes('moderate')) {
        return { level: 'MODERATE', color: '#f39c12', bgColor: 'rgba(243, 156, 18, 0.2)' };
      } else if (severity.includes('minor')) {
        return { level: 'MINOR', color: '#f1c40f', bgColor: 'rgba(241, 196, 15, 0.2)' };
      }
    }
    
    // Fallback to energy-based classification
    if (energy >= 100000) return { level: 'EXTINCTION', color: '#8B0000', bgColor: 'rgba(139, 0, 0, 0.2)' };
    if (energy >= 10000) return { level: 'CATASTROPHIC', color: '#e74c3c', bgColor: 'rgba(231, 76, 60, 0.2)' };
    if (energy >= 1000) return { level: 'MAJOR', color: '#e67e22', bgColor: 'rgba(230, 126, 34, 0.2)' };
    if (energy >= 100) return { level: 'MODERATE', color: '#f39c12', bgColor: 'rgba(243, 156, 18, 0.2)' };
    if (energy >= 10) return { level: 'MINOR', color: '#f1c40f', bgColor: 'rgba(241, 196, 15, 0.2)' };
    return { level: 'MINIMAL', color: '#2ecc71', bgColor: 'rgba(46, 204, 113, 0.2)' };
  };
  
  const dangerLevel = getDangerLevel();
  
  return (
    <Paper
      elevation={3}
      onMouseDown={handleMouseDown}
      sx={{
        position: 'absolute',
        top: `${position.y}px`,
        left: `${position.x}px`,
        p: 1.5,
        maxWidth: 280,
        bgcolor: 'rgba(10, 10, 20, 0.75)',
        backdropFilter: 'blur(20px)',
        border: `1px solid ${isVeryClose ? 'rgba(231, 76, 60, 0.6)' : isCloseApproach ? 'rgba(243, 156, 18, 0.4)' : 'rgba(52, 152, 219, 0.3)'}`,
        borderRadius: 1.5,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
        cursor: isDragging ? 'grabbing' : 'grab',
        userSelect: 'none',
        transition: isDragging ? 'none' : 'box-shadow 0.2s',
        '&:hover': {
          boxShadow: '0 12px 40px rgba(0, 0, 0, 0.6)',
        },
      }}
    >
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
        <Box>
          <Typography
            variant="subtitle2"
            color={isVeryClose ? '#e74c3c' : '#3498db'}
            fontWeight="600"
            sx={{ 
              fontSize: '0.875rem',
              textShadow: isVeryClose ? '0 0 8px rgba(231, 76, 60, 0.8)' : 'none',
              animation: isVeryClose ? 'pulse 1s infinite' : 'none',
              '@keyframes pulse': {
                '0%, 100%': { opacity: 1 },
                '50%': { opacity: 0.7 },
              },
            }}
          >
            {isVeryClose ? '⚠️ IMPACT' : 'Asteroid Tracker'}
          </Typography>
          <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.7rem' }}>
            NASA Tracking Mode
          </Typography>
        </Box>
        <IconButton 
          size="small" 
          onClick={() => setExpanded(!expanded)}
          sx={{ color: '#7f8c8d', p: 0.5 }}
        >
          {expanded ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
        </IconButton>
      </Box>
      
      {/* Danger Level Indicator */}
      {impactResults && (
        <Box 
          sx={{ 
            mb: 1, 
            p: 0.75, 
            bgcolor: dangerLevel.bgColor,
            border: `2px solid ${dangerLevel.color}`,
            borderRadius: 1,
            textAlign: 'center',
            boxShadow: `0 0 12px ${dangerLevel.bgColor}`,
          }}
        >
          <Typography 
            variant="caption" 
            sx={{ 
              color: dangerLevel.color, 
              fontWeight: 700,
              fontSize: '0.75rem',
              letterSpacing: '0.05em',
              textShadow: `0 0 4px ${dangerLevel.bgColor}`,
            }}
          >
            ⚠️ {dangerLevel.level} THREAT
          </Typography>
        </Box>
      )}
      
      <Collapse in={expanded}>
        <Divider sx={{ my: 1, bgcolor: 'rgba(255,255,255,0.08)' }} />
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
        <InfoItem 
          label="Diameter" 
          value={`${asteroidParams.diameter} m`}
          icon="📏"
        />
        
        <InfoItem 
          label="Current Velocity" 
          value={`${velocity.toFixed(1)} km/s`}
          icon="⚡"
        />
        
        <InfoItem
          label="Distance to Earth"
          value={distance > 6371 ? `${Math.round(distance - 6371)} km` : 'IMPACTING'}
          valueColor={
            distance < 6500 ? '#e74c3c' : 
            distance < 10000 ? '#f39c12' : 
            '#2ecc71'
          }
          icon="📍"
          highlight={distance < 10000}
        />
        
        <InfoItem
          label="Time to Impact"
          value={
            timeToImpact > 0
              ? `${Math.floor(timeToImpact / 60)}:${(Math.floor(timeToImpact % 60)).toString().padStart(2, '0')}`
              : 'IMPACT NOW!'
          }
          valueColor={timeToImpact < 600 ? '#e74c3c' : timeToImpact < 1800 ? '#f39c12' : '#2ecc71'}
          icon="⏰"
          highlight={timeToImpact < 600}
        />
        
        {impactLocation && (
          <>
            <Divider sx={{ my: 0.75, bgcolor: 'rgba(255,255,255,0.05)' }} />
            <InfoItem 
              label="Target" 
              value={`${impactLocation.latitude.toFixed(1)}°, ${impactLocation.longitude.toFixed(1)}°`}
              icon="🎯"
            />
          </>
        )}
        </Box>
        
        {trajectoryData.length === 0 && (
          <Box sx={{ mt: 1, p: 0.75, bgcolor: 'rgba(52, 152, 219, 0.08)', borderRadius: 0.5 }}>
            <Typography variant="caption" sx={{ color: '#3498db', fontSize: '0.7rem' }}>
              Run a simulation to generate trajectory data
            </Typography>
          </Box>
        )}
      </Collapse>
    </Paper>
  );
}

function InfoItem({
  label,
  value,
  icon,
  valueColor = '#ecf0f1',
  highlight = false,
}: {
  label: string;
  value: string;
  icon?: string;
  valueColor?: string;
  highlight?: boolean;
}) {
  return (
    <Box 
      display="flex" 
      justifyContent="space-between" 
      alignItems="center"
      sx={{
        py: 0.5,
        px: 0.75,
        borderRadius: 0.5,
        bgcolor: highlight ? 'rgba(231, 76, 60, 0.08)' : 'transparent',
        border: highlight ? '1px solid rgba(231, 76, 60, 0.2)' : 'none',
      }}
    >
      <Box display="flex" alignItems="center" gap={0.5}>
        {icon && <span style={{ fontSize: '0.85em' }}>{icon}</span>}
        <Typography variant="caption" color="#7f8c8d" fontWeight="500" sx={{ fontSize: '0.7rem' }}>
          {label}
        </Typography>
      </Box>
      <Typography 
        variant="body2" 
        color={valueColor} 
        fontWeight="600"
        sx={{
          fontSize: '0.8rem',
          textShadow: highlight ? `0 0 6px ${valueColor}` : 'none',
        }}
      >
        {value}
      </Typography>
    </Box>
  );
}

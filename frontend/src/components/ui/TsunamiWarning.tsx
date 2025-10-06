import { Paper, Box, Typography, Divider, IconButton, Collapse, Chip } from '@mui/material';
import { ExpandLess, ExpandMore, Waves } from '@mui/icons-material';
import { useState } from 'react';
import { useSimulationStore } from '../../stores/simulationStore';
import { useDraggable } from '../../hooks/useDraggable';

/**
 * Tsunami Warning Panel
 * Displays tsunami data if the impact is over water
 */
export function TsunamiWarning() {
  const [expanded, setExpanded] = useState(true);
  const { position, handleMouseDown, isDragging } = useDraggable(310, 12);
  const { impactResults } = useSimulationStore();
  
  // Check if tsunami data is available
  const tsunamiData = impactResults?.danger_assessment?.tsunami;
  
  if (!tsunamiData) return null;
  
  const formatNumber = (num: number | undefined, decimals: number = 1) => {
    if (num === undefined || num === null || isNaN(num)) return 'N/A';
    if (num >= 1000000) return `${(num / 1000000).toFixed(decimals)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(decimals)}K`;
    return num.toFixed(decimals);
  };
  
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
        bgcolor: 'rgba(10, 10, 20, 0.85)',
        backdropFilter: 'blur(20px)',
        border: '2px solid rgba(41, 128, 185, 0.6)',
        borderRadius: 1.5,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px rgba(41, 128, 185, 0.3)',
        minWidth: 280,
        maxWidth: 280,
        zIndex: 1000,
      }}
    >
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
        <Box display="flex" alignItems="center" gap={0.5}>
          <Waves sx={{ color: '#3498db', fontSize: '1.1rem' }} />
          <Typography 
            variant="subtitle2" 
            sx={{ 
              color: '#3498db', 
              fontWeight: 700, 
              fontSize: '0.875rem',
              textShadow: '0 0 8px rgba(52, 152, 219, 0.5)',
            }}
          >
            🌊 TSUNAMI WARNING
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
      
      <Collapse in={expanded}>
        {/* Warning Message */}
        {(tsunamiData.warning || tsunamiData.description) && (
          <Box 
            sx={{ 
              mb: 1, 
              p: 0.75, 
              bgcolor: 'rgba(231, 76, 60, 0.15)',
              border: '1px solid rgba(231, 76, 60, 0.4)',
              borderRadius: 0.5,
            }}
          >
            <Typography 
              variant="caption" 
              sx={{ 
                color: '#e74c3c', 
                fontWeight: 600,
                fontSize: '0.7rem',
                display: 'block',
                lineHeight: 1.4,
              }}
            >
              {tsunamiData.description || tsunamiData.warning}
            </Typography>
          </Box>
        )}
        
        <Divider sx={{ my: 1, bgcolor: 'rgba(52, 152, 219, 0.2)' }} />
        
        {/* Wave Height at Source */}
        <Box sx={{ mb: 1 }}>
          <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block' }}>
            {tsunamiData.initial_wave_amplitude_m ? 'INITIAL WAVE HEIGHT' : 'WAVE HEIGHT AT SOURCE'}
          </Typography>
          <Typography 
            variant="h5" 
            sx={{ 
              color: '#3498db', 
              fontWeight: 700, 
              fontSize: '1.5rem',
              textShadow: '0 0 10px rgba(52, 152, 219, 0.5)',
            }}
          >
            {formatNumber(tsunamiData.initial_wave_amplitude_m || tsunamiData.wave_height_at_source_m)} m
          </Typography>
        </Box>
        
        {/* Coastal Wave (if available) */}
        {tsunamiData.coastal_wave_height_m && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block' }}>
              COASTAL WAVE HEIGHT
            </Typography>
            <Typography 
              variant="h5" 
              sx={{ 
                color: '#e74c3c', 
                fontWeight: 700, 
                fontSize: '1.5rem',
                textShadow: '0 0 10px rgba(231, 76, 60, 0.5)',
              }}
            >
              {formatNumber(tsunamiData.coastal_wave_height_m)} m
            </Typography>
          </Box>
        )}
        
        {/* Tsunami Velocity */}
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 1 }}>
          <Box>
            <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block' }}>
              VELOCITY
            </Typography>
            <Typography variant="body2" sx={{ color: '#2ecc71', fontWeight: 600, fontSize: '0.85rem' }}>
              {formatNumber(tsunamiData.wave_speed_km_h || tsunamiData.tsunami_velocity_kmh, 0)} km/h
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block' }}>
              INUNDATION
            </Typography>
            <Typography variant="body2" sx={{ color: '#e67e22', fontWeight: 600, fontSize: '0.85rem' }}>
              {formatNumber(tsunamiData.inundation_distance_km ? tsunamiData.inundation_distance_km * 1000 : tsunamiData.coastal_inundation_distance_m)}m
            </Typography>
          </Box>
        </Box>
        
        {/* Ocean Depth and Risk Level */}
        {(tsunamiData.ocean_depth_m || tsunamiData.risk_level) && (
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 1 }}>
            {tsunamiData.ocean_depth_m && (
              <Box>
                <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block' }}>
                  OCEAN DEPTH
                </Typography>
                <Typography variant="body2" sx={{ color: '#3498db', fontWeight: 600, fontSize: '0.85rem' }}>
                  {formatNumber(tsunamiData.ocean_depth_m, 0)}m
                </Typography>
              </Box>
            )}
            {tsunamiData.risk_level && (
              <Box>
                <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block' }}>
                  RISK LEVEL
                </Typography>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    color: tsunamiData.risk_level === 'CATASTROPHIC' ? '#e74c3c' : '#f39c12', 
                    fontWeight: 700, 
                    fontSize: '0.85rem' 
                  }}
                >
                  {tsunamiData.risk_level}
                </Typography>
              </Box>
            )}
          </Box>
        )}
        
        <Divider sx={{ my: 1, bgcolor: 'rgba(52, 152, 219, 0.2)' }} />
        
        {/* Wave Heights at Distance */}
        {tsunamiData.wave_heights_at_distance && Object.keys(tsunamiData.wave_heights_at_distance).length > 0 && (
          <Box sx={{ mb: 1 }}>
            <Typography 
              variant="caption" 
              sx={{ 
                color: '#7f8c8d', 
                fontSize: '0.65rem', 
                display: 'block',
                mb: 0.5,
              }}
            >
              WAVE HEIGHT BY DISTANCE
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.4 }}>
              {Object.entries(tsunamiData.wave_heights_at_distance).map(([distance, height]) => (
                <Box 
                  key={distance}
                  sx={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    p: 0.5,
                    bgcolor: 'rgba(52, 152, 219, 0.05)',
                    borderRadius: 0.5,
                  }}
                >
                  <Typography variant="caption" sx={{ color: '#95a5a6', fontSize: '0.7rem' }}>
                    @ {distance}
                  </Typography>
                  <Chip
                    label={`${height.toFixed(1)}m`}
                    size="small"
                    sx={{
                      height: 18,
                      fontSize: '0.65rem',
                      bgcolor: 'rgba(52, 152, 219, 0.3)',
                      color: '#3498db',
                      fontWeight: 600,
                      '& .MuiChip-label': { px: 0.75, py: 0 }
                    }}
                  />
                </Box>
              ))}
            </Box>
          </Box>
        )}
        
        {/* Arrival Times */}
        {tsunamiData.arrival_time_hours && Object.keys(tsunamiData.arrival_time_hours).length > 0 && (
          <>
            <Divider sx={{ my: 1, bgcolor: 'rgba(52, 152, 219, 0.2)' }} />
            <Box>
              <Typography 
                variant="caption" 
                sx={{ 
                  color: '#7f8c8d', 
                  fontSize: '0.65rem', 
                  display: 'block',
                  mb: 0.5,
                }}
              >
                ⏱️ ESTIMATED ARRIVAL TIME
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.4 }}>
                {Object.entries(tsunamiData.arrival_time_hours).map(([location, hours]) => (
                  <Box 
                    key={location}
                    sx={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      p: 0.5,
                      bgcolor: 'rgba(243, 156, 18, 0.05)',
                      borderRadius: 0.5,
                    }}
                  >
                    <Typography variant="caption" sx={{ color: '#95a5a6', fontSize: '0.7rem' }}>
                      {location}
                    </Typography>
                    <Chip
                      label={`${hours.toFixed(1)}h`}
                      size="small"
                      sx={{
                        height: 18,
                        fontSize: '0.65rem',
                        bgcolor: 'rgba(243, 156, 18, 0.3)',
                        color: '#f39c12',
                        fontWeight: 600,
                        '& .MuiChip-label': { px: 0.75, py: 0 }
                      }}
                    />
                  </Box>
                ))}
              </Box>
            </Box>
          </>
        )}
        
        {/* Footer Info */}
        <Box 
          sx={{ 
            mt: 1, 
            p: 0.75, 
            bgcolor: 'rgba(52, 152, 219, 0.08)', 
            borderRadius: 0.5,
            borderLeft: '3px solid #3498db',
          }}
        >
          <Typography 
            variant="caption" 
            sx={{ 
              color: '#7f8c8d', 
              fontSize: '0.65rem',
              display: 'block',
              lineHeight: 1.3,
            }}
          >
            💡 Tsunami waves can travel across entire ocean basins at jet-like speeds
          </Typography>
        </Box>
      </Collapse>
    </Paper>
  );
}



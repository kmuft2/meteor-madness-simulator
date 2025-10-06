import { Box, Button, Slider, Typography, Paper, IconButton, Collapse } from '@mui/material';
import {
  PlayArrow,
  Pause,
  RestartAlt,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material';
import { useSimulationStore } from '../../stores/simulationStore';
import { useEffect, useState } from 'react';
import { useDraggable } from '../../hooks/useDraggable';

const SPEEDS = [0.5, 1, 2, 5, 10];

export function TimeControls() {
  const [expanded, setExpanded] = useState(true);
  const { position, handleMouseDown, isDragging } = useDraggable(window.innerWidth / 2 - 300, window.innerHeight - 92);
  const {
    time,
    maxTime,
    impactTime,
    playing,
    speed,
    setTime,
    setPlaying,
    setSpeed,
    reset,
    updateTime,
  } = useSimulationStore();
  
  // Animation loop
  useEffect(() => {
    if (!playing) return;
    
    let lastTime = Date.now();
    const interval = setInterval(() => {
      const now = Date.now();
      const delta = (now - lastTime) / 1000;
      lastTime = now;
      updateTime(delta);
    }, 16); // ~60fps
    
    return () => clearInterval(interval);
  }, [playing, updateTime]);
  
  // Format time display
  const formatTime = (seconds: number) => {
    const relativeTime = seconds - impactTime;
    const absTime = Math.abs(relativeTime);
    const minutes = Math.floor(absTime / 60);
    const secs = Math.floor(absTime % 60);
    const sign = relativeTime < 0 ? 'T-' : 'T+';
    return `${sign}${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  const isNearImpact = Math.abs(time - impactTime) < 300; // Within 5 minutes
  const timeToImpact = Math.max(0, impactTime - time);
  
  // Calculate distance for display
  const getDistance = () => {
    const startDistance = 50000;
    const progress = time / impactTime;
    if (progress >= 1) return 0;
    const distance = startDistance - (startDistance - 6371) * progress - 6371;
    return Math.max(0, distance);
  };
  const distance = getDistance();
  
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
        minWidth: 500,
        maxWidth: 600,
        bgcolor: 'rgba(10, 10, 20, 0.75)',
        backdropFilter: 'blur(20px)',
        border: `1px solid ${isNearImpact ? 'rgba(231, 76, 60, 0.6)' : 'rgba(52, 152, 219, 0.3)'}`,
        borderRadius: 1.5,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
      }}
    >
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
        <Typography variant="caption" color="#7f8c8d" sx={{ fontSize: '0.7rem' }}>
          ⏱️ Timeline
        </Typography>
        <Typography
          variant="h6"
          color="#f39c12"
          fontFamily="monospace"
          fontWeight="600"
          sx={{ fontSize: '1.1rem' }}
        >
          {formatTime(time)}
        </Typography>
        <IconButton 
          size="small" 
          onClick={() => setExpanded(!expanded)}
          sx={{ color: '#7f8c8d', p: 0.5 }}
        >
          {expanded ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
        </IconButton>
      </Box>
      
      <Collapse in={expanded}>
        <Box display="flex" gap={0.5} mb={1} justifyContent="flex-end">
          {SPEEDS.map((s) => (
            <Box
              key={s}
              onClick={() => setSpeed(s)}
              sx={{
                px: 0.75,
                py: 0.25,
                borderRadius: 0.5,
                bgcolor: speed === s ? 'rgba(52, 152, 219, 0.3)' : 'transparent',
                border: `1px solid ${speed === s ? '#3498db' : 'rgba(52, 152, 219, 0.2)'}`,
                color: speed === s ? '#3498db' : '#7f8c8d',
                fontSize: '0.7rem',
                cursor: 'pointer',
                '&:hover': {
                  bgcolor: 'rgba(52, 152, 219, 0.2)',
                },
              }}
            >
              {s}x
            </Box>
          ))}
        </Box>
      
        {/* Timeline Scrubber */}
        <Box mb={1.5}>
        <Box display="flex" justifyContent="space-between" mb={0.5}>
          <Typography variant="caption" color="#7f8c8d" sx={{ fontSize: '0.65rem' }}>T-30</Typography>
          <Typography variant="caption" color="#e74c3c" fontWeight="600" sx={{ fontSize: '0.65rem' }}>
            IMPACT
          </Typography>
          <Typography variant="caption" color="#7f8c8d" sx={{ fontSize: '0.65rem' }}>T+30</Typography>
        </Box>
        <Slider
          value={time}
          min={0}
          max={maxTime}
          onChange={(_event: Event, value: number | number[]) => setTime(value as number)}
          size="small"
          sx={{
            height: 4,
            '& .MuiSlider-track': {
              background: 'linear-gradient(to right, #2ecc71, #f39c12, #e74c3c)',
              border: 'none',
            },
            '& .MuiSlider-rail': {
              bgcolor: 'rgba(255, 255, 255, 0.1)',
            },
            '& .MuiSlider-thumb': {
              width: 14,
              height: 14,
              border: '2px solid #3498db',
              bgcolor: 'white',
              '&:hover, &.Mui-focusVisible': {
                boxShadow: '0 0 0 6px rgba(52, 152, 219, 0.3)',
              },
            },
          }}
        />
      </Box>
      
      {/* Playback Controls */}
      <Box display="flex" justifyContent="center" gap={1} alignItems="center">
        <Button
          variant="outlined"
          size="small"
          onClick={() => setPlaying(!playing)}
          sx={{
            bgcolor: playing ? 'rgba(243, 156, 18, 0.15)' : 'rgba(46, 204, 113, 0.15)',
            borderColor: playing ? '#f39c12' : '#2ecc71',
            color: playing ? '#f39c12' : '#2ecc71',
            minWidth: 100,
            px: 2,
            py: 0.5,
            fontSize: '0.75rem',
            '&:hover': {
              bgcolor: playing ? 'rgba(243, 156, 18, 0.25)' : 'rgba(46, 204, 113, 0.25)',
              borderColor: playing ? '#f39c12' : '#2ecc71',
            },
          }}
        >
          {playing ? <><Pause fontSize="small" sx={{ mr: 0.5 }} /> Pause</> : <><PlayArrow fontSize="small" sx={{ mr: 0.5 }} /> Play</>}
        </Button>
        <Button
          variant="outlined"
          size="small"
          onClick={reset}
          sx={{
            borderColor: 'rgba(231, 76, 60, 0.4)',
            color: '#e74c3c',
            px: 1.5,
            py: 0.5,
            fontSize: '0.75rem',
            minWidth: 'auto',
            '&:hover': {
              bgcolor: 'rgba(231, 76, 60, 0.1)',
              borderColor: '#e74c3c',
            },
          }}
        >
          <RestartAlt fontSize="small" />
        </Button>
        
        {/* Compact Info */}
        <Box display="flex" gap={2} ml={2}>
          <Box>
            <Typography variant="caption" color="#7f8c8d" sx={{ fontSize: '0.65rem' }}>Distance</Typography>
            <Typography variant="caption" color="#2ecc71" fontWeight="600" display="block" sx={{ fontSize: '0.75rem' }}>
              {distance > 0 ? `${Math.round(distance)} km` : 'IMPACT'}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="#7f8c8d" sx={{ fontSize: '0.65rem' }}>To Impact</Typography>
            <Typography variant="caption" color="#f39c12" fontWeight="600" display="block" sx={{ fontSize: '0.75rem' }}>
              {timeToImpact > 0
                ? `${Math.floor(timeToImpact / 60)}:${(Math.floor(timeToImpact % 60)).toString().padStart(2, '0')}`
                : 'NOW!'}
            </Typography>
          </Box>
        </Box>
      </Box>
      
      {/* Impact Warning */}
      {timeToImpact > 0 && timeToImpact < 300 && (
        <Box
          mt={1}
          p={0.75}
          textAlign="center"
          bgcolor="rgba(231, 76, 60, 0.15)"
          border="1px solid rgba(231, 76, 60, 0.4)"
          borderRadius={0.5}
        >
          <Typography variant="caption" color="#e74c3c" fontWeight="600" sx={{ fontSize: '0.7rem' }}>
            ⚠️ IMPACT IMMINENT
          </Typography>
        </Box>
      )}
      </Collapse>
    </Paper>
  );
}

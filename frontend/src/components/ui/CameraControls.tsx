import { Typography, Paper, Box, IconButton, Collapse } from '@mui/material';
import { ExpandLess, ExpandMore } from '@mui/icons-material';
import { useState } from 'react';
import { useDraggable } from '../../hooks/useDraggable';

export function CameraControls() {
  const [expanded, setExpanded] = useState(true);
  const { position, handleMouseDown, isDragging } = useDraggable(window.innerWidth - 122, window.innerHeight - 92);
  
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
        bgcolor: 'rgba(10, 10, 20, 0.75)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(52, 152, 219, 0.3)',
        borderRadius: 1.5,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
      }}
    >
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={0.5}>
        <Typography variant="caption" color="#7f8c8d" fontWeight="600" sx={{ fontSize: '0.7rem' }}>
          🎮 Controls
        </Typography>
        <IconButton 
          size="small" 
          onClick={() => setExpanded(!expanded)}
          sx={{ color: '#7f8c8d', p: 0.25 }}
        >
          {expanded ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
        </IconButton>
      </Box>
      <Collapse in={expanded}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
          <Typography variant="caption" color="#95a5a6" sx={{ fontSize: '0.65rem' }}>
            Drag: Rotate
          </Typography>
          <Typography variant="caption" color="#95a5a6" sx={{ fontSize: '0.65rem' }}>
            Right: Pan
          </Typography>
          <Typography variant="caption" color="#95a5a6" sx={{ fontSize: '0.65rem' }}>
            Scroll: Zoom
          </Typography>
        </Box>
      </Collapse>
    </Paper>
  );
}



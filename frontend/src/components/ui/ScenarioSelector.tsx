import { Box, Button, Paper, Typography, CircularProgress, IconButton, Collapse } from '@mui/material';
import { ExpandLess, ExpandMore } from '@mui/icons-material';
import { useState } from 'react';
import { useSimulationStore, SCENARIOS } from '../../stores/simulationStore';
import { useDraggable } from '../../hooks/useDraggable';

export function ScenarioSelector() {
  const [expanded, setExpanded] = useState(true);
  const { position, handleMouseDown, isDragging } = useDraggable(window.innerWidth - 232, 12);
  const { currentScenario, loadScenario, loading } = useSimulationStore();

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
        minWidth: 220,
        maxWidth: 220,
        zIndex: 1000,
      }}
    >
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
        <Box>
          <Typography variant="subtitle2" sx={{ color: '#3498db', fontWeight: 600, fontSize: '0.875rem' }}>
            📚 Example Scenario
          </Typography>
          <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem' }}>
            Historical reference
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
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
          {SCENARIOS.map((scenario) => (
            <Button
              key={scenario.id}
              variant={currentScenario === scenario.id ? 'contained' : 'outlined'}
              onClick={() => loadScenario(scenario.id)}
              disabled={loading}
              size="small"
              sx={{
                justifyContent: 'flex-start',
                textTransform: 'none',
                color: currentScenario === scenario.id ? '#fff' : '#3498db',
                borderColor: currentScenario === scenario.id ? 'rgba(52, 152, 219, 0.8)' : 'rgba(52, 152, 219, 0.3)',
                bgcolor: currentScenario === scenario.id ? 'rgba(52, 152, 219, 0.3)' : 'transparent',
                py: 0.5,
                px: 1,
                fontSize: '0.75rem',
                '&:hover': {
                  bgcolor: currentScenario === scenario.id ? 'rgba(52, 152, 219, 0.4)' : 'rgba(52, 152, 219, 0.15)',
                  borderColor: 'rgba(52, 152, 219, 0.6)',
                },
              }}
            >
              <span style={{ marginRight: 6, fontSize: '0.9em' }}>{scenario.icon}</span>
              {scenario.name}
            </Button>
          ))}
        
          <Button
            variant={currentScenario === 'custom' ? 'contained' : 'outlined'}
            onClick={() => {}}
            disabled={loading}
            size="small"
            sx={{
              justifyContent: 'flex-start',
              textTransform: 'none',
              color: currentScenario === 'custom' ? '#fff' : '#9b59b6',
              borderColor: currentScenario === 'custom' ? 'rgba(155, 89, 182, 0.8)' : 'rgba(155, 89, 182, 0.3)',
              bgcolor: currentScenario === 'custom' ? 'rgba(155, 89, 182, 0.3)' : 'transparent',
              py: 0.5,
              px: 1,
              fontSize: '0.75rem',
              '&:hover': {
                bgcolor: currentScenario === 'custom' ? 'rgba(155, 89, 182, 0.4)' : 'rgba(155, 89, 182, 0.15)',
                borderColor: 'rgba(155, 89, 182, 0.6)',
              },
            }}
          >
            <span style={{ marginRight: 6, fontSize: '0.9em' }}>⚙️</span>
            Custom
          </Button>
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mt: 1, p: 0.75, bgcolor: 'rgba(52, 152, 219, 0.1)', borderRadius: 0.5 }}>
            <CircularProgress size={12} sx={{ color: '#3498db' }} />
            <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.7rem' }}>
              Loading...
            </Typography>
          </Box>
        )}
      </Collapse>
    </Paper>
  );
}


import { Box, ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { Scene3D } from './components/3d/Scene3D';
import { TimeControls } from './components/ui/TimeControls';
import { InfoPanel } from './components/ui/InfoPanel';
import { CameraControls } from './components/ui/CameraControls';
import { RealAsteroidSelector } from './components/ui/RealAsteroidSelector';
import { ImpactDataPanel } from './components/ui/ImpactDataPanel';
import { OrbitalControls } from './components/ui/OrbitalControls';
import { MiniMap } from './components/ui/MiniMap';
import { TsunamiWarning } from './components/ui/TsunamiWarning';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#3498db',
    },
    secondary: {
      main: '#f39c12',
    },
    error: {
      main: '#e74c3c',
    },
    success: {
      main: '#2ecc71',
    },
    background: {
      default: '#000000',
      paper: 'rgba(10, 14, 39, 0.95)',
    },
  },
  typography: {
    fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box
        sx={{
          width: '100vw',
          height: '100vh',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {/* 3D Scene */}
        <Scene3D />
        
        {/* UI Overlays */}
        <InfoPanel />
        <RealAsteroidSelector />
        <ImpactDataPanel />
        <TsunamiWarning />
        <OrbitalControls />
        <TimeControls />
        <CameraControls />
        <MiniMap />
      </Box>
    </ThemeProvider>
  );
}

export default App;



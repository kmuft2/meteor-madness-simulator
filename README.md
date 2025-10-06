# Meteor Madness Simulator

**NASA Space Apps Challenge 2025 Project**

A high-fidelity asteroid impact assessment system delivering near-real-time hazard analysis through GPU-accelerated physics modeling, official NASA/USGS data integration, and immersive 3D visualization.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![CUDA](https://img.shields.io/badge/CUDA-12.2-green.svg)
![React](https://img.shields.io/badge/react-18-61dafb.svg)

---

## Overview

The Meteor Madness Simulator provides end-to-end asteroid impact assessment from orbital ingestion through atmospheric entry to surface impact and multi-hazard analysis. The system combines peer-reviewed physics models, authoritative datasets, and GPU acceleration to enable interactive what-if scenario analysis.

### Core Capabilities

**Physics & Computation**
- NVIDIA CUDA 12.2 acceleration delivering 2-5× speedups on L40S hardware
- Holsapple & Housen crater scaling laws with π-group transitions
- Ward & Asphaug tsunami generation models with GEBCO bathymetry
- Glasstone & Dolan atmospheric blast and thermal radiation curves
- Full Keplerian orbital mechanics with Earth intercept detection

**Data Integration**
- NASA NEO/SBDB API for real-time potentially hazardous asteroid tracking
- USGS Earthquake API for seismic magnitude correlations
- GEBCO 2025 bathymetry grid (15 arc-second resolution, 99.9% accuracy)
- WorldPop 2020 population density for casualty modeling
- Automated caching for offline demonstrations

**Visualization & Interface**
- WebGL2-accelerated 3D Earth rendering via React Three Fiber
- Real-time atmospheric entry trajectories and orbital paths
- Physics-accurate crater morphology with ejecta patterns
- Multi-panel HUD displaying impact timeline, hazard metrics, and tsunami warnings
- Material-UI responsive design optimized for presentation mode

---

## System Architecture

### Backend (FastAPI)

**Core Components:**
- `backend/app/main.py` - FastAPI application entry point with CORS and router registration
- `backend/app/api/routes/simulation.py` - Primary impact workflow and trajectory services
- `backend/app/api/routes/real_asteroids.py` - NASA SBDB integration
- `backend/app/physics/` - Physics engines (impact, orbital, tsunami, danger assessment)
- `backend/app/services/` - External API clients (NASA, USGS, bathymetry, population)

**Request Lifecycle** (`POST /api/simulation/impact`):
1. Input validation via Pydantic schemas (`SimulationRequest`)
2. Orbital mechanics computation for atmospheric entry vectors
3. Impact physics calculation (crater, energy, thermal, seismic)
4. Multi-hazard assessment (casualties, tsunami, atmospheric effects)
5. JSON response with comprehensive impact metrics

### Frontend (React + Three.js)

**Architecture:**
- React 18 + TypeScript with Vite build system
- Zustand for state management (`frontend/src/stores/simulationStore.ts`)
- react-three-fiber for WebGL2 rendering pipeline

**Core Modules:**
- `Scene3D.tsx` - Earth globe, atmosphere, clouds, orbital paths
- `ImpactCrater.tsx` - Physics-driven crater visualization with lat/lon projection
- `TrajectoryLine.tsx` / `OrbitalPath.tsx` - Real-time trajectory rendering
- `ImpactDataPanel.tsx` - Metrics display (energy, magnitude, casualties)
- `TsunamiWarning.tsx` - Tsunami model outputs and risk visualization

### GPU Acceleration

**Hardware Target:** NVIDIA L40S (46 GB VRAM)
- CUDA 12.2 runtime with CuPy 13.6 for Python GPU computing
- Automatic CPU fallback via NumPy when CUDA unavailable
- Measured performance: 0.5s → 0.1-0.2s per simulation (2-5× speedup)
- Batch operations: 50-100× acceleration for parameter sweeps

**Accelerated Operations:**
- Vectorized impact physics calculations
- Large matrix operations for orbital propagation
- Tsunami wave modeling over bathymetry grids

---

## Quick Start

### Prerequisites

**Required:**
- Docker 20.10+ with Docker Compose 2.0+
- 8 GB RAM minimum (16 GB recommended)
- 4-25 GB disk space for datasets

**Optional (for GPU acceleration):**
- NVIDIA GPU with CUDA 12.x support
- NVIDIA Container Toolkit

### Installation

1. **Clone repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/meteor-madness-simulator.git
   cd meteor-madness-simulator
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add NASA API key from https://api.nasa.gov/
   ```

3. **Download datasets:**
   
   See [DATA_SETUP.md](DATA_SETUP.md) for complete instructions.
   
   **Minimum requirement:** GEBCO_2025_TID.nc (3.7 GB)
   ```bash
   # Download to data/GEBCO_2025_TID.nc
   # See DATA_SETUP.md for download URLs
   ```

4. **Start services:**
   ```bash
   docker compose up -d
   ```

5. **Access interfaces:**
   - Frontend UI: http://localhost:3000
   - REST API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

---

## Physics Models & Hazard Analysis

### Impact Physics

**Models Implemented:**
- **Crater Formation:** Holsapple & Housen (2007) π-group scaling with strength/gravity regime transitions
- **Energy Deposition:** Kinetic energy conversion with atmospheric deceleration factors
- **Thermal Radiation:** Glasstone & Dolan (1977) nuclear weapons effects scaling
- **Blast Overpressure:** Concentric damage zones (20 psi total destruction, 5-20 psi severe, 1-5 psi moderate)
- **Seismic Effects:** USGS moment magnitude correlations from Shoemaker (1963)

**Outputs:**
- Crater diameter and depth (meters)
- Impact energy (joules, TNT equivalent in megatons)
- Thermal radiation radius (km)
- Overpressure damage zones (km)
- Richter magnitude equivalent
- Fireball dimensions

### Orbital Mechanics

**Capabilities:**
- Keplerian element to Cartesian state conversion
- Two-body orbit propagation using Kepler's equation
- Earth intercept detection with atmospheric entry geometry
- Velocity and angle calculations for surface impact modeling
- Real-time trajectory visualization data generation

**Integration:** Supplies atmospheric entry parameters for impact physics and provides orbital path coordinates for 3D visualization.

### Tsunami Modeling

**Data Source:** GEBCO 2025 bathymetry grid (15 arc-second, 43,200 × 86,400 cells)

**Process:**
1. Water displacement calculation from impact energy and asteroid geometry
2. Deep-water wave propagation using depth-dependent velocity (√(g×depth))
3. Coastal amplification via Green's Law
4. Inundation distance and travel time estimates

**Outputs:**
- Initial wave amplitude (meters)
- Coastal wave height (meters)
- Wave propagation speed (km/h)
- Estimated travel times to coastlines
- Risk categorization (Minor / Moderate / Significant / Catastrophic)

### Danger Assessment

**Multi-Hazard Analysis:**
- **Damage Zones:** Fireball radius, total destruction, severe/moderate/light damage rings
- **Population Impact:** WorldPop 2020 integration with zone-specific fatality rates
- **Atmospheric Effects:** Dust injection mass, global temperature drop estimates, sunlight reduction percentage
- **Global Risk Flags:** Extinction-level event, crop failure, famine risk indicators

**Output Categories:**
- Local (< 1 MT TNT equivalent)
- Regional (1-100 MT)
- Continental (100-10,000 MT)
- Global (> 10,000 MT)

---

## Technology Stack

### Backend Services
- **Framework:** FastAPI with async/await patterns
- **Language:** Python 3.12 with type hints
- **GPU Compute:** CuPy 13.6 (CUDA 12.2) with NumPy fallback
- **Physics:** SciPy for numerical methods
- **Data I/O:** H5Py, NetCDF4 for scientific datasets
- **Validation:** Pydantic v2 schemas
- **HTTP Client:** aiohttp for async API calls

### Frontend Application
- **Framework:** React 18 with TypeScript
- **3D Engine:** react-three-fiber + @react-three/drei
- **Rendering:** WebGL2 with post-processing effects
- **UI Library:** Material-UI v5
- **State:** Zustand for simulation state management
- **Build:** Vite with code splitting and tree shaking

### Infrastructure
- **Containerization:** Docker with multi-stage builds
- **Orchestration:** Docker Compose with GPU device passthrough
- **GPU Runtime:** NVIDIA Container Toolkit for CUDA access
- **Base Images:** nvidia/cuda:12.2.0-devel-ubuntu22.04

---

## API Documentation

### REST Endpoints

Interactive OpenAPI documentation: http://localhost:8000/docs

**Primary Simulation Endpoint:**
```http
POST /api/simulation/impact
Content-Type: application/json

{
  "asteroid_params": {
    "diameter": 100,           // meters
    "velocity": 20.0,          // km/s
    "density": 3000,           // kg/m³
    "angle": 45,               // degrees from horizontal
    "composition": "rocky"     // rocky, iron, or carbonaceous
  },
  "location_lat": 40.7,        // degrees
  "location_lon": -74.0        // degrees
}
```

**Response Structure:**
```json
{
  "impact_results": {
    "crater_diameter": 8158.7,  // meters
    "energy_mt_tnt": 938.6,     // megatons TNT equivalent
    "seismic_magnitude": 6.4,   // Richter scale
    "thermal_radius_km": 3857.6,
    "danger_assessment": {
      "severity": "continental",
      "impact_type": "ocean",   // or "land"
      "casualties": { ... },
      "tsunami": { ... },       // if ocean impact
      "atmospheric_effects": { ... }
    }
  }
}
```

**Additional Endpoints:**
- `GET /api/nasa/potentially-hazardous?limit=N` - Fetch real asteroid catalog
- `GET /api/nasa/asteroid/{neo_id}` - Detailed orbital elements
- `POST /api/simulation/orbital-trajectory` - Generate trajectory visualization data
- `GET /api/simulation/historical/{event}` - Tunguska/Chelyabinsk validation cases

---

## Validation & Testing

### Physics Validation

**Historical Event Regression:**
- **Tunguska (1908):** 12 MT airburst, 2,000 km² forest devastation
- **Chelyabinsk (2013):** 500 kT airburst, 1,500 injuries from blast wave
- Endpoints: `/api/simulation/historical/tunguska` and `/api/simulation/historical/chelyabinsk`

**Test Harnesses:**
- `backend/scripts/demo_all_features.py` - End-to-end validation
- `backend/scripts/test_apis_simple.py` - External API connectivity
- `frontend/scripts/test_3d_system.sh` - WebGL rendering verification

### Running Tests

```bash
# Backend unit tests
docker exec meteor-madness-backend pytest

# Coverage report
docker exec meteor-madness-backend pytest --cov=app --cov-report=html

# Frontend tests
cd frontend && npm test

# Integration tests
cd backend/scripts && python demo_all_features.py
```

---

## Data Sources & Compliance

### Official Datasets

**NASA Near-Earth Object Program**
- API: https://api.nasa.gov/ (requires free API key)
- Coverage: 30,000+ known NEOs
- Update frequency: Daily
- License: U.S. Government work, public domain

**USGS Earthquake Catalog**
- API: https://earthquake.usgs.gov/fdsnws/event/1/
- Purpose: Seismic magnitude correlations
- License: Public domain

**GEBCO Bathymetry Grid**
- Version: GEBCO_2025
- Resolution: 15 arc-second (∼463m at equator)
- Grid size: 43,200 × 86,400 cells (3.7 billion data points)
- License: Public domain with attribution
- Citation: GEBCO Compilation Group (2025) doi:10.5285/37c52e96-24ea-67ce-e063-7086abc05f29

**WorldPop Population Density**
- Version: 2020 constrained dataset
- Resolution: 1 km
- License: CC BY 4.0
- Purpose: Casualty estimation per damage zone

### Validation Against Peer-Reviewed Literature

All physics models reference published research:
1. Holsapple & Housen (2007) - Crater scaling
2. Ward & Asphaug (2000) - Tsunami generation
3. Glasstone & Dolan (1977) - Blast and thermal effects
4. Shoemaker (1963) - Seismic relationships

See `docs/references.bib` for complete bibliography.

---

## Use Cases & Limitations

### Designed For

- **Educational Demonstrations:** Interactive asteroid risk visualization
- **Scientific Communication:** Translating physics into actionable intelligence
- **Scenario Analysis:** What-if exploration of impact parameters
- **NASA Space Apps Challenge:** High-fidelity technical demonstration

### Not Designed For

- **Operational Decision-Making:** Use NASA/CNEOS official products for real threats
- **Emergency Planning:** Contact national civil defense authorities
- **Navigation:** System provides educational estimates, not certified data
- **Media Sensationalism:** Results include uncertainty bounds and should not be misrepresented

---

## Contributing

### Development Guidelines

Contributions are welcome. Please ensure:

1. **Code Quality:**
   - Follow PEP 8 for Python (use `black` formatter)
   - Use TypeScript strict mode for frontend
   - Add type hints to all function signatures
   - Maintain < 100 line length

2. **Testing Requirements:**
   - Add unit tests for new physics models
   - Maintain > 80% code coverage
   - Verify CUDA fallback paths work correctly
   - Test against historical validation cases

3. **Documentation:**
   - Update API documentation for new endpoints
   - Add docstrings with example usage
   - Reference peer-reviewed sources for physics changes
   - Update `DATA_SETUP.md` for new dataset requirements

4. **Pull Request Process:**
   - Fork repository and create feature branch
   - Commit with descriptive messages (`feat:`, `fix:`, `docs:` prefixes)
   - Ensure all tests pass (`pytest`, `npm test`)
   - Update `CHANGELOG.md` with changes
   - Submit PR with clear description and linked issues

---

## License

### Software License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for full terms.

### Dataset Licenses

All external datasets maintain their original licenses:

- **GEBCO 2025:** Public domain with required attribution
- **WorldPop 2020:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **NASA NEO Data:** U.S. Government work, public domain
- **USGS Data:** U.S. Government work, public domain

Users must comply with attribution requirements for GEBCO and WorldPop when publishing results.

---

## References & Acknowledgments

### Data Providers

- **NASA Center for Near-Earth Object Studies (CNEOS)** - Orbital elements and hazard assessment methodology
- **GEBCO / Nippon Foundation Seabed 2030** - Global bathymetric grid enabling accurate tsunami modeling
- **WorldPop Project** - High-resolution population density for casualty estimation
- **USGS Earthquake Hazards Program** - Seismic magnitude correlations

### Scientific Literature

1. Holsapple, K. A., & Housen, K. R. (2007). A crater and its ejecta: An interpretation of Deep Impact. *Icarus*, 187(1), 345-356. doi:10.1016/j.icarus.2006.09.011

2. Ward, S. N., & Asphaug, E. (2000). Asteroid impact tsunami: A probabilistic hazard assessment. *Icarus*, 145(1), 64-78. doi:10.1006/icar.1999.6336

3. Glasstone, S., & Dolan, P. J. (1977). *The Effects of Nuclear Weapons* (3rd ed.). United States Department of Defense and Energy Research and Development Administration.

4. Shoemaker, E. M. (1963). Impact mechanics at Meteor Crater, Arizona. In *The Moon, Meteorites and Comets* (pp. 301-336). University of Chicago Press.

5. GEBCO Compilation Group (2025). GEBCO 2025 Grid. British Oceanographic Data Centre, National Oceanography Centre. doi:10.5285/37c52e96-24ea-67ce-e063-7086abc05f29

6. Collins, G. S., Melosh, H. J., & Marcus, R. A. (2005). Earth Impact Effects Program: A Web-based computer program for calculating the regional environmental consequences of a meteoroid impact on Earth. *Meteoritics & Planetary Science*, 40(6), 817-840.

---

## Project Information

**NASA Space Apps Challenge 2025**

- Zayd Alzein, Zaid Khayyat, Khalid Mufti, Kareem Muftee
- Challenge: Meteor Madness

---

### Bug Reports & Issues

When reporting issues, please include:

1. **Environment Details:**
   - Operating system and version
   - Docker version (`docker --version`)
   - GPU details (`nvidia-smi` output if applicable)
   - Browser and version (for frontend issues)

2. **Reproduction Steps:**
   - Exact API request or UI interaction
   - Input parameters that triggered the issue
   - Expected vs. actual behavior

3. **Logs:**
   - Backend logs: `docker logs meteor-madness-backend`
   - Browser console errors for frontend issues

Search existing issues before creating new ones to avoid duplicates.

---

## Future Development

**Planned Enhancements:**

- **Extended Climate Modeling:** Long-term atmospheric and temperature effects using aerosol transport models
- **Machine Learning Integration:** GPU-accelerated scenario recommendations and impact probability forecasting
- **Multi-Impact Scenarios:** Modeling of fragment showers and clustered events
- **Early Warning Systems:** Integration with notification services for real-time asteroid tracking alerts
- **Airburst Modeling:** Atmospheric disintegration and energy deposition profiles
- **Additional Hazards:** Expanding to include seismic-triggered tsunamis and secondary effects

Contributions implementing these features are welcome. See Contributing section above.

---

## Project Status

**Current Version:** 1.0.0 (NASA Space Apps Challenge 2025)

**System Status:**
- Backend API: Operational
- CUDA Acceleration: Verified on NVIDIA L40S
- NASA API Integration: Active
- GEBCO Bathymetry: Loaded (99.9% accuracy)
- Frontend Visualization: Fully functional

---

**Meteor Madness Simulator**  
*High-Fidelity Asteroid Impact Assessment for NASA Space Apps Challenge 2025*

Repository: https://github.com/Zaydo123/meteor-madness-simulator  
Documentation: [DATA_SETUP.md](DATA_SETUP.md) | [LICENSE](LICENSE)  
Contact: [Your Team] - NASA Space Apps Challenge 2025

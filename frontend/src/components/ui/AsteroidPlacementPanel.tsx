import { useState } from 'react';
import { useSimulationStore } from '../../stores/simulationStore';

interface AsteroidPlacementPanelProps {
  onClose?: () => void;
}

export function AsteroidPlacementPanel({ onClose }: AsteroidPlacementPanelProps) {
  const {
    impactLocation,
    asteroidParams,
    orbitalElements,
    placeAsteroidAt,
  } = useSimulationStore();

  const [latitude, setLatitude] = useState<number>(impactLocation?.latitude ?? 0);
  const [longitude, setLongitude] = useState<number>(impactLocation?.longitude ?? 0);
  const [isPlacing, setIsPlacing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePlaceAsteroid = async () => {
    setIsPlacing(true);
    setError(null);
    try {
      await placeAsteroidAt(latitude, longitude);
      if (onClose) {
        onClose();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reposition asteroid');
    } finally {
      setIsPlacing(false);
    }
  };

  return (
    <div className="placement-panel">
      <div className="panel-header">
        <h2>Asteroid Placement</h2>
        {onClose && (
          <button onClick={onClose} className="close-button">×</button>
        )}
      </div>

      <div className="panel-content">
        <div className="section">
          <h3>Current Parameters</h3>
          <ul>
            <li>Diameter: {asteroidParams.diameter.toFixed(0)} m</li>
            <li>Velocity: {asteroidParams.velocity.toFixed(1)} km/s</li>
            <li>Density: {asteroidParams.density.toFixed(0)} kg/m³</li>
            <li>Entry angle: {asteroidParams.angle.toFixed(0)}°</li>
          </ul>
        </div>

        <div className="section">
          <h3>Impact Location</h3>
          <label>
            Latitude (°)
            <input
              type="number"
              value={latitude}
              onChange={(e) => setLatitude(Number(e.target.value))}
              min={-90}
              max={90}
              step={0.1}
            />
          </label>
          <label>
            Longitude (°)
            <input
              type="number"
              value={longitude}
              onChange={(e) => setLongitude(Number(e.target.value))}
              min={-180}
              max={180}
              step={0.1}
            />
          </label>
          <button
            className="primary"
            onClick={handlePlaceAsteroid}
            disabled={isPlacing}
          >
            {isPlacing ? 'Updating...' : 'Place Asteroid'}
          </button>
        </div>

        {orbitalElements && (
          <div className="section">
            <h3>Orbital Elements</h3>
            <ul>
              <li>Semi-major axis: {orbitalElements.semi_major_axis_au.toFixed(4)} AU</li>
              <li>Eccentricity: {orbitalElements.eccentricity.toFixed(4)}</li>
              <li>Inclination: {orbitalElements.inclination_deg.toFixed(2)}°</li>
              <li>Longitude of ascending node: {orbitalElements.longitude_ascending_node_deg.toFixed(2)}°</li>
              <li>Argument of periapsis: {orbitalElements.argument_periapsis_deg.toFixed(2)}°</li>
              <li>Mean anomaly: {orbitalElements.mean_anomaly_deg.toFixed(2)}°</li>
            </ul>
          </div>
        )}

        {error && <p className="error">⚠️ {error}</p>}
      </div>

      <style>{`
        .placement-panel {
          background: rgba(6, 12, 20, 0.95);
          border: 1px solid rgba(0, 188, 212, 0.3);
          border-radius: 12px;
          padding: 16px;
          color: #f1f4f8;
          width: 360px;
          box-shadow: 0 12px 40px rgba(0,0,0,0.45);
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .panel-header h2 {
          font-size: 1.25rem;
          margin: 0;
          color: #00bcd4;
        }

        .close-button {
          background: transparent;
          border: none;
          color: #9aa7b8;
          font-size: 24px;
          cursor: pointer;
        }

        .panel-content {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .section h3 {
          margin: 0 0 8px 0;
          color: #80deea;
          font-size: 0.95rem;
        }

        .section ul {
          margin: 0;
          padding-left: 16px;
          font-size: 0.85rem;
        }

        label {
          display: flex;
          flex-direction: column;
          gap: 6px;
          font-size: 0.85rem;
          color: #cfd8dc;
        }

        input {
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(0,188,212,0.3);
          color: #e0f7fa;
          padding: 6px 10px;
          border-radius: 6px;
        }

        .primary {
          margin-top: 10px;
          background: #00bcd4;
          color: #04121f;
          border: none;
          padding: 10px 16px;
          border-radius: 6px;
          font-weight: 600;
          cursor: pointer;
        }

        .primary:disabled {
          background: rgba(0, 188, 212, 0.4);
          cursor: not-allowed;
        }

        .error {
          margin: 0;
          color: #ff8a80;
          font-size: 0.85rem;
        }
      `}</style>
    </div>
  );
}

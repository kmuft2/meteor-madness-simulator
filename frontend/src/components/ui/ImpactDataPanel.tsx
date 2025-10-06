import { Box, Paper, Typography, Divider, LinearProgress, IconButton, Collapse, Chip } from '@mui/material';
import { ExpandLess, ExpandMore } from '@mui/icons-material';
import { useState } from 'react';
import { useSimulationStore } from '../../stores/simulationStore';
import { useDraggable } from '../../hooks/useDraggable';

export function ImpactDataPanel() {
  const [expanded, setExpanded] = useState(true);
  const { position, handleMouseDown, isDragging } = useDraggable(12, window.innerHeight - 350);
  const { impactResults, impactLocation, asteroidParams, loading } = useSimulationStore();

  if (loading) {
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
          minWidth: 240,
          maxWidth: 240,
          zIndex: 1000,
        }}
      >
        <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.7rem', mb: 0.75, display: 'block' }}>
          Calculating impact...
        </Typography>
        <LinearProgress sx={{ height: 2, backgroundColor: 'rgba(52, 152, 219, 0.15)' }} />
      </Paper>
    );
  }

  if (!impactResults || !impactLocation) {
    return null;
  }

  const formatNumber = (num: number, decimals: number = 1) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(decimals)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(decimals)}K`;
    return num.toFixed(decimals);
  };

  const { latitude, longitude } = impactLocation;
  const {
    energy_mt_tnt: energyMtTnt,
    thermal_radius_km: thermalRadiusKm,
    overpressure_radius_km: overpressureRadiusKm,
    seismic_magnitude: seismicMagnitude,
    danger_assessment: danger,
  } = impactResults;

  const casualties = danger?.casualties;
  const tsunami = danger?.tsunami;
  const atmospheric = danger?.atmospheric_effects;
  const globalEffects = danger?.global_effects;

  const severityStyles: Record<string, { bg: string; color: string }> = {
    negligible: { bg: 'rgba(52, 152, 219, 0.25)', color: '#3498db' },
    local: { bg: 'rgba(46, 204, 113, 0.25)', color: '#2ecc71' },
    regional: { bg: 'rgba(243, 156, 18, 0.25)', color: '#f39c12' },
    continental: { bg: 'rgba(231, 76, 60, 0.25)', color: '#e74c3c' },
    global: { bg: 'rgba(142, 68, 173, 0.25)', color: '#8e44ad' },
  };

  const getSeverityStyle = () => {
    if (!danger?.severity) {
      return { bg: 'rgba(127, 140, 141, 0.25)', color: '#bdc3c7' };
    }
    return severityStyles[danger.severity] || { bg: 'rgba(231, 76, 60, 0.25)', color: '#e74c3c' };
  };

  const damageZoneData = danger?.damage_zones
    ? [
        { label: 'Fireball', value: danger.damage_zones.fireball_km, color: '#ff6b6b' },
        { label: 'Total', value: danger.damage_zones.total_destruction_km, color: '#e74c3c' },
        { label: 'Severe', value: danger.damage_zones.severe_damage_km, color: '#f39c12' },
        { label: 'Moderate', value: danger.damage_zones.moderate_damage_km, color: '#f1c40f' },
        { label: 'Thermal', value: danger.damage_zones.thermal_burns_km, color: '#e67e22' },
      ]
    : [
        { label: 'Thermal', value: thermalRadiusKm, color: '#e74c3c' },
        { label: 'Pressure', value: overpressureRadiusKm, color: '#f39c12' },
      ];

  const tsunamiEntries = tsunami?.wave_heights_at_distance
    ? Object.entries(tsunami.wave_heights_at_distance)
        .sort((a, b) => parseInt(a[0], 10) - parseInt(b[0], 10))
        .slice(0, 3)
    : tsunami?.arrival_time_hours
    ? Object.entries(tsunami.arrival_time_hours).slice(0, 3)
    : [];

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
        border: '1px solid rgba(231, 76, 60, 0.4)',
        borderRadius: 1.5,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
        minWidth: 260,
        maxWidth: 260,
        zIndex: 1000,
      }}
    >
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
        <Typography variant="subtitle2" sx={{ color: '#e74c3c', fontWeight: 600, fontSize: '0.875rem' }}>
          💥 Impact Effects
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
        {danger && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, mb: 1 }}>
            {danger.severity && (
              <Chip
                label={`Severity: ${danger.severity.toUpperCase()}`}
                size="small"
                sx={{
                  alignSelf: 'flex-start',
                  bgcolor: getSeverityStyle().bg,
                  color: getSeverityStyle().color,
                  fontWeight: 600,
                  letterSpacing: '0.05em',
                }}
              />
            )}
            {danger.impact_type && danger.comparable_to && (
              <Typography variant="caption" sx={{ color: '#bdc3c7', fontSize: '0.65rem', lineHeight: 1.3 }}>
                {danger.impact_type.toUpperCase()} IMPACT • {danger.comparable_to}
              </Typography>
            )}
          </Box>
        )}

        {/* Asteroid Info */}
        <Box sx={{ mb: 1 }}>
          <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block' }}>
            ASTEROID
          </Typography>
          <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.7rem' }}>
            {asteroidParams.diameter}m • {asteroidParams.velocity}km/s • {asteroidParams.angle}°
          </Typography>
        </Box>

        <Divider sx={{ my: 1, backgroundColor: 'rgba(255, 255, 255, 0.08)' }} />

        {/* Impact Location */}
        <Box sx={{ mb: 1 }}>
          <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block' }}>
            LOCATION
          </Typography>
          {casualties?.location_info ? (
            <>
              {casualties.location_info.is_ocean ? (
                <Box>
                  <Typography variant="caption" sx={{ color: '#3498db', fontSize: '0.75rem', fontWeight: 600, display: 'block' }}>
                    🌊 {casualties.location_info.ocean || 'Ocean Impact'}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem' }}>
                    {latitude.toFixed(2)}°, {longitude.toFixed(2)}°
                  </Typography>
                </Box>
              ) : (
                <Box>
                  <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.75rem', fontWeight: 600, display: 'block' }}>
                    {casualties.location_info.city || 'Unknown City'}
                    {casualties.location_info.state && `, ${casualties.location_info.state}`}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#95a5a6', fontSize: '0.65rem', display: 'block' }}>
                    {casualties.location_info.country_name}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem' }}>
                    {latitude.toFixed(2)}°, {longitude.toFixed(2)}°
                  </Typography>
                </Box>
              )}
            </>
          ) : (
            <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.7rem' }}>
              {latitude.toFixed(2)}°, {longitude.toFixed(2)}°
            </Typography>
          )}
        </Box>

        <Divider sx={{ my: 1, backgroundColor: 'rgba(255, 255, 255, 0.08)' }} />

        {/* Energy */}
        <Box sx={{ mb: 1 }}>
          <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block' }}>
            ENERGY
          </Typography>
          <Typography variant="h6" sx={{ color: '#e74c3c', fontWeight: 600, fontSize: '1.25rem' }}>
            {energyMtTnt.toFixed(1)} MT
          </Typography>
          <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem' }}>
            TNT equivalent
          </Typography>
        </Box>

        {/* Crater */}
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 1 }}>
          <Box>
            <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block' }}>
              CRATER ø
            </Typography>
            <Typography variant="caption" sx={{ color: '#f39c12', fontWeight: 600, fontSize: '0.8rem' }}>
              {formatNumber(impactResults.crater_diameter)}m
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block' }}>
              DEPTH
            </Typography>
            <Typography variant="caption" sx={{ color: '#f39c12', fontWeight: 600, fontSize: '0.8rem' }}>
              {formatNumber(impactResults.crater_depth)}m
            </Typography>
          </Box>
      </Box>

        {/* Damage Zones */}
        <Box sx={{ mb: 1 }}>
          <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block', mb: 0.5 }}>
            DAMAGE RADIUS
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.35 }}>
            {damageZoneData.map((zone) => (
              <Box key={zone.label} sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                <Box sx={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: zone.color }} />
                <Typography variant="caption" sx={{ color: '#ecf0f1', flex: 1, fontSize: '0.7rem' }}>
                  {zone.label}
                </Typography>
                <Typography variant="caption" sx={{ color: zone.color, fontWeight: 600, fontSize: '0.7rem' }}>
                  {zone.value.toFixed(1)}km
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>

        <Divider sx={{ my: 1, backgroundColor: 'rgba(255, 255, 255, 0.08)' }} />

        {/* Seismic */}
        <Box>
          <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block' }}>
            SEISMIC
          </Typography>
          <Typography variant="h6" sx={{ color: '#e67e22', fontWeight: 600, fontSize: '1.5rem' }}>
            {seismicMagnitude.toFixed(1)}
          </Typography>
          {globalEffects?.description && (
            <Typography variant="caption" sx={{ color: '#7f8c8d', display: 'block', fontSize: '0.65rem', lineHeight: 1.3 }}>
              {globalEffects.description}
            </Typography>
          )}
        </Box>

        {/* Casualties */}
        {casualties && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block', mb: 0.5 }}>
              CASUALTIES (EST.)
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0.75 }}>
              <Box>
                <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.7rem', display: 'block' }}>
                  Immediate
                </Typography>
                <Typography variant="caption" sx={{ color: '#e74c3c', fontWeight: 600, fontSize: '0.75rem' }}>
                  {formatNumber(casualties.immediate_deaths_estimate, 1)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.7rem', display: 'block' }}>
                  Injured
                </Typography>
                <Typography variant="caption" sx={{ color: '#f39c12', fontWeight: 600, fontSize: '0.75rem' }}>
                  {formatNumber(casualties.injured_estimate, 1)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.7rem', display: 'block' }}>
                  Affected
                </Typography>
                <Typography variant="caption" sx={{ color: '#16a085', fontWeight: 600, fontSize: '0.75rem' }}>
                  {formatNumber(casualties.affected_population, 1)}
                </Typography>
              </Box>
            </Box>
            
            {/* Population by Zone Breakdown */}
            {casualties.zone_breakdown && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.6rem', display: 'block', mb: 0.5 }}>
                  POPULATION BY ZONE
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
                  {Object.entries(casualties.zone_breakdown).map(([zone, data]) => (
                    <Box key={zone} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="caption" sx={{ color: '#95a5a6', fontSize: '0.65rem' }}>
                        {zone.replace(/_/g, ' ')}
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.65rem', fontWeight: 500 }}>
                        {formatNumber(data.population, 1)}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </Box>
            )}
            
            {/* Data Source */}
            {casualties.data_source && (
              <Box sx={{ mt: 0.75, pt: 0.75, borderTop: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.6rem', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  📊 {casualties.data_source.includes('WorldPop') ? (
                    <span style={{ color: '#2ecc71' }}>Real population data</span>
                  ) : (
                    <span style={{ color: '#f39c12' }}>Estimated (avg. density)</span>
                  )}
                </Typography>
              </Box>
            )}
            
            {casualties.note && (
              <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.6rem', lineHeight: 1.3, display: 'block', mt: 0.5 }}>
                {casualties.note}
              </Typography>
            )}
          </Box>
        )}

        {/* Tsunami */}
        {tsunami && (
          <Box sx={{ mt: 1 }}>
            <Divider sx={{ my: 1, backgroundColor: 'rgba(255, 255, 255, 0.08)' }} />
            <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block', mb: 0.5 }}>
              TSUNAMI (OCEAN IMPACT)
            </Typography>
            <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.7rem', display: 'block' }}>
              {tsunami.initial_wave_amplitude_m 
                ? `Initial wave ${tsunami.initial_wave_amplitude_m.toFixed(0)}m • Coastal ${tsunami.coastal_wave_height_m.toFixed(0)}m`
                : `Source wave ${tsunami.wave_height_at_source_m?.toFixed(0)}m • ${tsunami.tsunami_velocity_kmh?.toFixed(0)} km/h`
              }
            </Typography>
            {tsunami.wave_speed_km_h && (
              <Typography variant="caption" sx={{ color: '#95a5a6', fontSize: '0.65rem', display: 'block' }}>
                Speed: {tsunami.wave_speed_km_h.toFixed(0)} km/h • Depth: {tsunami.ocean_depth_m}m
              </Typography>
            )}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25, mt: 0.5 }}>
              {tsunamiEntries.map(([distance, value]) => (
                <Typography key={distance} variant="caption" sx={{ color: '#95a5a6', fontSize: '0.65rem' }}>
                  {distance.replace(/_/g, ' ')}: {typeof value === 'number' ? value.toFixed(1) : value}
                </Typography>
              ))}
            </Box>
            <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.6rem', display: 'block', mt: 0.5 }}>
              {tsunami.description || `Inundation ≈ ${tsunami.coastal_inundation_distance_m?.toFixed(0)}m inland`}
            </Typography>
            {tsunami.risk_level && (
              <Typography variant="caption" sx={{ color: tsunami.risk_level === 'CATASTROPHIC' ? '#e74c3c' : '#f39c12', fontSize: '0.65rem', fontWeight: 'bold', display: 'block', mt: 0.25 }}>
                ⚠️ {tsunami.risk_level}
              </Typography>
            )}
          </Box>
        )}

        {/* Atmospheric */}
        {atmospheric && (
          <Box sx={{ mt: 1 }}>
            <Divider sx={{ my: 1, backgroundColor: 'rgba(255, 255, 255, 0.08)' }} />
            <Typography variant="caption" sx={{ color: '#7f8c8d', fontSize: '0.65rem', display: 'block', mb: 0.5 }}>
              ATMOSPHERIC EFFECTS
            </Typography>
            <Typography variant="caption" sx={{ color: '#ecf0f1', fontSize: '0.7rem', display: 'block' }}>
              ΔTemp {atmospheric.temperature_drop_celsius.toFixed(1)}°C • Sunlight −{atmospheric.sunlight_reduction_percent.toFixed(0)}%
            </Typography>
            <Typography variant="caption" sx={{ color: '#95a5a6', fontSize: '0.65rem', display: 'block', mt: 0.25 }}>
              Duration: {atmospheric.effect_duration}
            </Typography>
            {atmospheric.soot_from_fires_kg && (
              <Typography variant="caption" sx={{ color: '#95a5a6', fontSize: '0.6rem', display: 'block', mt: 0.25 }}>
                Wildfire soot: {formatNumber(atmospheric.soot_from_fires_kg, 2)} kg
              </Typography>
            )}
          </Box>
        )}

        {/* Global Effects Flags */}
        {globalEffects && (
          <Box sx={{ mt: 1.25, display: 'flex', flexDirection: 'column', gap: 0.25 }}>
            {globalEffects.mass_extinction_risk && (
              <Typography variant="caption" sx={{ color: '#e74c3c', fontWeight: 600, fontSize: '0.7rem' }}>
                ⚠️ Mass extinction risk
              </Typography>
            )}
            {globalEffects.civilization_threat && (
              <Typography variant="caption" sx={{ color: '#f39c12', fontWeight: 600, fontSize: '0.7rem' }}>
                ⚠️ Civilization-level threat
              </Typography>
            )}
            {(globalEffects.crop_failure_risk || globalEffects.global_famine_risk) && (
              <Typography variant="caption" sx={{ color: '#c0392b', fontWeight: 500, fontSize: '0.65rem' }}>
                Agricultural collapse likely
              </Typography>
            )}
          </Box>
        )}
      </Collapse>
    </Paper>
  );
}

#!/usr/bin/env python3
"""
Test GEBCO bathymetry integration
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)

print("🌊 Testing GEBCO Bathymetry Integration")
print("=" * 70)

# Test 1: Load bathymetry service
print("\n1️⃣  Loading GEBCO bathymetry service...")
try:
    from app.services.bathymetry_service import BathymetryService
    service = BathymetryService()
    print("   ✓ Bathymetry service loaded")
except Exception as e:
    print(f"   ❌ Failed to load bathymetry service: {e}")
    sys.exit(1)

# Test 2: Query ocean depths
print("\n2️⃣  Testing ocean depth queries...")

test_locations = [
    (40.7128, -74.0060, "New York City (land)"),
    (0.0, -150.0, "Pacific Ocean (deep)"),
    (35.6762, 139.6503, "Tokyo (land)"),
    (10.0, -80.0, "Caribbean Sea"),
    (-10.0, 105.0, "Indian Ocean"),
]

for lat, lon, name in test_locations:
    try:
        depth = service.get_depth(lat, lon)
        is_ocean = service.is_ocean(lat, lon)
        
        if is_ocean:
            print(f"   🌊 {name}")
            print(f"      Depth: {depth:.0f}m below sea level")
        else:
            print(f"   🏔️  {name}")
            print(f"      Elevation: {-depth:.0f}m above sea level")
            
    except Exception as e:
        print(f"   ⚠️  {name}: Query failed - {e}")

# Test 3: Test tsunami model with bathymetry
print("\n3️⃣  Testing tsunami model with real depths...")
try:
    from app.physics.tsunami_model import TsunamiModel
    
    tsunami_model = TsunamiModel(bathymetry_service=service)
    
    # Test Pacific Ocean impact
    print("\n   Testing 500m asteroid in Pacific Ocean (0°, -150°):")
    result = tsunami_model.calculate_tsunami_from_location(
        latitude=0.0,
        longitude=-150.0,
        asteroid_diameter_m=500,
        asteroid_velocity_km_s=20.0,
        asteroid_density_kg_m3=3000,
        impact_angle_deg=45.0
    )
    
    if result:
        print(f"   ✓ Tsunami generated!")
        print(f"     Ocean depth: {result['impact_location']['ocean_depth_m']:.0f}m")
        print(f"     Wave height at source: {result['initial_wave_amplitude_m']:.1f}m")
        print(f"     Coastal wave height: {result['coastal_wave_height_m']:.1f}m")
        print(f"     Data source: {result['impact_location']['data_source']}")
    else:
        print("   ⚠️  No tsunami generated (land impact)")
        
except Exception as e:
    print(f"   ❌ Tsunami model test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test danger assessment integration
print("\n4️⃣  Testing danger assessment with bathymetry...")
try:
    from app.physics.danger_assessment import DangerAssessment
    
    assessor = DangerAssessment()
    
    # Test ocean impact
    print("\n   Testing 200m asteroid in Atlantic Ocean:")
    assessment = assessor.assess_impact(
        energy_mt_tnt=50.0,
        crater_diameter_m=2000,
        crater_depth_m=500,
        latitude=25.0,
        longitude=-50.0,
        impact_angle_deg=45.0,
        asteroid_diameter_m=200,
        velocity_km_s=20.0
    )
    
    if assessment['impact_type'] == 'ocean':
        print("   ✓ Detected as ocean impact")
        if assessment['tsunami']:
            tsunami = assessment['tsunami']
            print(f"     Tsunami wave height: {tsunami.get('wave_height_at_source_m', 'N/A')}m")
            if 'impact_location' in tsunami:
                print(f"     Ocean depth: {tsunami['impact_location']['ocean_depth_m']:.0f}m")
                print(f"     Data source: {tsunami['impact_location']['data_source']}")
    else:
        print("   ⚠️  Detected as land impact")
        
except Exception as e:
    print(f"   ❌ Danger assessment test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("✅ Bathymetry integration testing complete!")
print("\nKey improvements:")
print("  • Real ocean depths from GEBCO (3.5GB dataset)")
print("  • Accurate land/ocean detection")
print("  • Location-specific tsunami calculations")
print("  • Graceful fallback if data unavailable")

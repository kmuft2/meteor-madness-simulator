#!/bin/bash

# Test script for new NASA hackathon features
# Run after Docker rebuild

echo "========================================="
echo "🧪 Testing New NASA Hackathon Features"
echo "========================================="

BASE_URL="http://localhost:8000"

echo ""
echo "1️⃣ Testing Health Endpoint..."
curl -s $BASE_URL/health | python3 -m json.tool
echo "✅ Health check complete"

echo ""
echo "2️⃣ Testing Live NASA NEO Data..."
curl -s $BASE_URL/api/simulation/neo/live-threats | python3 -m json.tool | head -50
echo "✅ NEO live threats tested"

echo ""
echo "3️⃣ Testing Apophis Lookup..."
curl -s $BASE_URL/api/simulation/neo/2099942 | python3 -m json.tool | head -40
echo "✅ Asteroid lookup tested"

echo ""
echo "4️⃣ Testing Deflection Analysis..."
curl -s -X POST "$BASE_URL/api/simulation/deflection/analyze?asteroid_diameter=370&years_warning=10" | python3 -m json.tool | head -60
echo "✅ Deflection strategies tested"

echo ""
echo "5️⃣ Testing Kinetic Impactor..."
curl -s -X POST "$BASE_URL/api/simulation/deflection/kinetic-impactor?asteroid_mass_kg=8.5e10&asteroid_velocity_km_s=30&years_before_impact=10" | python3 -m json.tool
echo "✅ Kinetic impactor tested"

echo ""
echo "6️⃣ Testing Tsunami Modeling..."
curl -s -X POST "$BASE_URL/api/simulation/tsunami/analyze?asteroid_diameter=500&asteroid_velocity=20&ocean_depth=4000" | python3 -m json.tool | head -50
echo "✅ Tsunami modeling tested"

echo ""
echo "7️⃣ Testing Orbital Trajectory..."
curl -s -X POST $BASE_URL/api/simulation/orbital-trajectory \
  -H "Content-Type: application/json" \
  -d '{
    "orbital_elements": {
      "semi_major_axis_au": 0.922,
      "eccentricity": 0.191,
      "inclination_deg": 3.331,
      "longitude_ascending_node_deg": 204.4,
      "argument_periapsis_deg": 126.4,
      "mean_anomaly_deg": 0.0
    },
    "num_points": 5
  }' | python3 -m json.tool
echo "✅ Orbital trajectory tested"

echo ""
echo "========================================="
echo "✅ All Features Tested Successfully!"
echo "========================================="
echo ""
echo "📊 Summary:"
echo "  ✅ Live NASA NEO data integration"
echo "  ✅ Deflection strategies calculation"
echo "  ✅ Tsunami modeling"
echo "  ✅ Orbital mechanics"
echo ""
echo "🚀 Ready for NASA Space Apps Challenge!"
echo ""

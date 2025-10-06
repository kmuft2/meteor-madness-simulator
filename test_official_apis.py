#!/usr/bin/env python3
"""
Test script for official NASA and USGS APIs
Validates connectivity and data retrieval before building the main application
"""

import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_nasa_neo_api():
    """Test official NASA NEO API"""
    api_key = os.getenv('NASA_API_KEY', 'DEMO_KEY')
    url = f"https://api.nasa.gov/neo/rest/v1/stats?api_key={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("✅ NASA NEO API: Connected successfully")
        print(f"   Near Earth Objects: {data.get('near_earth_object_count', 'N/A')}")
        print(f"   Last updated: {data.get('last_updated', 'N/A')}")
        return True, data
    except Exception as e:
        print(f"❌ NASA NEO API: Failed - {e}")
        return False, None

def test_nasa_sbdb_api():
    """Test official NASA Small-Body Database API"""
    url = "https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=433"  # Test with asteroid Eros
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("✅ NASA SBDB API: Connected successfully")
        print(f"   Test object: {data.get('object', {}).get('fullname', 'N/A')}")
        print(f"   Orbital data available: {bool(data.get('orbit', {}))}")
        return True, data
    except Exception as e:
        print(f"❌ NASA SBDB API: Failed - {e}")
        return False, None

def test_usgs_earthquake_api():
    """Test official USGS Earthquake API"""
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=1&minmagnitude=6"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("✅ USGS Earthquake API: Connected successfully")
        print(f"   Features returned: {len(data.get('features', []))}")
        if data.get('features'):
            feature = data['features'][0]
            props = feature.get('properties', {})
            print(f"   Latest major quake: {props.get('title', 'N/A')}")
        return True, data
    except Exception as e:
        print(f"❌ USGS Earthquake API: Failed - {e}")
        return False, None

def test_nasa_neo_feed():
    """Test NASA NEO feed for recent asteroids"""
    api_key = os.getenv('NASA_API_KEY', 'DEMO_KEY')
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        element_count = data.get('element_count', 0)
        print("✅ NASA NEO Feed: Connected successfully")
        print(f"   Asteroids in last 3 days: {element_count}")
        
        # Get first asteroid details
        neo_objects = data.get('near_earth_objects', {})
        if neo_objects:
            first_date = list(neo_objects.keys())[0]
            if neo_objects[first_date]:
                first_asteroid = neo_objects[first_date][0]
                print(f"   Sample asteroid: {first_asteroid.get('name', 'N/A')}")
                print(f"   Potentially hazardous: {first_asteroid.get('is_potentially_hazardous_asteroid', False)}")
        
        return True, data
    except Exception as e:
        print(f"❌ NASA NEO Feed: Failed - {e}")
        return False, None

def save_sample_data(filename, data):
    """Save sample API response for offline testing"""
    import json
    cache_dir = "data/cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    filepath = os.path.join(cache_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"   💾 Saved sample data to {filepath}")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Official NASA/USGS APIs")
    print("=" * 60)
    print()
    
    results = []
    
    # Test NASA NEO Stats
    print("1. Testing NASA NEO Statistics API...")
    success, data = test_nasa_neo_api()
    results.append(success)
    if success and data:
        save_sample_data("nasa_neo_stats.json", data)
    print()
    
    # Test NASA SBDB
    print("2. Testing NASA Small-Body Database API...")
    success, data = test_nasa_sbdb_api()
    results.append(success)
    if success and data:
        save_sample_data("nasa_sbdb_sample.json", data)
    print()
    
    # Test USGS Earthquake
    print("3. Testing USGS Earthquake Catalog API...")
    success, data = test_usgs_earthquake_api()
    results.append(success)
    if success and data:
        save_sample_data("usgs_earthquake_sample.json", data)
    print()
    
    # Test NASA NEO Feed
    print("4. Testing NASA NEO Feed API...")
    success, data = test_nasa_neo_feed()
    results.append(success)
    if success and data:
        save_sample_data("nasa_neo_feed_sample.json", data)
    print()
    
    # Summary
    print("=" * 60)
    print(f"APIs Working: {sum(results)}/{len(results)}")
    print("=" * 60)
    
    if all(results):
        print("🎉 All official APIs are ready!")
        print("✅ Sample data cached for offline development")
        print()
        print("Next steps:")
        print("1. Install Python dependencies: pip install -r backend/requirements.txt")
        print("2. Begin backend development with FastAPI")
        print("3. Implement CUDA physics kernels")
    else:
        print("⚠️  Some APIs need attention")
        print("Check your NASA_API_KEY in .env file")
        print("Verify network connectivity")
        if sum(results) > 0:
            print(f"✅ {sum(results)} API(s) working - can proceed with limited functionality")

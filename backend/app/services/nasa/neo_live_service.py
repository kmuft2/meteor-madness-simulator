"""
Live NASA NEO (Near-Earth Object) API Integration
Fetches real-time asteroid data from NASA's NEO API
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class NASANEOLiveService:
    """Integration with NASA's live NEO API for real-time asteroid data"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.nasa.gov/neo/rest/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache_dir = Path("data/cache/neo")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_close_approaches_today(self) -> List[Dict]:
        """Get asteroids making close approaches today"""
        today = datetime.now().strftime('%Y-%m-%d')
        return await self.get_close_approaches(today, today)
    
    async def get_close_approaches(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Get asteroids making close approaches in date range
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        
        Returns:
            List of close approach objects with asteroid data
        """
        url = f"{self.base_url}/feed"
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "api_key": self.api_key
        }
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
            
            # Extract asteroid data from response
            asteroids = []
            near_earth_objects = data.get('near_earth_objects', {})
            
            for date, objects in near_earth_objects.items():
                for obj in objects:
                    asteroid_data = self._parse_neo_object(obj)
                    asteroids.append(asteroid_data)
            
            logger.info(f"Retrieved {len(asteroids)} NEO objects from {start_date} to {end_date}")
            return asteroids
            
        except Exception as e:
            logger.error(f"Failed to fetch NEO close approaches: {e}")
            return self._load_cached_neos()
    
    async def get_asteroid_by_id(self, asteroid_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific asteroid
        
        Args:
            asteroid_id: NASA NEO ID (e.g., "2099942" for Apophis)
        
        Returns:
            Detailed asteroid data with orbital elements
        """
        url = f"{self.base_url}/neo/{asteroid_id}"
        params = {"api_key": self.api_key}
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
            
            return self._parse_detailed_neo(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch asteroid {asteroid_id}: {e}")
            return None
    
    async def get_potentially_hazardous(self) -> List[Dict]:
        """Get list of potentially hazardous asteroids (PHAs)"""
        # Get next 7 days of close approaches
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        all_asteroids = await self.get_close_approaches(start_date, end_date)
        
        # Filter for potentially hazardous
        hazardous = [
            ast for ast in all_asteroids 
            if ast.get('is_potentially_hazardous_asteroid', False)
        ]
        
        logger.info(f"Found {len(hazardous)} potentially hazardous asteroids")
        return hazardous
    
    def _parse_neo_object(self, neo_data: Dict) -> Dict:
        """Parse NASA NEO API object into our format"""
        try:
            # Get first close approach data
            close_approach = neo_data.get('close_approach_data', [{}])[0]
            
            # Extract diameter (average of min/max)
            diameter_data = neo_data.get('estimated_diameter', {}).get('meters', {})
            diameter = (
                diameter_data.get('estimated_diameter_min', 0) + 
                diameter_data.get('estimated_diameter_max', 0)
            ) / 2
            
            # Extract velocity (km/s)
            velocity_data = close_approach.get('relative_velocity', {})
            velocity = float(velocity_data.get('kilometers_per_second', 20.0))
            
            # Extract close approach distance
            miss_distance = close_approach.get('miss_distance', {})
            distance_km = float(miss_distance.get('kilometers', 0))
            distance_au = float(miss_distance.get('astronomical', 0))
            
            # Orbital data
            orbital_data = neo_data.get('orbital_data', {})
            
            return {
                'id': neo_data.get('id'),
                'name': neo_data.get('name', 'Unknown'),
                'nasa_jpl_url': neo_data.get('nasa_jpl_url'),
                'absolute_magnitude': neo_data.get('absolute_magnitude_h', 0),
                'is_potentially_hazardous': neo_data.get('is_potentially_hazardous_asteroid', False),
                'diameter_meters': diameter,
                'velocity_km_s': velocity,
                'close_approach_date': close_approach.get('close_approach_date'),
                'miss_distance_km': distance_km,
                'miss_distance_au': distance_au,
                'orbiting_body': close_approach.get('orbiting_body', 'Earth'),
                'orbital_elements': {
                    'semi_major_axis_au': float(orbital_data.get('semi_major_axis', 1.0)),
                    'eccentricity': float(orbital_data.get('eccentricity', 0.1)),
                    'inclination_deg': float(orbital_data.get('inclination', 0)),
                    'longitude_ascending_node_deg': float(orbital_data.get('ascending_node_longitude', 0)),
                    'argument_periapsis_deg': float(orbital_data.get('perihelion_argument', 0)),
                    'mean_anomaly_deg': float(orbital_data.get('mean_anomaly', 0)),
                    'orbital_period_days': float(orbital_data.get('orbital_period', 365.0))
                },
                'data_source': 'NASA_NEO_API_Live'
            }
        except Exception as e:
            logger.error(f"Error parsing NEO object: {e}")
            return {}
    
    def _parse_detailed_neo(self, data: Dict) -> Dict:
        """Parse detailed NEO data"""
        return self._parse_neo_object(data)
    
    def _load_cached_neos(self) -> List[Dict]:
        """Load cached NEO data"""
        cache_file = self.cache_dir / "recent_neos.json"
        if cache_file.exists():
            logger.info(f"Loading NEO data from cache: {cache_file}")
            with open(cache_file, 'r') as f:
                return json.load(f)
        return []
    
    def _cache_neos(self, neos: List[Dict]):
        """Cache NEO data"""
        cache_file = self.cache_dir / "recent_neos.json"
        with open(cache_file, 'w') as f:
            json.dump(neos, f, indent=2)
        logger.info(f"Cached {len(neos)} NEO objects to {cache_file}")


async def test_neo_live_service():
    """Test NASA NEO live service"""
    import os
    api_key = os.getenv('NASA_API_KEY', 'DEMO_KEY')
    
    async with NASANEOLiveService(api_key) as neo_service:
        # Test today's close approaches
        print("\n🌍 Today's Close Approaches:")
        today_asteroids = await neo_service.get_close_approaches_today()
        for ast in today_asteroids[:5]:
            print(f"  - {ast['name']}: {ast['diameter_meters']:.1f}m, "
                  f"velocity {ast['velocity_km_s']:.1f} km/s, "
                  f"miss distance {ast['miss_distance_au']:.4f} AU")
        
        # Test Apophis lookup
        print("\n☄️ Apophis (99942) Details:")
        apophis = await neo_service.get_asteroid_by_id("2099942")
        if apophis:
            print(f"  Name: {apophis['name']}")
            print(f"  Diameter: {apophis['diameter_meters']:.1f}m")
            print(f"  Potentially Hazardous: {apophis['is_potentially_hazardous']}")
            print(f"  Orbital Period: {apophis['orbital_elements']['orbital_period_days']:.1f} days")


if __name__ == "__main__":
    asyncio.run(test_neo_live_service())

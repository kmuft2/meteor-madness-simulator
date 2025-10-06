"""
Integration with official NASA-recommended APIs
Implements NASA NEO API and Small-Body Database API
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp not available, using synchronous fallback")
    import urllib.request as request
    from urllib.parse import urlencode


class OfficialNASAAPIService:
    """Integration with official NASA-recommended APIs"""
    
    def __init__(self, api_key: str, neo_api_url: str, sbdb_api_url: str):
        self.api_key = api_key
        self.neo_api_url = neo_api_url.rstrip('/')
        self.sbdb_api_url = sbdb_api_url
        self.session: Optional[object] = None
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def __aenter__(self):
        if AIOHTTP_AVAILABLE:
            self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and AIOHTTP_AVAILABLE:
            await self.session.close()
    
    async def get_neo_feed_official(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get NEO data from official NASA API endpoint"""
        url = f"{self.neo_api_url}/feed"
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "api_key": self.api_key
        }
        
        try:
            if AIOHTTP_AVAILABLE and self.session:
                async with self.session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
            else:
                # Synchronous fallback
                from urllib.parse import urlencode
                full_url = f"{url}?{urlencode(params)}"
                with request.urlopen(full_url, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
            
        except Exception as e:
            logger.error(f"Failed to fetch official NEO data: {e}")
            # Try to load from cache
            return self._load_from_cache("nasa_neo_feed_sample.json")
    
    async def get_sbdb_asteroid_details(
        self,
        asteroid_id: str,
        include_covariance: bool = False,
        covariance_format: str = "mat",
    ) -> Dict:
        """Get detailed orbital parameters from official NASA SBDB"""
        params = {
            "sstr": asteroid_id,
            "full-prec": "true",
            "phys-par": "true"
        }

        if include_covariance:
            params["cov"] = covariance_format

        try:
            if AIOHTTP_AVAILABLE and self.session:
                async with self.session.get(self.sbdb_api_url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
            else:
                from urllib.parse import urlencode
                full_url = f"{self.sbdb_api_url}?{urlencode(params)}"
                with request.urlopen(full_url, timeout=10) as resp:
                    data = json.loads(resp.read().decode())

            return self._extract_official_keplerian_elements(data)
        except Exception as e:
            logger.error(f"Failed to fetch SBDB details for {asteroid_id}: {e}")
            return {}

    def _extract_official_keplerian_elements(self, sbdb_data: Dict) -> Dict:
        """Extract Keplerian orbital elements from official SBDB response"""
        orbit_data = sbdb_data.get("orbit", {})
        elements = orbit_data.get("elements", [])
        
        # Map SBDB element names to standard parameters
        element_mapping = {
            "e": "eccentricity",
            "a": "semi_major_axis_au",
            "i": "inclination_deg",
            "om": "longitude_ascending_node_deg",
            "w": "argument_periapsis_deg",
            "ma": "mean_anomaly_deg",
            "tp": "time_periapsis_jd",
            "per": "orbital_period_days"
        }
        
        keplerian_elements = {}
        for element in elements:
            sbdb_name = element.get("name")
            if sbdb_name in element_mapping:
                std_name = element_mapping[sbdb_name]
                try:
                    keplerian_elements[std_name] = float(element.get("value", 0))
                except (ValueError, TypeError):
                    pass

        covariance_data = orbit_data.get("covariance")
        covariance = None

        if covariance_data:
            matrix = covariance_data.get("data")
            labels = covariance_data.get("labels", [])
            epoch = covariance_data.get("epoch")
            elements_at_epoch = covariance_data.get("elements")

            covariance = {
                "matrix": matrix,
                "labels": labels,
                "epoch_jd": epoch,
                "elements": elements_at_epoch,
            }

        return {
            "object_id": sbdb_data.get("object", {}).get("des", ""),
            "object_name": sbdb_data.get("object", {}).get("fullname", ""),
            "keplerian_elements": keplerian_elements,
            "physical_parameters": self._extract_physical_params(sbdb_data),
            "covariance": covariance,
            "data_source": "NASA_SBDB_Official"
        }
    
    def _extract_physical_params(self, sbdb_data: Dict) -> Dict:
        """Extract physical parameters from SBDB data"""
        phys_data = sbdb_data.get("phys_par", [])
        
        physical_params = {}
        for param in phys_data:
            name = param.get("name", "")
            if name in ["H", "G", "diameter", "albedo", "rot_per"]:
                try:
                    physical_params[name] = float(param.get("value", 0))
                except (ValueError, TypeError):
                    pass
        
        return physical_params
    
    async def get_potentially_hazardous_asteroids(self, limit: int = 100) -> List[Dict]:
        """Get PHAs from official NASA data for realistic threat scenarios"""
        url = f"{self.neo_api_url}/browse"
        params = {
            "api_key": self.api_key,
            "is_potentially_hazardous_asteroid": "true",
            "size": min(limit, 100)
        }
        
        try:
            if AIOHTTP_AVAILABLE and self.session:
                async with self.session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
            else:
                from urllib.parse import urlencode
                full_url = f"{url}?{urlencode(params)}"
                with request.urlopen(full_url, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
            
            phas = []
            for neo in data.get("near_earth_objects", [])[:limit]:
                pha_data = {
                    **neo,
                    "is_pha": True,
                    "data_source": "NASA_Official_PHA_List"
                }
                phas.append(pha_data)
            
            return phas
        except Exception as e:
            logger.error(f"Failed to fetch PHAs: {e}")
            return []
    
    def _process_official_neo_data(self, raw_data: Dict) -> Dict:
        """Process official NEO API response"""
        processed = {"asteroids": [], "metadata": {}}
        
        processed["metadata"] = {
            "element_count": raw_data.get("element_count", 0),
            "data_source": "NASA_NEO_API_Official",
            "links": raw_data.get("links", {})
        }
        
        for date, asteroids in raw_data.get("near_earth_objects", {}).items():
            for asteroid in asteroids:
                processed_asteroid = {
                    "id": asteroid.get("id"),
                    "neo_reference_id": asteroid.get("neo_reference_id"),
                    "name": asteroid.get("name", "Unknown"),
                    "nasa_jpl_url": asteroid.get("nasa_jpl_url"),
                    "absolute_magnitude_h": float(asteroid.get("absolute_magnitude_h", 0)),
                    "is_potentially_hazardous": asteroid.get("is_potentially_hazardous_asteroid", False),
                    "estimated_diameter": asteroid.get("estimated_diameter", {}),
                    "close_approach_data": [],
                    "orbital_data": asteroid.get("orbital_data", {}),
                    "data_source": "NASA_Official"
                }
                
                for approach in asteroid.get("close_approach_data", []):
                    approach_data = {
                        "close_approach_date": approach.get("close_approach_date_full"),
                        "relative_velocity": approach.get("relative_velocity", {}),
                        "miss_distance": approach.get("miss_distance", {}),
                        "orbiting_body": approach.get("orbiting_body", "Earth")
                    }
                    processed_asteroid["close_approach_data"].append(approach_data)
                
                processed["asteroids"].append(processed_asteroid)
        
        return processed
    
    def _load_from_cache(self, filename: str) -> Dict:
        """Load data from cache file"""
        cache_file = self.cache_dir / filename
        if cache_file.exists():
            logger.info(f"Loading data from cache: {cache_file}")
            with open(cache_file, 'r') as f:
                return json.load(f)
        return {"asteroids": [], "metadata": {"data_source": "cache_unavailable"}}


# Standalone test function
async def test_official_nasa_integration():
    """Test official NASA API integration"""
    api_key = "YOUR_API_KEY"
    neo_url = "https://api.nasa.gov/neo/rest/v1/"
    sbdb_url = "https://ssd-api.jpl.nasa.gov/sbdb.api"
    
    start_date = datetime.now() - timedelta(days=2)
    end_date = datetime.now()
    
    async with OfficialNASAAPIService(api_key, neo_url, sbdb_url) as nasa_service:
        # Test NEO feed
        neo_data = await nasa_service.get_neo_feed_official(start_date, end_date)
        print(f"✅ Retrieved {len(neo_data['asteroids'])} asteroids from NASA NEO API")
        
        # Test SBDB integration
        if neo_data['asteroids']:
            first_asteroid = neo_data['asteroids'][0]
            sbdb_details = await nasa_service.get_sbdb_asteroid_details(first_asteroid['id'])
            print(f"✅ SBDB details for {first_asteroid['name']}: {bool(sbdb_details)}")
        
        # Test PHA list
        phas = await nasa_service.get_potentially_hazardous_asteroids(10)
        print(f"✅ Retrieved {len(phas)} potentially hazardous asteroids")


if __name__ == "__main__":
    asyncio.run(test_official_nasa_integration())

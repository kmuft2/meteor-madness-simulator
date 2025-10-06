"""
Integration with official USGS Earthquake Catalog for seismic correlation
"""

import asyncio
import json
import logging
import math
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    import urllib.request as request


class USGSEarthquakeService:
    """Integration with official USGS Earthquake Catalog for seismic correlation"""
    
    def __init__(self, earthquake_api_url: str):
        self.earthquake_api_url = earthquake_api_url.rstrip('/')
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
    
    async def get_reference_earthquakes(self, min_magnitude: float = 6.0, 
                                       max_magnitude: float = 9.5, 
                                       limit: int = 1000) -> List[Dict]:
        """Get reference earthquakes from USGS for impact energy comparison"""
        params = {
            "format": "geojson",
            "minmagnitude": min_magnitude,
            "maxmagnitude": max_magnitude,
            "limit": limit,
            "orderby": "magnitude-desc"
        }
        
        try:
            url = f"{self.earthquake_api_url}/query"
            
            if AIOHTTP_AVAILABLE and self.session:
                async with self.session.get(url, params=params) as response:
                    if response.status == 400:
                        logger.warning(f"USGS API returned 400 for magnitude range {min_magnitude}-{max_magnitude}. No data available.")
                        return []
                    response.raise_for_status()
                    data = await response.json()
            else:
                from urllib.parse import urlencode
                full_url = f"{url}?{urlencode(params)}"
                try:
                    with request.urlopen(full_url, timeout=10) as resp:
                        data = json.loads(resp.read().decode())
                except Exception as e:
                    if "400" in str(e):
                        logger.warning(f"USGS API returned 400 for magnitude range {min_magnitude}-{max_magnitude}. No data available.")
                        return []
                    raise
            
            earthquakes = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                coords = feature.get("geometry", {}).get("coordinates", [])
                
                earthquake = {
                    "id": feature.get("id"),
                    "magnitude": props.get("mag", 0),
                    "place": props.get("place", "Unknown"),
                    "time": props.get("time", 0),
                    "coordinates": coords,
                    "magnitude_type": props.get("magType", "unknown"),
                    "depth": coords[2] if len(coords) > 2 else 0,
                    "title": props.get("title", ""),
                    "url": props.get("url", ""),
                    "data_source": "USGS_Official"
                }
                earthquakes.append(earthquake)
            
            return earthquakes
        except Exception as e:
            logger.warning(f"Failed to fetch USGS earthquake data: {e}")
            # Try cache
            return self._load_from_cache()
    
    def impact_energy_to_seismic_magnitude(self, impact_energy_joules: float) -> Dict:
        """
        Convert asteroid impact energy to equivalent earthquake magnitude
        using USGS seismic moment magnitude scale
        
        Based on:
        - Seismic moment: M0 = (2/3) * log10(E) - 10.7 (for energy in ergs)
        - Moment magnitude: Mw = (2/3) * log10(M0) - 10.7
        """
        try:
            # Convert joules to ergs for seismic calculations
            energy_ergs = impact_energy_joules * 1e7
            
            # Seismic moment magnitude calculation
            # Approximation for impact-generated seismic energy
            if energy_ergs > 0:
                magnitude = (2.0/3.0) * math.log10(energy_ergs) - 10.7
            else:
                magnitude = 0.0
            
            # Ensure realistic bounds
            magnitude = max(0, min(magnitude, 12.0))
            
            return {
                "equivalent_magnitude": magnitude,
                "energy_joules": impact_energy_joules,
                "energy_ergs": energy_ergs,
                "calculation_method": "seismic_moment_approximation",
                "data_source": "USGS_scaling_laws"
            }
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating seismic magnitude: {e}")
            return {"equivalent_magnitude": 0, "error": str(e)}
    
    async def find_similar_magnitude_earthquakes(self, target_magnitude: float, 
                                                tolerance: float = 0.5) -> List[Dict]:
        """Find historical earthquakes with similar magnitude for comparison"""
        # USGS database only has modern earthquakes (max ~9.5)
        # For prehistoric/theoretical impacts, return empty list
        if target_magnitude > 9.0:
            logger.info(f"Magnitude {target_magnitude} exceeds USGS database range (max ~9.5). No comparison earthquakes available.")
            return []
        
        min_mag = max(0, target_magnitude - tolerance)
        max_mag = min(9.5, target_magnitude + tolerance)  # Cap at 9.5 (largest recorded)
        
        try:
            earthquakes = await self.get_reference_earthquakes(min_mag, max_mag, 50)
            
            # Sort by similarity to target magnitude
            earthquakes.sort(key=lambda eq: abs(eq["magnitude"] - target_magnitude))
            
            return earthquakes[:10]
        except Exception as e:
            logger.warning(f"Could not fetch similar earthquakes for magnitude {target_magnitude}: {e}")
            return []
    
    def get_earthquake_damage_description(self, magnitude: float) -> Dict:
        """Get damage scale description based on USGS Modified Mercalli Intensity"""
        if magnitude < 2.0:
            intensity = "I"
            description = "Not felt except by a very few under especially favorable conditions"
            damage = "None"
        elif magnitude < 3.0:
            intensity = "II-III"
            description = "Felt only by a few persons at rest, especially on upper floors"
            damage = "None"
        elif magnitude < 4.0:
            intensity = "IV"
            description = "Felt by many indoors, few outdoors. Dishes, windows disturbed"
            damage = "None to slight"
        elif magnitude < 5.0:
            intensity = "V-VI"
            description = "Felt by nearly everyone. Some dishes, windows broken"
            damage = "Slight"
        elif magnitude < 6.0:
            intensity = "VI-VII"
            description = "Felt by all, many frightened. Some heavy furniture moved"
            damage = "Slight to moderate"
        elif magnitude < 7.0:
            intensity = "VIII"
            description = "Damage slight in specially designed structures, considerable in ordinary buildings"
            damage = "Moderate to considerable"
        elif magnitude < 8.0:
            intensity = "IX"
            description = "Damage considerable in specially designed structures, great in substantial buildings"
            damage = "Considerable to severe"
        elif magnitude < 9.0:
            intensity = "X"
            description = "Some well-built wooden structures destroyed, most masonry structures destroyed"
            damage = "Severe to extreme"
        else:
            intensity = "XI-XII"
            description = "Few, if any structures remain standing. Ground waves visible"
            damage = "Extreme catastrophic"
        
        return {
            "magnitude": magnitude,
            "mercalli_intensity": intensity,
            "description": description,
            "expected_damage": damage,
            "reference": "USGS Modified Mercalli Intensity Scale"
        }
    
    def _load_from_cache(self) -> List[Dict]:
        """Load earthquake data from cache"""
        cache_file = self.cache_dir / "usgs_earthquake_sample.json"
        if cache_file.exists():
            logger.info(f"Loading USGS data from cache: {cache_file}")
            with open(cache_file, 'r') as f:
                data = json.load(f)
                earthquakes = []
                for feature in data.get("features", []):
                    props = feature.get("properties", {})
                    coords = feature.get("geometry", {}).get("coordinates", [])
                    earthquakes.append({
                        "id": feature.get("id"),
                        "magnitude": props.get("mag", 0),
                        "place": props.get("place", "Unknown"),
                        "time": props.get("time", 0),
                        "coordinates": coords,
                        "title": props.get("title", ""),
                        "data_source": "USGS_Cached"
                    })
                return earthquakes
        return []


# Test function
async def test_usgs_integration():
    """Test USGS earthquake service"""
    api_url = "https://earthquake.usgs.gov/fdsnws/event/1/"
    
    async with USGSEarthquakeService(api_url) as usgs_service:
        # Test earthquake data retrieval
        earthquakes = await usgs_service.get_reference_earthquakes(7.0, 9.0, 10)
        print(f"✅ Retrieved {len(earthquakes)} major earthquakes from USGS")
        
        # Test impact energy conversion
        test_energy = 1e15  # 1 petajoule (roughly 0.24 MT TNT)
        magnitude_data = usgs_service.impact_energy_to_seismic_magnitude(test_energy)
        print(f"✅ 1 PJ impact energy = {magnitude_data['equivalent_magnitude']:.1f} magnitude earthquake")
        
        # Test damage description
        damage_info = usgs_service.get_earthquake_damage_description(magnitude_data['equivalent_magnitude'])
        print(f"✅ Damage scale: {damage_info['mercalli_intensity']} - {damage_info['expected_damage']}")


if __name__ == "__main__":
    asyncio.run(test_usgs_integration())

"""
USGS Earthquake Cache - Offline earthquake data for comparison
Provides fast access to historical earthquake data without API calls
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Path to cached data (go up from backend/app/services/usgs/ to project root)
CACHE_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "cache"


class EarthquakeCacheService:
    """Access cached USGS earthquake data for impact correlation"""
    
    def __init__(self):
        self.major_quakes_file = CACHE_DIR / "usgs_major_earthquakes_7plus.json"
        self.great_quakes_file = CACHE_DIR / "usgs_great_earthquakes_8plus.json"
        self._cache = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load earthquake data into memory"""
        try:
            # Load 7.0+ earthquakes
            if self.major_quakes_file.exists():
                with open(self.major_quakes_file, 'r') as f:
                    data = json.load(f)
                    self._cache['major'] = data.get('features', [])
                    logger.info(f"Loaded {len(self._cache['major'])} major earthquakes (7.0+)")
            
            # Load 8.0+ earthquakes
            if self.great_quakes_file.exists():
                with open(self.great_quakes_file, 'r') as f:
                    data = json.load(f)
                    self._cache['great'] = data.get('features', [])
                    logger.info(f"Loaded {len(self._cache['great'])} great earthquakes (8.0+)")
        
        except Exception as e:
            logger.error(f"Error loading earthquake cache: {e}")
            self._cache = {'major': [], 'great': []}
    
    def find_similar_magnitude(self, target_magnitude: float, tolerance: float = 0.5) -> List[Dict]:
        """
        Find earthquakes with similar magnitude to an asteroid impact
        
        Args:
            target_magnitude: Target earthquake magnitude
            tolerance: +/- tolerance for matching
        
        Returns:
            List of similar earthquakes with context
        """
        min_mag = target_magnitude - tolerance
        max_mag = target_magnitude + tolerance
        
        # Search appropriate cache
        cache_key = 'great' if target_magnitude >= 8.0 else 'major'
        quakes = self._cache.get(cache_key, [])
        
        similar = []
        for feature in quakes:
            props = feature['properties']
            mag = props.get('mag', 0)
            
            if min_mag <= mag <= max_mag:
                # Extract key information
                coords = feature.get('geometry', {}).get('coordinates', [0, 0, 0])
                
                earthquake = {
                    "magnitude": mag,
                    "magnitude_type": props.get('magType', 'unknown'),
                    "location": props.get('place', 'Unknown'),
                    "year": self._timestamp_to_year(props.get('time', 0)),
                    "date": self._timestamp_to_date(props.get('time', 0)),
                    "latitude": coords[1] if len(coords) > 1 else 0,
                    "longitude": coords[0] if len(coords) > 0 else 0,
                    "depth_km": coords[2] if len(coords) > 2 else 0,
                    "url": props.get('url', ''),
                    "tsunami": props.get('tsunami', 0) == 1,
                    "felt_reports": props.get('felt', 0),
                    "cdi": props.get('cdi'),  # Community Decimal Intensity
                    "mmi": props.get('mmi'),  # Modified Mercalli Intensity
                    "historical_context": self._get_historical_context(
                        mag, 
                        self._timestamp_to_year(props.get('time', 0)),
                        props.get('place', '')
                    )
                }
                
                similar.append(earthquake)
        
        # Sort by magnitude (descending)
        similar.sort(key=lambda x: x['magnitude'], reverse=True)
        
        return similar[:10]  # Return top 10 matches
    
    def get_famous_earthquakes(self) -> List[Dict]:
        """Get list of famous historical earthquakes for context"""
        famous = []
        
        for feature in self._cache.get('great', []):
            props = feature['properties']
            mag = props.get('mag', 0)
            place = props.get('place', '').lower()
            year = self._timestamp_to_year(props.get('time', 0))
            
            context = None
            
            # Identify famous earthquakes
            if ('sumatra' in place or 'andaman' in place) and year == 2004:
                context = "2004 Indian Ocean Tsunami - 230,000+ deaths"
            elif 'japan' in place and year == 2011:
                context = "2011 Tōhoku Japan - Fukushima nuclear disaster"
            elif 'chile' in place and year == 2010 and mag >= 8.5:
                context = "2010 Chile - 500+ deaths, $30B damage"
            elif 'alaska' in place and mag >= 8.0:
                context = f"{year} Alaska - Major seismic event"
            elif 'peru' in place and year == 2001:
                context = "2001 Peru - Magnitude 8.4"
            
            if context:
                famous.append({
                    "magnitude": mag,
                    "year": year,
                    "location": props.get('place'),
                    "context": context
                })
        
        return sorted(famous, key=lambda x: x['magnitude'], reverse=True)
    
    def get_magnitude_range_stats(self, min_mag: float, max_mag: float) -> Dict:
        """Get statistics for earthquakes in a magnitude range"""
        quakes = self._cache.get('major', []) + self._cache.get('great', [])
        
        in_range = [
            f['properties']['mag'] 
            for f in quakes 
            if min_mag <= f['properties'].get('mag', 0) <= max_mag
        ]
        
        if not in_range:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "average": 0
            }
        
        return {
            "count": len(in_range),
            "min": min(in_range),
            "max": max(in_range),
            "average": sum(in_range) / len(in_range),
            "magnitude_range": f"{min_mag}-{max_mag}"
        }
    
    def _timestamp_to_year(self, timestamp: int) -> int:
        """Convert millisecond timestamp to year"""
        from datetime import datetime
        try:
            return datetime.fromtimestamp(timestamp / 1000).year
        except:
            return 0
    
    def _timestamp_to_date(self, timestamp: int) -> str:
        """Convert millisecond timestamp to date string"""
        from datetime import datetime
        try:
            return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
        except:
            return "Unknown"
    
    def _get_historical_context(self, mag: float, year: int, place: str) -> str:
        """Add historical context for famous earthquakes"""
        place = place.lower()
        
        if ('sumatra' in place or 'andaman' in place) and year == 2004:
            return "2004 Indian Ocean Tsunami - One of deadliest disasters in history"
        elif 'japan' in place and year == 2011:
            return "2011 Tōhoku - Triggered Fukushima nuclear disaster"
        elif 'chile' in place and year == 2010 and mag >= 8.5:
            return "2010 Chile - 8th strongest earthquake ever recorded"
        elif 'alaska' in place and mag >= 8.0:
            return f"{year} Alaska - Major seismic event"
        elif mag >= 8.5:
            return "Great earthquake - Extreme seismic event"
        elif mag >= 8.0:
            return "Great earthquake - Major disaster potential"
        elif mag >= 7.5:
            return "Major earthquake - Significant damage expected"
        else:
            return ""


# Global instance
_earthquake_cache = None

def get_earthquake_cache() -> EarthquakeCacheService:
    """Get or create the global earthquake cache instance"""
    global _earthquake_cache
    if _earthquake_cache is None:
        _earthquake_cache = EarthquakeCacheService()
    return _earthquake_cache


# Example usage
if __name__ == "__main__":
    cache = get_earthquake_cache()
    
    print("Testing Earthquake Cache Service")
    print("=" * 70)
    
    # Test 1: Find similar to Tunguska (magnitude ~5.0)
    print("\n1. Earthquakes similar to Tunguska impact (~5.0 magnitude):")
    similar = cache.find_similar_magnitude(5.0, tolerance=0.5)
    print(f"   Found: {len(similar)} similar earthquakes")
    
    # Test 2: Find similar to large impact (magnitude 7.5)
    print("\n2. Earthquakes similar to large asteroid impact (~7.5 magnitude):")
    similar = cache.find_similar_magnitude(7.5, tolerance=0.5)
    for eq in similar[:3]:
        print(f"   {eq['magnitude']:.1f} - {eq['location']} ({eq['year']})")
        if eq['historical_context']:
            print(f"        {eq['historical_context']}")
    
    # Test 3: Famous earthquakes
    print("\n3. Famous historical earthquakes:")
    famous = cache.get_famous_earthquakes()
    for eq in famous[:5]:
        print(f"   {eq['magnitude']:.1f} ({eq['year']}) - {eq['context']}")
    
    print("\n" + "=" * 70)
    print("✅ Earthquake cache working correctly!")


"""
WorldPop 2020 Population Data Service
Loads real population density data by country for accurate casualty estimates
Uses 1km resolution ASCII XYZ CSV data
Uses BigDataCloud free reverse geocoding API for country detection
"""

import logging
import csv
import math
import os
import requests
from typing import Dict, List, Optional
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)

# BigDataCloud free reverse geocoding API (no auth required)
REVERSE_GEOCODE_API = "https://api.bigdatacloud.net/data/reverse-geocode-client"
GEOCODE_CACHE = {}  # Cache geocoding results to minimize API calls

# ISO code mappings (loaded from file)
ISO2_TO_ISO3: Dict[str, str] = {}


def _load_iso_mappings() -> Dict[str, str]:
    """
    Load ISO-2 to ISO-3 country code mappings from iso-translations.txt
    
    Returns:
        Dict mapping ISO-2 codes (US) to ISO-3 codes (USA)
    """
    iso_file = Path(__file__).parent.parent.parent.parent / "data" / "iso-translations.txt"
    mappings = {}
    
    try:
        with open(iso_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('Country'):  # Skip header
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 3:
                    # Format: Country\tAlpha-2\tAlpha-3\tNumeric
                    iso2 = parts[1].strip()
                    iso3 = parts[2].strip()
                    if iso2 and iso3:
                        mappings[iso2] = iso3
        
        logger.info(f"Loaded {len(mappings)} ISO country code mappings")
        return mappings
    
    except FileNotFoundError:
        logger.warning(f"ISO translations file not found: {iso_file}, using fallback")
        # Fallback to essential codes if file not found
        return {
            'US': 'USA', 'CN': 'CHN', 'IN': 'IND', 'BR': 'BRA',
            'RU': 'RUS', 'JP': 'JPN', 'DE': 'DEU', 'GB': 'GBR',
            'FR': 'FRA', 'MX': 'MEX', 'IT': 'ITA', 'ES': 'ESP',
            'CA': 'CAN', 'AU': 'AUS'
        }
    except Exception as e:
        logger.error(f"Error loading ISO mappings: {e}")
        return {}


# Load ISO mappings at module initialization
ISO2_TO_ISO3 = _load_iso_mappings()


class PopulationDataService:
    """Service for loading and querying WorldPop 2020 population data"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Use environment variable or relative path from backend directory
            data_dir = os.environ.get('WORLDPOP_DATA_DIR', '../data/worldpop_2020')
        
        self.data_dir = Path(data_dir).resolve()
        self.cache = {}  # Cache loaded country data
        self.cache_size_limit = 3  # Keep max 3 countries in memory
        
        if not self.data_dir.exists():
            logger.warning(f"WorldPop data directory not found: {self.data_dir}")
    
    def _get_country_code(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Determine country code and location info using BigDataCloud reverse geocoding API
        Returns dict with country_code, city, state, etc.
        """
        # Check cache first (round to 2 decimal places for cache key)
        cache_key = (round(latitude, 2), round(longitude, 2))
        if cache_key in GEOCODE_CACHE:
            return GEOCODE_CACHE[cache_key]
        
        try:
            # Call BigDataCloud free API (no auth required)
            response = requests.get(
                REVERSE_GEOCODE_API,
                params={'latitude': latitude, 'longitude': longitude},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant fields
                country_code = data.get('countryCode', 'UNKNOWN')
                
                # Get ocean name safely
                ocean_name = None
                if not country_code:
                    try:
                        locality_info = data.get('localityInfo', {})
                        admin_list = locality_info.get('administrative', [])
                        if admin_list and len(admin_list) > 0:
                            ocean_name = admin_list[0].get('name')
                    except (KeyError, IndexError, TypeError):
                        ocean_name = 'Ocean'
                
                # Map ISO-2 to ISO-3 using loaded mappings
                iso3_code = ISO2_TO_ISO3.get(country_code, country_code) if country_code else 'OCEAN'
                
                location_info = {
                    'country_code': iso3_code,
                    'country_code_iso2': country_code if country_code else None,
                    'country_name': data.get('countryName') if country_code else (ocean_name or 'Ocean'),
                    'city': data.get('city') or data.get('locality') or data.get('principalSubdivision'),
                    'state': data.get('principalSubdivision'),
                    'continent': data.get('continent'),
                    'ocean': ocean_name or 'International Waters',
                    'is_ocean': not bool(country_code),
                    'latitude': latitude,
                    'longitude': longitude
                }
                
                # Cache result
                GEOCODE_CACHE[cache_key] = location_info
                
                logger.debug(f"Geocoded {latitude},{longitude} -> {location_info['country_name']} ({location_info['country_code']})")
                return location_info
            else:
                logger.warning(f"Geocoding API returned status {response.status_code}")
                return None
        
        except requests.exceptions.Timeout:
            logger.warning(f"Geocoding API timeout for {latitude},{longitude}")
            return None
        except Exception as e:
            logger.warning(f"Geocoding failed: {e}")
            return None
    
    def _load_country_data(self, country_code: str) -> Optional[Dict]:
        """Load population data for a country into memory grid"""
        if country_code in self.cache:
            return self.cache[country_code]
        
        csv_file = self.data_dir / country_code.upper() / f"{country_code.lower()}_pd_2020_1km_ASCII_XYZ.csv"
        
        if not csv_file.exists():
            logger.warning(f"Population data file not found: {csv_file}")
            return None
        
        logger.info(f"Loading population data for {country_code}...")
        
        grid = defaultdict(float)
        count = 0
        total_pop = 0
        
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        lon = float(row['X'])
                        lat = float(row['Y'])
                        pop_density = float(row['Z'])
                        
                        if pop_density > 0:
                            key = (round(lat, 2), round(lon, 2))
                            grid[key] += pop_density
                            total_pop += pop_density
                            count += 1
                    except (ValueError, KeyError):
                        continue
                    
                    if count % 1000000 == 0:
                        logger.info(f"  Loaded {count:,} cells...")
        
        except Exception as e:
            logger.error(f"Error loading {country_code}: {e}")
            return None
        
        logger.info(f"✓ Loaded {count:,} cells, {total_pop:,.0f} total population for {country_code}")
        
        country_data = {
            'grid': dict(grid),
            'cell_count': count,
            'total_population': total_pop,
            'resolution_deg': 0.01
        }
        
        if len(self.cache) >= self.cache_size_limit:
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        
        self.cache[country_code] = country_data
        return country_data
    
    def get_population_in_zones(
        self,
        latitude: float,
        longitude: float,
        zone_radii_km: List[float],
        country_code: Optional[str] = None
    ) -> Dict:
        """
        Get population in concentric damage zones using real data
        
        Args:
            latitude: Impact center
            longitude: Impact center
            zone_radii_km: Damage zone radii (sorted smallest to largest)
            country_code: Optional country override
            
        Returns:
            Dict with population per zone and location info
        """
        # Get location info from geocoding API
        location_info = None
        if country_code is None:
            location_info = self._get_country_code(latitude, longitude)
            if location_info is None:
                return self._get_fallback_zones(latitude, longitude, zone_radii_km)
            country_code = location_info['country_code']
        
        # Try to load country data
        country_data = self._load_country_data(country_code)
        if country_data is None:
            result = self._get_fallback_zones(latitude, longitude, zone_radii_km)
            # Add location info if available
            if location_info:
                result['location_info'] = location_info
            return result
        
        grid = country_data['grid']
        resolution = country_data['resolution_deg']
        sorted_radii = sorted(zone_radii_km)
        max_radius = sorted_radii[-1]
        
        # Bounding box for largest radius
        lat_range = max_radius / 111.0
        lon_range = max_radius / (111.0 * math.cos(math.radians(latitude)))
        
        lat_min = latitude - lat_range
        lat_max = latitude + lat_range
        lon_min = longitude - lon_range
        lon_max = longitude + lon_range
        
        # Accumulate populations
        zone_populations = [0.0] * len(sorted_radii)
        
        lat = lat_min
        while lat <= lat_max:
            lon = lon_min
            while lon <= lon_max:
                dist_km = self._haversine_distance(latitude, longitude, lat, lon)
                
                # Check if this cell is within the largest radius
                if dist_km <= max_radius:
                    key = (round(lat, 2), round(lon, 2))
                    pop = grid.get(key, 0)
                    
                    if pop > 0:
                        # Add population to ALL zones that contain this cell
                        for i, radius in enumerate(sorted_radii):
                            if dist_km <= radius:
                                zone_populations[i] += pop
                
                lon += resolution
            lat += resolution
        
        # Build zone results
        zones = []
        for i, radius in enumerate(sorted_radii):
            annular_pop = zone_populations[i]
            if i > 0:
                annular_pop -= zone_populations[i-1]
            
            zones.append({
                'radius_km': radius,
                'cumulative_population': int(zone_populations[i]),
                'annular_population': int(annular_pop),
                'area_km2': math.pi * radius ** 2
            })
        
        result = {
            'country_code': country_code,
            'center': {'latitude': latitude, 'longitude': longitude},
            'zones': zones,
            'total_affected': int(zone_populations[-1]),
            'data_source': f'WorldPop_2020_{country_code}'
        }
        
        # Add detailed location info if available
        if location_info:
            result['location_info'] = location_info
        
        return result
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km using Haversine formula"""
        R = 6371.0
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _get_fallback_zones(self, lat: float, lon: float, radii: List[float]) -> Dict:
        """Fallback using global average density (~60/km²)"""
        zones = []
        prev_pop = 0
        
        for radius in sorted(radii):
            area_km2 = math.pi * radius ** 2
            cumulative_pop = int(area_km2 * 60)
            annular_pop = cumulative_pop - prev_pop
            
            zones.append({
                'radius_km': radius,
                'cumulative_population': cumulative_pop,
                'annular_population': annular_pop,
                'area_km2': area_km2
            })
            prev_pop = cumulative_pop
        
        return {
            'country_code': 'UNKNOWN',
            'center': {'latitude': lat, 'longitude': lon},
            'zones': zones,
            'total_affected': prev_pop,
            'data_source': 'FALLBACK_GLOBAL_AVERAGE'
        }


# Singleton
_population_service = None

def get_population_service() -> PopulationDataService:
    """Get singleton population service instance"""
    global _population_service
    if _population_service is None:
        _population_service = PopulationDataService()
    return _population_service

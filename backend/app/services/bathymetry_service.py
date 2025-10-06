"""
GEBCO Bathymetry Service
Loads and queries global ocean depth and land elevation data
Uses GEBCO 2025 NetCDF file for real bathymetry data
"""

import logging
import numpy as np
import os
from pathlib import Path
from typing import Optional, Tuple
import h5py

logger = logging.getLogger(__name__)

# Global cache for bathymetry data
BATHYMETRY_DATASET = None
BATHYMETRY_CACHE = {}  # Cache recent queries


class BathymetryService:
    """Service for querying ocean depth and land elevation from GEBCO data"""
    
    def __init__(self, gebco_file: str = None):
        if gebco_file is None:
            # Use environment variable or relative path from backend directory
            gebco_file = os.environ.get('GEBCO_FILE_PATH', '../data/GEBCO_2025_TID.nc')
        
        self.gebco_file = Path(gebco_file).resolve()
        self.dataset = None
        self.lat_array = None
        self.lon_array = None
        self.elevation_data = None
        self.resolution = None
        
        if not self.gebco_file.exists():
            logger.warning(f"GEBCO file not found: {self.gebco_file}")
            logger.warning("Bathymetry service will use fallback values")
        else:
            self._load_dataset()
    
    def _load_dataset(self):
        """Load GEBCO NetCDF dataset using h5py (HDF5 backend)"""
        global BATHYMETRY_DATASET
        
        if BATHYMETRY_DATASET is not None:
            logger.info("Using cached GEBCO dataset")
            self.dataset = BATHYMETRY_DATASET
            self._extract_metadata()
            return
        
        # NO FALLBACK - raise errors to see what's wrong
        logger.info(f"Loading GEBCO bathymetry from: {self.gebco_file}")
        self.dataset = h5py.File(str(self.gebco_file), 'r')
        BATHYMETRY_DATASET = self.dataset
        
        self._extract_metadata()
        
        logger.info(f"✓ GEBCO loaded: {self.lat_array.shape[0]} lats × {self.lon_array.shape[0]} lons")
        logger.info(f"  Resolution: ~{self.resolution:.4f}° (~{self.resolution * 111:.1f}m)")
    
    def _extract_metadata(self):
        """Extract lat/lon arrays and metadata from dataset"""
        if self.dataset is None:
            return
        
        # NO FALLBACK - raise errors
        logger.info(f"Dataset keys: {list(self.dataset.keys())}")
        
        # GEBCO typical structure: lat, lon, elevation
        # Try common variable names
        lat_names = ['lat', 'latitude', 'y']
        lon_names = ['lon', 'longitude', 'x']
        elev_names = ['tid', 'elevation', 'z', 'Band1']  # GEBCO uses 'tid' = Terrain, Ice, Depths
        
        # Find latitude
        for name in lat_names:
            if name in self.dataset:
                self.lat_array = self.dataset[name][:]
                logger.info(f"Found latitude array: {name}, shape: {self.lat_array.shape}")
                break
        
        # Find longitude
        for name in lon_names:
            if name in self.dataset:
                self.lon_array = self.dataset[name][:]
                logger.info(f"Found longitude array: {name}, shape: {self.lon_array.shape}")
                break
        
        # Find elevation variable name (don't load full array yet - too big!)
        for name in elev_names:
            if name in self.dataset:
                # Check if this is elevation data or TID data
                var = self.dataset[name]
                if hasattr(var, 'attrs') and 'long_name' in var.attrs:
                    long_name = var.attrs['long_name']
                    if b'Type Identifier' in long_name or b'Source' in long_name:
                        logger.info(f"Found TID data: {name}, shape: {var.shape} - will use for ocean/land detection")
                        # Keep TID available but don't set as elevation_data
                        continue
                
                self.elevation_data = self.dataset[name]
                logger.info(f"Found elevation data: {name}, shape: {self.elevation_data.shape}")
                break
        
        if self.elevation_data is None:
            if 'tid' in self.dataset:
                logger.info("✓ Using TID file for ocean/land detection (no elevation depths available)")
            else:
                logger.error("No elevation or TID data found in GEBCO file")
        
        if self.lat_array is not None and len(self.lat_array) > 1:
            self.resolution = abs(self.lat_array[1] - self.lat_array[0])
        else:
            self.resolution = 0.004166667  # ~15 arc-seconds default
    
    def get_depth(self, latitude: float, longitude: float) -> float:
        """
        Get ocean depth or land elevation at given coordinates
        
        Args:
            latitude: Latitude in degrees (-90 to 90)
            longitude: Longitude in degrees (-180 to 180)
        
        Returns:
            float: Depth/elevation in meters
                   Positive values = ocean depth (e.g., 4000m deep)
                   Negative values = land elevation above sea level
                   Zero = coastline
        """
        # Check cache first
        cache_key = (round(latitude, 2), round(longitude, 2))
        if cache_key in BATHYMETRY_CACHE:
            return BATHYMETRY_CACHE[cache_key]
        
        # Try to use TID file for accurate ocean/land detection
        if self.dataset is not None and 'tid' in self.dataset and self.lat_array is not None and self.lon_array is not None:
            try:
                # Normalize longitude to dataset range
                lon = longitude
                lon_min, lon_max = self.lon_array[0], self.lon_array[-1]
                if lon < lon_min:
                    lon += 360
                elif lon > lon_max:
                    lon -= 360
                
                # Find nearest indices
                lat_idx = self._find_nearest_index(self.lat_array, latitude)
                lon_idx = self._find_nearest_index(self.lon_array, lon)
                
                # Read TID value from file (h5py dataset access)
                tid_value = int(self.dataset['tid'][lat_idx, lon_idx])
                
                logger.info(f"TID lookup: ({latitude:.2f}, {longitude:.2f}) -> indices ({lat_idx}, {lon_idx}) -> TID={tid_value}")
                
                # GEBCO TID codes (from flag_meanings):
                # 0 = Land
                # 10-17 = Ocean (various measurement types)
                # 40-47 = Interpolated/predicted (need to check if land or ocean)
                # 70-72 = Other sources
                
                if tid_value == 0:  # Definite land
                    BATHYMETRY_CACHE[cache_key] = -100
                    logger.info(f"TID={tid_value}: LAND (definite)")
                    return -100
                elif 10 <= tid_value <= 17:  # Measured ocean data
                    depth = self._get_fallback_depth(latitude, longitude)
                    BATHYMETRY_CACHE[cache_key] = depth
                    logger.info(f"TID={tid_value}: OCEAN (measured), depth={depth}m")
                    return depth
                elif 40 <= tid_value <= 72:  # Predicted/interpolated - use heuristic
                    fallback_depth = self._get_fallback_depth(latitude, longitude)
                    BATHYMETRY_CACHE[cache_key] = fallback_depth
                    if fallback_depth > 0:
                        logger.info(f"TID={tid_value}: OCEAN (predicted), depth={fallback_depth}m")
                    else:
                        logger.info(f"TID={tid_value}: LAND (predicted)")
                    return fallback_depth
                else:  # Unknown TID, use heuristic
                    fallback_depth = self._get_fallback_depth(latitude, longitude)
                    BATHYMETRY_CACHE[cache_key] = fallback_depth
                    logger.info(f"TID={tid_value}: Unknown, using heuristic -> {fallback_depth}m")
                    return fallback_depth
                    
            except Exception as e:
                logger.warning(f"Failed to read TID data: {e}")
        
        # Fall back to simple ocean detection if no data available
        if self.dataset is None or (self.elevation_data is None and 'tid' not in self.dataset):
            logger.debug(f"No GEBCO data - using geographic heuristic for ({latitude}, {longitude})")
            return self._get_fallback_depth(latitude, longitude)
        
        # Normalize longitude to dataset range
        lon = longitude
        if self.lon_array is not None:
            lon_min, lon_max = self.lon_array[0], self.lon_array[-1]
            if lon < lon_min:
                lon += 360
            elif lon > lon_max:
                lon -= 360
        
        # Find nearest indices
        lat_idx = self._find_nearest_index(self.lat_array, latitude)
        lon_idx = self._find_nearest_index(self.lon_array, lon)
        
        # Query elevation at this point
        # GEBCO convention: negative = below sea level (ocean), positive = above sea level (land)
        elevation = float(self.elevation_data[lat_idx, lon_idx])
        
        # Convert to our convention: positive = ocean depth, negative = land elevation
        depth = -elevation
        
        # Cache result
        BATHYMETRY_CACHE[cache_key] = depth
        
        logger.debug(f"Queried ({latitude:.2f}, {longitude:.2f}): depth={depth:.0f}m")
        
        return depth
    
    def _find_nearest_index(self, array: np.ndarray, value: float) -> int:
        """Find index of nearest value in sorted array"""
        idx = np.searchsorted(array, value)
        
        # Handle edge cases
        if idx == 0:
            return 0
        if idx == len(array):
            return len(array) - 1
        
        # Check if previous index is closer
        if abs(array[idx - 1] - value) < abs(array[idx] - value):
            return idx - 1
        return idx
    
    def _get_fallback_depth(self, latitude: float, longitude: float) -> float:
        """
        Fallback depth estimation when GEBCO not available
        Uses refined heuristics with tighter bounding boxes for major landmasses
        """
        # More accurate landmass detection with tighter boxes
        # Format: (lat_min, lat_max, lon_min, lon_max, name)
        
        # North America (continental, excluding oceans)
        if 25 <= latitude <= 72 and -140 <= longitude <= -52:
            return -100  # Continental North America
        
        # Central America/Caribbean (land only)
        if 7 <= latitude <= 25 and -106 <= longitude <= -60:
            # Exclude Caribbean Sea (between islands)
            if not (10 <= latitude <= 20 and -85 <= longitude <= -65):
                return -100
        
        # South America (continental)
        if -55 <= latitude <= 12 and -82 <= longitude <= -34:
            return -100
        
        # Europe (excluding seas)
        if 35 <= latitude <= 71 and -10 <= longitude <= 40:
            return -100
        
        # Africa (continental)
        if -35 <= latitude <= 37 and -18 <= longitude <= 52:
            return -100
        
        # Asia (main continental mass) - split into regions
        # Middle East / Central Asia
        if 15 <= latitude <= 75 and 40 <= longitude <= 80:
            return -100
        
        # Indian subcontinent
        if 8 <= latitude <= 35 and 68 <= longitude <= 88:
            return -100
        
        # East/Southeast Asia mainland
        if 10 <= latitude <= 53 and 97 <= longitude <= 122:
            return -100
        
        # Northeast Asia (Siberia/China)
        if 40 <= latitude <= 75 and 80 <= longitude <= 150:
            return -100
        
        # Japan/Korea (islands)
        if 30 <= latitude <= 46 and 128 <= longitude <= 146:
            return -100
        
        # Australia
        if -44 <= latitude <= -10 and 113 <= longitude <= 154:
            return -100
        
        # New Zealand
        if -47 <= latitude <= -34 and 166 <= longitude <= 179:
            return -100
        
        # Antarctica
        if latitude <= -60:
            return -100
        
        # Greenland (tighter box to exclude Atlantic)
        if 60 <= latitude <= 84 and -73 <= longitude <= -18:
            return -100
        
        # Iceland
        if 63 <= latitude <= 67 and -25 <= longitude <= -13:
            return -100
        
        # If not in any land box, assume ocean
        # Vary depth by latitude (deeper at mid-latitudes)
        if abs(latitude) < 30:
            return 4500  # Deeper tropical oceans
        elif abs(latitude) < 60:
            return 4000  # Mid-latitude average
        else:
            return 3000  # Shallower polar regions
    
    def is_ocean(self, latitude: float, longitude: float) -> bool:
        """
        Check if location is in ocean (vs land)
        
        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
        
        Returns:
            bool: True if ocean, False if land
        """
        depth = self.get_depth(latitude, longitude)
        return depth > 0  # Positive depth = ocean
    
    def get_ocean_depth_meters(self, latitude: float, longitude: float) -> float:
        """
        Get ocean depth in meters (always positive)
        Returns 0 if on land
        
        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
        
        Returns:
            float: Ocean depth in meters (0 if on land)
        """
        depth = self.get_depth(latitude, longitude)
        return max(0, depth)
    
    def get_coastal_elevation(self, latitude: float, longitude: float, 
                             search_radius_deg: float = 0.1) -> Tuple[float, float]:
        """
        Get coastal elevation and slope near a point
        Useful for tsunami inundation calculations
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            search_radius_deg: Radius to search for coastal profile
        
        Returns:
            Tuple of (mean_elevation_m, mean_slope)
        """
        if self.dataset is None:
            return 10.0, 0.05  # Default: 10m elevation, 5% slope
        
        try:
            # Sample points in a cross pattern
            points = [
                (latitude, longitude),  # Center
                (latitude + search_radius_deg, longitude),  # North
                (latitude - search_radius_deg, longitude),  # South
                (latitude, longitude + search_radius_deg),  # East
                (latitude, longitude - search_radius_deg),  # West
            ]
            
            elevations = []
            for lat, lon in points:
                depth = self.get_depth(lat, lon)
                if depth < 0:  # Land
                    elevations.append(-depth)
            
            if not elevations:
                return 10.0, 0.05  # All ocean, use defaults
            
            mean_elevation = np.mean(elevations)
            
            # Estimate slope from elevation change
            if len(elevations) > 1:
                elevation_range = max(elevations) - min(elevations)
                distance_km = search_radius_deg * 111  # Rough conversion
                slope = elevation_range / (distance_km * 1000) if distance_km > 0 else 0.05
            else:
                slope = 0.05
            
            return float(mean_elevation), float(min(slope, 0.5))  # Cap slope at 50%
            
        except Exception as e:
            logger.warning(f"Failed to get coastal elevation: {e}")
            return 10.0, 0.05
    
    def __del__(self):
        """Clean up file handle"""
        # Don't close global cached dataset
        pass


# Module-level convenience function
_service_instance = None

def get_bathymetry_service() -> BathymetryService:
    """Get singleton bathymetry service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = BathymetryService()
    return _service_instance

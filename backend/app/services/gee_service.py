"""
Google Earth Engine Data Service
Integrates GEE datasets for terrain, population, land use, and other data overlays
NASA Space Apps Challenge 2025 - Meteor Madness
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import math

logger = logging.getLogger(__name__)

# Try to import Earth Engine
try:
    import ee
    GEE_AVAILABLE = True
except ImportError:
    logger.warning("Google Earth Engine not available. Install with: pip install earthengine-api")
    GEE_AVAILABLE = False


class GoogleEarthEngineService:
    """Service for fetching and processing Google Earth Engine datasets"""
    
    def __init__(self):
        self.initialized = False
        if GEE_AVAILABLE:
            try:
                # Try to initialize Earth Engine
                # For authentication, you'll need to run: earthengine authenticate
                # Or use a service account key
                ee.Initialize()
                self.initialized = True
                logger.info("Google Earth Engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Google Earth Engine: {e}")
                logger.info("Using mock data for demonstration")
    
    async def get_elevation_data(self, latitude: float, longitude: float, 
                                 radius_km: float = 5) -> Dict:
        """
        Get SRTM elevation data for a region
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            
        Returns:
            Dictionary with elevation data
        """
        if not self.initialized:
            return self._generate_mock_elevation_data(latitude, longitude, radius_km)
        
        try:
            # Define region of interest
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(radius_km * 1000)  # Convert km to meters
            
            # Load SRTM dataset (30m resolution)
            dem = ee.Image('USGS/SRTMGL1_003')
            
            # Get elevation data
            elevation = dem.select('elevation').clip(region)
            
            # Sample the data
            sample = elevation.sample(
                region=region,
                scale=30,  # 30m resolution
                numPixels=10000,
                geometries=True
            )
            
            # Convert to Python list
            features = sample.getInfo()['features']
            
            # Extract elevation values and coordinates
            values = []
            coordinates = []
            
            for feature in features:
                if 'elevation' in feature['properties']:
                    values.append(feature['properties']['elevation'])
                    coords = feature['geometry']['coordinates']
                    coordinates.append(coords)
            
            return {
                'dataset': 'USGS/SRTMGL1_003',
                'center': {'latitude': latitude, 'longitude': longitude},
                'radius_km': radius_km,
                'resolution_m': 30,
                'values': values,
                'coordinates': coordinates,
                'width': int(math.sqrt(len(values))),
                'height': int(math.sqrt(len(values))),
                'min_elevation': min(values) if values else 0,
                'max_elevation': max(values) if values else 0,
                'mean_elevation': sum(values) / len(values) if values else 0
            }
        except Exception as e:
            logger.error(f"Error fetching elevation data: {e}")
            return self._generate_mock_elevation_data(latitude, longitude, radius_km)
    
    async def get_population_data(self, latitude: float, longitude: float,
                                  radius_km: float = 5) -> Dict:
        """
        Get population density data from WorldPop
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            
        Returns:
            Dictionary with population data
        """
        if not self.initialized:
            return self._generate_mock_population_data(latitude, longitude, radius_km)
        
        try:
            # Define region
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(radius_km * 1000)
            
            # Load WorldPop dataset (100m resolution)
            # Note: WorldPop has different datasets per country
            population = ee.ImageCollection('WorldPop/GP/100m/pop').mosaic()
            
            # Sample the data
            pop_data = population.clip(region)
            
            sample = pop_data.sample(
                region=region,
                scale=100,  # 100m resolution
                numPixels=10000,
                geometries=True
            )
            
            # Convert to Python
            features = sample.getInfo()['features']
            
            values = []
            coordinates = []
            
            for feature in features:
                if 'population' in feature['properties']:
                    values.append(feature['properties']['population'])
                    coords = feature['geometry']['coordinates']
                    coordinates.append(coords)
            
            total_population = sum(values) if values else 0
            
            return {
                'dataset': 'WorldPop/GP/100m/pop',
                'center': {'latitude': latitude, 'longitude': longitude},
                'radius_km': radius_km,
                'resolution_m': 100,
                'values': values,
                'coordinates': coordinates,
                'width': int(math.sqrt(len(values))),
                'height': int(math.sqrt(len(values))),
                'total_population': int(total_population),
                'population_density': total_population / (math.pi * radius_km * radius_km) if radius_km > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error fetching population data: {e}")
            return self._generate_mock_population_data(latitude, longitude, radius_km)
    
    async def get_landcover_data(self, latitude: float, longitude: float,
                                radius_km: float = 5) -> Dict:
        """
        Get land cover data from ESRI 10m dataset
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            
        Returns:
            Dictionary with land cover data
        """
        if not self.initialized:
            return self._generate_mock_landcover_data(latitude, longitude, radius_km)
        
        try:
            # Define region
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(radius_km * 1000)
            
            # Load ESRI land cover (10m resolution)
            # Note: This is a community dataset
            landcover = ee.Image('projects/sat-io/open-datasets/landcover/ESRI_Global_LULC_10m')
            
            # Sample the data
            lc_data = landcover.clip(region)
            
            sample = lc_data.sample(
                region=region,
                scale=10,
                numPixels=10000,
                geometries=True
            )
            
            features = sample.getInfo()['features']
            
            values = []
            for feature in features:
                # ESRI land cover classes
                if 'b1' in feature['properties']:
                    values.append(feature['properties']['b1'])
            
            return {
                'dataset': 'ESRI_Global_LULC_10m',
                'center': {'latitude': latitude, 'longitude': longitude},
                'radius_km': radius_km,
                'resolution_m': 10,
                'values': values,
                'width': int(math.sqrt(len(values))),
                'height': int(math.sqrt(len(values))),
                'land_cover_classes': self._analyze_land_cover(values)
            }
        except Exception as e:
            logger.error(f"Error fetching land cover data: {e}")
            return self._generate_mock_landcover_data(latitude, longitude, radius_km)
    
    async def get_urban_data(self, latitude: float, longitude: float,
                            radius_km: float = 5) -> Dict:
        """
        Get urban built-up areas from GHSL dataset
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            
        Returns:
            Dictionary with urban data
        """
        if not self.initialized:
            return self._generate_mock_urban_data(latitude, longitude, radius_km)
        
        try:
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(radius_km * 1000)
            
            # Load GHSL built-up data
            ghsl = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/2020')
            
            built = ghsl.select('built_surface').clip(region)
            
            sample = built.sample(
                region=region,
                scale=100,
                numPixels=10000,
                geometries=True
            )
            
            features = sample.getInfo()['features']
            
            values = []
            for feature in features:
                if 'built_surface' in feature['properties']:
                    values.append(feature['properties']['built_surface'])
            
            return {
                'dataset': 'JRC/GHSL/P2023A/GHS_BUILT',
                'center': {'latitude': latitude, 'longitude': longitude},
                'radius_km': radius_km,
                'resolution_m': 100,
                'values': values,
                'width': int(math.sqrt(len(values))),
                'height': int(math.sqrt(len(values))),
                'urban_percentage': (sum(1 for v in values if v > 0) / len(values) * 100) if values else 0
            }
        except Exception as e:
            logger.error(f"Error fetching urban data: {e}")
            return self._generate_mock_urban_data(latitude, longitude, radius_km)
    
    async def get_water_data(self, latitude: float, longitude: float,
                            radius_km: float = 5) -> Dict:
        """
        Get surface water data from JRC Global Surface Water
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            
        Returns:
            Dictionary with water data
        """
        if not self.initialized:
            return self._generate_mock_water_data(latitude, longitude, radius_km)
        
        try:
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(radius_km * 1000)
            
            # Load JRC Global Surface Water
            gsw = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
            
            water = gsw.select('occurrence').clip(region)
            
            sample = water.sample(
                region=region,
                scale=30,
                numPixels=10000,
                geometries=True
            )
            
            features = sample.getInfo()['features']
            
            values = []
            for feature in features:
                if 'occurrence' in feature['properties']:
                    values.append(feature['properties']['occurrence'])
            
            return {
                'dataset': 'JRC/GSW1_4/GlobalSurfaceWater',
                'center': {'latitude': latitude, 'longitude': longitude},
                'radius_km': radius_km,
                'resolution_m': 30,
                'values': values,
                'width': int(math.sqrt(len(values))),
                'height': int(math.sqrt(len(values))),
                'water_percentage': (sum(1 for v in values if v > 50) / len(values) * 100) if values else 0
            }
        except Exception as e:
            logger.error(f"Error fetching water data: {e}")
            return self._generate_mock_water_data(latitude, longitude, radius_km)
    
    async def calculate_affected_population(self, latitude: float, longitude: float,
                                          damage_radii_km: List[float]) -> Dict:
        """
        Calculate affected population in multiple damage zones
        
        Args:
            latitude: Impact latitude
            longitude: Impact longitude
            damage_radii_km: List of damage radii in km
            
        Returns:
            Dictionary with affected population by zone
        """
        zones = []
        
        for i, radius in enumerate(damage_radii_km):
            pop_data = await self.get_population_data(latitude, longitude, radius)
            
            zone = {
                'zone_number': i + 1,
                'radius_km': radius,
                'population': int(pop_data['total_population']),
                'population_density': pop_data['population_density']
            }
            
            zones.append(zone)
        
        total_affected = sum(zone['population'] for zone in zones)
        
        return {
            'impact_location': {'latitude': latitude, 'longitude': longitude},
            'zones': zones,
            'total_affected_population': total_affected
        }
    
    # Helper methods for mock data generation
    
    def _generate_mock_elevation_data(self, lat: float, lon: float, radius: float) -> Dict:
        """Generate mock elevation data for testing"""
        size = 64
        values = []
        
        for i in range(size * size):
            # Generate realistic-looking elevation
            x = (i % size) / size
            y = (i // size) / size
            elevation = (np.sin(x * 10) * np.cos(y * 10) * 500 + 
                        np.random.normal(0, 50) + 200)
            values.append(max(0, elevation))
        
        return {
            'dataset': 'MOCK_SRTM',
            'center': {'latitude': lat, 'longitude': lon},
            'radius_km': radius,
            'resolution_m': 30,
            'values': values,
            'width': size,
            'height': size,
            'min_elevation': min(values),
            'max_elevation': max(values),
            'mean_elevation': sum(values) / len(values)
        }
    
    def _generate_mock_population_data(self, lat: float, lon: float, radius: float) -> Dict:
        """Generate mock population data"""
        size = 64
        values = []
        
        # Simulate population density (higher near center)
        center_x, center_y = size // 2, size // 2
        
        for i in range(size * size):
            x = i % size
            y = i // size
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            pop_density = max(0, 1000 * np.exp(-dist / 10) + np.random.normal(0, 50))
            values.append(pop_density)
        
        return {
            'dataset': 'MOCK_WorldPop',
            'center': {'latitude': lat, 'longitude': lon},
            'radius_km': radius,
            'resolution_m': 100,
            'values': values,
            'width': size,
            'height': size,
            'total_population': int(sum(values)),
            'population_density': sum(values) / (math.pi * radius * radius)
        }
    
    def _generate_mock_landcover_data(self, lat: float, lon: float, radius: float) -> Dict:
        """Generate mock land cover data"""
        size = 64
        values = []
        
        for i in range(size * size):
            # Random land cover classes (1-11)
            land_type = np.random.choice([1, 2, 4, 5, 7, 8, 10], 
                                        p=[0.3, 0.15, 0.2, 0.15, 0.1, 0.05, 0.05])
            values.append(land_type)
        
        return {
            'dataset': 'MOCK_ESRI_LULC',
            'center': {'latitude': lat, 'longitude': lon},
            'radius_km': radius,
            'resolution_m': 10,
            'values': values,
            'width': size,
            'height': size,
            'land_cover_classes': self._analyze_land_cover(values)
        }
    
    def _generate_mock_urban_data(self, lat: float, lon: float, radius: float) -> Dict:
        """Generate mock urban data"""
        size = 64
        values = []
        
        center_x, center_y = size // 2, size // 2
        
        for i in range(size * size):
            x = i % size
            y = i // size
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            urban_value = max(0, 100 * np.exp(-dist / 8))
            values.append(urban_value)
        
        return {
            'dataset': 'MOCK_GHSL',
            'center': {'latitude': lat, 'longitude': lon},
            'radius_km': radius,
            'resolution_m': 100,
            'values': values,
            'width': size,
            'height': size,
            'urban_percentage': (sum(1 for v in values if v > 10) / len(values) * 100)
        }
    
    def _generate_mock_water_data(self, lat: float, lon: float, radius: float) -> Dict:
        """Generate mock water data"""
        size = 64
        values = []
        
        for i in range(size * size):
            # Simulate water presence
            water = np.random.choice([0, 50, 100], p=[0.85, 0.1, 0.05])
            values.append(water)
        
        return {
            'dataset': 'MOCK_JRC_GSW',
            'center': {'latitude': lat, 'longitude': lon},
            'radius_km': radius,
            'resolution_m': 30,
            'values': values,
            'width': size,
            'height': size,
            'water_percentage': (sum(1 for v in values if v > 50) / len(values) * 100)
        }
    
    def _analyze_land_cover(self, values: List[int]) -> Dict[str, float]:
        """Analyze land cover distribution"""
        class_names = {
            1: 'Trees',
            2: 'Shrubland',
            4: 'Grassland',
            5: 'Cropland',
            7: 'Built Area',
            8: 'Water',
            9: 'Snow/Ice',
            10: 'Bare Ground',
            11: 'Wetlands'
        }
        
        total = len(values)
        distribution = {}
        
        for class_id, name in class_names.items():
            count = sum(1 for v in values if int(v) == class_id)
            percentage = (count / total * 100) if total > 0 else 0
            distribution[name] = round(percentage, 2)
        
        return distribution


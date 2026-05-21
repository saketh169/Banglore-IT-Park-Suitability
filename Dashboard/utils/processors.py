import numpy as np
import rasterio
from rasterio.plot import show
import geopandas as gpd
from pathlib import Path
from typing import Tuple, Dict

class RasterProcessor:
    """Handle raster data loading and processing"""
    
    def __init__(self, raster_folder: str):
        self.raster_folder = Path(raster_folder)
        self.loaded_rasters = {}
    
    def load_raster(self, filename: str) -> Tuple[np.ndarray, dict]:
        """Load a single raster file"""
        if filename in self.loaded_rasters:
            return self.loaded_rasters[filename]
        
        filepath = self.raster_folder / filename
        try:
            with rasterio.open(filepath) as src:
                data = src.read(1)
                profile = src.profile
                self.loaded_rasters[filename] = (data, profile)
                return data, profile
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None, None
    
    def normalize_raster(self, data: np.ndarray) -> np.ndarray:
        """Normalize raster to 0-5 scale"""
        data = data.astype(float)
        data_min = np.nanmin(data)
        data_max = np.nanmax(data)
        
        if data_max > data_min:
            normalized = 5.0 * (data - data_min) / (data_max - data_min)
        else:
            normalized = np.zeros_like(data)
        
        return normalized
    
    def weighted_overlay(self, layers: Dict[str, np.ndarray], weights: Dict[str, float]) -> np.ndarray:
        """
        Perform weighted overlay analysis
        
        Args:
            layers: Dict of layer_name: raster_array
            weights: Dict of layer_name: weight (0-1)
        """
        # Normalize weights to sum to 1
        total_weight = sum(weights.values())
        if total_weight == 0:
            return np.zeros_like(next(iter(layers.values())))
        
        normalized_weights = {k: v/total_weight for k, v in weights.items()}
        
        # Initialize result
        result = np.zeros_like(next(iter(layers.values())), dtype=float)
        
        # Apply weighted overlay
        for layer_name, raster_data in layers.items():
            if layer_name in normalized_weights:
                weight = normalized_weights[layer_name]
                result += raster_data * weight
        
        return result
    
    def apply_mask(self, raster: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Apply boolean mask to raster (mask=1 keeps, mask=0 removes)"""
        masked_result = raster.copy()
        masked_result[mask == 0] = np.nan
        return masked_result


class VectorProcessor:
    """Handle vector data operations"""
    
    def __init__(self, vector_folder: str):
        self.vector_folder = Path(vector_folder)
        self.loaded_vectors = {}
    
    def load_vector(self, filename: str) -> gpd.GeoDataFrame:
        """Load a vector file (shapefile, gpkg, etc.)"""
        if filename in self.loaded_vectors:
            return self.loaded_vectors[filename]
        
        filepath = self.vector_folder / filename
        try:
            gdf = gpd.read_file(filepath)
            self.loaded_vectors[filename] = gdf
            return gdf
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None
    
    def get_bounds_wgs84(self, gdf: gpd.GeoDataFrame) -> Tuple[float, float, float, float]:
        """Get bounds in WGS84 (lat/lon) for map initialization"""
        if gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        
        bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
        return bounds


class ScoreboardCalculator:
    """
    Calculate individual scores for a specific pixel
    Used for the radar chart/scorecard feature
    """
    
    def __init__(self, layers_dict: Dict[str, np.ndarray]):
        self.layers = layers_dict
    
    def get_pixel_scores(self, row: int, col: int) -> Dict[str, float]:
        """Get scores for all layers at a specific pixel"""
        scores = {}
        for layer_name, raster_data in self.layers.items():
            try:
                if 0 <= row < raster_data.shape[0] and 0 <= col < raster_data.shape[1]:
                    value = raster_data[row, col]
                    if not np.isnan(value):
                        scores[layer_name] = float(value)
                    else:
                        scores[layer_name] = 0.0
                else:
                    scores[layer_name] = 0.0
            except Exception as e:
                print(f"Error getting score for {layer_name}: {e}")
                scores[layer_name] = 0.0
        
        return scores

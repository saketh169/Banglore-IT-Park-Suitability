import folium
from folium.plugins import HeatMap
import streamlit as st
import numpy as np
import rasterio
from pathlib import Path
from typing import Tuple

class MapBuilder:
    """Build interactive maps using Folium"""
    
    @staticmethod
    def create_base_map(center_lat: float = 13.0, center_lon: float = 77.6, zoom_level: int = 12) -> folium.Map:
        """Create a base map with satellite imagery"""
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_level,
            tiles="OpenStreetMap"
        )
        
        # Add satellite layer option
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Satellite",
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        return m
    
    @staticmethod
    def add_raster_heatmap(m: folium.Map, raster_data: np.ndarray, 
                          bounds: Tuple[float, float, float, float], 
                          name: str = "Suitability",
                          opacity: float = 0.7):
        """Add raster data as heatmap overlay"""
        
        # Normalize data to 0-1 for colormap
        data_min = np.nanmin(raster_data)
        data_max = np.nanmax(raster_data)
        
        if data_max > data_min:
            normalized = (raster_data - data_min) / (data_max - data_min)
        else:
            normalized = np.zeros_like(raster_data)
        
        # Add as image overlay
        folium.raster_layers.ImageOverlay(
            image=normalized,
            bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
            opacity=opacity,
            name=name,
            colormap=lambda x: f"rgba({int(x*255)}, {int((1-x)*255)}, 0, 0.5)" if not np.isnan(x) else "rgba(0,0,0,0)"
        ).add_to(m)
        
        return m
    
    @staticmethod
    def add_vector_layer(m: folium.Map, gdf, name: str = "Vector Layer", color: str = "blue"):
        """Add vector layer to map"""
        # Convert to WGS84 if needed
        if gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        
        # Add GeoJSON
        folium.GeoJson(
            data=gdf.__geo_interface__,
            name=name,
            style_function=lambda x: {
                'fillColor': color,
                'color': color,
                'weight': 2,
                'opacity': 0.6
            }
        ).add_to(m)
        
        return m
    
    @staticmethod
    def add_marker_popup(m: folium.Map, lat: float, lon: float, 
                        popup_text: str, icon_color: str = "blue"):
        """Add a marker with popup to the map"""
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color=icon_color)
        ).add_to(m)
        
        return m

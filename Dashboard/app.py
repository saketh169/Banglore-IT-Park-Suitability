import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
from pathlib import Path
import tempfile
import base64
from io import BytesIO
from PIL import Image
from rasterio.warp import reproject, Resampling
from collections import namedtuple
from matplotlib.colors import LinearSegmentedColormap

# Define Bounds namedtuple at module level for pickle serialization
Bounds = namedtuple('Bounds', ['left', 'bottom', 'right', 'top'])

# Create custom colormap: White → Blue → Violet → Cyan → Green → Yellow → Orange → Red
custom_colors = [
    '#FFFFFF',  # White (lowest suitability)
    '#87CEEB',  # Sky Blue (low suitability)
    '#0000FF',  # Blue (low suitability)
    '#9370DB',  # Medium Purple/Violet (low suitability)
    '#20B2AA',  # Light Sea Green/Deep Cyan (low-moderate)
    '#00FF00',  # Green (moderate suitability)
    '#FFFF00',  # Yellow (good suitability)
    '#FFA500',  # Orange (high suitability)
    '#FF0000'   # Red (highest suitability - prime zones)
]
custom_cmap = LinearSegmentedColormap.from_list('suitability_custom', custom_colors)

# Register colormap only if not already registered
try:
    plt.colormaps.register(custom_cmap)
except ValueError:
    pass  # Colormap already registered, skip

# Upload tracking
if 'uploads' not in st.session_state:
    st.session_state.uploads = {
        'accessibility': None,
        'business': None,
        'physical': None,
        'infrastructure': None,
        'environmental': None
    }
if 'uploads_initialized' not in st.session_state:
    st.session_state.uploads_initialized = False
if 'upload_weights' not in st.session_state:
    st.session_state.upload_weights = {
        'accessibility': 30,        # Talent attraction & commute access
        'business': 25,             # Market demand
        'physical': 15,             # Terrain & land acquisition feasibility
        'infrastructure': 15,       # Power, roads, utilities
        'environmental': 15         # Green space, temperature, liveability
    }
if 'final_heatmap_cmap' not in st.session_state:
    st.session_state.final_heatmap_cmap = 'turbo'

# Track selected layer category (for All Layers navigation)
if 'selected_layer_category' not in st.session_state:
    st.session_state.selected_layer_category = None

# Track final suitability map generation
if 'final_suitability_generated' not in st.session_state:
    st.session_state.final_suitability_generated = False

# Track ML prediction display
if 'ml_prediction_shown' not in st.session_state:
    st.session_state.ml_prediction_shown = False

# Store final suitability data and bounds for comparison
if 'final_suitability_data' not in st.session_state:
    st.session_state.final_suitability_data = None
if 'suitability_bounds' not in st.session_state:
    st.session_state.suitability_bounds = None

def load_default_files():
    """Load default raster files from Final Analysis folder on first app load."""
    if st.session_state.uploads_initialized:
        return  # Only load once per session
    
    RASTER_PATH = Path(__file__).parent.parent / "Banglore" / "Final Analysis"
    
    # Map keys to primary filenames - USE ONLY RECLASS FILES (normalized for 1-5 scale)
    default_files = {
        'accessibility': ['reclass_accessibility.tif'],
        'business': ['reclass_business.tif'],
        'physical': ['reclass_physical.tif'],
        'infrastructure': ['reclass_infrastructure.tif'],
        'environmental': ['reclass_environment.tif']
    }
    
    for key, filenames in default_files.items():
        # Try each filename in order until one exists
        for filename in filenames:
            filepath = RASTER_PATH / filename
            if filepath.exists():
                st.session_state.uploads[key] = str(filepath)
                break
    
    st.session_state.uploads_initialized = True

# Load default files on app start
load_default_files()

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="IT Park Development Zone Analysis",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS STYLING ====================
custom_css = """
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/7.0.1/css/all.min.css" integrity="sha512-2SwdPD6INVrV/lHTZbO2nodKhrnDdJK9/kg2XD1r9uGqPo1cUbujc+IYdlYdEErWNu69gVcYgdxlmVmzTWnetw==" crossorigin="anonymous" referrerpolicy="no-referrer" />
<style>
    /* Root theme colors - White & Blue */
    :root {
        --primary-blue: #0066cc;
        --light-blue: #e6f2ff;
        --dark-blue: #003d99;
        --white: #ffffff;
        --light-gray: #f8f9fa;
        --border-gray: #e0e0e0;
    }
    
    /* Overall app styling */
    .reportview-container {
        background-color: var(--white);
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--dark-blue) 100%);
        color: var(--white);
        padding: 30px 20px;
        border-radius: 0;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0, 102, 204, 0.1);
    }
    
    .header-title {
        font-size: 2.5em;
        font-weight: 700;
        color: var(--white);
        margin-bottom: 10px;
    }
    
    .header-subtitle {
        font-size: 1.1em;
        color: rgba(255, 255, 255, 0.9);
        margin: 0;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: var(--light-gray);
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--light-gray) !important;
    }
    
    /* Card styling */
    .metric-card {
        background-color: var(--light-blue);
        border-left: 4px solid var(--primary-blue);
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: var(--primary-blue) !important;
        color: var(--white) !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background-color: var(--dark-blue) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3) !important;
    }
    
    /* Input styling */
    .stNumberInput > div > div > input,
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        border: 2px solid var(--border-gray) !important;
        border-radius: 6px !important;
        padding: 10px !important;
    }
    
    .stNumberInput > div > div > input:focus,
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 3px var(--light-blue) !important;
    }
    
    /* Section headers */
    h2 {
        color: var(--primary-blue);
        border-bottom: 3px solid var(--primary-blue);
        padding-bottom: 10px;
        margin-top: 30px;
        margin-bottom: 20px;
    }
    
    h3 {
        color: var(--dark-blue);
        margin-top: 20px;
    }
    
    /* Info/Warning boxes */
    .stAlert {
        border-radius: 8px !important;
    }
    
    .stInfo {
        background-color: var(--light-blue) !important;
        color: var(--dark-blue) !important;
        border-left: 4px solid var(--primary-blue) !important;
    }
    
    .stWarning {
        background-color: #fff3cd !important;
        color: #856404 !important;
        border-left: 4px solid #ffc107 !important;
    }
    
    .stSuccess {
        background-color: #d4edda !important;
        color: #155724 !important;
        border-left: 4px solid #28a745 !important;
    }
    
    /* Divider styling */
    hr {
        border: 0;
        border-top: 2px solid var(--light-blue);
        margin: 25px 0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] button {
        color: var(--dark-blue);
        border-bottom: 3px solid transparent;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: var(--primary-blue);
        border-bottom-color: var(--primary-blue);
    }
    
    /* Metric boxes */
    [data-testid="metric-container"] {
        background-color: var(--light-blue);
        border-radius: 8px;
        padding: 15px !important;
    }
    
    /* File uploader styling */
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed var(--primary-blue) !important;
        border-radius: 8px !important;
        background-color: var(--light-blue) !important;
    }
    
    /* Caption and text styling */
    .stCaption {
        color: #666;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--light-blue);
        color: var(--primary-blue);
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# ==================== HEADER ====================
header_html = """
<div class="header-container">
    <div class="header-title"><i class="fas fa-map"></i> IT Park Development Zone Analysis</div>
    <div class="header-subtitle">Bengaluru IT Corridor | Mahadevapura | Multi-Criteria Suitability Analysis</div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# ==================== PATHS ====================
BASE_PATH = Path(__file__).parent.parent
FINAL_ANALYSIS_PATH = BASE_PATH / "Banglore" / "Final Analysis"  # For feature maps and constraint
RASTER_PATH = BASE_PATH / "Banglore" / "Raster" / "IT"  # For browsing all raster layers
VECTOR_PATH = BASE_PATH / "Banglore" / "Vector" / "IT"

# ==================== HELPER FUNCTION: RENDER RASTER WITH MAP ====================
def raster_to_base64_image(data, cmap='viridis'):
    """Convert numpy raster array to base64-encoded PNG image"""
    try:
        # Normalize data to 0-255
        data_normalized = ((data - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data)) * 255).astype(np.uint8)
        
        # Create PIL image
        img = Image.fromarray(data_normalized)
        if len(img.mode) == 1:  # Grayscale
            img = img.convert('RGB')
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        st.error(f"Error converting raster: {e}")
        return None

@st.cache_data
def load_geopandas_file(file_path):
    """Load geopackage file with geopandas and cache it"""
    import geopandas as gpd
    return gpd.read_file(str(file_path))

@st.cache_data
def load_raster_data(file_path):
    """Load raster data and cache it with WGS84 bounds conversion and metadata"""
    from rasterio.warp import transform_bounds
    
    with rasterio.open(file_path) as src:
        # Read data and metadata
        orig_data = src.read(1)
        data = orig_data.astype(float)
        bounds = src.bounds
        crs = src.crs
        
        # Get additional metadata
        data_type = str(orig_data.dtype)  # Data type (uint8, float32, etc.)
        height, width = src.height, src.width  # Dimensions
        
        # Get pixel resolution (absolute values)
        transform = src.transform
        pixel_width = abs(transform.a)
        pixel_height = abs(transform.e)
        
        # Convert bounds to WGS84 if not already
        if crs and crs.to_string() != 'EPSG:4326':
            left, bottom, right, top = transform_bounds(crs, 'EPSG:4326', bounds.left, bounds.bottom, bounds.right, bounds.top)
        else:
            left, bottom, right, top = bounds.left, bounds.bottom, bounds.right, bounds.top
        
        # Use module-level Bounds namedtuple for pickle serialization
        bounds = Bounds(left, bottom, right, top)
        
        # Store all metadata in a dict
        metadata = {
            'data_type': data_type,
            'dimensions': f"{height} × {width}",
            'resolution': f"{pixel_width:.2f} × {pixel_height:.2f}",
            'crs': str(crs) if crs else "Unknown"
        }
    
    return data, bounds, crs, metadata

def render_vector_layer(gpkg_path, layer_name):
    """Display vector layer in 2-column format with overlay on Leaflet map"""
    try:
        gdf = load_geopandas_file(gpkg_path)
        
        if len(gdf) == 0:
            st.warning(f"No features found in {layer_name}")
            return
        
        # Reproject to EPSG:4326 (WGS84) for Leaflet
        if gdf.crs and gdf.crs.to_string() != 'EPSG:4326':
            gdf = gdf.to_crs('EPSG:4326')
        
        # Get bounds and center
        bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        # Convert to GeoJSON
        geojson_str = gdf.to_json()
        
        # Determine geometry type
        geom_types = gdf.geometry.type.unique()
        geom_type = ', '.join(geom_types) if len(geom_types) > 0 else 'Unknown'
        
        col_map, col_plot = st.columns(2)
        
        # LEFT: Leaflet map with vector overlay
        with col_map:
            st.markdown(f"**{layer_name} - Map View**")
            
            # Create Leaflet map with GeoJSON overlay
            leaflet_html = f"""
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
            <div id="map" style="height: 500px; width: 100%;"></div>
            
            <script>
                var map = L.map('map').setView([{center_lat}, {center_lon}], 13);
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© OpenStreetMap contributors',
                    maxZoom: 19
                }}).addTo(map);
                
                // Add GeoJSON layer
                var geojson = {geojson_str};
                var geojsonLayer = L.geoJSON(geojson, {{
                    style: function(feature) {{
                        return {{
                            color: '#45B7D1',
                            weight: 2,
                            opacity: 0.8,
                            fillOpacity: 0.4
                        }};
                    }},
                    pointToLayer: function(feature, latlng) {{
                        return L.circleMarker(latlng, {{
                            radius: 6,
                            color: '#FF6B6B',
                            weight: 2,
                            opacity: 0.8,
                            fillOpacity: 0.7
                        }});
                    }}
                }}).addTo(map);
                
                // Fit map to bounds
                map.fitBounds(geojsonLayer.getBounds().pad(0.05));
            </script>
            """
            
            components.html(leaflet_html, height=500)
        
        # RIGHT: Matplotlib plot of vector geometries
        with col_plot:
            st.markdown(f"**{layer_name} - Geometry Plot**")
            
            # Create matplotlib plot
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Color based on geometry type
            color_map = {
                'Point': '#FF6B6B',
                'LineString': '#4ECDC4',
                'Polygon': '#45B7D1',
                'MultiPoint': '#FFA07A',
                'MultiLineString': '#98D8C8',
                'MultiPolygon': '#6C63FF'
            }
            
            # Plot geometries
            for idx, row in gdf.iterrows():
                geom = row.geometry
                geom_type_single = geom.geom_type
                color = color_map.get(geom_type_single, '#CCCCCC')
                
                if geom_type_single == 'Point':
                    ax.plot(geom.x, geom.y, 'o', color=color, markersize=8, alpha=0.7)
                elif geom_type_single in ['LineString', 'MultiLineString']:
                    if geom_type_single == 'LineString':
                        x, y = geom.xy
                        ax.plot(x, y, color=color, linewidth=2, alpha=0.7)
                    else:
                        for line in geom.geoms:
                            x, y = line.xy
                            ax.plot(x, y, color=color, linewidth=2, alpha=0.7)
                elif geom_type_single in ['Polygon', 'MultiPolygon']:
                    if geom_type_single == 'Polygon':
                        x, y = geom.exterior.xy
                        ax.fill(x, y, color=color, alpha=0.5, edgecolor=color, linewidth=1.5)
                    else:
                        for poly in geom.geoms:
                            x, y = poly.exterior.xy
                            ax.fill(x, y, color=color, alpha=0.5, edgecolor=color, linewidth=1.5)
            
            ax.set_title(f"{layer_name} Geometries", fontweight='bold')
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig, use_container_width=True)
            plt.close()
        
        # Layer Details
        st.markdown("---")
        detail_c1, detail_c2, detail_c3, detail_c4 = st.columns(4)
        detail_c1.metric("Data Type", "Vector")
        detail_c2.metric("Resolution", "N/A")
        detail_c3.metric("Dimensions", f"{len(gdf)} features")
        detail_c4.metric("CRS", str(gdf.crs) if gdf.crs else "Unknown")
    
    except Exception as e:
        st.error(f"Error rendering {layer_name}: {e}")

def raster_to_colored_base64_image(data, cmap_name='turbo', mask_zero=False, vmin=None, vmax=None):
    """Convert numpy raster array to a colorized base64-encoded PNG image
    
    Args:
        data: numpy array
        cmap_name: matplotlib colormap name
        mask_zero: if True, render 0 values as pure black (for masked areas)
        vmin: minimum value for normalization (if None, uses data min)
        vmax: maximum value for normalization (if None, uses data max)
    """
    try:
        data = np.asarray(data, dtype=float)
        finite = np.isfinite(data)
        if not finite.any():
            return None

        data_min = np.nanmin(data)
        data_max = np.nanmax(data)
        
        # Use provided vmin/vmax if available, else use data range
        norm_min = vmin if vmin is not None else data_min
        norm_max = vmax if vmax is not None else data_max
        
        # Identify zero pixels BEFORE normalization
        zero_mask = data < 0.001 if mask_zero else np.zeros_like(data, dtype=bool)
        
        # Standard normalization using norm_min and norm_max
        if norm_max == norm_min:
            normalized = np.zeros_like(data, dtype=float)
        else:
            normalized = (data - norm_min) / (norm_max - norm_min)
            # Clip to [0, 1] range
            normalized = np.clip(normalized, 0, 1)

        cmap = plt.get_cmap(cmap_name)
        
        # Apply colormap to normalized values
        rgba = cmap(np.clip(normalized, 0, 1))
        
        # Override zero pixels with pure black (RGBA: 0, 0, 0, 1)
        if mask_zero:
            rgba[zero_mask] = np.array([0.0, 0.0, 0.0, 1.0])
        
        # Set alpha channel for invalid values
        rgba[~finite, 3] = 0.0
        
        # Convert to RGB uint8
        rgb_img = (rgba[:, :, :3] * 255).astype(np.uint8)

        img = Image.fromarray(rgb_img)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        st.error(f"Error colorizing raster: {e}")
        return None
        return None

def render_upload_with_colored_map(upload_path, map_title, opacity=0.8, colormap='viridis'):
    """Display uploaded raster with colored overlay on map - same approach as raster layers"""
    try:
        from rasterio.warp import transform_bounds
        
        with rasterio.open(upload_path) as src:
            # Read data and metadata
            orig_data = src.read(1)
            data = orig_data.astype(float)
            bounds = src.bounds
            crs = src.crs
            
            # Get metadata
            data_type = str(orig_data.dtype)
            height, width = src.height, src.width
            
            # Get pixel resolution (absolute values)
            transform = src.transform
            pixel_width = abs(transform.a)
            pixel_height = abs(transform.e)
            
            # Convert bounds to WGS84 if not already
            if crs and crs.to_string() != 'EPSG:4326':
                left, bottom, right, top = transform_bounds(crs, 'EPSG:4326', bounds.left, bounds.bottom, bounds.right, bounds.top)
            else:
                left, bottom, right, top = bounds.left, bounds.bottom, bounds.right, bounds.top
            
            # Leaflet bounds format: [[south, west], [north, east]]
            leaflet_bounds_str = f"[[{bottom}, {left}], [{top}, {right}]]"
            center_lat = (bottom + top) / 2
            center_lon = (left + right) / 2
            
            # Store metadata
            metadata = {
                'data_type': data_type,
                'dimensions': f"{height} × {width}",
                'resolution': f"{pixel_width:.2f} × {pixel_height:.2f}",
                'crs': str(crs) if crs else "Unknown"
            }
            
            col_map, col_gray = st.columns(2)
            
            # LEFT: Leaflet Map with raster overlay
            with col_map:
                st.markdown(f"**{map_title} - Map View**")
                
                # Create colored base64 image for overlay
                overlay_base64 = raster_to_colored_base64_image(data, cmap_name=colormap)
                
                leaflet_html = f"""
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
                <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
                <div id="map" style="height: 500px; width: 100%;"></div>
                
                <script>
                    var map = L.map('map').setView([{center_lat}, {center_lon}], 12);
                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                        attribution: '© OpenStreetMap contributors',
                        maxZoom: 19
                    }}).addTo(map);
                    
                    // Add raster overlay with proper bounds
                    var rasterImage = new Image();
                    rasterImage.src = '{overlay_base64}';
                    rasterImage.onload = function() {{
                        var imageBounds = {leaflet_bounds_str};
                        var rasterLayer = L.imageOverlay(rasterImage.src, imageBounds, {{
                            opacity: 0.8
                        }}).addTo(map);
                        
                        // Fit map to raster bounds (auto-zoom to layer extent)
                        map.fitBounds(imageBounds);
                    }};
                </script>
                """
                
                components.html(leaflet_html, height=500)
            
            # RIGHT: Colored heatmap
            with col_gray:
                st.markdown(f"**{map_title} - Heatmap**")
                
                fig, ax = plt.subplots(figsize=(8, 6))
                im = ax.imshow(data, cmap=colormap, aspect='auto')
                ax.set_title(f"Heatmap Visualization", fontweight='bold')
                ax.set_xlabel("X (pixels)")
                ax.set_ylabel("Y (pixels)")
                cbar = plt.colorbar(im, ax=ax, label="Value")
                st.pyplot(fig, use_container_width=True)
                plt.close()
            
            # Layer Details
            st.markdown("---")
            detail_c1, detail_c2, detail_c3, detail_c4 = st.columns(4)
            detail_c1.metric("Data Type", metadata['data_type'])
            detail_c2.metric("Resolution", metadata['resolution'])
            detail_c3.metric("Dimensions", metadata['dimensions'])
            detail_c4.metric("CRS", metadata['crs'])
    
    except Exception as e:
        st.error(f"Error rendering {map_title}: {e}")

def render_raster_with_map(layer_path, layer_name, overlay_path=None, overlay_opacity=0.7):
    """Display raster with proper bounds overlay on Leaflet map - uses cached data"""
    
    try:
        # Use cached raster loading (bounds already in WGS84)
        data, bounds, crs, metadata = load_raster_data(layer_path)
        
        # Determine colormap: LULC gets turbo, population gets viridis, rest get grayscale
        layer_lower = layer_name.lower()
        
        if 'lulc' in layer_lower or 'land_cover' in layer_lower:
            cmap_name = 'turbo'  # Multi-color for LULC classes
        elif 'population' in layer_lower or 'reclass_population' in layer_lower:
            cmap_name = 'viridis'  # Viridis for population density
        else:
            cmap_name = 'gray'  # Grayscale for all other layers
        
        # Leaflet bounds format: [[south, west], [north, east]]
        # Properly format bounds string for JavaScript (bounds already in WGS84 from load_raster_data)
        leaflet_bounds_str = f"[[{bounds.bottom}, {bounds.left}], [{bounds.top}, {bounds.right}]]"
            
        col_map, col_gray = st.columns(2)
        
        # LEFT: Leaflet Map with raster overlay
        with col_map:
            st.markdown(f"**{layer_name} - Map View**")
            
            # Create colored base64 image for overlay (grayscale for most, turbo for LULC)
            overlay_base64 = raster_to_colored_base64_image(data, cmap_name=cmap_name)
            
            leaflet_html = f"""
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
            <div id="map" style="height: 500px; width: 100%;"></div>
            
            <script>
                var map = L.map('map').setView([13.2, 77.6], 10);
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© OpenStreetMap contributors',
                    maxZoom: 19
                }}).addTo(map);
                
                // Add raster overlay with proper bounds
                var rasterImage = new Image();
                rasterImage.src = '{overlay_base64}';
                rasterImage.onload = function() {{
                    var imageBounds = {leaflet_bounds_str};
                    var rasterLayer = L.imageOverlay(rasterImage.src, imageBounds, {{
                        opacity: 0.8
                    }}).addTo(map);
                    
                    // Fit map to raster bounds (auto-zoom to layer extent)
                    map.fitBounds(imageBounds);
                }};
            </script>
            """
            
            components.html(leaflet_html, height=500)
        
        # RIGHT: Colored heatmap
        with col_gray:
            st.markdown(f"**{layer_name} - Heatmap**")
            
            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(data, cmap=cmap_name, aspect='auto')
            ax.set_title(f"Heatmap Visualization", fontweight='bold')
            ax.set_xlabel("X (pixels)")
            ax.set_ylabel("Y (pixels)")
            cbar = plt.colorbar(im, ax=ax, label="Value")
            st.pyplot(fig, use_container_width=True)
            plt.close()
        
        # Layer Details
        st.markdown("---")
        detail_c1, detail_c2, detail_c3, detail_c4 = st.columns(4)
        detail_c1.metric("Data Type", metadata['data_type'])
        detail_c2.metric("Resolution", metadata['resolution'])
        detail_c3.metric("Dimensions", metadata['dimensions'])
        detail_c4.metric("CRS", metadata['crs'])
    
    except Exception as e:
        st.error(f"Error rendering {layer_name}: {e}")

# ==================== SCAN LAYERS ====================
vector_layers = []
raster_layers = []
mask_layers = []
reclass_rasters = []
proximity_rasters = []

if RASTER_PATH.exists():
    for file in sorted(RASTER_PATH.glob("*.tif")):
        name = file.name.replace(".tif", "")
        if "mask_" in name:
            mask_layers.append(name)
        elif "reclass_" in name:
            reclass_rasters.append(name)
        elif "Proximity_" in name or "Proxmity_" in name:
            proximity_rasters.append(name)
        else:
            raster_layers.append(name)

if VECTOR_PATH.exists():
    for file in sorted(VECTOR_PATH.glob("*.gpkg")):
        vector_layers.append(file.name.replace(".gpkg", ""))

# ==================== SIDEBAR NAVIGATION ====================
with st.sidebar:
    st.markdown("""
    <style>
        .sidebar-title {
            font-size: 1.3em;
            font-weight: 700;
            color: #0066cc;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-title">Navigation Menu</div>', unsafe_allow_html=True)
    
    main_option = st.radio(
        "Choose Analysis View:",
        ["Feature Maps", "All Layers", "ML Model"],
        index=0,
        key="main_nav"
    )
    
    st.markdown("---")
    
    with st.expander('About This Tool', expanded=False):
        st.markdown("""
        **IT Park Development Zone Analysis**
        
        A comprehensive multi-criteria spatial analysis tool for identifying suitable zones for IT park development in Bengaluru's Mahadevapura area.
        
        **Features:**
        - 5 key evaluation criteria
        - Customizable weighted analysis
        - Interactive map visualization
        - Constraint-based filtering
        """)
    
    
    # Conditional sidebar formulas based on selected view
    if main_option == "Feature Maps":
        with st.expander('📐 Sub-Thematic Feature Map Formulas', expanded=False):
            st.markdown("""
            ### **1. Accessibility_Map**
            *Transport connectivity for talent attraction & commute access*
            
            ```sql
            ("reclass_roads@1" * 0.4) + 
            ("reclass_busStop@1" * 0.3) + 
            ("reclass_railway@1" * 0.2) + 
            ("reclass_airport@1" * 0.1)
            ```
            
            **Weights:** Roads 40% | Bus 30% | Railway 20% | Airport 10%
            
            ---
            
            ### **2. Business_Demand_Map**
            *Market viability & economic opportunities*
            
            ```sql
            ("reclass_it-hubs@1" * 0.4) + 
            ("reclass_industrial@1" * 0.2) + 
            ("reclass_population@1" * 0.2) + 
            ("reclass_power@1" * 0.2)
            ```
            
            **Weights:** IT Hubs 40% | Industrial 20% | Population 20% | Power 20%
            
            ---
            
            ### **3. Physical_Suitability_Map**
            *Terrain & land acquisition feasibility*
            
            ```sql
            ("reclass_slope@1" * 0.5) + 
            ("reclass_LULC@1" * 0.3) + 
            ("reclass_NDWI@1" * 0.2)
            ```
            
            **Weights:** Slope 50% | LULC 30% | NDWI 20%
            
            ---
            
            ### **4. Infrastructure_Reliability_Map**
            *Utility readiness & operational stability*
            
            ```sql
            ("reclass_power@1" * 0.5) + 
            ("reclass_NDBI@1" * 0.3) + 
            ("reclass_roads@1" * 0.2)
            ```
            
            **Weights:** Power 50% | NDBI 30% | Roads 20%
            
            ---
            
            ### **5. Environment_Liveability_Map**
            *Green space, temperature & livability*
            
            ```sql
            ("reclass_NDVI@1" * 0.45) + 
            ("reclass_LST@1" * 0.35) + 
            ("reclass_NDWI@1" * 0.2)
            ```
            
            **Weights:** NDVI 45% | LST 35% | NDWI 20%
            """)
    
    elif main_option == "All Layers":
        with st.expander('📐 Raster Layer Formulas', expanded=False):
            st.markdown("""
            ### Spectral Indices - Raster Queries
            
            **NDVI** - Vegetation Index
            ```sql
            ("B5@1" - "B4@1") / ("B5@1" + "B4@1")
            ```
            ✓ Green vegetation & forest coverage
            
            ---
            
            **NDWI** - Water Index
            ```sql
            ("B3@1" - "B5@1") / ("B3@1" + "B5@1")
            ```
            ✓ Water bodies & moisture areas
            
            ---
            
            **NDBI** - Built-up Index
            ```sql
            ("B6@1" - "B5@1") / ("B6@1" + "B5@1")
            ```
            ✓ Urban density & built structures
            
            ---
            
            **LST** - Land Surface Temperature
            ```sql
            ("B10@1" * 0.00341802 + 149.0) - 273.15
            ```
            ✓ Temperature in °C
            
            ---
            
            **RGB** - True Color Composite
            ```sql
            R: B4@1 | G: B3@1 | B: B2@1
            ```
            ✓ Visual reference imagery
            
            ---
            
            ### Band Reference
            - B2 = Blue
            - B3 = Green
            - B4 = Red
            - B5 = Near Infrared (NIR)
            - B6 = SWIR1
            - B10 = Thermal Infrared
            """)
    
    elif main_option == "ML Model":
        pass  # No additional sidebar content for ML Model

# ==================== MAIN PAGE ====================
clean_option = main_option.split()[-1] if " " in main_option else main_option

if clean_option == "Maps":
    st.markdown("---")
    st.markdown('## <i class="fas fa-chart-bar"></i> Feature Maps Dashboard', unsafe_allow_html=True)
    st.markdown("Upload and overlay your custom feature maps for analysis")
    st.markdown('<div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; border-left: 4px solid #0066cc;"><i class="fas fa-cube"></i> <b>Default files are pre-loaded from Final Analysis folder!</b> All maps are ready to use. Upload new files anytime to override them.</div>', unsafe_allow_html=True)

    def percentage_input(map_key, label, input_key):
        if input_key not in st.session_state:
            st.session_state[input_key] = int(st.session_state.upload_weights[map_key])

        value = st.number_input(
            f"{label} %",
            min_value=1,
            max_value=100,
            step=1,
            key=input_key,
            help="Enter a percentage value. The app keeps your input and normalizes internally if needed."
        )
        st.session_state.upload_weights[map_key] = int(value)
    
    # Accessibility
    st.markdown('<h3 style="color: #0066cc; border-left: 4px solid #0066cc; padding-left: 15px;"><i class="fas fa-road"></i> 1. Accessibility Map</h3>', unsafe_allow_html=True)
    st.caption('Classification: 1=Poor Accessibility | 2=Low Accessibility | 3=Moderate Accessibility | 4=High Accessibility | 5=Optimal Accessibility')
    
    col_upload, col_pct, col_weight = st.columns([2.2, 1.1, 0.7])
    with col_upload:
        file_a = st.file_uploader('Upload Accessibility', type=["tif", "tiff"], key="upload_a")
        if st.session_state.uploads['accessibility'] and not file_a:
            st.caption('<i class="fas fa-cube"></i> Default file loaded (click to replace)', unsafe_allow_html=True)
    
    with col_pct:
        percentage_input('accessibility', "Accessibility", "pct_a_input")
    with col_weight:
        st.metric("Weight", f"{st.session_state.upload_weights['accessibility']}%", label_visibility="collapsed")
    
    # Accessibility - Upload & Render
    if file_a:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
            tmp.write(file_a.getbuffer())
            st.session_state.uploads['accessibility'] = tmp.name
    
    if st.session_state.uploads['accessibility']:
        render_upload_with_colored_map(st.session_state.uploads['accessibility'], 
                                       "Accessibility Feature Map", 
                                       colormap='RdYlGn')
        st.divider()
    
    # Infrastructure
    st.markdown('<h3 style="color: #0066cc; border-left: 4px solid #0066cc; padding-left: 15px;"><i class="fas fa-plug"></i> 2. Infrastructure Reliability Map</h3>', unsafe_allow_html=True)
    st.caption('Classification: 1=Unsuitable | 2=Low | 3=Moderate | 4=High | 5=Optimal (Plug-and-Play)')
    
    col_upload, col_pct, col_weight = st.columns([2.2, 1.1, 0.7])
    with col_upload:
        file_i = st.file_uploader('Upload Infrastructure', type=["tif", "tiff"], key="upload_i")
        if st.session_state.uploads['infrastructure'] and not file_i:
            st.caption('<i class="fas fa-cube"></i> Default file loaded (click to replace)', unsafe_allow_html=True)
    
    with col_pct:
        percentage_input('infrastructure', "Infrastructure", "pct_i_input")
    with col_weight:
        st.metric("Weight", f"{st.session_state.upload_weights['infrastructure']}%", label_visibility="collapsed")
    
    # Infrastructure - Upload & Render
    if file_i:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
            tmp.write(file_i.getbuffer())
            st.session_state.uploads['infrastructure'] = tmp.name
    
    if st.session_state.uploads['infrastructure']:
        render_upload_with_colored_map(st.session_state.uploads['infrastructure'], 
                                       "Infrastructure Reliability Feature Map", 
                                       colormap='RdYlGn')
        st.divider()
    
    # Business
    st.markdown('<h3 style="color: #0066cc; border-left: 4px solid #0066cc; padding-left: 15px;"><i class="fas fa-briefcase"></i> 3. Business Demand Map</h3>', unsafe_allow_html=True)
    st.caption('Classification: 1.0-2.2=Very Low | 2.2-2.9=Low | 2.9-3.6=Moderate | 3.6-4.2=High | 4.2-5.0=Prime')
    
    col_upload, col_pct, col_weight = st.columns([2.2, 1.1, 0.7])
    with col_upload:
        file_b = st.file_uploader('Upload Business Demand', type=["tif", "tiff"], key="upload_b")
        if st.session_state.uploads['business'] and not file_b:
            st.caption('<i class="fas fa-cube"></i> Default file loaded (click to replace)', unsafe_allow_html=True)
    
    with col_pct:
        percentage_input('business', "Business Demand", "pct_b_input")
    with col_weight:
        st.metric("Weight", f"{st.session_state.upload_weights['business']}%", label_visibility="collapsed")
    
    # Business - Upload & Render
    if file_b:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
            tmp.write(file_b.getbuffer())
            st.session_state.uploads['business'] = tmp.name
    
    if st.session_state.uploads['business']:
        render_upload_with_colored_map(st.session_state.uploads['business'], 
                                       "Business Demand Feature Map", 
                                       colormap='RdYlGn')
        st.divider()
    
    # Environmental
    st.markdown('<h3 style="color: #0066cc; border-left: 4px solid #0066cc; padding-left: 15px;"><i class="fas fa-leaf"></i> 4. Environment Liveability Map</h3>', unsafe_allow_html=True)
    st.caption('Classification: 1=Poor Liveability | 2=Fair Liveability | 3=Good Liveability | 4=Excellent Liveability | 5=Optimal Liveability')
    
    col_upload, col_pct, col_weight = st.columns([2.2, 1.1, 0.7])
    with col_upload:
        file_e = st.file_uploader('Upload Environmental & Social', type=["tif", "tiff"], key="upload_e")
        if st.session_state.uploads['environmental'] and not file_e:
            st.caption('<i class="fas fa-cube"></i> Default file loaded (click to replace)', unsafe_allow_html=True)
    
    with col_pct:
        percentage_input('environmental', "Environmental & Social", "pct_e_input")
    with col_weight:
        st.metric("Weight", f"{st.session_state.upload_weights['environmental']}%", label_visibility="collapsed")
    
    # Environmental - Upload & Render
    if file_e:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
            tmp.write(file_e.getbuffer())
            st.session_state.uploads['environmental'] = tmp.name
    
    if st.session_state.uploads['environmental']:
        render_upload_with_colored_map(st.session_state.uploads['environmental'], 
                                       "Environment Liveability Map", 
                                       colormap='RdYlGn')
        st.divider()
    
    # Physical
    st.markdown('<h3 style="color: #0066cc; border-left: 4px solid #0066cc; padding-left: 15px;"><i class="fas fa-mountain"></i> 5. Physical Suitability Map</h3>', unsafe_allow_html=True)
    st.caption('Classification: 1.8-2.6=Very Low (Steep) | 2.6-3.5=Low (Uneven) | 3.5-4.3=Moderate (Average) | 4.3-5.1=High (Flat) | >5.0=Optimal')
    
    col_upload, col_pct, col_weight = st.columns([2.2, 1.1, 0.7])
    with col_upload:
        file_p = st.file_uploader('Upload Physical Suitability', type=["tif", "tiff"], key="upload_p")
        if st.session_state.uploads['physical'] and not file_p:
            st.caption('<i class="fas fa-cube"></i> Default file loaded (click to replace)', unsafe_allow_html=True)
    
    with col_pct:
        percentage_input('physical', "Physical Suitability", "pct_p_input")
    with col_weight:
        st.metric("Weight", f"{st.session_state.upload_weights['physical']}%", label_visibility="collapsed")
    
    # Physical - Upload & Render
    if file_p:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
            tmp.write(file_p.getbuffer())
            st.session_state.uploads['physical'] = tmp.name
    
    if st.session_state.uploads['physical']:
        render_upload_with_colored_map(st.session_state.uploads['physical'], 
                                       "Physical Suitability Feature Map", 
                                       colormap='RdYlGn')
        st.divider()
    
    # Constraint Map
    st.markdown('<h3 style="color: #0066cc; border-left: 4px solid #0066cc; padding-left: 15px;"><i class="fas fa-ban"></i> 6. Constraint Map (No-Build Zones)</h3>', unsafe_allow_html=True)
    constraint_path = BASE_PATH / "Banglore" / "Final Analysis" / "constraint_mask.tif"
    if constraint_path.exists():
        st.caption("Shows restricted areas: Water • Railway • Settlements • Protected Areas (white = buildable, black = restricted)")
        try:
            render_raster_with_map(str(constraint_path), "Constraint Mask", overlay_opacity=0.8)
        except Exception as e:
            st.error(f"Error loading Constraint Map: {e}")
    else:
        st.warning(f"constraint_mask.tif not found at {constraint_path}")
    st.divider()
    
    # Display total
    st.markdown("---")
    st.markdown('<h3 style="color: #0066cc;"><i class="fas fa-chart-bar"></i> Weight Summary</h3>', unsafe_allow_html=True)
    total_weight = sum(st.session_state.upload_weights.values())
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric('Accessibility', f"{st.session_state.upload_weights['accessibility']}%")
    col2.metric('Business', f"{st.session_state.upload_weights['business']}%")
    col3.metric('Physical', f"{st.session_state.upload_weights['physical']}%")
    col4.metric('Infrastructure', f"{st.session_state.upload_weights['infrastructure']}%")
    col5.metric('Environment', f"{st.session_state.upload_weights['environmental']}%")
    
    st.info('Total Percentage: **' + str(total_weight) + '%**')
    if total_weight != 100:
        st.markdown('<div style="background-color: #ffebee; border: 1px solid #ef5350; border-radius: 5px; padding: 12px;"><i class="fas fa-exclamation-triangle"></i> <b style="color: #c62828;">Percentages must add up to exactly 100%. Please adjust your weights.</b></div>', unsafe_allow_html=True)
        st.stop()

    w_accessibility = st.session_state.upload_weights['accessibility']
    w_business = st.session_state.upload_weights['business']
    w_physical = st.session_state.upload_weights['physical']
    w_infrastructure = st.session_state.upload_weights['infrastructure']
    w_environmental = st.session_state.upload_weights['environmental']
    
    # Convert to fractions for calculations
    w_a = w_accessibility / 100
    w_b = w_business / 100
    w_p = w_physical / 100
    w_i = w_infrastructure / 100
    w_e = w_environmental / 100
    
    st.markdown("---")
    st.markdown('<h3 style="color: #0066cc;"><i class="fas fa-play-circle"></i> Generate Final Suitability Map</h3>', unsafe_allow_html=True)
    
    # Constraint mask always applied
    apply_mask = True
    
    st.info('⚙️ Constraint mask always applied: Water • Railway • Settlements • Protected Areas')
    st.caption('Uploaded layers are used first; project raster files are used as fallback.')
    
    # Display formula
    st.markdown("---")
    st.markdown('<h3 style="color: #0066cc;"><i class="fas fa-calculator"></i> Applied Formula</h3>', unsafe_allow_html=True)
    st.caption("The percentage values above are the exact values used when generating the final map.")
    
    # Build formula - show constraint mask in display
    mask_suffix = " × Constraint_Mask" if apply_mask else ""
    
    formula = f"""```
Final Suitability = (
    Accessibility × {w_accessibility}% / 100 = {w_a:.3f} +
    Business × {w_business}% / 100 = {w_b:.3f} +
    Physical × {w_physical}% / 100 = {w_p:.3f} +
    Infrastructure × {w_infrastructure}% / 100 = {w_i:.3f} +
    Environment × {w_environmental}% / 100 = {w_e:.3f}
){mask_suffix}
```"""
    
    st.code(formula, language="text")
    
    # Final suitability map uses custom colormap (white/cream → violet/blue → yellow → orange → red)
    # st.session_state.final_heatmap_cmap = 'suitability_custom'
    st.session_state.final_heatmap_cmap = 'turbo'

    # Layer sources - USE ONLY RECLASS FILES (normalized 1-5 scale for weighted analysis)
    layer_sources = [
        ("accessibility", "reclass_accessibility.tif", "Accessibility_Map", w_a),
        ("business", "reclass_business.tif", "Business_Demand_Map", w_b),
        ("physical", "reclass_physical.tif", "Physical_Suitability_Map", w_p),
        ("infrastructure", "reclass_infrastructure.tif", "Infrastructure_Reliability_Map", w_i),
        ("environmental", "reclass_environment.tif", "Environment_Liveability_Map", w_e),
    ]

    def load_layer_info(upload_key, fallback_filename):
        upload_path = st.session_state.uploads.get(upload_key)
        source_path = upload_path or str(FINAL_ANALYSIS_PATH / fallback_filename)
        if not source_path or not Path(source_path).exists():
            return None

        with rasterio.open(source_path) as src:
            return {
                "data": src.read(1).astype(float),
                "transform": src.transform,
                "crs": src.crs,
                "nodata": src.nodata,
                "bounds": src.bounds,  # Add bounds in original CRS
            }

    def align_to_reference(layer_info, reference_info):
        source_data = np.nan_to_num(layer_info["data"], nan=0.0)
        if (
            layer_info["data"].shape == reference_info["data"].shape
            and layer_info["transform"] == reference_info["transform"]
            and layer_info["crs"] == reference_info["crs"]
        ):
            return source_data

        aligned = np.zeros(reference_info["data"].shape, dtype=np.float32)
        reproject(
            source=source_data,
            destination=aligned,
            src_transform=layer_info["transform"],
            src_crs=layer_info["crs"],
            dst_transform=reference_info["transform"],
            dst_crs=reference_info["crs"],
            resampling=Resampling.bilinear,
            src_nodata=layer_info["nodata"],
            dst_nodata=0,
        )
        return aligned
    
    st.markdown("---")
    
    if st.button('Generate Suitability Map', use_container_width=True, type="primary"):
        st.session_state.final_suitability_generated = True
    
    if st.session_state.final_suitability_generated:
        st.info('Processing uploaded and fallback layers...')
        
        try:
            layers = {}
            weight_lookup = {}
            reference_info = None

            for upload_key, fallback_filename, layer_name, weight in layer_sources:
                layer_info = load_layer_info(upload_key, fallback_filename)
                if layer_info is not None:
                    layers[layer_name] = layer_info
                    weight_lookup[layer_name] = weight
                    if reference_info is None:
                        reference_info = layer_info
            
            if layers:
                final = np.zeros(reference_info["data"].shape, dtype=np.float32)

                for layer_name, layer_info in layers.items():
                    aligned_layer = align_to_reference(layer_info, reference_info)
                    final += aligned_layer * weight_lookup[layer_name]
                
                # Initialize masking statistics
                num_masked = 0
                total_pixels = final.size
                pct_masked = 0.0
                
                # Apply constraints - CONSTRAINT MASK APPLIED
                if apply_mask:
                    constraint_path = BASE_PATH / "Banglore" / "Final Analysis" / "constraint_mask.tif"
                    if constraint_path.exists():
                        with rasterio.open(constraint_path) as src:
                            constraint_info = {
                                "data": src.read(1).astype(float),
                                "transform": src.transform,
                                "crs": src.crs,
                                "nodata": src.nodata,
                            }
                            constraint = align_to_reference(constraint_info, reference_info)
                            
                            # Get masked pixels (constraint value = 0 or close to 0)
                            masked_pixels = constraint < 0.5
                            
                            # Set masked areas to 0 in final suitability score
                            final[masked_pixels] = 0
                            
                            # Calculate masking statistics
                            num_masked = int(np.sum(masked_pixels))
                            total_pixels = masked_pixels.size
                            pct_masked = (num_masked / total_pixels * 100) if total_pixels > 0 else 0.0

                min_value = float(np.nanmin(final))
                max_value = float(np.nanmax(final))
                hotspot_threshold = float(np.nanpercentile(final, 85))
                
                # Show status of mask application
                st.markdown(f'<div style="background-color: #c8e6c9; padding: 15px; border-radius: 5px; border-left: 4px solid #2e7d32;"><i class="fas fa-check-circle"></i> <b>Constraint mask applied:</b> {num_masked:,} pixels masked ({pct_masked:.1f}%)</div>', unsafe_allow_html=True)
                
                # Calculate proper bounds from reference raster FIRST
                # Project bounds from source CRS to WGS84 (EPSG:4326)
                from rasterio.warp import transform_bounds
                ref_bounds = reference_info["bounds"]
                ref_crs = reference_info["crs"]
                
                # Transform bounds to WGS84
                if ref_crs and ref_crs.to_string() != 'EPSG:4326':
                    left, bottom, right, top = transform_bounds(ref_crs, 'EPSG:4326', ref_bounds.left, ref_bounds.bottom, ref_bounds.right, ref_bounds.top)
                else:
                    left, bottom, right, top = ref_bounds.left, ref_bounds.bottom, ref_bounds.right, ref_bounds.top
                
                center_lat = (bottom + top) / 2
                center_lon = (left + right) / 2
                
                # Store final suitability in session state for comparison in ML section
                st.session_state.final_suitability_data = final.copy()
                st.session_state.suitability_bounds = (left, bottom, right, top)
                
                st.markdown("---")
                col_map, col_gray = st.columns(2)
                
                with col_map:
                    st.markdown('<h4 style="color: #0066cc;"><i class="fas fa-map"></i> Final Suitability - Map View</h4>', unsafe_allow_html=True)
                    
                    # Use bounds already calculated above
                    leaflet_bounds_str = f"[[{bottom}, {left}], [{top}, {right}]]"
                    final_base64 = raster_to_colored_base64_image(final, cmap_name=st.session_state.final_heatmap_cmap, mask_zero=False)
                    
                    # 2. BLACK MASK OVERLAY 
                    # This specifically creates a layer where restricted = Black, buildable = Transparent
                    black_mask_base64 = None
                    # BLACK MASK OVERLAY DISABLED FOR NOW
                    # if apply_mask:
                    #     constraint_file = BASE_PATH / "Banglore" / "Raster" / "Final Analysis" / "constraint_map.tif"
                    #     if constraint_file.exists():
                    #         with rasterio.open(constraint_file) as c_src:
                    #             c_data = c_src.read(1).astype(float)
                    #             # Set restricted areas to 0.0 (Pure Black in 'gray' cmap) and others to NaN
                    #             black_zones = np.where(c_data < 0.5, 0.0, np.nan)
                    #             
                    #             # Use 'gray' colormap - 0.0 is always Black
                    #             black_mask_base64 = raster_to_colored_base64_image(black_zones, cmap_name='gray')
                    
                    overlay_scripts = []

                    # Add the colorful suitability map first
                    if final_base64:
                        overlay_scripts.append(f"""
                        var suitability_img = new Image();
                        suitability_img.src = '{final_base64}';
                        suitability_img.onload = function() {{
                            L.imageOverlay(suitability_img.src, {leaflet_bounds_str}, {{
                                opacity: 0.85,
                                zIndex: 1
                            }}).addTo(map);
                        }};
                        """)

                    # Add the SOLID BLACK MASK on top
                    if black_mask_base64:
                        overlay_scripts.append(f"""
                        var black_mask_img = new Image();
                        black_mask_img.src = '{black_mask_base64}';
                        black_mask_img.onload = function() {{
                            L.imageOverlay(black_mask_img.src, [[13.0, 77.4], [13.4, 77.8]], {{
                                opacity: 1.0,  // Full opacity for solid black regions
                                zIndex: 10,    // Ensure it's on top of the suitability map
                                interactive: false
                            }}).addTo(map);
                        }};
                        """)
                    
                    all_overlays = "\n".join(overlay_scripts)
                    
                    # Leaflet Map Component
                    leaflet_html = f"""
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
                    <div id="map" style="height: 550px; width: 100%; background: #f0f0f0;"></div>
                    <script>
                        var map = L.map('map').setView([{center_lat}, {center_lon}], 12);
                        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                            attribution: '© OpenStreetMap contributors',
                            maxZoom: 19
                        }}).addTo(map);
                        
                        {all_overlays}
                        
                        // Fit map to raster bounds
                        var bounds = {leaflet_bounds_str};
                        map.fitBounds(bounds);
                    </script>
                    """
                    components.html(leaflet_html, height=600)
                
                with col_gray:
                    st.markdown('<h4 style="color: #0066cc;"><i class="fas fa-image"></i> Final Suitability - Color Heatmap</h4>', unsafe_allow_html=True)
                    
                    fig, ax = plt.subplots(figsize=(8, 6))
                    # Fill NaN values with minimum value to avoid white spots
                    final_filled = np.nan_to_num(final, nan=min_value)
                    im = ax.imshow(final_filled, cmap=st.session_state.final_heatmap_cmap, aspect='auto', vmin=min_value, vmax=max_value)
                    ax.set_title("Final Result", fontweight='bold')
                    ax.set_xlabel("X (pixels)")
                    ax.set_ylabel("Y (pixels)")
                    cbar = plt.colorbar(im, ax=ax, label="Suitability Score")
                    
                    # Set colorbar ticks to show 1-5 within the data range
                    cbar_ticks = np.linspace(min_value, max_value, 5)
                    cbar.set_ticks(cbar_ticks)
                    cbar.set_ticklabels(['1', '2', '3', '4', '5'])
                    
                    st.pyplot(fig, use_container_width=True)
                    plt.close()
                    
                    # Add legend table for score interpretation
                    st.markdown('<h4 style="color: #0066cc; margin-top: 20px;"><i class="fas fa-table"></i> Suitability Score Legend</h4>', unsafe_allow_html=True)
                    
                    # Create score legend data
                    score_range_low = min_value
                    score_range_high = max_value
                    score_range = score_range_high - score_range_low
                    
                    legend_data = {
                        'Level': ['1: Poor', '2: Fair', '3: Moderate', '4: Good', '5: Excellent'],
                        'Range': [
                            f'{score_range_low:.2f} - {score_range_low + score_range*0.2:.2f}',
                            f'{score_range_low + score_range*0.2:.2f} - {score_range_low + score_range*0.4:.2f}',
                            f'{score_range_low + score_range*0.4:.2f} - {score_range_low + score_range*0.6:.2f}',
                            f'{score_range_low + score_range*0.6:.2f} - {score_range_low + score_range*0.8:.2f}',
                            f'{score_range_low + score_range*0.8:.2f} - {score_range_high:.2f}'
                        ],
                        'Description': [
                            '⚫ Not suitable for IT park development',
                            '🟢 Marginally suitable for IT park development',
                            '🟡 Moderately suitable for IT park development',
                            '🟠 Suitable for IT park development',
                            '🔴 Highly suitable (Prime Zone) for IT park development'
                        ]
                    }
                    
                    df_legend = pd.DataFrame(legend_data)
                    st.dataframe(df_legend, use_container_width=True, hide_index=True)
            else:
                st.warning("Upload at least one layer map or make sure the project TIFFs exist in Banglore/Raster/IT.")
        
        except Exception as e:
            st.error(f"Error: {e}")
        
        # ==================== ML PREDICTION COMPARISON ====================
        if layers:  # Only show ML prediction if we have valid layers
            st.markdown("---")
            st.markdown('<h3 style="color: #0066cc;"><i class="fas fa-brain"></i> Apply ML Prediction</h3>', unsafe_allow_html=True)
            st.markdown("Compare final suitability with ML-based predictions")
            
            ML_RESULTS_PATH = Path(__file__).parent / "ML_Results"
            ml_pred_path = ML_RESULTS_PATH / "ml_classifier_predictions.tif"
            
            if ml_pred_path.exists():
                if st.button('Predict', use_container_width=True, type="primary", key="ml_predict_btn"):
                    st.session_state.ml_prediction_shown = True
                
                if st.session_state.ml_prediction_shown:
                    try:
                        # ===== LIVE PREDICTION: Run the trained model on the features =====
                        st.info("🔄 Running ML prediction on feature maps...")
                        
                        # Import ML dependencies
                        from sklearn.ensemble import RandomForestClassifier
                        import pickle
                        import warnings
                        
                        # Load trained model and scaler
                        ML_RESULTS_PATH = Path(__file__).parent / "ML_Results"
                        model_path = ML_RESULTS_PATH / "trained_model.pkl"
                        scaler_path = ML_RESULTS_PATH / "scaler.pkl"
                        
                        if not model_path.exists():
                            st.error("⚠️ Trained model not found. Run `python ml_simple.py` to train the model.")
                            st.stop()
                        
                        try:
                            with open(model_path, 'rb') as f:
                                trained_model = pickle.load(f)
                        except (TypeError, ValueError) as e:
                            # Handle sklearn version compatibility issues
                            if "incompatible dtype" in str(e) or "missing_go_to_left" in str(e):
                                st.warning("⚠️ Model format incompatible with current sklearn version. Retrain the model by running: `python ml_simple.py`")
                                st.stop()
                            raise
                        
                        try:
                            with open(scaler_path, 'rb') as f:
                                scaler = pickle.load(f)
                        except Exception as e:
                            st.error(f"Error loading scaler: {str(e)}")
                            st.stop()
                        
                        st.success("✅ Model loaded successfully!")
                        
                        # Extract features from the same layers used for Final Suitability
                        feature_names = ['Accessibility_Map', 'Business_Demand_Map', 'Physical_Suitability_Map', 
                                        'Infrastructure_Reliability_Map', 'Environment_Liveability_Map']
                        features_dict = {}
                        
                        for feature_name, layer_info in layers.items():
                            aligned_layer = align_to_reference(layer_info, reference_info)
                            features_dict[feature_name] = aligned_layer
                        
                        # Stack features into (height, width, num_features)
                        height, width = reference_info["data"].shape
                        num_features = len(features_dict)
                        
                        feature_array = np.zeros((height, width, num_features), dtype=np.float64)
                        for idx, (fname, fdata) in enumerate(features_dict.items()):
                            # Ensure data is float64 before assignment
                            fdata_float = np.asarray(fdata, dtype=np.float64)
                            feature_array[:, :, idx] = np.nan_to_num(fdata_float, nan=0.0)
                        
                        # Reshape to (num_pixels, num_features) as float64
                        X = feature_array.reshape(-1, num_features).astype(np.float64)
                        
                        st.info(f"🔮 Predicting on {X.shape[0]:,} pixels with {X.shape[1]} features...")
                        
                        # Scale features using the same scaler from training
                        X_scaled = scaler.transform(X).astype(np.float64)
                        
                        # Run prediction
                        predictions = trained_model.predict(X_scaled)
                        
                        # Reshape predictions back to (height, width)
                        ml_pred_data = predictions.reshape(height, width).astype(float)
                        
                        st.success("✅ Prediction complete!")
                        
                        # APPLY CONSTRAINT MASK to ML predictions
                        constraint_path = BASE_PATH / "Banglore" / "Final Analysis" / "constraint_mask.tif"
                        if constraint_path.exists():
                            with rasterio.open(constraint_path) as src:
                                constraint_info = {
                                    "data": src.read(1).astype(float),
                                    "transform": src.transform,
                                    "crs": src.crs,
                                    "nodata": src.nodata,
                                }
                                constraint = align_to_reference(constraint_info, reference_info)
                                
                                # Mask out restricted areas (constraint value < 0.5)
                                masked_pixels_ml = constraint < 0.5
                                ml_pred_data[masked_pixels_ml] = 0
                                
                                # Calculate masking statistics
                                num_masked_ml = int(np.sum(masked_pixels_ml))
                                pct_masked_ml = (num_masked_ml / masked_pixels_ml.size * 100) if masked_pixels_ml.size > 0 else 0.0
                        
                        st.markdown("---")
                        st.markdown(f'<div style="background-color: #c8e6c9; padding: 15px; border-radius: 5px; border-left: 4px solid #2e7d32;"><i class="fas fa-check-circle"></i> <b>Constraint mask applied to ML prediction:</b> {num_masked_ml:,} pixels masked ({pct_masked_ml:.1f}%)</div>', unsafe_allow_html=True)
                        
                        st.markdown("---")
                        col_map, col_heat = st.columns(2)
                        
                        # MAP VIEW (LEAFLET)
                        with col_map:
                            st.markdown('<h4 style="color: #0066cc;"><i class="fas fa-map"></i> ML Prediction - Map View</h4>', unsafe_allow_html=True)
                            
                            # Use the same bounds as Final Suitability Map for spatial alignment
                            leaflet_bounds_str = f"[[{bottom}, {left}], [{top}, {right}]]"
                            center_lat = (bottom + top) / 2
                            center_lon = (left + right) / 2
                            
                            # Convert ML predictions to base64 image - Apply mask_zero=True to show masked areas as black
                            # Use vmin=0, vmax=5 to match the heatmap scale
                            ml_base64 = raster_to_colored_base64_image(ml_pred_data.astype(float), cmap_name='turbo', mask_zero=True, vmin=0, vmax=5)
                            
                            # Leaflet Map
                            leaflet_html = f"""
                            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
                            <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
                            <div id="ml_map" style="height: 550px; width: 100%; background: #f0f0f0;"></div>
                            <script>
                                var map = L.map('ml_map').setView([{center_lat}, {center_lon}], 12);
                                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                                    attribution: '© OpenStreetMap contributors',
                                    maxZoom: 19
                                }}).addTo(map);
                                
                                var ml_img = new Image();
                                ml_img.src = '{ml_base64}';
                                ml_img.onload = function() {{
                                    L.imageOverlay(ml_img.src, {leaflet_bounds_str}, {{
                                        opacity: 0.85,
                                        zIndex: 1
                                    }}).addTo(map);
                                }};
                                
                                var bounds = {leaflet_bounds_str};
                                map.fitBounds(bounds);
                            </script>
                            """
                            components.html(leaflet_html, height=600)
                        
                        # HEATMAP VIEW
                        with col_heat:
                            st.markdown('<h4 style="color: #0066cc;"><i class="fas fa-image"></i> ML Prediction - Heatmap</h4>', unsafe_allow_html=True)
                            
                            fig, ax = plt.subplots(figsize=(8, 6))
                            ml_filled = np.nan_to_num(ml_pred_data.astype(float), nan=0)
                            im = ax.imshow(ml_filled, cmap='turbo', aspect='auto', vmin=0, vmax=5)
                            ax.set_title("ML Predictions with Constraint Mask Applied", fontweight='bold')
                            ax.set_xlabel("X (pixels)")
                            ax.set_ylabel("Y (pixels)")
                            cbar = plt.colorbar(im, ax=ax, label="Suitability Score")
                            cbar.set_ticks([1, 2, 3, 4, 5])
                            cbar.set_ticklabels(['1', '2', '3', '4', '5'])
                            
                            st.pyplot(fig, use_container_width=True)
                            plt.close()
                        
                        # LEGEND TABLE
                        st.markdown("---")
                        st.markdown('<h4 style="color: #0066cc;"><i class="fas fa-table"></i> ML Prediction - Score Legend</h4>', unsafe_allow_html=True)
                        
                        # Convert to int for bincount (predictions are 1-5, 0 is masked)
                        ml_pred_int = ml_pred_data.astype(np.int32)
                        class_counts = np.bincount(ml_pred_int[ml_pred_int > 0], minlength=6)[1:]
                        total_valid = np.sum(ml_pred_int > 0)
                        
                        ml_legend_data = {
                            'Level': ['1: Low', '2: Below Avg', '3: Average', '4: Above Avg', '5: High'],
                            'Range': ['0.0 - 1.0', '1.0 - 2.0', '2.0 - 3.0', '3.0 - 4.0', '4.0 - 5.0'],
                            'Description': [
                                '⚫ Low suitability for IT park',
                                '🟢 Below average suitability',
                                '🟡 Average suitability',
                                '🟠 Above average suitability',
                                '🔴 Highly suitable (Prime Zone)'
                            ]
                        }
                        
                        ml_df_legend = pd.DataFrame(ml_legend_data)
                        st.dataframe(ml_df_legend, use_container_width=True, hide_index=True)
                        
                        # COMPARISON SECTION
                        st.markdown("---")
                        st.markdown('<h3 style="color: #0066cc;"><i class="fas fa-exchange-alt"></i> Methodology Comparison: Weighted Overlay vs ML Prediction</h3>', unsafe_allow_html=True)
                        
                        # SIDE-BY-SIDE MAP COMPARISON
                        comp_col1, comp_col2 = st.columns(2)
                        
                        # Use Final Suitability from session state
                        if hasattr(st.session_state, 'final_suitability_data'):
                            final_comp = st.session_state.final_suitability_data
                            bounds_tuple = st.session_state.suitability_bounds
                            left_b, bottom_b, right_b, top_b = bounds_tuple
                        else:
                            st.error("Final Suitability data not available for comparison. Please generate it first.")
                            final_comp = None
                        
                        if final_comp is not None and ml_pred_data is not None:
                            # Convert both to base64 for comparison maps - USING SAME TURBO COLORMAP with fixed scale 0-5
                            final_comp_base64 = raster_to_colored_base64_image(final_comp.astype(float), cmap_name='turbo', mask_zero=False, vmin=0, vmax=5)
                            ml_comp_base64 = raster_to_colored_base64_image(ml_pred_data.astype(float), cmap_name='turbo', mask_zero=False, vmin=0, vmax=5)
                            
                            # LEFT: FINAL SUITABILITY
                            with comp_col1:
                                st.markdown('<h4 style="color: #0066cc;"><i class="fas fa-tasks"></i> Weighted Overlay Result</h4>', unsafe_allow_html=True)
                                
                                comp_leaflet_bounds_str = f"[[{bottom_b}, {left_b}], [{top_b}, {right_b}]]"
                                
                                comp_leaflet_html_1 = f"""
                                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
                                <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
                                <div id="comp_map_1" style="height: 450px; width: 100%; background: #f0f0f0;"></div>
                                <script>
                                    var map1 = L.map('comp_map_1').setView([{(bottom_b + top_b) / 2}, {(left_b + right_b) / 2}], 12);
                                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                                        attribution: '© OpenStreetMap contributors',
                                        maxZoom: 19
                                    }}).addTo(map1);
                                    
                                    var final_img = new Image();
                                    final_img.src = '{final_comp_base64}';
                                    final_img.onload = function() {{
                                        L.imageOverlay(final_img.src, {comp_leaflet_bounds_str}, {{
                                            opacity: 0.85,
                                            zIndex: 1
                                        }}).addTo(map1);
                                    }};
                                    
                                    var bounds = {comp_leaflet_bounds_str};
                                    map1.fitBounds(bounds);
                                </script>
                                """
                                components.html(comp_leaflet_html_1, height=500)
                            
                            # RIGHT: ML PREDICTION
                            with comp_col2:
                                st.markdown('<h4 style="color: #0066cc;"><i class="fas fa-robot"></i> ML Classifier Prediction</h4>', unsafe_allow_html=True)
                                
                                comp_leaflet_html_2 = f"""
                                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
                                <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
                                <div id="comp_map_2" style="height: 450px; width: 100%; background: #f0f0f0;"></div>
                                <script>
                                    var map2 = L.map('comp_map_2').setView([{(bottom_b + top_b) / 2}, {(left_b + right_b) / 2}], 12);
                                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                                        attribution: '© OpenStreetMap contributors',
                                        maxZoom: 19
                                    }}).addTo(map2);
                                    
                                    var ml_img = new Image();
                                    ml_img.src = '{ml_comp_base64}';
                                    ml_img.onload = function() {{
                                        L.imageOverlay(ml_img.src, {comp_leaflet_bounds_str}, {{
                                            opacity: 0.85,
                                            zIndex: 1
                                        }}).addTo(map2);
                                    }};
                                    
                                    var bounds = {comp_leaflet_bounds_str};
                                    map2.fitBounds(bounds);
                                </script>
                                """
                                components.html(comp_leaflet_html_2, height=500)
                        
                    except Exception as e:
                        st.error(f"Error loading ML prediction: {e}")
            else:
                st.info("ML Prediction data not available. Run `python ml_simple.py` in the Dashboard folder to generate predictions.")

elif clean_option == "Layers":
    st.markdown("---")
    st.markdown('## <i class="fas fa-map"></i> All Layers', unsafe_allow_html=True)
    
    # If no category selected, show category selection screen
    if st.session_state.selected_layer_category is None:
        st.markdown("**Select a layer category to browse**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶ Vector Layers", key="btn_vector", use_container_width=True):
                st.session_state.selected_layer_category = "vector"
                st.rerun()
        
        with col2:
            if st.button("▶ Raster Layers", key="btn_raster", use_container_width=True):
                st.session_state.selected_layer_category = "raster"
                st.rerun()
        
        with col3:
            if st.button("▶ Proximity Maps", key="btn_proximity", use_container_width=True):
                st.session_state.selected_layer_category = "proximity"
                st.rerun()
        
        col4, col5 = st.columns(2)
        
        with col4:
            if st.button("▶ Reclassified", key="btn_reclass", use_container_width=True):
                st.session_state.selected_layer_category = "reclassified"
                st.rerun()
        
        with col5:
            if st.button("▶ Masks", key="btn_masks", use_container_width=True):
                st.session_state.selected_layer_category = "masks"
                st.rerun()
    
    # If category selected, show layers for that category
    else:
        # Back button at the right
        col_title, col_back = st.columns([5, 1])
        with col_title:
            category_display = {
                'vector': 'Vector Layers',
                'raster': 'Core Raster Layers',
                'proximity': 'Proximity Maps',
                'reclassified': 'Reclassified Layers',
                'masks': 'Constraint Mask Layers'
            }
            st.markdown(f"### {category_display.get(st.session_state.selected_layer_category, 'Layers')}")
        
        with col_back:
            if st.button("← Back", key="btn_back", use_container_width=True):
                st.session_state.selected_layer_category = None
                st.rerun()
        
        st.markdown("---")
        
        # Display layers based on selected category
        if st.session_state.selected_layer_category == "vector":
            if vector_layers:
                for layer in vector_layers:
                    with st.expander(f"▶ {layer}", expanded=False):
                        try:
                            layer_path = VECTOR_PATH / f"{layer}.gpkg"
                            render_vector_layer(layer_path, layer)
                        except Exception as e:
                            st.error(f"Error loading {layer}: {e}")
            else:
                st.info("No vector layers found")
        
        elif st.session_state.selected_layer_category == "raster":
            if raster_layers:
                for layer_name in raster_layers:
                    with st.expander(f"▶ {layer_name}", expanded=False):
                        layer_path = RASTER_PATH / f"{layer_name}.tif"
                        if layer_path.exists():
                            try:
                                render_raster_with_map(str(layer_path), layer_name)
                            except Exception as e:
                                st.error(f"Error loading {layer_name}: {e}")
            else:
                st.info("No core raster layers found")
        
        elif st.session_state.selected_layer_category == "proximity":
            if proximity_rasters:
                for layer_name in proximity_rasters:
                    with st.expander(f"▶ {layer_name}", expanded=False):
                        layer_path = RASTER_PATH / f"{layer_name}.tif"
                        if layer_path.exists():
                            try:
                                render_raster_with_map(str(layer_path), layer_name)
                            except Exception as e:
                                st.error(f"Error loading {layer_name}: {e}")
            else:
                st.info("No proximity layers found")
        
        elif st.session_state.selected_layer_category == "reclassified":
            if reclass_rasters:
                for layer_name in reclass_rasters:
                    with st.expander(f"▶ {layer_name}", expanded=False):
                        layer_path = RASTER_PATH / f"{layer_name}.tif"
                        if layer_path.exists():
                            try:
                                render_raster_with_map(str(layer_path), layer_name)
                            except Exception as e:
                                st.error(f"Error loading {layer_name}: {e}")
            else:
                st.info("No reclassified layers found")
        
        elif st.session_state.selected_layer_category == "masks":
            if mask_layers:
                for layer_name in mask_layers:
                    with st.expander(f"▶ {layer_name}", expanded=False):
                        layer_path = RASTER_PATH / f"{layer_name}.tif"
                        if layer_path.exists():
                            try:
                                render_raster_with_map(str(layer_path), layer_name)
                            except Exception as e:
                                st.error(f"Error loading {layer_name}: {e}")
            else:
                st.info("No mask layers found")

elif clean_option == "Model":
    st.markdown("---")
    st.markdown('## <i class="fas fa-brain"></i> ML Model Information & Statistics', unsafe_allow_html=True)
    
    st.markdown("---")
    
    ML_RESULTS_PATH = Path(__file__).parent / "ML_Results"
    ml_pred_path = ML_RESULTS_PATH / "ml_classifier_predictions.tif"
    
    if ml_pred_path.exists():
        try:
            with rasterio.open(ml_pred_path) as src:
                ml_pred_data = src.read(1)
            
            # Model Statistics (Expanded by default)
            st.markdown('### <i class="fas fa-chart-bar"></i> Model Statistics', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            
            valid_pixels = np.sum(ml_pred_data > 0)
            restricted_pixels = np.sum(ml_pred_data == 0)
            
            with col1:
                st.metric("Total Pixels", f"{ml_pred_data.size:,}")
            with col2:
                st.metric("Valid Pixels", f"{valid_pixels:,}")
            with col3:
                st.metric("Restricted Areas", f"{restricted_pixels:,}")
            with col4:
                st.metric("Test Accuracy", "99.83%")
            
            st.markdown("---")
            
            # Model Information
            st.markdown('### <i class="fas fa-info-circle"></i> Model Information', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **Algorithm Details:**
                - **Algorithm:** Random Forest Classifier
                - **Number of Trees:** 100 estimators
                - **Max Depth:** 20
                - **Feature Importance:** Auto-calculated
                - **Output Classes:** 5 (Low to High Suitability)
                """)
            
            with col2:
                st.markdown("""
                **Training Data:**
                - **Training Samples:** 235,677 pixels
                - **Test Samples:** 78,560 pixels
                - **Data Split:** 75% train / 25% test
                - **Features Used:** 5 suitability criteria
                - **Validation Accuracy:** 99.83%
                """)
            
            st.markdown("---")
            
            st.markdown("""
            **Features Used in Model:**
            1. **Accessibility Map** - Roads, bus stops, railway, airport proximity
            2. **Business Demand Map** - IT hubs, industrial areas, population, power
            3. **Physical Suitability Map** - Slope, land use, water availability
            4. **Infrastructure Reliability Map** - Power supply, built-up areas, road network
            5. **Environmental & Social Map** - Temperature, vegetation, hospitals, amenities
            """)
        
        except Exception as e:
            st.error(f"Error loading ML model data: {e}")
    
    else:
        st.warning("ML Model data not found. Please run the ML training script first.")
        st.info("Run: `python ml_simple.py` in the Dashboard folder to generate model data.")

st.markdown("---")

with st.expander('Layer Composition Reference'):
    st.markdown("""
| Layer | Components |
|-------|-----------|
| Accessibility | Roads 40% + Bus 30% + Railway 20% + Airport 10% |
| Business_Demand | IT Hubs 40% + Industrial 20% + Population 20% + Power 20% |
| Physical | Slope 50% + Land Use 30% + Water 20% |
| Infrastructure | Power 50% + Built-up 30% + Roads 20% |
| Environment | Temp 25% + Veg 25% + Hospital 25% + Amenities 15% + Pop 10% |
| Constraint | Water • Railway • Settlements • Protected Areas |
    """)

st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; margin-top: 40px; border-top: 2px solid #e0e0e0;'>
    <p style='color: #666; margin: 0;'><small>IT Park Development Zone Analysis Tool | Bengaluru IT Corridor | Built with Streamlit & GIS</small></p>
</div>
""", unsafe_allow_html=True)

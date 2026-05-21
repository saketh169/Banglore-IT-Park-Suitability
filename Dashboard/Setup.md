# GEOTA IT Park DSS - Web Dashboard Setup & Deployment Guide


Analyzed file: C:\Users\saket\SEM6-PROJECTS\GEOTA\Banglore\Raster\Final Analysis\Output Result.tif (band 1)

Extent: 784187.5633999999845400,1425830.5667000000830740 : 806927.5633999999845400,1444010.5667000000830740

Projection: EPSG:32643 - WGS 84 / UTM zone 43N

Width in pixels: 758 (units per pixel 30)

Height in pixels: 606 (units per pixel 30)

Total pixel count: 459348

NoData pixel count: 115825

Value	Pixel count	Area (m²)
0	144087	129678300
1.27	1	900
1.3	1	900
1.6	16	14400
1.7	5	4500
1.75	16	14400
1.79	1	900
1.8	1	900
1.85	10	9000
1.9	20	18000
1.95	18	16200
2	76	68400
2.05	23	20700
2.09	1	900
2.1	40	36000
2.15	284	255600
2.16	1	900
2.2	10	9000
2.22	2	1800
2.25	847	762300
2.28	1	900
2.3	406	365400
2.31	7	6300
2.35	55	49500
2.37	4	3600
2.4	2099	1889100
2.45	508	457200
2.46	2	1800
2.5	161	144900
2.52	5	4500
2.55	3436	3092400
2.6	383	344700
2.62	3	2700
2.65	801	720900
2.67	2	1800
2.7	6195	5575500
2.75	715	643500
2.77	5	4500
2.8	1156	1040400
2.83	1	900
2.85	6465	5818500
2.9	1336	1202400
2.92	2	1800
2.95	1949	1754100
2.96	1	900
3	3900	3510000
3.01	1	900
3.05	2776	2498400
3.1	3240	2916000
3.11	2	1800
3.15	2428	2185200
3.2	4957	4461300
3.25	2893	2603700
3.26	1	900
3.3	6330	5697000
3.32	2	1800
3.35	3903	3512700
3.4	1864	1677600
3.45	13424	12081600
3.5	2023	1820700
3.55	1020	918000
3.6	19532	17578800
3.65	1340	1206000
3.7	2202	1981800
3.75	20776	18698400
3.8	711	639900
3.85	5092	4582800
3.9	12284	11055600
3.95	291	261900
4	12722	11449800
4.05	3613	3251700
4.1	311	279900
4.15	14586	13127400
4.2	649	584100
4.25	1200	1080000
4.3	11580	10422000
4.35	152	136800
4.4	2527	2274300
4.45	5495	4945500
4.55	2845	2560500
4.6	1021	918900
4.7	2610	2349000
4.75	100	90000
4.85	1903	1712700
5	59	53100


## 📋 Overview
This is a Streamlit-based Decision Support System (DSS) for IT Park site suitability analysis in Bengaluru. It enables interactive weighted overlay analysis with real-time map visualization.

---

## 🛠️ Technology Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| **Web Framework** | Streamlit | Fast Python web UI for data apps |
| **Map Engine** | Folium/Leaflet | Interactive spatial visualization |
| **GIS Processing** | GeoPandas + Rasterio | Vector and raster data handling |
| **Charts** | Plotly | Interactive data visualization |
| **Deployment** | Streamlit Cloud | Free hosting (or Docker locally) |

---

## 🔬 Sub-Thematic Query Formulas

These are the 5 core weighted overlay calculations used to generate the final suitability map:

### **1. Accessibility_Map**
**Goal:** Measuring transport and connectivity.
```sql
("reclass_roads@1" * 0.4) + ("reclass_busStop@1" * 0.3) + ("reclass_railway@1" * 0.2) + ("reclass_airport@1" * 0.1)
```
**Weights:** Roads (40%) | Bus Stops (30%) | Railway (20%) | Airport (10%)

---

### **2. Business_Demand_Map**
**Goal:** Measuring economic clusters and workforce.
```sql
("reclass_it-hubs@1" * 0.4) + ("reclass_industrial@1" * 0.2) + ("reclass_population@1" * 0.2) + ("reclass_power@1" * 0.2)
```
**Weights:** IT Hubs (40%) | Industrial (20%) | Population (20%) | Power (20%)

---

### **3. Physical_Suitability_Map**
**Goal:** Measuring construction ease and terrain.
```sql
("reclass_slope@1" * 0.5) + ("reclass_LULC@1" * 0.3) + ("reclass_NDWI@1" * 0.2)
```
**Weights:** Slope (50%) | Land Use/Land Cover (30%) | Water Index (20%)

---

### **4. Infrastructure_Reliability_Map**
**Goal:** Measuring utility readiness and urban stability.
```sql
("reclass_power@1" * 0.5) + ("reclass_NDBI@1" * 0.3) + ("reclass_roads@1" * 0.2)
```
**Weights:** Power (50%) | Built-up Index (30%) | Roads (20%)

---

### **5. Environmental_Social_Map**
**Goal:** Measuring quality of life and sustainability (Park layer removed).
```sql
("reclass_LST@1" * 0.30) + ("reclass_NDVI@1" * 0.30) + ("reclass_hospital@1" * 0.25) + ("reclass_amenities@1" * 0.15)
```
**Weights:** Land Surface Temperature (30%) | Vegetation Index (30%) | Hospitals (25%) | Amenities (15%)

---

### **Final Weighted Overlay**
These 5 sub-maps are combined with the following weights:

```sql
(Accessibility_Map * 0.25) + (Business_Demand_Map * 0.30) + (Physical_Suitability_Map * 0.15) + (Infrastructure_Reliability_Map * 0.15) + (Environmental_Social_Map * 0.15)
```

**Final Weights:**
| Factor | Weight |
|--------|--------|
| **Accessibility** | 25% |
| **Business Demand** | 30% |
| **Physical Suitability** | 15% |
| **Infrastructure Reliability** | 15% |
| **Environmental & Social** | 15% |

---

## 📦 Installation & Setup

### Step 1: Create Python Environment
```bash
# Navigate to Dashboard folder
cd c:\Users\saket\SEM6-PROJECTS\GEOTA\Dashboard

# Create virtual environment
python -m venv venv

# Activate environment
## On Windows:
venv\Scripts\activate

## On MacOS/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Verify File Structure
Your Dashboard folder should look like:
```
Dashboard/
├── app.py                    (main Streamlit app)
├── requirements.txt          (Python dependencies)
└── utils/
    ├── __init__.py          (empty file)
    ├── processors.py        (raster/vector processing)
    ├── map_builder.py       (map visualization)
    └── chart_builder.py     (charts & analytics)
```

---

## 🚀 Running Locally

### Option A: Using Streamlit (Development)
```bash
streamlit run app.py
```

The app will open at: `http://localhost:8501`

### Option B: Using Python Direct (No Streamlit)
```bash
python app.py
```

---

## 🌐 Deployment Options

### **1. Streamlit Cloud (Easiest - FREE)**

#### Prerequisites:
- GitHub account
- Streamlit Cloud account (free)
- Your code on GitHub

#### Steps:
1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add GEOTA Dashboard"
   git push origin main
   ```

2. **Go to Streamlit Cloud:**
   - Visit: https://share.streamlit.io
   - Click "New app"
   - Select your GitHub repo
   - Select `Dashboard/app.py` as main file
   - Click "Deploy"

3. **Share URL:**
   - Your app is now live at: `https://share.streamlit.io/[username]/[repo]/app.py`

---

### **2. Docker (Local Server)**

#### Create `Dockerfile`:
```dockerfile
FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Run Docker:
```bash
docker build -t geota-dss .
docker run -p 8501:8501 geota-dss
```

Access at: `http://localhost:8501`

---

### **3. Using Gunicorn (Production)**

#### Install Gunicorn:
```bash
pip install gunicorn
```

#### Run:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## ⚙️ Configuration & Customization

### Adjust Raster Paths
In `app.py`, modify line 42-43:
```python
RASTER_PATH = BASE_PATH / "Banglore" / "Raster" / "IT"
VECTOR_PATH = BASE_PATH / "Banglore" / "Vector" / "IT"
```

### Change Default Weights
In the sidebar section (around line 95), modify default values:
```python
weights['Roads'] = st.sidebar.slider("Roads", 0, 100, **25**, key="roads") / 100
#                                                          ^^
#                                                    Change this (default: 25%)
```

### Adjust Map Center & Zoom
In the map creation (around line 180):
```python
m = MapBuilder.create_base_map(
    center_lat=13.0,      # Latitude (13.0 = Bengaluru)
    center_lon=77.7,      # Longitude
    zoom_level=12         # Zoom (1=world, 20=building)
)
```

---

## 📊 Features Explanation

### 1. **Weighted Overlay Mode**
- Adjust sliders to change layer importance
- Result updates in real-time
- Hard constraints black out restricted zones
- Visualize on satellite base map

### 2. **Individual Layer View**
- Inspect single layers in detail
- View value distribution histogram
- Check min/max/mean statistics

### 3. **Constraint Analysis**
- Understand what areas are restricted
- See percentage of developable land
- Toggle off specific constraints dynamically

---

## 🔧 Troubleshooting

### Issue: "No module named 'streamlit'"
**Solution:**
```bash
pip install streamlit
```

### Issue: "Raster not found"
**Solution:**
1. Check file paths in `app.py`
2. Verify `.tif` files exist in `Banglore/Raster/IT/`
3. Ensure file names match exactly (case-sensitive on Unix)

### Issue: "Port 8501 already in use"
**Solution:**
```bash
streamlit run app.py --server.port=8502
```

### Issue: Map not displaying
**Solution:**
- Clear browser cache (Ctrl+Shift+Delete)
- Try incognito mode
- Check internet connection (requires tile servers)

---

## 📝 Adding New Layers

To add a new reclassified layer:

1. **In `app.py`, modify `layer_files` dict (line ~125):**
   ```python
   layer_files = {
       'Roads': 'reclass_roads.tif',
       'Your_Layer': 'reclass_your_layer.tif',  # ADD THIS
       'Airport': 'reclass_airport.tif',
   }
   ```

2. **Add slider in sidebar (line ~95):**
   ```python
   weights['Your_Layer'] = st.sidebar.slider("Your Layer", 0, 100, 10, key="yourlayer") / 100
   ```

---

## 📚 API Reference

### `RasterProcessor` Class
```python
processor = RasterProcessor(raster_folder_path)
data, profile = processor.load_raster("filename.tif")
normalized = processor.normalize_raster(data)
result = processor.weighted_overlay(layers_dict, weights_dict)
masked = processor.apply_mask(raster, mask)
```

### `MapBuilder` Class
```python
m = MapBuilder.create_base_map(center_lat, center_lon, zoom_level)
MapBuilder.add_raster_heatmap(m, raster_data, bounds, name, opacity)
MapBuilder.add_vector_layer(m, gdf, name, color)
MapBuilder.add_marker_popup(m, lat, lon, popup_text, icon_color)
```

### `ChartBuilder` Class
```python
fig = ChartBuilder.create_radar_chart(scores_dict, title)
fig = ChartBuilder.create_score_bar_chart(scores_dict, title)
fig = ChartBuilder.create_weight_summary(weights_dict)
```

---

## 🎯 Next Steps (Phase 2)

- Add **Point-Click Query Tool** to get pixel-level scores
- Implement **Radar/Scorecard Charts** for selected sites
- Add **Export to GIS** functionality (generate shapefile)
- Integrate **Machine Learning** for site ranking
- Add **Time-Series Analysis** for temporal trends
- Build **Multi-Criteria Decision Analysis (MCDA)** interface

---

## 📞 Support & Documentation

- Streamlit Docs: https://docs.streamlit.io
- Folium Docs: https://python-visualization.github.io/folium/
- GeoPandas Docs: https://geopandas.org
- Rasterio Docs: https://rasterio.readthedocs.io
- Plotly Docs: https://plotly.com/python/

---

## 📄 License & Attribution

**Project:** GEOTA - GIS-based Environmental & Occupational Technology Analysis  
**Institution:** SEM6 Academic Project  
**Study Area:** Mahadevapura IT Corridor, Bengaluru  
**Status:** v1.0 - Interactive Decision Support System

---

**Last Updated:** April 5, 2026  
**Status:** Ready for Deployment

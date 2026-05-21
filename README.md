# IT Park Development Zone Analysis in Bangalore Using GIS and Remote Sensing

**Project ID:** S20230010169  
**Study Area:** Mahadevapura IT Corridor, East Bengaluru  
**Recommended Project CRS:** EPSG:32643 — WGS 84 / UTM Zone 43N  
**Main GIS Software:** QGIS  

---

## 1. Project Aim

This project is a GIS-based suitability analysis to identify favorable locations for IT park development in the Mahadevapura / East Bengaluru IT corridor by combining:

- Satellite-derived environmental indicators (NDVI, NDWI, NDBI, LST)
- OpenStreetMap infrastructure layers (roads, rail, power, etc.)
- Vector-to-raster conversion
- Proximity analysis (distance modeling)
- Reclassification (standardization to 1–5 scale)
- Weighted overlay analysis (MCDA)

The final output is a suitability heatmap showing best and worst locations for IT development.

---

## 2. Study Area Summary

### Region
- **Official name:** Mahadevapura Assembly Constituency
- **Common name:** East Bengaluru IT Belt / Whitefield–Bellandur Corridor
- **Area:** ~132 to 135 km²
- **North–South span:** ~17.2 km
- **East–West span:** ~18.5 km

### Why This Area?
- Major IT clusters (existing)
- Dense road infrastructure
- Metro and railway connectivity
- Airport access
- Water bodies and green zones
- Ongoing urban expansion

---

## 3. Overall Workflow (What You Did)

1. <span class="fas fa-check"></span> Download Landsat raster bands
2. <span class="fas fa-check"></span> Calculate spectral indices (NDVI, NDWI, NDBI, LST)
3. <span class="fas fa-check"></span> Download OSM vector layers (roads, rail, power, amenities, etc.)
4. <span class="fas fa-check"></span> Reproject all vectors to EPSG:32643 (UTM)
5. <span class="fas fa-check"></span> Establish CRS rules (critical! same CRS for all)
6. <span class="fas fa-check"></span> Rasterize vector layers (convert to pixels)
7. <span class="fas fa-check"></span> Generate proximity rasters (distance from each feature)
8. <span class="fas fa-check"></span> Reclassify all rasters to 1–5 suitability scale
9. <span class="fas fa-check"></span> Create constraint masks (0/1 for no-build zones)
10. <span class="fas fa-check"></span> Perform weighted overlay (MCDA to final map)
11. <span class="fas fa-check"></span> Style final heatmap for presentation

---

## 4. Data Sources

### Landsat Data Downloaded
**Landsat 9 Scene ID:** `LC09_L2SP_144051_20241231_20250102_02_T1`
- **Satellite:** Landsat 9 (LC09)
- **Processing Level:** L2SP (Collection 2 Level-2 Science Product)
- **Date:** December 31, 2024
- **WRS Path/Row:** 144/051
- **Status:** Downloaded

---

## 5. Remote Sensing Layers (Landsat Spectral Indices)

These are raster-based layers derived from Landsat imagery using Raster Calculator.

### 4.1 NDVI — Normalized Difference Vegetation Index

**Purpose:** Identify vegetation and green zones (good for environmental quality)

**Formula:**
```
("B5@1" - "B4@1") / ("B5@1" + "B4@1")
```

**Band Meaning:**
- B5 = Near Infrared (NIR)
- B4 = Red

**Output:**
- High NDVI (>0.4) = Dense vegetation
- Low NDVI (<0.2) = Built-up or barren
- NDVI Score: Higher = Better for amenities

---

### 4.2 NDWI — Normalized Difference Water Index

**Purpose:** Identify water bodies and moisture-rich surfaces

**Formula:**
```
("B3@1" - "B5@1") / ("B3@1" + "B5@1")
```

**Band Meaning:**
- B3 = Green
- B5 = NIR

**Output:**
- High NDWI = Water/wetlands (constraint!)
- Low NDWI = Non-water surfaces
- NDWI Score: Lower = Better for building

---

### 4.3 NDBI — Normalized Difference Built-up Index

**Purpose:** Identify built-up surfaces and urban density

**Formula:**
```
("B6@1" - "B5@1") / ("B6@1" + "B5@1")
```

**Band Meaning:**
- B6 = SWIR1 (Short-wave infrared)
- B5 = NIR

**Output:**
- High NDBI = Dense buildings/concrete
- Low NDBI = Vegetation or open space
- NDBI Score: Moderate = Infrastructure indicator

---

### 4.4 LST — Land Surface Temperature

**Purpose:** Identify heat islands (cooler is better for operations)

**Formula:**
```
("B10@1" * 0.00341802 + 149.0) - 273.15
```

**Output:** Temperature in °C
- Hot zones (>35°C) = Heat island, high cooling costs
- Cool zones (<30°C) = Better for IT operations
- LST Score: Lower temperature = Higher score

---

## 4.5 Reclassification Rules (Value Mapping to Suitability Scores)

All spectral indices and proximity layers are reclassified to a standardized **1–5 suitability scale** where:
- **5 = Ideal** (best for IT park)
- **4 = High** (very suitable)
- **3 = Moderate** (acceptable)
- **2 = Low** (marginal)
- **1 = Avoid** (unsuitable)
- **0 = Mask/Exclusion** (no-build zones)

### 4.5.1 NDVI Reclassification (Vegetation Index)

| Range | Score | Suitability | Reasoning |
|-------|-------|-------------|-----------|
| -1.0 to 0.0 | 0 | Exclusion | Water Bodies: Lakes and tanks. Construction strictly prohibited by KLCDA. |
| 0.0 to 0.15 | 1 | Lowest | Saturated Urban: High concrete density. Heat islands with zero room for campus. Acquisition costs astronomical. |
| 0.15 to 0.3 | 4 | High | Low-Vegetation Land: Fallow/scrub land. Highly suitable—easy to clear while outside congested urban core. |
| 0.3 to 0.55 | 5 | Ideal | Green Campus Zone: Healthy shrubs/grassland. "Goldilocks" zone—easily integrated into modern IT park with high biophilic value. |
| 0.55 to 1.0 | 2 | Low | Protected Greenery: Dense canopy/forests. Legally restricted due to tree-felling laws and high environmental impact. |

### 4.5.2 NDBI Reclassification (Built-up Index)

| Min Value | Max Value | Score | Suitability | Reasoning |
|-----------|-----------|-------|-------------|-----------|
| -1.0 | -0.1 | 5 | Ideal | Open/Green Land: No existing buildings. Perfect for new campus. |
| -0.1 | 0.1 | 4 | High | Suburban/Fallow: Very few structures. Easy to consolidate land. |
| 0.1 | 0.3 | 2 | Low | Residential: Already built-up. High cost of acquisition/demolition. |
| 0.3 | 1.0 | 1 | Avoid | Commercial/Dense Urban: Fully developed "Grey" areas. No space available. |

### 4.5.3 NDWI Reclassification (Water Index)

| Min Value | Max Value | Score | Suitability | Reasoning |
|-----------|-----------|-------|-------------|-----------|
| -1.0 | -0.2 | 5 | Ideal | Deep Dry Land: Ideal for stable foundations. |
| -0.2 | 0.0 | 3 | Moderate | Low Moisture: Likely grasslands. Check for seasonal dampness. |
| 0.0 | 0.2 | 1 | Avoid | Marshy/Wetland: High risk of flooding and sinking. |
| 0.2 | 1.0 | 0 | Mask/Exclusion | Open Water: Lakes/tanks. Illegal to build. |

### 4.5.4 LST Reclassification (Land Surface Temperature)

| Min Temperature (°C) | Max Temperature (°C) | Score | Suitability Level | Reasoning |
|----------------------|----------------------|-------|-------------------|-----------|
| 19.5 | 25.0 | 5 | Ideal | Very cool, likely near heavy green cover. Best for comfortable operations. |
| 25.0 | 30.0 | 4 | High | Comfortable microclimate. Good thermal conditions. |
| 30.0 | 35.0 | 3 | Moderate | Standard urban heat. Acceptable but requires climate control. |
| 35.0 | 38.0 | 2 | Low | Hot. Will require high cooling costs. Marginal for IT operations. |
| 38.0 | 42.0 | 1 | Avoid | Extreme heat island. Poor for staff comfort. High energy costs. |

---

## 5. OSM Vector Data Collection (Overpass Queries)

Vector layers were downloaded from OpenStreetMap using Overpass Turbo with polygon-based queries.

### 5.1 Study Area Polygon (Mahadevapura IT Corridor)

```
12.915 77.635
12.980 77.620
13.045 77.710
13.010 77.790
12.930 77.780
12.890 77.690
12.915 77.635
```

### 5.2 Example: Roads Query

```
[out:json][timeout:300];
(
  way["highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified"]
  (poly:"12.915 77.635 ...");
);
out body;
>;
out skel qt;
```

### 5.3 Example: Buildings Query (for Constraint Mask)

```
[out:json][timeout:600];
(
  way["building"](poly:"12.915 77.635 ...");
  relation["building"](poly:"12.915 77.635 ...");
);
out body;
>;
out skel qt;
```

---

## 6. Critical Rule: Coordinate Reference System (CRS)

### <span class="fas fa-exclamation-triangle"></span> THE RULE
**All layers used in final analysis MUST be in the same CRS.**

### Why EPSG:32643 (UTM Zone 43N)?
- EPSG:4326 uses **degrees** (lat/lon) → Can't do proximity
- EPSG:32643 uses **meters** → Proximity & buffering work correctly
- Raster alignment requires same CRS
- Consistency ensures all distances are comparable

### How to Reproject a Vector Layer

**QGIS Navigation:**
1. Right-click layer → **Export → Save Features As...**
2. Set:
   - **Format:** ESRI Shapefile (or GeoPackage)
   - **CRS:** EPSG:32643 (click globe icon)
3. Save as: `Layer_name_UTM.shp`

**Result:** Your layer is now in meters, ready for buffering and rasterization.

---

## 7. Shapefile Components — What to Keep

A "shapefile" is NOT one file—it's a family of files that must stay together.

### Files You Must Keep

| Extension | Purpose | Critical? |
|-----------|---------|-----------|
| `.shp` | Geometry (points/lines/polygons) | <i class="fas fa-check"></i> YES |
| `.shx` | Shape index (location index) | <i class="fas fa-check"></i> YES |
| `.dbf` | Attribute table (names, types, IDs) | <i class="fas fa-check"></i> YES |
| `.prj` | Projection info (CRS metadata) | ✅ YES |
| `.cpg` | Code page (text encoding) | ⚠️ Sometimes |
| `.qpj` | QGIS projection info | ⚠️ Sometimes |

**Important:** Keep all files in the same folder with the same base name:
```
roads_utm.shp
roads_utm.shx
roads_utm.dbf
roads_utm.prj
```

If any `.shp`, `.shx`, `.dbf`, or `.prj` is missing, the layer won't load.

---

## 8. Which Vector Layers You Used

### Transportation Infrastructure
- `roads_UTM.gpkg` — Road network
- `railway_UTM.gpkg` — Railway lines
- `railway_subway_UTM.gpkg` — Metro/subway network
- `bus_stop_UTM.gpkg` — Bus stop points
- `airport_UTM.gpkg` — Airport boundary

### Power & Utilities
- `power_line_UTM.gpkg` — High-voltage transmission lines
- `power_poles_UTM.gpkg` — Pole points

### Water & Environment
- `water_UTM.gpkg` — Water bodies (lakes, rivers)
- `Protected_Areas_UTM.gpkg` — Forests, protected zones

### Development & Land Use
- `industrial_UTM.gpkg` — Industrial zones
- `it-hubs_UTM.gpkg` — Existing IT clusters
- `Settlement_Areas_UTM.gpkg` — Buildings & settlements

### Services & Amenities
- `hospital_UTM.gpkg` — Hospital locations
- `amenities_UTM.gpkg` — Parks, markets, schools, etc.

### Administrative
- `banglore_outline_UTM.gpkg` — City boundary
- `Mahadevapura IT Outline_UTM.gpkg` — Study area boundary

---

## 9. Which Utility Layer to Prefer

For power infrastructure, you have 3 options:

| Layer | Best For | Why |
|-------|----------|-----|
| **Substations** | ✅ PRIMARY | Represents actual power supply feasibility |
| **Power Lines** | ⚠️ SECONDARY | Shows transmission corridor, less precise |
| **Power Poles** | ❌ NOT RECOMMENDED | Repeated points, less meaningful for suitability |

**Recommendation:** Use **Substations / Power Stations** for real power supply analysis.

---

## 10. Three Critical Technical Steps

### 10.1 Export & Reproject Vector to UTM (CRS Conversion)

**QGIS Navigation:**
1. Right-click vector layer
2. **Export → Save Features As...**
3. **Format:** ESRI Shapefile
4. **CRS:** Click globe → EPSG:32643
5. **File Name:** `Layer_UTM.shp`
6. **Click OK**

**Result:** Your vector is now in meters (UTM).

---

### 10.2 Rasterize: Convert Vector to Pixels

**QGIS Navigation:**
1. **Processing → Toolbox** (or Ctrl+Alt+T)
2. Search: **"Rasterize (vector to raster)"**
3. **Input Layer:** Your `Layer_UTM.shp`
4. **A Fixed Value to Burn:** `1` (1 = feature present, 0 = empty)
5. **Output Raster Size Units:** `Georeferenced units`
6. **Width Resolution:** `30` (meters, matches Landsat)
7. **Height Resolution:** `30`
8. **Output Extent:** Click `...` → `Calculate from Layer` → Select `Mahadevapura IT Outline_UTM`
9. **Output Name:** `Layer_rasterized.tif`
10. **Click Run**

**Result:** Binary raster (1 = feature, 0 = no feature).

---

### 10.3 Proximity Analysis: Create Distance Raster

**QGIS Navigation:**
1. **Processing → Toolbox**
2. Search: **"Proximity (raster distance)"**
3. **Input Layer:** The rasters from Step 10.2
4. **Values to Consider:** `1` (measure away from the 1s)
5. **Distance Units:** `Georeferenced coordinates` (meters!)
6. **Max Distance:** 
   - `5000` for Roads/Metro/Hospitals
   - `30000` for Airport
7. **Output Data Type:** `Float32`
8. **Output Name:** `Proximity_Layer.tif`
9. **Click Run**

**Result:** Each pixel shows distance to nearest feature (in meters).
- Dark = close (0m)
- Light = far (5000m)

---

## 11. Why Reclassify?

You have these different types of data:
- **Distances** in meters (0–5000m)
- **Temperature** in °C (25–35°C)
- **NDVI values** (-1.0 to +1.0)
- **NDBI values** (-1.0 to +1.0)

**You CANNOT add these together!** 
Solution: Reclassify everything to the **same 1–5 score scale**.

---

## 12. Reclassification Process

**QGIS Navigation:**
1. **Processing → Toolbox**
2. Search: **"Reclassify by table"**
3. **Input Layer:** Your proximity or spectral raster
4. **Add Reclassification Rules:**
   - Min Value | Max Value | New Value
   - 0 | 500 | 5 (close = good)
   - 500 | 1500 | 4
   - 1500 | 3000 | 3
   - 3000 | 5000 | 2
   - 5000 | 99999 | 1 (far = bad)
5. **Output Name:** `reclass_Layer.tif`
6. **Click OK**

**Result:** All values now on 1–5 scale (1 = worst, 5 = best).

---

## 13. Complete Suitability Scoring Tables

All layers reclassified using these criteria:

### Transportation & Infrastructure

#### Roads
| Min (m) | Max (m) | Score | Logic |
|---------|---------|-------|-------|
| 0 | 500 | 5 | Excellent: Direct access |
| 500 | 1500 | 4 | Good: Short distance |
| 1500 | 3000 | 3 | Average: Moderate distance |
| 3000 | 5000 | 2 | Poor: Far, requires extension |
| 5000 | 99999 | 1 | Unsuitable: Very far |

#### Metro / Railway (Transit-Oriented Development)
| Min (m) | Max (m) | Score | Logic |
|---------|---------|-------|-------|
| 0 | 1000 | 5 | Prime TOD: Walking distance (12 mins) |
| 1000 | 3500 | 4 | Shuttle Zone: 5-10 min feeder access |
| 3500 | 5500 | 3 | Average: Common urban commute |
| 5500 | 9000 | 2 | Poor: High last-mile friction |
| 9000 | 999999 | 1 | Unsuitable: Not viable daily option |

#### Power / Electricity
| Min (m) | Max (m) | Score | Logic |
|---------|---------|-------|-------|
| 0 | 500 | 5 | Excellent: Plug & play |
| 500 | 1200 | 4 | Very Good: Standard feeder distance |
| 1200 | 2500 | 3 | Average: Requires investment |
| 2500 | 5000 | 2 | Poor: High transmission loss |
| 5000 | 99999 | 1 | Unsuitable: Off-grid |

#### Airport
| Min (m) | Max (m) | Score | Logic |
|---------|---------|-------|-------|
| 0 | 3000 | 1 | Danger: Flight path restrictions |
| 3000 | 8000 | 3 | Buffer: Noisy but acceptable |
| 8000 | 18000 | 5 | Prime: 25-min drive (best for IT) |
| 18000 | 30000 | 3 | Fair: Bit far for business travel |
| 30000 | 999999 | 1 | Too Far: >1.5 hour commute |

### Healthcare & Amenities

#### Healthcare / Hospitals
| Min (m) | Max (m) | Score | Logic |
|---------|---------|-------|-------|
| 0 | 800 | 5 | Critical: Emergency response <5 mins |
| 800 | 2500 | 4 | Good: Accessible specialized care |
| 2500 | 5000 | 3 | Average: Standard urban reach |
| 5000 | 10000 | 2 | Poor: Risky for corporate hub |
| 10000 | 99999 | 1 | Unsuitable: Healthcare isolation |

#### Bus Stops
| Min (m) | Max (m) | Score | Logic |
|---------|---------|-------|-------|
| 0 | 300 | 5 | Excellent: 5-min walk |
| 300 | 800 | 4 | Very Good: 10 min accessible |
| 800 | 1500 | 3 | Average: Shuttle distance |
| 1500 | 3000 | 2 | Poor: Daily pedestrian friction |
| 3000 | 99999 | 1 | Unsuitable: Isolated from transit |

#### IT Hubs (Cluster Synergy)
| Min (m) | Max (m) | Score | Logic |
|---------|---------|-------|-------|
| 0 | 1000 | 5 | Excellent: Direct synergy & talent |
| 1000 | 2500 | 4 | Very Good: 5-10 min shuttle reach |
| 2500 | 5000 | 3 | Average: Peripheral to corridor |
| 5000 | 8500 | 2 | Poor: Too far for cluster benefits |
| 8500 | 999999 | 1 | Unsuitable: Isolated from IT ecosystem |

#### Amenities (Parks, Schools, Markets)
| Min (m) | Max (m) | Score | Logic |
|---------|---------|-------|-------|
| 0 | 300 | 5 | Excellent: Direct walking access |
| 300 | 800 | 4 | Very Good: 10 min walk |
| 800 | 1500 | 3 | Average: Shuttle/auto distance |
| 1500 | 3000 | 2 | Poor: Too far for daily use |
| 3000 | 99999 | 1 | Unsuitable: Area isolated |

### Industrial & Land Use

#### Industrial Zones
| Min (m) | Max (m) | Score | Logic |
|---------|---------|-------|-------|
| 0 | 1000 | 2 | Buffer Zone: Avoid heavy noise/traffic |
| 1000 | 2500 | 5 | Sweet Spot: Near logistics, not dirty |
| 2500 | 5500 | 4 | Good: Accessible support |
| 5500 | 8500 | 3 | Average: Standard industrial reach |
| 8500 | 99999 | 1 | Unsuitable: Too far for logistics |

### Environmental & Terrain

#### Spectral Indices (NDVI, LST, Slope, etc.)

These have REVERSE logic (constraint-type):

**For NDVI (Vegetation):**
- High NDVI (>0.5) = 5 (Better green space, cooler)
- Medium NDVI (0.3–0.5) = 3
- Low NDVI (<0.3) = 1 (Built-up, hot)

**For LST (Temperature):**
- Cool zones (<30°C) = 5 (Better)
- Moderate (30–32°C) = 3
- Hot zones (>32°C) = 1 (Heat island)

**For Slope:**
- Flat (0–5°) = 5 (Easy to build)
- Gentle (5–15°) = 3
- Steep (>15°) = 1 (Difficult terrain)

---

## 14. Create the "No-Build Zone" Mask

Before finding good sites, define areas where building is illegal/impossible.

### Generalized Masking Process

All masks follow the same workflow:
1. **For vector layers:** Buffer them if needed, then rasterize
2. **Rasterization logic:** Burn value = `0` (forbidden zone), NoData = `1` (buildable zone)
3. **Resolution:** Match your analysis raster (typically 10m or 30m)
4. **Extent:** `Mahadevapura IT Outline_UTM`
5. **Data Type:** Float32
6. **Save as:** `.tif` format

### Fixed Buffer Distances (Legally & Environmentally Mandated)

| Mask | Distance | Rationale |
|------|----------|-----------|
| mask_water | 50m | NGT mandated buffer for lakes & primary drains |
| mask_railway | 30m | Safety setback from track center for RCC structures |
| mask_protected | 100m | Prohibited area buffer around heritage & protected forests |
| mask_settlements | 0m | Exact footprint (no buffer — hard boundary) |

---

### Mask Layers to Create

**1. mask_water.tif**
- Source: `water_UTM.gpkg`
- **Buffer Distance:** 50 meters (NGT mandated for lakes & primary storm-water drains)
- **Vector → Geoprocessing Tools → Buffer**
  - Distance: 50 meters
  - Dissolve Result: ✅ CHECK
  - Output: `Buffer_Water_50m.gpkg`
- **Raster → Conversion → Rasterize (Vector to Raster)**
  - Input Layer: `Buffer_Water_50m`
  - A Fixed Value to Burn: `0` (water zone = forbidden)
  - Resolution: 10 meters
  - Output: `mask_water.tif` (0 = water buffer, 1 = buildable)

**2. mask_railway.tif**
- Source: `railway_UTM.gpkg`
- **Buffer Distance:** 30 meters (mandatory safety setback from track center)
- **Vector → Geoprocessing Tools → Buffer**
  - Distance: 30 meters
  - Dissolve Result: ✅ CHECK
  - Output: `Buffer_Railway_30m.gpkg`
- **Raster → Conversion → Rasterize (Vector to Raster)**
  - Input Layer: `Buffer_Railway_30m`
  - A Fixed Value to Burn: `0` (railway zone = forbidden)
  - Resolution: 10 meters
  - Output: `mask_railway.tif` (0 = railway buffer, 1 = outside buffer)

**3. mask_protected.tif**
- Source: `Protected_Areas_UTM.gpkg`
- **Buffer Distance:** 100 meters (baseline prohibited area around heritage/protected forests)
- **Vector → Geoprocessing Tools → Buffer**
  - Distance: 100 meters
  - Dissolve Result: ✅ CHECK
  - Output: `Buffer_Protected_100m.gpkg`
- **Raster → Conversion → Rasterize (Vector to Raster)**
  - Input Layer: `Buffer_Protected_100m`
  - A Fixed Value to Burn: `0` (protected = forbidden)
  - Output Raster Size Units: `Georeferenced units`
  - Resolution (Width & Height): 10 meters
  - Output Extent: `Mahadevapura IT Outline_UTM`
  - Assign NoData Value: `1` (unprotected = available)
  - Output Data Type: `Float32`
  - Advanced: Check `All-Touched` (catches small patches)
  - Output: `mask_protected.tif` (0 = protected buffer, 1 = allowed)

**4. mask_settlements.tif**
- Source: `Settlement_Areas_UTM.gpkg` or `buildings_UTM.gpkg`
- **Buffer Distance:** 0 meters (exact existing footprint — hard boundary, no buffer)
- **Raster → Conversion → Rasterize (Vector to Raster)**
  - Input Layer: Direct from source (NO buffer)
  - A Fixed Value to Burn: `0` (buildings = forbidden)
  - Resolution: 10 meters
  - Output: `mask_settlements.tif` (0 = existing buildings, 1 = empty land)

### Combine All Masks into Single Constraint Mask

**QGIS Navigation:**
1. **Processing → Toolbox**
2. Search: **"Cell Statistics"** (Professional method)
3. **Input Layers:** Select all 4 masks
   - mask_water.tif
   - mask_railway.tif
   - mask_settlements.tif
   - mask_protected.tif
4. **Statistic:** `Minimum` (If ANY mask = 0, result = 0)
5. **Reference Layer:** Select `Slope.tif` or `DEM.tif`
6. **Output Name:** `Constraint_Mask.tif`
7. **Click Run**

**Final Constraint Mask Logic:**
- Pixels with **1** = Buildable (passes all 4 constraints)
- Pixels with **0** = Forbidden (fails at least one constraint)
7. **Click Run**

**Final Constraint Mask Logic:**
- Pixels with **1** = Buildable (passes all 4 constraints)
- Pixels with **0** = Forbidden (fails at least one constraint)

---

## 15. Basic Weighted Overlay

### Step 1: Create Sub-Thematic Maps

You combine related layers into 5 independent sub-maps:

#### **Sub-Map 1: Accessibility_Map**
**Goal:** Transport connectivity

**Formula:**
```
("reclass_roads@1" * 0.4) + 
("reclass_busStop@1" * 0.3) + 
("reclass_railway@1" * 0.2) + 
("reclass_airport@1" * 0.1)
```

**Weights:** Roads (40%) > Bus (30%) > Rail (20%) > Airport (10%)

---

#### **Sub-Map 2: Business_Demand_Map**
**Goal:** Economic viability & workforce

**Formula:**
```
("reclass_it-hubs@1" * 0.4) + 
("reclass_industrial@1" * 0.2) + 
("reclass_population@1" * 0.2) + 
("reclass_power@1" * 0.2)
```

**Weights:** IT Hubs (40%) > Industrial/Population/Power (20% each)

---

#### **Sub-Map 3: Physical_Suitability_Map**
**Goal:** Construction ease & terrain

**Formula:**
```
("reclass_slope@1" * 0.5) + 
("reclass_LULC@1" * 0.3) + 
("reclass_NDWI@1" * 0.2)
```

**Weights:** Slope (50%) > Land Use (30%) > Water (20%)

---

#### **Sub-Map 4: Infrastructure_Reliability_Map**
**Goal:** Utility readiness & stability

**Formula:**
```
("reclass_power@1" * 0.5) + 
("reclass_NDBI@1" * 0.3) + 
("reclass_roads@1" * 0.2)
```

**Weights:** Power (50%) > Built-up (30%) > Roads (20%)

---

#### **Sub-Map 5: Environmental_Social_Map**
**Goal:** Quality of life & sustainability

**Formula:**
```
("reclass_LST@1" * 0.25) + 
("reclass_NDVI@1" * 0.25) + 
("reclass_hospital@1" * 0.25) + 
("reclass_amenities@1" * 0.15) + 
("reclass_population@1" * 0.10)
```

**Weights:** Temperature (25%) = Vegetation (25%) = Hospital (25%) > Amenities (15%) > Population (10%)

---

### Step 2: Run Each Sub-Map Formula in Raster Calculator

**QGIS Navigation:**
1. **Raster → Raster Calculator**
2. **CRUCIAL STEP:** Before pasting formula:
   - Right-click first layer in formula
   - Select "Set as Canvas Extent"
   - In Raster Calculator, click "Calculate from Layer" for cell size
3. Paste formula
4. **Output Layer Name:** Exactly as above (e.g., `Accessibility_Map`)
5. **Click OK**
6. **Repeat for all 5 sub-maps**

---

## 16. Final Master Map (Combine 5 Sub-Maps)

Run this ONLY after all 5 sub-maps are created and visible.

**Formula:**
```
(
  ("Accessibility_Map@1" * 0.25) + 
  ("Business_Demand_Map@1" * 0.20) + 
  ("Infrastructure_Reliability_Map@1" * 0.15) + 
  ("Physical_Suitability_Map@1" * 0.15) + 
  ("Environmental_Social_Map@1" * 0.25)
) * "Constraint_Mask@1"
```

**Final Weights:**
- Accessibility (25%) = Environmental (25%)
- Business (20%)
- Infrastructure (15%) = Physical (15%)

**Constraint Mask as FILTER (Not Multiplication):**
The `Constraint_Mask@1` acts as a **spatial filter/selector**, not mathematical scaling:
- **Where Constraint_Mask = 1** (Buildable zones): Display full suitability score (1–5)
- **Where Constraint_Mask = 0** (Forbidden zones): Hide/exclude (treated as NoData)

Result: Final suitability map shows scores ONLY in legally/environmentally allowed areas. Restricted zones appear as black/empty.

**Output Name:** `Final_IT_Park_Suitability.tif`

---

## 17. Style the Final Heatmap (PPT-Ready)

### Step 1: Apply Color Ramp

1. Right-click `Final_IT_Park_Suitability`
2. **Properties → Symbology**
3. **Render Type:** `Singleband pseudocolor`
4. **Color Ramp:** `RdYlGn` (Red-Yellow-Green)
5. **Min Value:** 0
6. **Max Value:** 5
7. **Click OK**

### Step 2: Interpretation Guide

| Score | Color | Meaning | Action |
|-------|-------|---------|--------|
| 4.5–5.0 | 🟢 Dark Green | Excellent | Priority development zones |
| 3.5–4.4 | 🟢 Light Green | Very Good | Strong candidates |
| 2.5–3.4 | 🟡 Yellow | Average | Needs mitigation |
| 1.5–2.4 | 🟠 Orange | Poor | Not recommended |
| 0.0–1.4 | 🔴 Red | Unsuitable | Avoid entirely |
| **NaN** | ⬛ Black | Restricted | Legal/environmental constraints |

---

## 18. Extract Statistics & Findings

**Analysis Steps:**
1. Calculate % of land in each suitability tier
2. Identify top 5 green sites by coordinates
3. Validate with satellite imagery
4. Export map as GeoTIFF for stakeholders

---

## 19. Complete Mapping Reference Table

Shows all maps created and their input layers:

| Map Name | Layers Used | Purpose |
|----------|-------------|---------|
| **Constraint_Mask** | mask_settlements, mask_protected, mask_railway, mask_water | Define no-build zones |
| **Accessibility_Map** | reclass_roads, reclass_busStop, reclass_railway, reclass_airport | Transport connectivity |
| **Business_Demand_Map** | reclass_it-hubs, reclass_industrial, reclass_population, reclass_power | Economic viability |
| **Physical_Suitability_Map** | reclass_slope, reclass_LULC, reclass_NDWI | Construction ease |
| **Infrastructure_Reliability_Map** | reclass_power, reclass_NDBI, reclass_roads | Utility readiness |
| **Environmental_Social_Map** | reclass_LST, reclass_NDVI, reclass_hospital, reclass_amenities, reclass_population | QoL & sustainability |
| **FINAL** | (5 sub-maps combined) × Constraint_Mask | Site suitability heatmap |

---

## 20. File Types to Keep

### Vectors (Recommended Order)
- `.gpkg` (GeoPackage, single file, best practice)
- `.geojson` (GeoJSON, web-friendly, human-readable)
- `.shp` `.shx` `.dbf` `.prj` (ESRI Shapefile family, must keep all 4)
- `.kml` (KML, Google Earth compatible)

### Rasters
- `.tif` (GeoTIFF, standard with georeference)

### Projects
- `.qgz` (QGIS project, includes layer settings, symbols, styling)
- `.qmd` (QGIS metadata, documentation)

### Why Each Format?
- **GPKG:** Most efficient, single file, full spatial support
- **GeoJSON:** Easy to version control, web integration, readable
- **Shapefile:** Legacy standard, wide compatibility, but messy (4 files)
- **KML:** Visualize in Google Earth, useful for stakeholders
- **TIF:** Raster standard, maintains georeferencing and metadata

---

## 21. Question: Is it wrong to use the same layer in multiple sub-maps?

### ✅ Answer: YES, it's absolutely CORRECT and PROFESSIONAL

**Layers Appearing Multiple Times:**
- **roads** → Accessibility_Map (40%) + Infrastructure_Reliability_Map (20%)
  - Context 1: Transport accessibility value
  - Context 2: Infrastructure backbone reliability
  
- **power** → Business_Demand_Map (20%) + Infrastructure_Reliability_Map (50%)
  - Context 1: Business resource availability
  - Context 2: Utility criticality for IT operations
  
- **population** → Business_Demand_Map (30%)
  - Context: Commercial resource availability & market demand

**This is Multi-Criteria Decision Analysis (MCDA):**
- Each sub-map has its own independent formula
- Same layer appears with DIFFERENT weights in DIFFERENT thematic contexts
- Final master map combines all sub-maps fairly (25% + 25% + 20% + 15% + 15% = 100%)

**What IS wrong (Double-Counting):**
```
❌ ("roads@1" * 0.5) + ("roads@1" * 0.5) ← Inside ONE formula
```

**What you ARE doing (Correct):**
```
✅ Accessibility_Map: roads weighted 40% (transport context)
✅ Infrastructure_Map: roads weighted 20% (utility context)
✅ Each map is separate; roads contribute different perspectives in different thematic lenses
```

**Professional Methodology:**
Using the same layer in multiple contexts is standard practice in GIS site suitability analysis. It reflects real-world complexity where a single infrastructure (roads, power, etc.) serves multiple needs and must be evaluated from multiple perspectives.

---

## 22. Project Methodology (For Presentation)

**5 Phases You Completed:**

1. **Phase 1: Data Preparation**
   - 39+ UTM-projected layers (vector + raster)
   - Standardized CRS: EPSG:32643

2. **Phase 2: Proximity Modeling**
   - Euclidean distance analysis
   - 12+ proximity rasters generated

3. **Phase 3: Standardized Scoring**
   - Reclassification to 1–5 suitability scale
   - Constraint masking (exclusion zones)

4. **Phase 4: Weighted Aggregation**
   - Multi-Criteria Decision Analysis (MCDA)
   - 6 sub-thematic maps
   - Weighted combination (15+ factors)

5. **Phase 5: Site Identification**
   - Final heatmap generation
   - Spatial hotspots identified
   - Ready for stakeholder planning

---

## 23. Final Suitability Formula (Recommended Weights)

### Best-Practice Weighted Overlay Formula

After multi-scenario testing, the following formula provides the most balanced and robust IT park suitability assessment:

```
FINAL_SUITABILITY = 
  (reclass_demand × 0.30) +
  (reclass_accessibility × 0.25) +
  (reclass_physical × 0.15) +
  (reclass_infrastructure × 0.15) +
  (reclass_environment × 0.15)
```

### Weight Rationale

| Layer | Weight | Justification |
|-------|--------|---------------|
| **Business Demand** | 30% | Highest tier: Market validation is essential. A site with zero IT business interest cannot be suitable. |
| **Accessibility** | 25% | Second tier: Talent attraction & commute patterns. IT employees require good road/transit access. |
| **Physical Suitability** | 15% | Equal weight: Terrain, slope, and land acquisition feasibility directly impact construction viability. |
| **Infrastructure Reliability** | 15% | Equal weight: Power, roads, and utility connections are enablers—critical but secondary to market demand. |
| **Environment Liveability** | 15% | Equal weight: Green space, LST, and environmental quality support long-term operational resilience. |
| **TOTAL** | **100%** | Balanced MCDA framework. Business demand is weighted highest; infrastructure, physical, and environment equally weighted as foundation factors. |

### Applied Constraints

The final suitability map is multiplied by a binary **constraint mask**:

```
FINAL_OUTPUT = FINAL_SUITABILITY × CONSTRAINT_MASK
```

**Where CONSTRAINT_MASK = 0 for:**
- Open water bodies (50m buffer)
- Railway zones (30m buffer)
- Protected areas (100m buffer)
- Existing dense settlements (hard boundary)

**Result:** All restricted areas display as 0 (unsuitable); suitable zones range from 1–5.

### Why These Weights?

1. **Business Demand at 30%:** IT parks exist to serve IT companies. Without business demand, all other factors are academic.
2. **Accessibility at 25%:** Talent attraction is the #1 operational challenge for IT hubs. A site with poor commute access will struggle to hire.
3. **Equal 15% for Physical, Infrastructure, Environment:** These are foundational enablers. While critical, they're enablers, not differentiators. Flexibility exists:
   - A flat site (physical = 5) without power (infrastructure = 1) is not viable.
   - A pristine green site (environment = 5) with no road access (accessibility = 1) will not attract talent.

### How to Adjust Weights

If your stakeholders prioritize differently, modify the formula:

```
Example: "We want greenest possible IT park"
ADJUSTED = (reclass_demand × 0.25) +
           (reclass_accessibility × 0.20) +
           (reclass_physical × 0.15) +
           (reclass_infrastructure × 0.15) +
           (reclass_environment × 0.25)  ← Increased from 15% to 25%
```

---

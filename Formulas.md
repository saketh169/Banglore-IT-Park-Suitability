# IT Park Suitability Analysis — Complete Formulas Reference

---

## 1. Raster Layer Formulas

These are the core spectral indices calculated from Landsat satellite bands.

| Index | Formula | Description |
|-------|---------|-------------|
| **NDVI** | `("B5@1" - "B4@1") / ("B5@1" + "B4@1")` | Normalized Difference Vegetation Index (vegetation & green zones) |
| **NDWI** | `("B3@1" - "B5@1") / ("B3@1" + "B5@1")` | Normalized Difference Water Index (water bodies & moisture) |
| **NDBI** | `("B6@1" - "B5@1") / ("B6@1" + "B5@1")` | Normalized Difference Built-up Index (urban density) |
| **LST** | `("B10@1" * 0.00341802 + 149.0) - 273.15` | Land Surface Temperature (in °C) |
| **RGB** | `RGB: B4 (Red) + B3 (Green) + B2 (Blue)` | True Color Composite (visual reference) |

**Band Reference:**
- B2 = Blue
- B3 = Green
- B4 = Red
- B5 = Near Infrared (NIR)
- B6 = SWIR1 (Short-wave Infrared)
- B10 = Thermal Infrared

---

## 2. Sub-Thematic Feature Maps

These are the 5 key evaluation criteria for IT park suitability, each combining multiple reclassified layers.

### **Sub-Map 1: Accessibility_Map**

**Purpose:** Evaluate transport connectivity for talent attraction and commute access

**Formula:**
```sql
("reclass_roads@1" * 0.4) + 
("reclass_busStop@1" * 0.3) + 
("reclass_railway@1" * 0.2) + 
("reclass_airport@1" * 0.1)
```

**Component Weights:**
- Roads: 40% (highest priority for daily commute)
- Bus Stops: 30% (public transit access)
- Railway/Metro: 20% (long-distance connectivity)
- Airport: 10% (business travel, lowest priority)

---

### **Sub-Map 2: Business_Demand_Map**

**Purpose:** Identify market viability and economic opportunities

**Formula:**
```sql
("reclass_it-hubs@1" * 0.4) + 
("reclass_industrial@1" * 0.2) + 
("reclass_population@1" * 0.2) + 
("reclass_power@1" * 0.2)
```

**Component Weights:**
- IT Hubs: 40% (cluster synergy & proximity to existing tech ecosystem)
- Industrial Zones: 20% (logistics and supply chain support)
- Population: 20% (workforce availability & market demand)
- Power/Utilities: 20% (infrastructure readiness)

---

### **Sub-Map 3: Physical_Suitability_Map**

**Purpose:** Assess terrain and land acquisition feasibility

**Formula:**
```sql
("reclass_slope@1" * 0.5) + 
("reclass_LULC@1" * 0.3) + 
("reclass_NDWI@1" * 0.2)
```

**Component Weights:**
- Slope: 50% (flat terrain is critical for construction)
- Land Use/Land Cover: 30% (existing land type & acquisition ease)
- Water Index (NDWI): 20% (moisture/wetland avoidance)

---

### **Sub-Map 4: Infrastructure_Reliability_Map**

**Purpose:** Evaluate utility readiness and operational stability

**Formula:**
```sql
("reclass_power@1" * 0.5) + 
("reclass_NDBI@1" * 0.3) + 
("reclass_roads@1" * 0.2)
```

**Component Weights:**
- Power/Electricity: 50% (critical for 24/7 IT operations)
- Built-up Index (NDBI): 30% (infrastructure maturity indicator)
- Roads: 20% (maintenance & supply chain logistics)

---

### **Sub-Map 5: Environmental_Social_Map**

**Purpose:** Assess quality of life and environmental sustainability

**Formula:**
```sql
("reclass_LST@1" * 0.30) + 
("reclass_NDVI@1" * 0.30) + 
("reclass_hospital@1" * 0.25) + 
("reclass_amenities@1" * 0.15)
```

**Component Weights:**
- Land Surface Temperature (LST): 30% (cooler zones = better for operations & staff comfort)
- NDVI (Vegetation): 30% (green space = environmental quality & employee wellness)
- Healthcare/Hospitals: 25% (employee health & emergency services)
- Amenities (Parks, Schools, Markets): 15% (quality of life & social infrastructure)

---

## 3. Final Master Formula

**Combines all 5 sub-thematic maps into a single suitability index**

### Formula:
```sql
FINAL_SUITABILITY = 
  (Accessibility_Map × 0.30) + 
  (Business_Demand_Map × 0.25) + 
  (Physical_Suitability_Map × 0.15) + 
  (Infrastructure_Reliability_Map × 0.15) + 
  (Environmental_Social_Map × 0.15)
```

**Applied with Constraint Mask:**
```sql
FINAL_OUTPUT = FINAL_SUITABILITY × CONSTRAINT_MASK
```

### Final Weights:
| Layer | Weight | Rationale |
|-------|--------|-----------|
| **Accessibility** | 30% | Highest priority: Talent attraction & commute access |
| **Business Demand** | 25% | Market validation essential for IT park viability |
| **Physical Suitability** | 15% | Foundation: Terrain & land acquisition feasibility |
| **Infrastructure Reliability** | 15% | Enabler: Utility & connectivity backbone |
| **Environmental/Social** | 15% | Sustainability: Staff wellness & environmental quality |
| **TOTAL** | **100%** | Balanced MCDA framework |

### Constraint Mask Application:
- **Value = 1:** Buildable zone (passes all constraints)
- **Value = 0:** Forbidden zone (no-build area)

**Constraints Applied:**
- Water bodies (50m buffer) → NGT mandated
- Railway zones (30m buffer) → Safety setback
- Protected areas (100m buffer) → Environmental compliance
- Existing settlements (hard boundary) → No impact on occupied land

---

## 4. Output Interpretation

| Score Range | Classification | Color | Recommendation |
|-------------|-----------------|-------|-----------------|
| 4.5 - 5.0 | Excellent | 🟢 Dark Green | **Priority Development** - Immediate action |
| 3.5 - 4.4 | Very Good | 🟢 Light Green | **Strong Candidate** - Recommended |
| 2.5 - 3.4 | Moderate | 🟡 Yellow | **Acceptable** - Needs mitigation planning |
| 1.5 - 2.4 | Poor | 🟠 Orange | **Not Recommended** - High risk |
| 0.0 - 1.4 | Unsuitable | 🔴 Red | **Avoid** - Critical issues |
| **0 (Masked)** | **Restricted** | ⬛ Black | **No construction** - Legal/environmental barriers |

---

## 5. Quick Reference: Formula Structure

All sub-thematic maps follow this pattern:

```
Sub_Map = (Layer1 × Weight1) + (Layer2 × Weight2) + ... + (LayerN × WeightN)
```

Where weights always sum to 1.0 (100%) within each sub-map.

The final overlay combines 5 sub-maps with their own weights (30%, 25%, 15%, 15%, 15% = 100%).

---

## 6. File Naming Convention

| Component | File Pattern |
|-----------|--------------|
| Raster source bands | `B2.TIF`, `B3.TIF`, `B4.TIF`, `B5.TIF`, `B6.TIF`, `B10.TIF` |
| Spectral indices | `NDVI.tif`, `NDWI.tif`, `NDBI.tif`, `LST.tif` |
| Proximity maps | `Proximity_Roads.tif`, `Proximity_Railway.tif`, etc. |
| Reclassified layers | `reclass_roads.tif`, `reclass_hospital.tif`, etc. |
| Sub-thematic maps | `Accessibility_Map.tif`, `Business_Demand_Map.tif`, etc. |
| Constraint masks | `constraint_mask.tif`, `mask_water.tif`, `mask_railway.tif` |
| Final output | `Final_IT_Park_Suitability.tif` |

---

## 7. Notes

- All index values are **reclassified to 1–5 scale** for uniform comparison
- **Positive index = Good suitability** (NDVI, proximity to amenities)
- **Negative/Low index = Avoid** (proximity to hazards, high LST)
- Final scores range from **0 (forbidden) to 5 (optimal)**
- Constraint zones show as **0 or NoData** (appear black on maps)

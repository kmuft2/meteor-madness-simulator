# 📊 Data Setup Guide

This document explains how to obtain the large datasets required for the Meteor Madness Simulator.

## ⚠️ Important Note

**Large datasets are NOT included in this repository** due to size constraints (several GB). You need to download them separately.

---

## 🌊 Required Datasets

### 1. GEBCO Bathymetry Data (REQUIRED for Ocean Detection)

**File:** `GEBCO_2025_TID.nc` (3.7 GB)

**Purpose:** Determines whether an impact location is ocean or land, used for tsunami calculations.

**Download:**
1. Visit: https://www.gebco.net/data_and_products/gridded_bathymetry_data/
2. Download **GEBCO_2025 Grid** → **Type Identifier (TID) Grid**
3. Place in: `data/GEBCO_2025_TID.nc`

**Alternative (Full Elevation Data):**
- For actual ocean depths: Download `GEBCO_2025.nc` (~10-20 GB)
- Provides real bathymetry instead of estimated depths

**License:** Open access under GEBCO terms of use

---

### 2. WorldPop Population Data (OPTIONAL but Recommended)

**Directory:** `data/worldpop_2020/`

**Purpose:** Accurate population density for casualty estimates.

**Download:**
1. Visit: https://www.worldpop.org/geodata/listing?id=29
2. Download country-specific population datasets (2020, 1km resolution)
3. Extract to: `data/worldpop_2020/[COUNTRY_CODE]/`

**Format:** CSV files with columns: `latitude, longitude, population_2020`

**Countries to prioritize:**
- USA: `data/worldpop_2020/USA/usa_pd_2020_1km_ASCII_XYZ.csv`
- Major populated regions for your demo scenarios

**License:** Creative Commons Attribution 4.0 International

**Fallback:** System uses global average population density if not available.

---

### 3. NASA NEO Data (Automatically Cached)

**Directory:** `data/nasa/` (auto-created)

**Purpose:** Real-time asteroid orbital data from NASA's Near-Earth Object API.

**Setup:** Requires NASA API key in `.env` file (free from https://api.nasa.gov/)

**Note:** Data is cached automatically on first request.

---

## 📁 Directory Structure

```
data/
├── GEBCO_2025_TID.nc              # 3.7 GB - REQUIRED for ocean detection
├── GEBCO_Grid_documentation.pdf   # Included - documentation
├── GEBCO_Grid_terms_of_use.pdf   # Included - license terms
├── worldpop_2020/                 # OPTIONAL - population data
│   ├── USA/
│   │   └── usa_pd_2020_1km_ASCII_XYZ.csv
│   ├── GBR/
│   ├── JPN/
│   └── [other countries]/
├── nasa/                          # Auto-created cache
├── usgs/                          # Auto-created cache
└── cache/                         # Auto-created cache
```

---

## 🚀 Quick Start (Minimum Setup)

**For basic functionality:**

1. **Download GEBCO TID file** (3.7 GB):
   ```bash
   cd data/
   wget https://www.bodc.ac.uk/data/open_download/gebco/gebco_2025_tid/zip/
   unzip GEBCO_2025_TID.zip
   ```

2. **Get NASA API key** (free):
   - Visit: https://api.nasa.gov/
   - Copy key to `.env` file

3. **Run the app:**
   ```bash
   docker compose up -d
   ```

**System will work with:**
- ✅ Accurate ocean/land detection (from GEBCO TID)
- ✅ Tsunami calculations with estimated depths
- ⚠️  Population estimates using global averages (less accurate)

---

## 🎯 Full Setup (Best Accuracy)

**For production/demo:**

1. **GEBCO TID file** (3.7 GB) - as above
2. **WorldPop data** for key regions:
   ```bash
   # Download for your demo regions
   cd data/worldpop_2020/
   # Download from https://www.worldpop.org/
   ```

3. **GEBCO elevation data** (optional, 10-20 GB):
   ```bash
   cd data/
   # Download GEBCO_2025.nc for real ocean depths
   ```

**With full setup:**
- ✅ Accurate ocean/land detection
- ✅ Real ocean depths from GEBCO
- ✅ Precise population-based casualty estimates
- ✅ Production-ready for NASA Space Apps demo

---

## 💾 Storage Requirements

- **Minimum:** 4 GB (GEBCO TID only)
- **Recommended:** 10 GB (GEBCO + some population data)
- **Full:** 25+ GB (all datasets)

---

## 🔍 Verifying Your Setup

Run this command to check your data files:

```bash
python backend/scripts/verify_data.py
```

Or manually check:

```bash
ls -lh data/GEBCO*.nc
ls -R data/worldpop_2020/
```

---

## 📖 Data Sources & Citations

### GEBCO
```
GEBCO Compilation Group (2025) GEBCO 2025 Grid 
(doi:10.5285/37c52e96-24ea-67ce-e063-7086abc05f29)
```

### WorldPop
```
WorldPop (www.worldpop.org - School of Geography and Environmental Science, 
University of Southampton; Department of Geography and Geosciences, 
University of Louisville; Département de Géographie, Université de Namur) 
and Center for International Earth Science Information Network (CIESIN), 
Columbia University (2018). Global High Resolution Population Denominators 
Project - Funded by The Bill and Melinda Gates Foundation (OPP1134076).
```

### NASA NEO API
```
NASA/JPL Near-Earth Object Program
https://cneos.jpl.nasa.gov/
```

---

## 🆘 Need Help?

- **Issue:** Cannot download GEBCO data
  - **Solution:** Try alternate mirror or contact GEBCO support

- **Issue:** Simulator works but gives warning about population data
  - **Solution:** This is expected if WorldPop not installed. System uses fallback estimates.

- **Issue:** Out of disk space
  - **Solution:** Start with just GEBCO TID (3.7 GB), add population data later

---

## 📝 License Compliance

All datasets have specific license requirements:

- **GEBCO:** Free for all uses, attribution required
- **WorldPop:** CC BY 4.0, attribution required  
- **NASA:** Public domain, U.S. Government work

See individual data provider websites for full terms.

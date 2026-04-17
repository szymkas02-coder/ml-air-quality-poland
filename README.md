# ML Air Quality Poland

Machine learning pipeline for predicting PM2.5 air quality across Polish monitoring stations (2016–2019), combining air quality measurements from the Chief Inspectorate of Environmental Protection (GIOŚ), meteorological data from the Open-Meteo archive API, and geospatial features from OpenStreetMap (OSMnx) and Copernicus GHSL satellite rasters.

## 💡 Inspiration & Background

This project was inspired by recent research on air quality modeling in Poland:
> **Vovk, T., Kryza, M., & Werner, M. (2024).** *Using random forest to improve EMEP4PL model estimates of daily PM2.5 in Poland.* Atmospheric Environment, 332, 120615. [https://doi.org/10.1016/j.atmosenv.2024.120615](https://doi.org/10.1016/j.atmosenv.2024.120615)

**How this project differs:**
While the original paper focuses on a **hybrid approach** (using ML to correct bias in the EMEP4PL physical-chemical model), this pipeline implements a **Direct ML approach**. It predicts concentrations directly from raw meteorological and spatial data, making it more lightweight and independent of large-scale CTM (Chemical Transport Models) simulations.

## 🚀 Key Features
- **End-to-End Pipeline:** From raw GIOŚ archives and API calls to trained models.
- **Advanced Feature Engineering:** Automated extraction of road density and building counts via `OSMnx` and population data from `Copernicus GHSL` rasters.
- **Temporal & Spatial Validation:** Models are tested not only on unseen time periods but also on **unseen monitoring stations** to evaluate geographical generalization.
- **Hybrid Modeling:** Comparison between classical Gradient Boosting (XGBoost, LightGBM) and Deep Learning (LSTM) for time-series forecasting.

## Dataset

- **45 monitoring stations** across Poland, filtered for completeness (≥3 years with ≥12 months each having ≥14 valid days)
- **65,745 daily rows** and **280,504 hourly rows**
- **21 features** per record: PM2.5, meteorological variables (temperature, wind, humidity, pressure, boundary layer height, cloud cover), and spatial features (road network density, building count, population, built-up volume, elevation)

## Notebooks

| Notebook | Description |
|---|---|
| `01_data.ipynb` | Full data ingestion pipeline: GIOŚ PM2.5 download, completeness filtering, Open-Meteo weather fetching, OSMnx road/building features, Copernicus GHSL raster extraction, final dataset assembly |
| `02_single_station.ipynb` | Single-station ML model: feature engineering, model training and evaluation for an individual monitoring station |
| `03_all_stations.ipynb` | Multi-station generalized model: cross-station training, leave-one-station-out validation |
| `04_lstm.ipynb` | LSTM time-series model for PM2.5 forecasting using sequential hourly data |
| `05_classification.ipynb` | Air quality class prediction (categorical: Good / Moderate / Unhealthy / etc.) |

## Helper Modules

| File | Description |
|---|---|
| `fetch_osm_features.py` | Extract road and building features from OpenStreetMap via OSMnx for each station within a 5 km buffer |
| `read_data.py` | Load and parse daily PM2.5 data downloaded from GIOŚ archives |
| `read_data_hour.py` | Load and parse hourly PM2.5 data from GIOŚ |
| `read_openmeteo.py` | Fetch daily meteorological data from the Open-Meteo archive API |
| `read_openmeteo_hour.py` | Fetch hourly meteorological data from the Open-Meteo archive API |

## Data Sources

- **PM2.5**: GIOŚ (Chief Inspectorate of Environmental Protection) — https://powietrze.gios.gov.pl/pjp/archives
- **Weather**: Open-Meteo archive API — https://open-meteo.com/
- **Spatial**: OpenStreetMap via OSMnx, Copernicus GHSL (population, built-up surface, built-up volume at 100 m resolution)

## Technologies

- Python, Jupyter Notebooks
- `scikit-learn`, `tensorflow`/`keras` (LSTM)
- `osmnx`, `rasterio`, `geopandas`, `xarray`
- `pandas`, `numpy`, `matplotlib`, `seaborn`

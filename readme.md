# Antonio’s Severe Weather Dashboard  
## Version 2.2.x

A modular Streamlit-based severe weather dashboard built for real-time monitoring of SPC outlooks, NWS observations, and radar data.

This project is designed as a portfolio-grade meteorology application focused on clean architecture, performance optimization, and operational weather awareness.

---

## 🚀 Current Version: 2.2.x

### 🏠 Home Page

- SPC Day 1–7 Outlook Images  
  - Day 1–3 Categorical  
  - Day 4–7 Probabilistic  

- Dynamic SPC % Risk Breakdown at Selected Location  
  - Tornado  
  - Wind  
  - Hail  

- National Warning Counters (YTD)  
  - Tornado Warnings  
  - Severe Thunderstorm Warnings  

- Location Selector (Preset Cities)

---

### 🌡 Observations Page

- Latest NWS Surface Observation near selected location  
  - Temperature  
  - Dewpoint  
  - Relative Humidity  
  - Sea Level Pressure  
  - Visibility  
  - Wind (direction, speed, gusts)  

- Nearest NWS Radar (auto-detected via API)  
  - Base Reflectivity Loop  
  - Base Velocity Loop  

- Radar cache-busting updates every minute  

---

## ⚡ Performance Improvements in v2.2

- Replaced `st.tabs()` with conditional navigation rendering  
- Removed forced `st.rerun()` calls  
- Cached SPC percentage calculations  
- Cached national warning counters  
- Cached NWS API requests  
- Modularized page architecture  

---

## 🧱 Project Architecture
evere-dashboard-v2/
│
├── app.py
├── utils/
│ ├── home.py
│ ├── observations.py
│ ├── spc.py
│ ├── state.py
│ ├── config.py
│ ├── tornado_warning_counter.py
│ ├── severe_thunderstorm_warning_counter.py
│ └── ui.py

Pages are modular and rendered conditionally to prevent unnecessary API calls.

---

## 🔌 Data Sources

- NOAA / NWS API  
- SPC Outlook Products  
- NWS RIDGE Radar GIFs  

---

## 📌 Roadmap

- Model Forecast Page (HRRR / GFS)
- Interactive radar (Leaflet-based)
- Device-based geolocation
- Historical warning analytics
- Mesonet integration
- Deployment refinement

---

## 🧠 Author

Antonio McElfresh  
Meteorology Major – University of Oklahoma  
GIS Minor  
Amateur Radio Licensed  

---

## ⚠️ Disclaimer

This dashboard is for educational and informational purposes only.  
Official forecasts and warnings should always be obtained directly from NOAA/NWS.


# Antonio's Severe Weather Dashboard
## Version 3.0

Operational severe weather dashboard built with Streamlit for fast, location-aware monitoring of SPC outlooks, NWS observations, radar, and active severe alerts.

---

## What's New in v3

- New nationwide severe alert ticker at the top of the app:
  - Filters to only:
    - Tornado Warning
    - Severe Thunderstorm Warning
    - Tornado Watch
    - Severe Thunderstorm Watch
  - Color-coded alert pills by alert type
  - Continuous scrolling marquee with seamless loop
  - Auto speed based on content length
  - Safe fallback messages when no qualifying alerts are active or NWS is unavailable

- Updated branding hero:
  - Integrated custom logo in the hero section
  - Current location and profile links retained under the logo

- Simplified location workflow:
  - Preset severe-weather city selector for broad U.S. situational awareness
  - Optional "Use Device" geolocation for local context
  - Shared location state across pages

---

## Core Features

### Home

- SPC Day 1-3 categorical outlook images
- SPC Day 4-7 probabilistic outlook images
- Location-based SPC hazard percentages
  - Day 1: tornado, wind, hail
  - Day 2: tornado, wind, hail

### Observations

- SPC mesoanalysis embedded viewer
- Nearest radar selection from NWS points API
- Radar loops:
  - Base Reflectivity
  - Base Velocity
- Nearest and most complete NWS surface observation selection
- Observation cards:
  - Temperature
  - Dewpoint
  - Relative Humidity
  - Sea Level Pressure
  - Visibility
  - Wind and conditions

### Statistics

- Year-to-date warning counters and related summary metrics

### Model Forecasts

- Placeholder section reserved for upcoming model integration

---

## Project Structure

```text
severe-dashboard-v2/
|-- app.py
|-- assets/
|   |-- banner.jpg
|   |-- logo.png
|-- utils/
|   |-- about.py
|   |-- config.py
|   |-- home.py
|   |-- location.py
|   |-- nws_alerts.py
|   |-- observations.py
|   |-- satelite.py
|   |-- spc.py
|   |-- state.py
|   |-- statistics.py
|   |-- ticker.py
|   |-- tornado_warning_counter.py
|   |-- severe_thunderstorm_warning_counter.py
|   `-- ui.py
`-- requirements.txt
```

---

## Data Sources

- NOAA / NWS API:
  - `https://api.weather.gov/alerts/active`
  - `https://api.weather.gov/points/{lat},{lon}`
  - station observations and related endpoints
- SPC Outlook Products
- NWS RIDGE radar imagery

---

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Deployment Notes

- Streamlit Cloud-safe (no desktop GUI dependencies)
- Cached NWS/SPC requests to reduce API load
- Ensure `assets/logo.png` and `assets/banner.jpg` are present before deploy

---

## Author

Antonio McElfresh  
Meteorology - University of Oklahoma  
GIS Minor

---

## Disclaimer

This dashboard is for educational and informational use only.  
For life-safety decisions, always use official NOAA/NWS products and local emergency management guidance.

# Antonio's Severe Weather Dashboard (v2.1.1)

A real-time severe weather situational awareness dashboard built with Streamlit.

Developed by Antonio McElfresh  
Meteorology Student — University of Oklahoma  

---

## Overview

This project is a modular severe weather dashboard designed to provide operational awareness using live SPC data and national warning statistics. It combines meteorological analysis concepts with modern Python-based dashboard development.

---

## What’s New in v2.1.1

- Fixed minor UI typo on Home page  
- Improved README structure and clarity  
- Stabilized branch structure (main only)  
- Confirmed Streamlit Cloud deployment alignment  

---

## Major Features (v2.1)

### National Tornado Warning Counter (Year-to-Date)
- Automatically calculates total U.S. Tornado Warnings issued for the current calendar year  
- Powered by the IEM VTEC archive  
- Cached for performance  
- Displayed prominently on the Home page  

### SPC Probabilities at Your Location
- Day 1: Tornado, Wind, Hail  
- Day 2: Tornado, Wind, Hail  
- Day 3: Probabilistic Severe %  
- Location-based using preset coordinates  
- Custom styled metric-card interface  

### Modular Architecture
severe-dashboard-v2/
│
├── app.py
├── README.md
├── requirements.txt
├── .streamlit/
│
└── utils/
├── config.py
├── spc.py
├── state.py
├── ui.py
└── tornado_warning_counter.py


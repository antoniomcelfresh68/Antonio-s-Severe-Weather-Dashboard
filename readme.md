# Antonio's Severe Weather Dashboard (v2.1.1)

A real-time severe weather situational awareness dashboard built with Streamlit.

Developed by Antonio McElfresh  
Meteorology Student — University of Oklahoma  

---

## Overview

This project is a modular, production-style severe weather dashboard designed to provide:

- SPC Convective Outlooks
- Location-based severe probabilities (Day 1–3)
- National Tornado Warning Counter (Year-to-Date)
- Clean custom UI styling
- Streamlit Cloud deployment

The goal of this project is to combine operational meteorology concepts with modern Python-based dashboard development.

---

## What’s New in v2.1.1

- Fixed minor UI typo on Home page
- Improved README structure and clarity
- Stabilized branch structure (`main` only)
- Confirmed Streamlit Cloud deployment on `main`

---

## v2.1 Major Features

### National Tornado Warning Counter (YTD)
- Automatically calculates total U.S. Tornado Warnings issued for the current calendar year
- Powered by the IEM VTEC archive
- Cached for performance
- Displayed prominently on the Home page

### SPC Probabilities at Your Location
- Day 1: Tornado, Wind, Hail
- Day 2: Tornado, Wind, Hail
- Day 3: Probabilistic Severe %
- Location-based using preset coordinates
- Clean metric-card UI styling

### Modular Architecture

Project structure:

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


- `ui.py` – Global styling and theme
- `spc.py` – SPC outlook data retrieval and processing
- `tornado_warning_counter.py` – National YTD warning logic
- `state.py` – Session state management

---

## Tech Stack

- Python
- Streamlit
- Pandas
- Requests
- SPC Outlook Data
- IEM VTEC Archive

---

## Running Locally

```bash
git clone https://github.com/antoniomcelfresh68/Antonio-s-Severe-Weather-Dashboard-v2.git
cd Antonio-s-Severe-Weather-Dashboard-v2
pip install -r requirements.txt
streamlit run app.py

Deployment

Hosted via Streamlit Cloud
Primary Branch: main

Project Purpose

This dashboard serves as:

A meteorology-focused portfolio project

A demonstration of API integration and data parsing

A modular Python architecture example

A real-time operational severe weather tool

Future Roadmap

Active Tornado Warning counter

Radar integration

Historical severe trend analysis

Automated geolocation

Expanded outlook visualization

Version History

v2.1.1 – UI typo fix, README update, deployment stabilization

v2.1 – National Tornado Warning Counter + UI upgrade

v2.0 – Modular refactor and layout redesign

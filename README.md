# LCOE Space Solar Cost Model Analysis

An interactive Streamlit web application for analyzing Levelized Cost of Energy (LCOE) for space solar power systems.

## Features

- Interactive input controls:
  - Discount Rate slider (1-15%)
  - Project Lifetime text input (positive integers)
  - Power Generation Rate dropdown (terrestrial vs space)
  - Array Capital Cost slider ($0.10 - $10.00/W)

- Real-time 3D surface plot showing LCOE as a function of:
  - Launch Cost ($/kg) - log scale: $100 to $10,000
  - Panel Weight (kg/W) - log scale: 0.01 to 10

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running Locally

```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`

## Deployment on Render

1. Create a new Web Service on Render
2. Connect your GitHub repository (or use Render's Git integration)
3. Configure the service:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
4. Deploy!

Note: Render will automatically assign a port via the `$PORT` environment variable. Streamlit needs to be configured to use this port and listen on all interfaces (0.0.0.0).

## LCOE Formula

The current LCOE calculation uses:
```
LCOE = (launch_cost × array_weight + array_capex) / (project_duration + discount_rate/100)
```

This formula can be adjusted in the `calculate_lcoe()` function in `app.py` based on your specific cost model requirements.


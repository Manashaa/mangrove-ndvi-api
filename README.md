# Mangrove NDVI Prediction API

Author: Manasha Karunarathna

Project: Explainable AI-Based Early Warning System for Mangrove Degradation in Sri Lanka

Purpose:
This package provides predicted NDVI values for mangrove polygons from 2026 to 2030.

------------------------------------------------------------

API Endpoint

GET /ndvi/{polygon_id}

Example:

GET /ndvi/P0001

------------------------------------------------------------

Response Format

{
    "polygon_id": "P0001",
    "nearest_place": "Mangalaeliya",
    "latitude": 7.854714,
    "longitude": 79.809541,
    "predictions": [
        {
            "year": 2026,
            "predicted_ndvi": 0.235084
        }
    ]
}

------------------------------------------------------------

Important notes

• This package is intended only for the Blue Carbon component.

• The original dataset is not included.

• The classification model is not included.

• Training scripts are not included.

• Modifications should not affect the original work.

------------------------------------------------------------

Required libraries

- FastAPI
- Uvicorn
- Pandas

------------------------------------------------------------

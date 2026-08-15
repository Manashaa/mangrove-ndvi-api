from fastapi import FastAPI, HTTPException, Header
from pathlib import Path
import pandas as pd
import os


app = FastAPI(
    title="Mangrove NDVI Prediction API",
    description="Read-only API providing predicted mangrove NDVI values for 2026-2030.",
    version="1.0.0"
)


BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "ndvi_future_predictions.csv"


data = pd.read_csv(DATA_PATH)

data["polygon_id"] = (
    data["polygon_id"]
    .astype(str)
    .str.strip()
)


API_KEY = os.getenv("NDVI_API_KEY")


def verify_api_key(x_api_key: str):

    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="API key is not configured."
        )

    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key."
        )


@app.get("/")
def home():

    return {
        "service": "Mangrove NDVI Prediction API",
        "status": "running",
        "prediction_period": "2026-2030"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "records": len(data),
        "polygons": data["polygon_id"].nunique()
    }


@app.get("/ndvi/{polygon_id}")
def get_ndvi(
    polygon_id: str,
    x_api_key: str = Header(...)
):

    verify_api_key(x_api_key)

    polygon_id = polygon_id.strip().upper()

    result = data[
        data["polygon_id"] == polygon_id
    ].copy()

    if result.empty:

        raise HTTPException(
            status_code=404,
            detail=f"Polygon '{polygon_id}' not found."
        )

    result = result.sort_values("year")

    first = result.iloc[0]

    predictions = []

    for _, row in result.iterrows():

        predictions.append(
            {
                "year": int(row["year"]),
                "predicted_ndvi": round(
                    float(row["predicted_ndvi"]),
                    6
                )
            }
        )

    return {
        "polygon_id": str(first["polygon_id"]),
        "nearest_place": str(first["nearest_place"]),
        "latitude": round(float(first["latitude"]), 6),
        "longitude": round(float(first["longitude"]), 6),
        "predictions": predictions
    }
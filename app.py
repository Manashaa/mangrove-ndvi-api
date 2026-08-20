from fastapi import FastAPI, HTTPException, Header, Query
from pathlib import Path
import pandas as pd
import os


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Mangrove NDVI Prediction API",
    description=(
        "Read-only API providing predicted mangrove NDVI "
        "values for 2026-2030 using human-readable "
        "monitoring locations."
    ),
    version="2.0.0"
)


# =========================================================
# FILE PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "ndvi_future_predictions.csv"


# =========================================================
# LOAD DATA
# =========================================================

data = pd.read_csv(DATA_PATH)

data["polygon_id"] = (
    data["polygon_id"]
    .astype(str)
    .str.strip()
)

data["nearest_place"] = (
    data["nearest_place"]
    .fillna("Unknown Location")
    .astype(str)
    .str.strip()
)


# =========================================================
# API KEY
# =========================================================

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


# =========================================================
# MONITORING AREA LOGIC
#
# SAME LOGIC USED BY CLASSIFICATION DASHBOARD
# =========================================================

def assign_monitoring_area_labels(place_df):

    areas = (
        place_df[
            [
                "polygon_id",
                "nearest_place",
                "latitude",
                "longitude",
            ]
        ]
        .drop_duplicates(subset=["polygon_id"])
        .sort_values(
            by=["latitude", "longitude"],
            ascending=[False, True],
        )
        .reset_index(drop=True)
        .copy()
    )

    total = len(areas)

    if total == 1:

        areas["zone_name"] = (
            "Central Mangrove Area"
        )

    elif total == 2:

        areas["zone_name"] = [
            "Northern Mangrove Area",
            "Southern Mangrove Area",
        ]

    else:

        zone_names = []

        for index in range(total):

            relative_position = (
                index / max(total - 1, 1)
            )

            if relative_position < 1 / 3:

                zone_names.append(
                    "Northern Mangrove Area"
                )

            elif relative_position < 2 / 3:

                zone_names.append(
                    "Central Mangrove Area"
                )

            else:

                zone_names.append(
                    "Southern Mangrove Area"
                )

        areas["zone_name"] = zone_names


    # -----------------------------------------------------
    # NUMBER REPEATED AREAS
    # -----------------------------------------------------

    zone_counts = (
        areas["zone_name"]
        .value_counts()
        .to_dict()
    )

    running_counts = {}

    labels = []

    for zone_name in areas["zone_name"]:

        running_counts[zone_name] = (
            running_counts.get(zone_name, 0)
            + 1
        )

        if zone_counts[zone_name] > 1:

            label = (
                f"{zone_name} "
                f"{running_counts[zone_name]}"
            )

        else:

            label = zone_name

        labels.append(label)

    areas["monitoring_area"] = labels

    return areas


# =========================================================
# BUILD GLOBAL LOCATION LOOKUP
# =========================================================

def build_area_label_lookup(dataframe):

    lookup_frames = []

    for nearest_place, place_group in dataframe.groupby(
        "nearest_place",
        dropna=False
    ):

        lookup_frames.append(
            assign_monitoring_area_labels(
                place_group
            )
        )

    if not lookup_frames:

        return pd.DataFrame(
            columns=[
                "polygon_id",
                "nearest_place",
                "monitoring_area",
                "latitude",
                "longitude",
            ]
        )

    return (
        pd.concat(
            lookup_frames,
            ignore_index=True
        )
        [
            [
                "polygon_id",
                "nearest_place",
                "monitoring_area",
                "latitude",
                "longitude",
            ]
        ]
        .drop_duplicates(
            subset=["polygon_id"]
        )
    )


area_lookup = build_area_label_lookup(
    data
)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "service":
            "Mangrove NDVI Prediction API",

        "status":
            "running",

        "version":
            "2.0.0",

        "prediction_period":
            "2026-2030",

        "location_search":
            "enabled"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "records": len(data),
        "polygons":
            data["polygon_id"].nunique(),
        "nearest_locations":
            data["nearest_place"].nunique()
    }


# =========================================================
# SEARCH NEAREST LOCATIONS
# =========================================================

@app.get("/locations")
def search_locations(
    search: str = Query(
        default="",
        description=(
            "Search nearest location, "
            "for example Mangalaeliya"
        )
    ),
    x_api_key: str = Header(...)
):

    verify_api_key(x_api_key)

    places = sorted(
        place
        for place in data[
            "nearest_place"
        ].dropna().unique()
        if str(place).strip()
        and str(place).strip()
        != "Unknown Location"
    )

    if search.strip():

        query = search.strip().lower()

        places = [
            place
            for place in places
            if query in place.lower()
        ]

    return {
        "search": search,
        "count": len(places),
        "locations": places
    }


# =========================================================
# GET MONITORING AREAS FOR A LOCATION
# =========================================================

@app.get("/locations/{nearest_place}/areas")
def get_monitoring_areas(
    nearest_place: str,
    x_api_key: str = Header(...)
):

    verify_api_key(x_api_key)

    result = area_lookup[
        area_lookup[
            "nearest_place"
        ].str.lower()
        ==
        nearest_place.strip().lower()
    ].copy()

    if result.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Location '{nearest_place}' "
                "not found."
            )
        )

    result = result.reset_index(drop=True)

    areas = []

    for _, row in result.iterrows():

        areas.append(
            {
                "monitoring_area":
                    str(
                        row[
                            "monitoring_area"
                        ]
                    ),

                "latitude":
                    round(
                        float(
                            row["latitude"]
                        ),
                        6
                    ),

                "longitude":
                    round(
                        float(
                            row["longitude"]
                        ),
                        6
                    )
            }
        )

    return {
        "nearest_place":
            str(
                result.iloc[0][
                    "nearest_place"
                ]
            ),

        "count":
            len(areas),

        "monitoring_areas":
            areas
    }


# =========================================================
# GET NDVI USING FRIENDLY LOCATION
# =========================================================

@app.get("/ndvi/by-location")
def get_ndvi_by_location(
    nearest_place: str = Query(
        ...,
        description=(
            "Nearest location, "
            "for example Mangalaeliya"
        )
    ),

    monitoring_area: str = Query(
        ...,
        description=(
            "Monitoring area, for example "
            "Northern Mangrove Area 1"
        )
    ),

    x_api_key: str = Header(...)
):

    verify_api_key(x_api_key)


    # -----------------------------------------------------
    # FIND THE INTERNAL POLYGON
    # -----------------------------------------------------

    match = area_lookup[
        (
            area_lookup[
                "nearest_place"
            ].str.lower()
            ==
            nearest_place.strip().lower()
        )
        &
        (
            area_lookup[
                "monitoring_area"
            ].str.lower()
            ==
            monitoring_area.strip().lower()
        )
    ]


    if match.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                "Monitoring area not found "
                "for the selected location."
            )
        )


    polygon_id = str(
        match.iloc[0][
            "polygon_id"
        ]
    )


    # -----------------------------------------------------
    # GET NDVI PREDICTIONS
    # -----------------------------------------------------

    result = data[
        data["polygon_id"]
        == polygon_id
    ].copy()


    if result.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                "NDVI predictions are "
                "not available."
            )
        )


    result = result.sort_values(
        "year"
    )

    first = result.iloc[0]

    predictions = []

    for _, row in result.iterrows():

        predictions.append(
            {
                "year":
                    int(row["year"]),

                "predicted_ndvi":
                    round(
                        float(
                            row[
                                "predicted_ndvi"
                            ]
                        ),
                        6
                    )
            }
        )


    return {
        "nearest_place":
            str(first["nearest_place"]),

        "monitoring_area":
            monitoring_area,

        "latitude":
            round(
                float(first["latitude"]),
                6
            ),

        "longitude":
            round(
                float(first["longitude"]),
                6
            ),

        "predictions":
            predictions
    }


# =========================================================
# EXISTING POLYGON ENDPOINT
#
# KEEP FOR BACKWARD COMPATIBILITY
# =========================================================

@app.get("/ndvi/{polygon_id}")
def get_ndvi(
    polygon_id: str,
    x_api_key: str = Header(...)
):

    verify_api_key(x_api_key)

    polygon_id = (
        polygon_id
        .strip()
        .upper()
    )

    result = data[
        data["polygon_id"]
        == polygon_id
    ].copy()

    if result.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Polygon '{polygon_id}' "
                "not found."
            )
        )

    result = result.sort_values(
        "year"
    )

    first = result.iloc[0]


    # -----------------------------------------------------
    # FIND FRIENDLY AREA NAME
    # -----------------------------------------------------

    area_match = area_lookup[
        area_lookup["polygon_id"]
        == polygon_id
    ]

    if not area_match.empty:

        monitoring_area = str(
            area_match.iloc[0][
                "monitoring_area"
            ]
        )

    else:

        monitoring_area = (
            "Mangrove Monitoring Area"
        )


    predictions = []

    for _, row in result.iterrows():

        predictions.append(
            {
                "year":
                    int(row["year"]),

                "predicted_ndvi":
                    round(
                        float(
                            row[
                                "predicted_ndvi"
                            ]
                        ),
                        6
                    )
            }
        )


    return {
        "polygon_id":
            str(first["polygon_id"]),

        "nearest_place":
            str(first["nearest_place"]),

        "monitoring_area":
            monitoring_area,

        "latitude":
            round(
                float(first["latitude"]),
                6
            ),

        "longitude":
            round(
                float(first["longitude"]),
                6
            ),

        "predictions":
            predictions
    }
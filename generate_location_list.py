import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "ndvi_future_predictions.csv"
OUTPUT_PATH = BASE_DIR / "location_monitoring_areas.csv"


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

        areas["zone_name"] = "Central Mangrove Area"

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


    zone_counts = (
        areas["zone_name"]
        .value_counts()
        .to_dict()
    )

    running_counts = {}

    labels = []

    for zone_name in areas["zone_name"]:

        running_counts[zone_name] = (
            running_counts.get(zone_name, 0) + 1
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


all_locations = []

for nearest_place, group in data.groupby(
    "nearest_place"
):

    result = assign_monitoring_area_labels(
        group
    )

    all_locations.append(result)


location_df = pd.concat(
    all_locations,
    ignore_index=True
)


location_df = location_df[
    [
        "nearest_place",
        "monitoring_area",
        "latitude",
        "longitude",
    ]
]


location_df = location_df.sort_values(
    [
        "nearest_place",
        "latitude",
    ],
    ascending=[
        True,
        False,
    ]
)


location_df.to_csv(
    OUTPUT_PATH,
    index=False
)


print(
    "Location list created successfully."
)

print(
    "Saved:",
    OUTPUT_PATH
)

print(
    "Nearest locations:",
    location_df[
        "nearest_place"
    ].nunique()
)

print(
    "Monitoring areas:",
    len(location_df)
)
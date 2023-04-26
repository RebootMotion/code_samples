import os

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.rebootmotion.com"
API_HEADER = {'x-api-key': os.getenv("API_KEY")}
CSV_FILE = "../resources/movements_with_pitch_types.csv"
DOM_HAND = "RHA"        # Right Handed
MOVEMENT_TYPE_ID = 2    # baseball-pitching
MOCAP_TYPE_ID = 104     # Hawk-Eye High Frame Rate


def main():
    csv_df = pd.read_csv(CSV_FILE)

    primary_df = csv_df[csv_df["PitchType"] == "Fastball"]
    primary_segment_id = requests.post(
        f"{API_BASE}/player_group_segments",
        headers=API_HEADER,
        json={
            "external_context_ids": (
                primary_df["Identifier"].tolist()
            ),
            "movement_type_id": MOVEMENT_TYPE_ID,
            "mocap_type_id": MOCAP_TYPE_ID,
            "dom_hand": DOM_HAND
        }
    ).json()["analysis_segment_id"]

    comparison_df = csv_df[csv_df["PitchType"] == "Curveball"]
    comparison_segment_id = requests.post(
        f"{API_BASE}/player_group_segments",
        headers=API_HEADER,
        json={
            "external_context_ids": comparison_df["Identifier"].tolist(),
            "movement_type_id": MOVEMENT_TYPE_ID,
            "mocap_type_id": MOCAP_TYPE_ID,
            "dom_hand": DOM_HAND
        }
    ).json()["analysis_segment_id"]

    requested_analysis = requests.post(
        f"{API_BASE}/requested_analyses",
        headers=API_HEADER,
        json={
            "name": "Example Pitcher Fastballs vs Curveballs",
            "primary_analysis_segment_id": int(primary_segment_id),
            "comparison_analysis_segment_id": int(comparison_segment_id),
            "status": "requested"
        }
    )

    print(requested_analysis.json())


if __name__ == "__main__":
    main()

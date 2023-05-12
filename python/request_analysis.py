#################################################################
# This script demonstrates how to submit a "requested analysis" #
# (AKA a custom report) to Reboot Motion's API. This script is  #
# provided subject to the LICENSE file at the root of this      #
# repository. It is not intended to be used as-is in a          #
# production environment.                                       #
#                                                               #
# Detailed documentation for working with the Reboot Motion API #
# can be found here: https://api.rebootmotion.com/docs          #
#################################################################
import os

# The pandas and requests libraries are not required to use the
# Reboot Motion API, but are used in this example to simplify the
# processing of reading/filtering a CSV file and making HTTP
# requests, respectively. You may use any libraries you wish to
# read your data and make HTTP requests.
import pandas as pd
import requests

# This example assumes that you have set your API key as an
# environment variable. If you have not done so, you can replace
# the os.getenv("API_KEY") call with a string containing your API
# key. Please be careful not to commit your API Key to a public
# repository.
API_KEY = os.getenv("API_KEY")

API_HEADER = {'x-api-key': os.getenv("API_KEY")}
DOM_HAND = "RHA"        # Right Handed
MOVEMENT_TYPE_ID = 2    # baseball-pitching
MOCAP_TYPE_ID = 104     # Hawk-Eye High Frame Rate


def main():
    # Step 1. Read CSV file in as a Pandas DataFrame. This
    # (example) CSV file contains two columns. The first
    # column is labeled MLBPlayId and contains a list of
    # MLB Play IDs. The second column is labeled PitchType,
    # which contains the corresponding pitch type for each
    # MLB Play ID. (In this example, the only pitch types
    # included are "Fastball" and "Curveball", since that
    # is what we are interested in comparing.)
    #
    # This CSV is included as an example of how data could
    # be aggregated and passed into a Python script for use
    # with the Reboot Motion API; in practice, you will need
    # to create your own CSV file with the data you want to
    # analyze.
    csv_df = pd.read_csv("../resources/movements_with_pitch_types.csv")

    # Step 2. Create a new "Primary Segment Dataframe" by filtering
    # the original DataFrame to only include the rows where the
    # movement's PitchType is "Fastball". In this example, we are
    # comparing fastballs to curveballs, so our primary segment will
    # be the one containing fastballs.
    primary_df = csv_df[csv_df["PitchType"] == "Fastball"]

    # Step 3. Create our Primary Segment (called a Player Group Segment)
    # by making a POST request to Reboot Motion's /player_group_segments
    # API endpoint. A Player Group Segment is the underlying
    # grouping of movements that will be analyzed. To construct the
    # player group segment, we pass in the criteria for generating
    # the segment, which includes:
    #
    # - "external_context_ids": The list of MLB Play IDs that we want to
    #       analyze, which we get from the "MLBPlayId" column of our CSV
    #       (and, therefore, our DataFrame).
    #
    # - "movement_type_id": The type of movement we want to analyze. In
    #       this example, we are analyzing baseball pitching movements,
    #       so we use the Movement Type ID for `baseball-pitching`,
    #       which is 2. For the names/IDs of other movement types, you
    #       can query the API:
    #       https://api.rebootmotion.com/docs#tag/Settings/operation/list_movement_types_movement_types_get
    #
    # - "mocap_type_id": The type of motion capture data we want to analyze.
    #       In this example, we are analyzing Hawk-Eye High Frame Rate data
    #       (AKA the Hawk-Eye data provided by the MLB Stats API for games in
    #       2023+), so we use the corresponding Mocap Type ID, which is `104`.
    #       For standard, team-provided Hawk-Eye data (2023+ Minor League;
    #       2021/2022 Major League, etc.), the Mocap Type ID is 2. For the
    #       names/IDs of other mocap types, you can query the API:
    #       https://api.rebootmotion.com/docs#tag/Settings/operation/list_mocap_types_mocap_types_get
    #
    # - "dom_hand": The dominant hand for the movements we want to analyze.
    #       In this example, we are analyzing right-handed movements, so
    #       we use the value `RHA`. For left-handed movements, you would
    #       use the value `LHA`.

    # Step 3a. Construct a dictionary with the criteria.
    primary_segment_criteria = {
        # Use the MLBPlayId column from the primary_df DataFrame.
        # "external_context_id" is the way we refer to a third-party
        # system's ID for a movement and map it to a movement in
        # Reboot Motion's database. In this case, we are using the
        # MLB Play ID as the external_context_id.
        "external_context_ids": primary_df["MLBPlayId"].tolist(),
        "movement_type_id": 2,  # baseball-pitching
        "mocap_type_id": 104,   # Hawk-Eye High Frame Rate
        "dom_hand": "RHA"       # Right Handed
    }

    # Step 3b. Send the API request to create the Primary Segment.
    # Since we're using the requests library, passing the
    # `primary_segment_criteria` dictionary to the `json=`
    # parameter will automatically convert the dictionary to JSON
    # and use it as the body of the request. We authenticate with the
    # API using the `x-api-key` header as detailed in the API documentation.
    create_primary_segment = requests.post(
        "https://api.rebootmotion.com/player_group_segments",
        headers={'x-api-key': API_KEY},
        json=primary_segment_criteria
    )

    # Step 3c. The response from the API will also be JSON, so we convert
    # it back to a dictionary and retrieve the `analysis_segment_id`
    # parameter, which we will use in our later request to submit the
    # analysis.
    primary_segment_id = create_primary_segment.json()["analysis_segment_id"]

    # Step 4. Repeat steps 2 and 3, except for the "Comparison Segment".
    # Since we want to compare fastballs to curveballs, curveballs will
    # be our comparison segment. Therefore, we filter the DataFrame to
    # only include the rows that contain movement where the PitchType
    # is "Curveball".
    comparison_df = csv_df[csv_df["PitchType"] == "Curveball"]

    # Step 4a. Construct a dictionary with the criteria.
    comparison_segment_criteria = {
        # Use the MLBPlayId column from the comparison_df DataFrame
        "external_context_ids": comparison_df["MLBPlayId"].tolist(),
        # The movement_type_id, mocap_type_id, and dom_hand values
        # for this segment MUST be the same as the values for the
        # primary segment, as we cannot compare across types.
        "movement_type_id": 2,  # baseball-pitching
        "mocap_type_id": 104,   # Hawk-Eye High Frame Rate
        "dom_hand": "RHA"       # Right Handed
    }

    # Step 4b. Send the API request to create the Comparison Segment.
    create_comparison_segment = requests.post(
        "https://api.rebootmotion.com/player_group_segments",
        headers={'x-api-key': API_KEY},
        json=comparison_segment_criteria
    )

    # Step 4c. Retrieve the comparison segment's analysis_segment_id.
    comparison_segment_id = create_comparison_segment.json()["analysis_segment_id"]

    # Step 5. Submit the analysis request to the API. This will create
    # a new "Requested Analysis" (AKA a custom report) in Reboot Motion's
    # system. The API will return a JSON response containing the ID of the
    # new Requested Analysis, which we can use to retrieve the analysis
    # once it has been completed. The Requested Analysis will also be
    # available in the Reboot Motion Dashboard (dashboard.rebootmotion.com).
    #
    # Currently, requested analyses are only visible to the user who
    # created them.

    # Step 5a. Construct a dictionary with the Requested Analysis criteria.
    requested_analysis_criteria = {
        # Give the Requested Analysis a (unique) name so you can find
        # it later in the Reboot Motion Dashboard.
        "name": "Example Pitcher Fastballs vs Curveballs",
        # Pass the analysis_segment_id values for the Primary Segment,
        # which we retrieved in Step 3c. above.
        "primary_analysis_segment_id": int(primary_segment_id),
        # Pass the analysis_segment_id values for the Comparison Segment,
        # which we retrieved in Step 4c. above.
        "comparison_analysis_segment_id": int(comparison_segment_id),
        # The status of the requested analysis. This should always
        # be "requested" when creating a new analysis; it will be
        # updated as the analysis is processed.
        "status": "requested"
    }

    # Step 5b. Send the API request to create the Requested Analysis.
    create_requested_analysis = requests.post(
        "https://api.rebootmotion.com/requested_analyses",
        headers={'x-api-key': API_KEY},
        json=requested_analysis_criteria
    )

    # Optional: output the response from the API.
    print(create_requested_analysis.json())


if __name__ == "__main__":
    main()

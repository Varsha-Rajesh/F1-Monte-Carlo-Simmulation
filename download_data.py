import fastf1
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CACHE_DIR = BASE_DIR / "cache"
DATA_DIR = BASE_DIR / "data"

CACHE_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

fastf1.Cache.enable_cache(str(CACHE_DIR))

YEAR = 2026

# LOAD 2026 SCHEDULE


print("Loading 2026 F1 schedule...")

schedule = fastf1.get_event_schedule(YEAR)

schedule["EventDate"] = pd.to_datetime(
    schedule["EventDate"]
)


# FIND BELGIAN AND HUNGARIAN GRAND PRIX

prior_race = schedule[
    schedule["EventName"].str.contains(
        "Belgian Grand Prix",
        case=False,
        na=False
    )
].iloc[0]

predicted_gp = schedule[
    schedule["EventName"].str.contains(
        "Hungarian Grand Prix",
        case=False,
        na=False
    )
].iloc[0]


# SELECT RACES FROM FIRST RACE THROUGH BELGIAN GP

race_schedule = schedule[
    schedule["EventDate"] <= prior_race["EventDate"]
].copy()

race_schedule = race_schedule[
    race_schedule["EventName"].str.contains(
        "Grand Prix",
        case=False,
        na=False
    )
]

race_schedule = race_schedule.sort_values(
    "EventDate"
)

print(
    f"\nFound {len(race_schedule)} races "
    f"through the Belgian Grand Prix."
)

print("-" * 50)



# DOWNLOAD RACE RESULTS


race_data = []

for _, event in race_schedule.iterrows():

    race_name = event["EventName"]
    round_number = int(event["RoundNumber"])

    print(f"Loading {race_name}...")

    try:

        session = fastf1.get_session(
            YEAR,
            round_number,
            "R"
        )

        session.load(
            laps=False,
            telemetry=False,
            weather=False,
            messages=False
        )

        results = session.results

        for _, driver in results.iterrows():

            position = pd.to_numeric(
                driver["Position"],
                errors="coerce"
            )

            status = str(
                driver["Status"]
            )

            # Record DNF instead of finishing position
            if (
                pd.isna(position)
                or (
                    "Finished" not in status
                    and "Lapped" not in status
                )
            ):
                finishing_position = "DNF"

            else:
                finishing_position = int(position)

            race_data.append({
                "race": race_name,
                "driver_abbreviation": driver["Abbreviation"],
                "finishing_position": finishing_position
            })

    except Exception as e:

        print(
            f"Error loading {race_name}: {e}"
        )


# SAVE RACE DATA

race_df = pd.DataFrame(
    race_data
)

race_file = DATA_DIR / "race_data.csv"

race_df.to_csv(
    race_file,
    index=False
)

print("\nRace data saved to:")
print(race_file)

print("-" * 50)


# LOAD HUNGARIAN GRAND PRIX

print(
    "\nLoading Hungarian Grand Prix..."
)

predicted_session = fastf1.get_session(
    YEAR,
    int(predicted_gp["RoundNumber"]),
    "R"
)

predicted_session.load(
    laps=False,
    telemetry=False,
    weather=False,
    messages=False
)

predicted_results = (
    predicted_session.results
)


# EXTRACT STARTING POSITIONS

starting_grid = []

for _, driver in predicted_results.iterrows():

    starting_position = pd.to_numeric(
        driver["GridPosition"],
        errors="coerce"
    )

    starting_grid.append({
        "race": predicted_gp["EventName"],
        "driver_abbreviation": driver["Abbreviation"],
        "starting_position": starting_position
    })


# SAVE STARTING POSITION DATA

grid_df = pd.DataFrame(
    starting_grid
)

grid_df = grid_df.sort_values(
    "starting_position",
    na_position="last"
)

grid_file = (
    DATA_DIR / "starting_position.csv"
)

grid_df.to_csv(
    grid_file,
    index=False
)

print(
    "\nStarting position data saved to:"
)

print(grid_file)

print("-" * 50)

print("\nDownload complete.")
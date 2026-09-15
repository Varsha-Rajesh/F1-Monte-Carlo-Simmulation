import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# SETTINGS

N_SIMULATIONS = 20000

X = 0.25

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"

RESULTS_DIR.mkdir(exist_ok=True)

RACE_DATA_FILE = DATA_DIR / "race_data.csv"
STARTING_POSITION_FILE = DATA_DIR / "starting_position.csv"

np.random.seed(42)

# LOAD DATA

print("Loading race data...")

try:

    race_df = pd.read_csv(RACE_DATA_FILE)
    starting_df = pd.read_csv(STARTING_POSITION_FILE)

except FileNotFoundError as e:

    print(f"File not found: {e}")
    exit()

print("Data loaded successfully.")
print("-" * 50)


# PREPROCESS DATA

race_df["driver_abbreviation"] = (
    race_df["driver_abbreviation"]
    .astype(str)
    .str.upper()
    .str.strip()
)

starting_df["driver_abbreviation"] = (
    starting_df["driver_abbreviation"]
    .astype(str)
    .str.upper()
    .str.strip()
)

race_df["finishing_position"] = (
    race_df["finishing_position"]
    .astype(str)
    .str.strip()
)

finished_races = race_df[
    race_df["finishing_position"] != "DNF"
].copy()

finished_races["finishing_position"] = pd.to_numeric(
    finished_races["finishing_position"],
    errors="coerce"
)

starting_df["starting_position"] = pd.to_numeric(
    starting_df["starting_position"],
    errors="coerce"
)

finished_races = finished_races.dropna(
    subset=["finishing_position"]
)

starting_df = starting_df.dropna(
    subset=["starting_position"]
)


# DRIVER STATISTICS

print("Calculating driver statistics...")

dnf_probability = (
    race_df
    .groupby("driver_abbreviation")["finishing_position"]
    .apply(
        lambda x: (x == "DNF").mean()
    )
    .rename("dnf_probability")
)

driver_statistics = (
    finished_races
    .groupby("driver_abbreviation")[
        "finishing_position"
    ]
    .agg(["mean", "std"])
    .reset_index()
)

driver_statistics.rename(
    columns={
        "mean": "average_position",
        "std": "standard_deviation"
    },
    inplace=True
)

driver_statistics = driver_statistics.merge(
    dnf_probability,
    on="driver_abbreviation",
    how="left"
)

driver_statistics = driver_statistics.merge(
    starting_df[
        [
            "driver_abbreviation",
            "starting_position"
        ]
    ],
    on="driver_abbreviation",
    how="inner"
)

driver_statistics["dnf_probability"] = (
    driver_statistics["dnf_probability"]
    .fillna(0)
)

mean_std = driver_statistics[
    "standard_deviation"
].mean()

driver_statistics["standard_deviation"] = (
    driver_statistics["standard_deviation"]
    .fillna(mean_std)
)

driver_statistics = driver_statistics[
    [
        "driver_abbreviation",
        "average_position",
        "starting_position",
        "standard_deviation",
        "dnf_probability"
    ]
]

driver_statistics = driver_statistics.sort_values(
    "starting_position"
).reset_index(drop=True)

print("\nDriver statistics:")
print(driver_statistics)

driver_statistics.to_csv(
    RESULTS_DIR / "driver_statistics.csv",
    index=False
)

print("-" * 50)


# SIMULATE RACE

def simulate_race(driver_stats):

    race_results = {}

    for _, driver in driver_stats.iterrows():

        driver_name = driver[
            "driver_abbreviation"
        ]

        average_position = driver[
            "average_position"
        ]

        starting_position = driver[
            "starting_position"
        ]

        standard_deviation = driver[
            "standard_deviation"
        ]

        dnf_probability = driver[
            "dnf_probability"
        ]

        if np.random.rand() < dnf_probability:

            performance_score = 999

        else:

            expected_position = (
                X * average_position
                + (1 - X) * starting_position
            )

            performance_score = np.random.normal(
                loc=expected_position,
                scale=standard_deviation
            )

        race_results[
            driver_name
        ] = performance_score

    final_ranking = sorted(
        race_results.items(),
        key=lambda item: item[1]
    )

    return [
        driver
        for driver, score in final_ranking
    ]


# MONTE CARLO SIMULATION

print(
    f"Running {N_SIMULATIONS:,} simulations..."
)

all_results = []

for _ in range(N_SIMULATIONS):

    all_results.append(
        simulate_race(driver_statistics)
    )

results_df = pd.DataFrame(
    all_results
)

results_df.columns = [
    f"P{i + 1}"
    for i in range(
        len(driver_statistics)
    )
]

print("Simulation complete.")
print("-" * 50)


# WIN PROBABILITY

print("Calculating win probabilities...")

win_probability_df = (
    results_df["P1"]
    .value_counts(normalize=True)
    .mul(100)
    .rename("win_probability")
    .reset_index()
)

win_probability_df.columns = [
    "driver_abbreviation",
    "win_probability"
]

win_probability_df.to_csv(
    RESULTS_DIR / "win_probability_data.csv",
    index=False
)


# WIN PROBABILITY GRAPH

print("Generating win probability graph...")

plot_data = win_probability_df.sort_values(
    "win_probability"
)

plt.figure(
    figsize=(12, 9)
)

plt.barh(
    plot_data[
        "driver_abbreviation"
    ],
    plot_data[
        "win_probability"
    ]
)

plt.xlabel(
    "Probability of Winning (%)"
)

plt.ylabel(
    "Driver"
)

plt.title(
    f"F1 Race Win Probability\n"
    f"{N_SIMULATIONS:,} Monte Carlo Simulations"
)

plt.grid(
    axis="x",
    linestyle="--",
    alpha=0.5
)

for i, value in enumerate(
    plot_data["win_probability"]
):

    plt.text(
        value + 0.1,
        i,
        f"{value:.2f}%",
        va="center"
    )

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "win_probabilities.png",
    dpi=300
)

plt.close()

# PREDICTED FINISHING POSITION

print("Calculating predicted finishing positions...")

predicted_finish_data = []

for driver in driver_statistics["driver_abbreviation"]:

    expected_position = 0
    position_probabilities = {}

    for position in range(1, len(driver_statistics) + 1):

        probability = (
            results_df[f"P{position}"] == driver
        ).mean()

        position_probabilities[f"P{position}_probability"] = (
            probability * 100
        )

        expected_position += position * probability

    predicted_finish_data.append({
        "driver_abbreviation": driver,
        "expected_finishing_position": expected_position    })


predicted_finish_df = pd.DataFrame(
    predicted_finish_data
)


predicted_finish_df = predicted_finish_df.sort_values(
    "expected_finishing_position"
).reset_index(drop=True)


predicted_finish_df.insert(
    0,
    "predicted_finish",
    range(1, len(predicted_finish_df) + 1)
)

predicted_finish_df["expected_finishing_position"] = (
    predicted_finish_df["expected_finishing_position"].round(4)
)

probability_columns = [
    column
    for column in predicted_finish_df.columns
    if column.endswith("_probability")
]

predicted_finish_df[probability_columns] = (
    predicted_finish_df[probability_columns].round(4)
)


predicted_finish_df.to_csv(
    RESULTS_DIR / "predicted_finish.csv",
    index=False
)


print("\nPredicted finishing order:")
print(
    predicted_finish_df[
        [
            "predicted_finish",
            "driver_abbreviation",
            "expected_finishing_position"
        ]
    ].to_string(index=False)
)

# COMPLETE

print("\n" + "=" * 50)
print("SIMULATION COMPLETE")
print("=" * 50)

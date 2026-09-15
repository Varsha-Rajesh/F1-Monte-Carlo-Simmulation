# Formula 1 Monte Carlo Race Simulation

## Overview

This project implements a Monte Carlo simulation framework for predicting Formula 1 race outcomes using historical race results and starting-grid data.

The model retrieves Formula 1 data using the FastF1 Python library, calculates driver-level performance statistics, and uses those statistics to generate 20,000 simulated race outcomes. The resulting distribution of outcomes is used to estimate driver win probabilities and expected finishing positions.

The current implementation uses the 2026 Formula 1 season, with historical race data collected through the Belgian Grand Prix and starting-grid information from the Hungarian Grand Prix.

---

## Methodology

The simulation consists of three primary stages:

1. Data acquisition
2. Statistical preprocessing
3. Monte Carlo simulation and analysis

### 1. Data Acquisition

`download_data.py` uses FastF1 to retrieve the 2026 Formula 1 schedule and race results.

The script identifies the Belgian Grand Prix as the prediction race and the Hungarian Grand Prix as the source for starting-grid information. Race results are collected from the beginning of the 2026 season through the Belgian Grand Prix.

For each race, the following information is collected:

* Grand Prix
* Driver abbreviation
* Finishing position
* DNF status

Drivers who do not finish a race are recorded as `DNF`.

The resulting datasets are stored in the `data/` directory:

```text
data/
├── race_data.csv
└── starting_position.csv
```

The starting-grid dataset contains the driver's starting position from the Hungarian Grand Prix.

---

## Statistical Model

Before simulation, the race data is processed to calculate driver-level statistics.

For each driver, the model calculates:

* Average finish position across completed races
* Standard deviation of finishing positions
* DNF probability of a driver
* Driver's starting position for the race being predicted

The resulting driver statistics are stored as:

```text
average_position
standard_deviation
dnf_probability
starting_position
```

These statistics are generated in `sim.py` and saved to `results/driver_statistics.csv`.

---

## Race Simulation

Each simulated race generates a performance score for every driver.

The expected position for each driver is calculated using a weighted combination of historical finishing position and starting position:

```text
Expected Position =
    X × Average Finishing Position
    + (1 − X) × Starting Position
```

The current value of `X` is:

```text
X = 0.25
```

Therefore, the current model assigns:

* 25% weight to historical average finishing position
* 75% weight to starting position

The model then generates a random performance score using a normal distribution centered on the driver's expected position and scaled by the driver's historical standard deviation.

Lower performance scores correspond to better finishing positions.

### DNF Modeling

DNFs are incorporated probabilistically using each driver's historical DNF probability.

For every simulation, a random value is generated and compared with the driver's DNF probability. If the driver is selected as a DNF, their performance score is assigned a value of `999`, effectively placing them behind all classified drivers.

---

## Monte Carlo Simulation

The current implementation performs:

```text
20,000 simulations
```

For each simulation, every driver is assigned a simulated performance score. Drivers are then ranked according to their scores to produce a complete simulated finishing order.

The simulation results are stored in a Pandas DataFrame, with each column representing a finishing position:

```text
P1
P2
P3
...
```

Each row represents one simulated race.

A fixed NumPy random seed is used:

```python
np.random.seed(42)
```

This allows the simulation to produce reproducible results when the same input data and parameters are used.

---

## Output Analysis

Following the simulations, the program calculates two primary prediction metrics.

### Win Probability

Win probability is calculated as the percentage of simulations in which a driver finishes in first place.

```text
Win Probability =
    Number of P1 Finishes
    ---------------------
      Total Simulations
```

The results are saved to:

```text
results/win_probability_data.csv
```

The simulation also generates a horizontal bar chart displaying the calculated win probabilities.

### Expected Finishing Position

For each driver, the model calculates the probability of finishing in every available position.

The expected finishing position is calculated as:

```text
Expected Position =
    Σ(Position × Probability of Position)
```

Drivers are then sorted by their expected finishing position to produce the model's predicted finishing order.

---

## Execution

### Step 1: Retrieve Data

Run:

```bash
python download_data.py
```

This retrieves the required Formula 1 data and generates:

```text
data/race_data.csv
data/starting_position.csv
```

FastF1 caching is enabled to reduce the need to repeatedly download the same data.

### Step 2: Run the Simulation

After the datasets have been generated, run:

```bash
python sim.py
```

The program will:

1. Load the race and starting-grid datasets.
2. Standardize driver identifiers.
3. Remove incomplete finishing-position records from performance calculations.
4. Calculate driver statistics.
5. Run 20,000 race simulations.
6. Calculate driver win probabilities.
7. Calculate expected finishing positions.
8. Generate the win-probability visualization.
9. Save the resulting datasets and visualization.

---

## Configuration

The primary simulation parameters are defined in `sim.py`:

```python
N_SIMULATIONS = 20000
X = 0.25
```

### Number of Simulations

`N_SIMULATIONS` determines the number of races generated by the model.

For example:

```python
N_SIMULATIONS = 100000
```

can be used to increase the number of simulated outcomes.

### Historical Performance Weight

`X` determines the relative contribution of historical average finishing position to the expected position calculation.

```text
X = 0.00
```

Uses starting position exclusively.

```text
X = 0.25
```

Uses 25% historical performance and 75% starting position.

```text
X = 0.50
```

Uses equal weighting.

```text
X = 1.00
```

Uses historical average finishing position exclusively.

---

## Generated Files

### `driver_statistics.csv`

Contains the statistical inputs used by the simulation:

```text
driver_abbreviation
average_position
starting_position
standard_deviation
dnf_probability
```

### `win_probability_data.csv`

Contains the calculated probability of each driver winning the simulated race.

### `predicted_finish.csv`

Contains the predicted finishing order, expected finishing position, and finishing-position probability data.

### `win_probabilities.png`

A visualization of the calculated driver win probabilities across all simulations.

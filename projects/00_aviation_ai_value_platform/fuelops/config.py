"""Single source of truth for paths, feature contracts, benchmarks and thresholds.

Everything a reviewer might want to challenge lives here, not scattered across
scripts: which columns the model is allowed to see, which levers count as
controllable, what "benchmark operations" means, and where the decision layer
draws its lines.
"""
from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
MODEL_DIR = PROJECT_ROOT / "models"
RESULTS_MD = PROJECT_ROOT / "RESULTS.md"

SEED = 42
N_FLIGHTS = 24_000

# --------------------------------------------------------------------------- #
# Feature contract
# --------------------------------------------------------------------------- #
# The model may only see columns listed here. Anything prefixed `true_` is
# simulator ground truth used for validation and must never reach the model;
# tests/test_synthetic_data.py enforces that.
TARGET = "avoidable_fuel_kg"

CONTEXTUAL_FEATURES = [
    "distance_km",
    "payload_tons",
    "headwind_kts",
    "temperature_c",
    "aircraft_age_years",
    "month",
]

CONTROLLABLE_FEATURES = [
    "taxi_out_min",
    "departure_delay_min",
    "cruise_speed_delta_pct",
    "apu_minutes",
    "route_efficiency_score",
]

CATEGORICAL_FEATURES = ["departure_station", "aircraft_type"]

NUMERIC_FEATURES = CONTEXTUAL_FEATURES + CONTROLLABLE_FEATURES
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Segment keys used for sliced evaluation. `route_family` is derived from
# distance and is deliberately NOT a model feature.
SEGMENT_KEYS = ["route_family", "aircraft_type", "departure_station"]

GROUND_TRUTH_COLUMNS = [
    "true_contextual_kg",
    "true_controllable_kg",
    "true_noise_kg",
    "true_lever_taxi_out_min_kg",
    "true_lever_departure_delay_min_kg",
    "true_lever_cruise_speed_delta_pct_kg",
    "true_lever_apu_minutes_kg",
    "true_lever_route_efficiency_score_kg",
]

# --------------------------------------------------------------------------- #
# Benchmark operations
# --------------------------------------------------------------------------- #
# "Controllable opportunity" is defined relative to these operating targets.
# In production they would be agreed with flight operations (and could be
# segment-specific quantiles instead of constants); here they are explicit so
# the attribution can be validated against the simulator.
LEVER_BENCHMARKS = {
    "taxi_out_min": 12.0,
    "departure_delay_min": 0.0,
    "cruise_speed_delta_pct": 0.0,
    "apu_minutes": 8.0,
    "route_efficiency_score": 1.0,
}

LEVER_LABELS = {
    "taxi_out_min": "Taxi-out / ground congestion",
    "departure_delay_min": "Departure delay",
    "cruise_speed_delta_pct": "Cruise-speed profile",
    "apu_minutes": "APU usage / ground power",
    "route_efficiency_score": "Route efficiency",
}

# --------------------------------------------------------------------------- #
# Validation design
# --------------------------------------------------------------------------- #
TEMPORAL_TEST_FRACTION = 0.25      # last 25% of flights by date are held out
INTERVAL_QUANTILES = (0.10, 0.90)  # 80% nominal prediction interval

# --------------------------------------------------------------------------- #
# Decision policy
# --------------------------------------------------------------------------- #
MIN_CONTROLLABLE_KG = 300.0        # below this, not worth an operator's time
MIN_CONTROLLABLE_SHARE = 0.30      # excess must be mostly controllable to act
MAX_INTERVAL_WIDTH_RATIO = 2.0     # abstain when interval > 2x median width
OOD_RANGE_MARGIN = 0.05            # abstain when a feature is 5% outside train range
TOP_K_FRACTION = 0.10              # review capacity: top 10% of flights

# --------------------------------------------------------------------------- #
# Drift policy
# --------------------------------------------------------------------------- #
PSI_REVIEW_THRESHOLD = 0.20
PSI_WATCH_THRESHOLD = 0.10
RESIDUAL_SHIFT_Z_THRESHOLD = 3.0
# Calendar features shift by construction between any two windows; they are
# handled by season-matching the reference window, not by PSI.
DRIFT_EXCLUDED_FEATURES = ["month"]

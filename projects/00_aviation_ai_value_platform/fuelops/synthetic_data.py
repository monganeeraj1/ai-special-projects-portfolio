"""Simulator for flight-level avoidable fuel.

Why a simulator, and why it is disclosed in full
-------------------------------------------------
Client flight data is confidential, so this project cannot show a model
trained on real operations. A simulator with a *known* data-generating
process (DGP) is not a substitute for that; it is a different tool. Because
the ground truth is known, every downstream component can be *tested* rather
than eyeballed:

* the model's benchmark is judged against the noise floor the DGP imposes,
  not presented as an achievement;
* the counterfactual attribution (controllable vs contextual) is checked
  against the simulator's true split;
* the drift monitor is checked against an injected shift;
* the decision engine's ranking is checked against the oracle ranking.

None of the numbers this produces say anything about a real airline. They
say whether the *method* holds up under noise, interactions, segment effects
and temporal structure.

Structure of the DGP
--------------------
    avoidable_fuel_kg = contextual(x) + controllable(x) + noise

* `contextual` depends on distance, payload, headwind, temperature, aircraft
  age, departure station and season. These are not intervention levers.
* `controllable` depends on five levers measured as excess over an operating
  benchmark (see `config.LEVER_BENCHMARKS`), with interactions: taxi-out
  excess costs more on heavy aircraft, APU excess costs more in heat, cruise
  and routing deviations scale with sector length.
* `noise` is heteroscedastic: longer sectors carry more unexplained variance.

Every component is written to the frame as a `true_*` column so it can be
used for validation. Those columns are excluded from the model by contract
(see `config.FEATURES`).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

STATIONS = ["HUB", "EUR-A", "EUR-B", "ASIA-A", "ASIA-B", "OCE-A"]
STATION_SHARE = [0.45, 0.11, 0.11, 0.11, 0.11, 0.11]

# Station-level operating character: ground congestion multiplies typical
# taxi-out time; the offset is a contextual fuel penalty (e.g. long standard
# departure routings) that the model must learn but no operator can change.
STATION_PROFILE = {
    "HUB": {"taxi_mult": 1.00, "context_offset_kg": 0.0},
    "EUR-A": {"taxi_mult": 1.35, "context_offset_kg": 90.0},
    "EUR-B": {"taxi_mult": 1.15, "context_offset_kg": 40.0},
    "ASIA-A": {"taxi_mult": 1.25, "context_offset_kg": 60.0},
    "ASIA-B": {"taxi_mult": 0.95, "context_offset_kg": 15.0},
    "OCE-A": {"taxi_mult": 1.05, "context_offset_kg": 150.0},
}

START_DATE = np.datetime64("2023-01-01")
N_DAYS = 730  # 24 months of operations


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def _payload_fraction(payload_tons: np.ndarray) -> np.ndarray:
    return np.clip((payload_tons - 18.0) / (72.0 - 18.0), 0.0, 1.0)


def lever_contributions(df: pd.DataFrame, benchmarks: dict[str, float] | None = None) -> pd.DataFrame:
    """Controllable fuel (kg) attributable to each lever, relative to benchmarks.

    Exposed as a function so the attribution test can compute the truth at
    whatever benchmark the pipeline is configured with.
    """
    b = dict(config.LEVER_BENCHMARKS if benchmarks is None else benchmarks)
    payload_frac = _payload_fraction(df["payload_tons"].to_numpy())
    heat = np.clip((df["temperature_c"].to_numpy() - 30.0) / 15.0, 0.0, None)
    sector = df["distance_km"].to_numpy() / 3000.0

    taxi_excess = np.clip(df["taxi_out_min"].to_numpy() - b["taxi_out_min"], 0.0, None)
    apu_excess = np.clip(df["apu_minutes"].to_numpy() - b["apu_minutes"], 0.0, None)
    delay_excess = np.clip(df["departure_delay_min"].to_numpy() - b["departure_delay_min"], 0.0, None)
    cruise_dev = np.abs(df["cruise_speed_delta_pct"].to_numpy() - b["cruise_speed_delta_pct"])
    route_gap = np.clip(b["route_efficiency_score"] - df["route_efficiency_score"].to_numpy(), 0.0, None)

    out = pd.DataFrame(index=df.index)
    out["true_lever_taxi_out_min_kg"] = 6.0 * taxi_excess * (1.0 + 0.6 * payload_frac)
    out["true_lever_departure_delay_min_kg"] = 2.8 * delay_excess
    out["true_lever_cruise_speed_delta_pct_kg"] = 45.0 * cruise_dev * (0.5 + 0.5 * sector)
    out["true_lever_apu_minutes_kg"] = 5.0 * apu_excess * (1.0 + 0.5 * heat)
    out["true_lever_route_efficiency_score_kg"] = 900.0 * route_gap * np.sqrt(sector)
    return out


def contextual_component(df: pd.DataFrame) -> np.ndarray:
    """Fuel (kg) explained by operating context that no lever can change."""
    payload_frac = _payload_fraction(df["payload_tons"].to_numpy())
    station_offset = df["departure_station"].map(
        {k: v["context_offset_kg"] for k, v in STATION_PROFILE.items()}
    ).to_numpy()
    # Mild seasonal effect on top of the temperature channel (e.g. seasonal
    # routing / airspace constraints), peaking mid-year.
    season = 35.0 * (1.0 + np.sin((df["month"].to_numpy() - 4.0) / 12.0 * 2.0 * np.pi)) / 2.0

    # Contextual excess is deliberately large and variable: a heavy long-haul
    # sector into headwind carries far more "excess" than a short hop, none of
    # which an operator can act on. That is what makes ranking on the total
    # prediction the wrong policy, and what the decision layer must handle.
    return (
        0.060 * df["distance_km"].to_numpy()
        + 1.4 * df["payload_tons"].to_numpy()
        + 4.0 * np.clip(df["headwind_kts"].to_numpy(), 0.0, None)
        + 1.2 * np.clip(df["temperature_c"].to_numpy() - 30.0, 0.0, None)
        + 4.0 * df["aircraft_age_years"].to_numpy()
        + 0.030 * df["distance_km"].to_numpy() * payload_frac  # heavy long sectors
        + station_offset
        + season
    )


def generate(n: int = config.N_FLIGHTS, seed: int = config.SEED) -> pd.DataFrame:
    """Generate `n` synthetic flights with full ground truth, sorted by date."""
    rng = np.random.default_rng(seed)

    day_offsets = np.sort(rng.integers(0, N_DAYS, n))
    flight_date = START_DATE + day_offsets.astype("timedelta64[D]")
    month = (flight_date.astype("datetime64[M]").astype(int) % 12) + 1

    distance_km = rng.uniform(250.0, 7200.0, n)
    is_widebody = rng.random(n) < _sigmoid((distance_km - 3000.0) / 800.0)
    aircraft_type = np.where(is_widebody, "widebody", "narrowbody")
    payload_tons = np.where(
        is_widebody, rng.uniform(35.0, 72.0, n), rng.uniform(18.0, 40.0, n)
    )

    departure_station = rng.choice(STATIONS, size=n, p=STATION_SHARE)
    taxi_mult = pd.Series(departure_station).map(
        {k: v["taxi_mult"] for k, v in STATION_PROFILE.items()}
    ).to_numpy()

    # Seasonal context for a Gulf hub: hot summers, seasonal wind regime.
    season_phase = (month - 4.0) / 12.0 * 2.0 * np.pi
    temperature_c = 24.0 + 14.0 * np.sin(season_phase) + rng.normal(0.0, 4.0, n)
    headwind_kts = rng.normal(5.0 + 6.0 * np.cos(season_phase), 18.0, n)

    df = pd.DataFrame(
        {
            "flight_date": flight_date,
            "month": month.astype(int),
            "departure_station": departure_station,
            "aircraft_type": aircraft_type,
            "distance_km": distance_km,
            "payload_tons": payload_tons,
            "headwind_kts": headwind_kts,
            "temperature_c": temperature_c,
            "aircraft_age_years": rng.uniform(1.0, 18.0, n),
            # Lever distributions are right-skewed on purpose: most flights
            # operate near benchmark and a minority carry most of the excess.
            # That concentration is what makes prioritisation worth doing.
            "taxi_out_min": (rng.gamma(shape=2.0, scale=6.5, size=n) + 5.0) * taxi_mult,
            "departure_delay_min": rng.gamma(shape=1.3, scale=10.0, size=n),
            "cruise_speed_delta_pct": np.where(
                rng.random(n) < 0.80, rng.normal(0.0, 1.0, n), rng.normal(0.0, 4.5, n)
            ),
            "apu_minutes": rng.gamma(shape=1.3, scale=10.0, size=n),
            "route_efficiency_score": 1.0 - 0.35 * rng.beta(1.0, 5.0, n),
        }
    )
    df["route_family"] = pd.cut(
        df["distance_km"],
        bins=[0, 1500, 4000, np.inf],
        labels=["short_haul", "medium_haul", "long_haul"],
    ).astype(str)

    levers = lever_contributions(df)
    df = pd.concat([df, levers], axis=1)
    df["true_controllable_kg"] = levers.sum(axis=1)
    df["true_contextual_kg"] = contextual_component(df)
    df["true_noise_kg"] = rng.normal(0.0, 40.0 + 0.012 * df["distance_km"].to_numpy())

    raw = df["true_contextual_kg"] + df["true_controllable_kg"] + df["true_noise_kg"]
    df[config.TARGET] = np.clip(raw, 0.0, None)
    return df.reset_index(drop=True)


def load_or_generate(path=None) -> pd.DataFrame:
    """Read the cached dataset if present, otherwise generate and cache it."""
    path = config.DATA_DIR / "synthetic_flights.csv" if path is None else path
    if path.exists():
        return pd.read_csv(path, parse_dates=["flight_date"])
    df = generate()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df


if __name__ == "__main__":
    frame = generate()
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = config.DATA_DIR / "synthetic_flights.csv"
    frame.to_csv(out, index=False)
    share = frame["true_controllable_kg"].sum() / (
        frame["true_controllable_kg"].sum() + frame["true_contextual_kg"].sum()
    )
    print(f"Generated {len(frame):,} flights -> {out}")
    print(f"Mean target: {frame[config.TARGET].mean():.0f} kg | true controllable share: {share:.1%}")

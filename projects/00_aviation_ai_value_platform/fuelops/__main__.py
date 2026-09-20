"""End-to-end pipeline. Run from the project directory:

    python -m fuelops

Steps: simulate -> temporal split -> fit + calibrate -> evaluate vs baselines
-> counterfactual attribution (validated) -> decision queue (scored against
oracle / naive / random) -> drift scenarios -> value model -> RESULTS.md.
"""
from __future__ import annotations

import json
import sys
import time

import joblib

from . import attribution, config, decision_engine, drift_monitor, report, synthetic_data, train, value_model


def run(n_flights: int = config.N_FLIGHTS, seed: int = config.SEED, write_outputs: bool = True) -> dict:
    t0 = time.time()
    log = lambda msg: print(f"[{time.time() - t0:5.1f}s] {msg}", file=sys.stderr)

    log(f"simulating {n_flights:,} flights (seed {seed})")
    df = synthetic_data.generate(n_flights, seed)

    log("temporal split, fitting baselines + gradient boosting + quantile models, calibrating interval")
    models, train_df, test_df, model_report = train.train_and_evaluate(df)

    log("counterfactual attribution (exact Shapley over 5 levers) on held-out window")
    attr = attribution.attribute(models, test_df)
    attribution_validation = attribution.validate_against_truth(attr, test_df)

    log("building decision queue and scoring ranking policies")
    queue = decision_engine.build_queue(models.encoder, test_df, attr)
    policy_report = decision_engine.evaluate_policies(queue)

    log("drift monitoring: clean window + two injected scenarios")
    reference = drift_monitor.season_matched_reference(train_df, test_df)
    drift = {
        "Held-out window, unmodified": drift_monitor.drift_report(models, reference, test_df),
        "Scenario A — measurement drift (+20% recorded taxi-out, fuel unchanged)":
            drift_monitor.drift_report(models, reference, drift_monitor.inject_measurement_drift(test_df)),
        "Scenario B — operational drift (airspace constraint, route efficiency −0.08, fuel recomputed)":
            drift_monitor.drift_report(models, reference, drift_monitor.inject_operational_drift(test_df)),
    }

    results = {
        "n_flights": int(len(df)),
        "model_report": model_report,
        "attribution_validation": attribution_validation,
        "policy_report": policy_report,
        "drift": drift,
        "value_table": value_model.value_table(policy_report),
    }

    if write_outputs:
        for d in (config.DATA_DIR, config.OUTPUT_DIR, config.MODEL_DIR):
            d.mkdir(parents=True, exist_ok=True)
        df.to_csv(config.DATA_DIR / "synthetic_flights.csv", index=False)
        joblib.dump(models, config.MODEL_DIR / "fuel_opportunity_models.joblib")
        queue.to_csv(config.OUTPUT_DIR / "prioritized_interventions.csv", index=False)
        model_report["importance"].to_csv(config.OUTPUT_DIR / "feature_importance.csv", index=False)
        for name, rep in drift.items():
            slug = name.split("—")[0].strip().lower().replace(" ", "_").replace(",", "")
            rep.to_csv(config.OUTPUT_DIR / f"drift_{slug}.csv", index=False)
        serialisable = {
            "model": {k: v for k, v in model_report.items() if k not in ("importance", "segments")},
            "segments": model_report["segments"],
            "attribution_validation": attribution_validation,
            "policy": policy_report,
        }
        (config.OUTPUT_DIR / "metrics.json").write_text(json.dumps(serialisable, indent=2, default=float))
        report.write(results)
        log(f"wrote {config.RESULTS_MD.relative_to(config.PROJECT_ROOT)} and outputs/")

    log("done")
    return results


if __name__ == "__main__":
    run()

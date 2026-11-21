#!/usr/bin/env python3
"""Keep running optimizer batches until the same feasible rocket wins repeatedly."""
from __future__ import annotations

import argparse
import time
from dataclasses import asdict
from pathlib import Path
import random

from arc_optimizer import Constraints, Design, append_run_ledger, optimize, write_outputs


def design_key(result) -> tuple:
    """Identify a rocket by its design parameters, not its random run metadata."""
    values = asdict(result.design)
    values.pop("name", None)
    return tuple(sorted(values.items()))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run optimizer batches until one feasible rocket is best repeatedly"
    )
    parser.add_argument("--iterations", type=int, default=250)
    parser.add_argument("--population", type=int, default=120)
    parser.add_argument("--target-altitude", type=float, default=259.0)
    parser.add_argument("--altitude-tolerance", type=float, default=12.0)
    parser.add_argument("--max-velocity", type=float, default=230.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--required-best-runs", type=int, default=3)
    parser.add_argument("--max-batches", type=int, default=0, help="0 means run until success")
    parser.add_argument("--pause-seconds", type=float, default=0.0)
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--ledger", type=Path, default=Path("arc-runs.csv"))
    args = parser.parse_args()
    if args.required_best_runs < 1:
        parser.error("--required-best-runs must be at least 1")

    constraints = Constraints(args.target_altitude, args.altitude_tolerance, args.max_velocity)
    previous_key = None
    consecutive_best = 0
    batch = 0

    print(f"Running until the same feasible rocket is best {args.required_best_runs} times.")
    print("Press Ctrl+C to stop safely. Results are appended to the ledger after every batch.")
    try:
        while args.max_batches == 0 or batch < args.max_batches:
            batch += 1
            run_seed = args.seed + batch - 1
            results = optimize(
                Design(), constraints, args.iterations, args.population, random.Random(run_seed)
            )
            write_outputs(results, args.output)
            run_id = append_run_ledger(results, args.ledger, run_seed, args.iterations, args.population)
            best = results[0]
            key = design_key(best)
            if best.feasible and key == previous_key:
                consecutive_best += 1
            elif best.feasible:
                consecutive_best = 1
            else:
                consecutive_best = 0
            previous_key = key if best.feasible else None
            print(
                f"batch={batch} run={run_id} best_score={best.score:.5f} "
                f"apogee={best.apogee_m:.2f}m stability={best.stability_calibers:.2f}cal "
                f"feasible={best.feasible} stable_best={consecutive_best}/{args.required_best_runs}"
            )
            if best.feasible and consecutive_best >= args.required_best_runs:
                print("Success condition reached: the same feasible rocket was best repeatedly.")
                return
            if args.pause_seconds:
                time.sleep(args.pause_seconds)
    except KeyboardInterrupt:
        print("Stopped by user. The last completed batch remains in the output files and ledger.")

    if args.max_batches:
        print(f"Stopped after --max-batches {args.max_batches} without reaching the success condition.")


if __name__ == "__main__":
    main()

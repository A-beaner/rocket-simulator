#!/usr/bin/env python3
"""Fast, transparent rocket-design iteration tool for ARC concept exploration.

This is a lightweight screening model, not a replacement for OpenRocket or a
flight-safety review. Use it to search a design space, then verify finalists in
OpenRocket with the exact motor, recovery system, launch site, and current ARC
rules before building or flying.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import asdict, dataclass, replace
from pathlib import Path

G = 9.80665
RHO = 1.225


@dataclass(frozen=True)
class Design:
    name: str = "arc-candidate"
    body_length_m: float = 0.85
    body_diameter_m: float = 0.054
    nose_length_m: float = 0.18
    fin_span_m: float = 0.075
    fin_root_m: float = 0.16
    fin_tip_m: float = 0.07
    fin_sweep_m: float = 0.035
    dry_mass_kg: float = 0.095
    payload_mass_kg: float = 0.113
    motor_prop_mass_kg: float = 0.014
    motor_impulse_ns: float = 20.0
    burn_time_s: float = 1.15
    cd: float = 0.50


@dataclass(frozen=True)
class Constraints:
    target_altitude_m: float = 259.0
    altitude_tolerance_m: float = 12.0
    max_velocity_m_s: float = 230.0
    min_stability_calibers: float = 1.0
    max_mass_kg: float = 0.35


@dataclass(frozen=True)
class Result:
    design: Design
    apogee_m: float
    max_velocity_m_s: float
    stability_calibers: float
    total_mass_kg: float
    time_to_apogee_s: float
    score: float
    feasible: bool


def stability_calibers(d: Design) -> float:
    # A deliberately conservative Barrowman-inspired screening estimate.
    fin_area = max(d.fin_root_m * d.fin_span_m, 1e-6)
    body_area = math.pi * (d.body_diameter_m / 2) ** 2
    fin_effect = 0.55 * fin_area / body_area
    cg_from_tip = 0.54 * d.body_length_m
    cp_from_tip = 0.67 * d.body_length_m - 0.16 * d.nose_length_m + 0.08 * d.body_length_m / (1 + fin_effect)
    return (cg_from_tip - cp_from_tip) / d.body_diameter_m


def simulate(d: Design, dt: float = 0.01) -> tuple[float, float, float]:
    """Return apogee, max speed, and time-to-apogee using 1-D vertical flight."""
    mass = d.dry_mass_kg + d.payload_mass_kg + d.motor_prop_mass_kg
    burn_rate = d.motor_prop_mass_kg / max(d.burn_time_s, 1e-6)
    thrust = d.motor_impulse_ns / max(d.burn_time_s, 1e-6)
    area = math.pi * (d.body_diameter_m / 2) ** 2
    altitude = velocity = max_velocity = time = 0.0
    while time < 120.0:
        if time < d.burn_time_s and mass > d.dry_mass_kg + d.payload_mass_kg:
            current_thrust = thrust
            mass = max(mass - burn_rate * dt, d.dry_mass_kg + d.payload_mass_kg)
        else:
            current_thrust = 0.0
        drag = 0.5 * RHO * velocity * abs(velocity) * d.cd * area
        acceleration = (current_thrust - drag) / mass - G
        velocity += acceleration * dt
        altitude = max(0.0, altitude + velocity * dt)
        max_velocity = max(max_velocity, velocity)
        time += dt
        if time > d.burn_time_s and velocity <= 0:
            return altitude, max_velocity, time
        if altitude <= 0 and time > d.burn_time_s + 0.5:
            break
    return altitude, max_velocity, time


def evaluate(d: Design, c: Constraints) -> Result:
    apogee, max_velocity, tta = simulate(d)
    stability = stability_calibers(d)
    total_mass = d.dry_mass_kg + d.payload_mass_kg + d.motor_prop_mass_kg
    altitude_error = abs(apogee - c.target_altitude_m) / max(c.altitude_tolerance_m, 1)
    score = altitude_error
    score += max(0.0, c.min_stability_calibers - stability) * 8
    score += max(0.0, max_velocity - c.max_velocity_m_s) / 20
    score += max(0.0, total_mass - c.max_mass_kg) * 100
    feasible = (
        altitude_error <= 1
        and stability >= c.min_stability_calibers
        and max_velocity <= c.max_velocity_m_s
        and total_mass <= c.max_mass_kg
    )
    return Result(d, apogee, max_velocity, stability, total_mass, tta, score, feasible)


RANGES = {
    "body_length_m": (0.55, 1.40), "body_diameter_m": (0.040, 0.080),
    "nose_length_m": (0.10, 0.32), "fin_span_m": (0.040, 0.14),
    "fin_root_m": (0.08, 0.28), "fin_tip_m": (0.02, 0.14),
    "fin_sweep_m": (0.0, 0.10), "dry_mass_kg": (0.045, 0.19),
    "motor_prop_mass_kg": (0.008, 0.040), "motor_impulse_ns": (5.0, 40.0),
    "burn_time_s": (0.55, 2.20), "cd": (0.35, 0.75),
}


def mutate(d: Design, rng: random.Random, strength: float = 0.12) -> Design:
    values = asdict(d)
    for key, (lo, hi) in RANGES.items():
        if rng.random() < 0.45:
            span = hi - lo
            values[key] = min(hi, max(lo, values[key] + rng.gauss(0, span * strength)))
    values["name"] = d.name
    values["payload_mass_kg"] = d.payload_mass_kg
    return Design(**values)


def optimize(seed: Design, constraints: Constraints, generations: int, population_size: int, rng: random.Random) -> list[Result]:
    population = [seed] + [mutate(seed, rng, 0.35) for _ in range(population_size - 1)]
    best: list[Result] = []
    for _ in range(generations):
        ranked = sorted((evaluate(d, constraints) for d in population), key=lambda r: r.score)
        best.extend(ranked[:5])
        elites = [r.design for r in ranked[:max(2, population_size // 8)]]
        population = elites[:]
        while len(population) < population_size:
            parent = rng.choice(elites)
            population.append(mutate(parent, rng, 0.08 if rng.random() < 0.75 else 0.20))
    return sorted(best, key=lambda r: (not r.feasible, r.score))[:20]


def write_outputs(results: list[Result], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = []
    for r in results:
        item = asdict(r)
        item["design"] = asdict(r.design)
        payload.append(item)
    (output_dir / "results.json").write_text(json.dumps(payload, indent=2) + "\n")
    with (output_dir / "results.csv").open("w", newline="") as f:
        fields = ["rank", "feasible", "score", "apogee_m", "max_velocity_m_s", "stability_calibers", "total_mass_kg", "time_to_apogee_s"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for rank, r in enumerate(results, 1):
            writer.writerow({"rank": rank, "feasible": r.feasible, "score": round(r.score, 5), "apogee_m": round(r.apogee_m, 3), "max_velocity_m_s": round(r.max_velocity_m_s, 3), "stability_calibers": round(r.stability_calibers, 3), "total_mass_kg": round(r.total_mass_kg, 4), "time_to_apogee_s": round(r.time_to_apogee_s, 3)})


def main() -> None:
    p = argparse.ArgumentParser(description="Iterate ARC rocket concepts with a lightweight screening simulation")
    p.add_argument("--iterations", type=int, default=100, help="optimization generations")
    p.add_argument("--population", type=int, default=80)
    p.add_argument("--target-altitude", type=float, default=259.0)
    p.add_argument("--altitude-tolerance", type=float, default=12.0)
    p.add_argument("--max-velocity", type=float, default=230.0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", type=Path, default=Path("results"))
    args = p.parse_args()
    constraints = Constraints(args.target_altitude, args.altitude_tolerance, args.max_velocity)
    results = optimize(Design(), constraints, args.iterations, args.population, random.Random(args.seed))
    write_outputs(results, args.output)
    for i, r in enumerate(results[:10], 1):
        print(f"{i:2}. {'PASS' if r.feasible else '----'} apogee={r.apogee_m:7.1f} m  v={r.max_velocity_m_s:6.1f} m/s  stability={r.stability_calibers:4.2f} cal  score={r.score:6.3f}")
    print(f"\nWrote {args.output / 'results.json'} and {args.output / 'results.csv'}")
    print("Verify finalists in OpenRocket and against the current ARC rules before construction or launch.")


if __name__ == "__main__":
    main()

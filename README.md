# rocket-simulator

A lightweight, repeatable rocket-design iteration tool for American Rocketry Challenge (ARC) concept exploration.

## Run it

Requires Python 3.10+ and no third-party packages:

```bash
python arc_optimizer.py --iterations 250 --population 120 --seed 7
```

Each execution now:

1. Generates and evaluates many candidate designs.
2. Ranks the best candidates.
3. Writes the latest results to `results/results.json` and `results/results.csv`.
4. Appends every ranked candidate to the cumulative `arc-runs.csv` ledger.

Use a different ledger path if desired:

```bash
python arc_optimizer.py --iterations 500 --population 200 --ledger data/my-runs.csv
```

Useful options:

```text
--target-altitude 259       target apogee in metres
--altitude-tolerance 12     acceptable target band in metres
--max-velocity 230          screening velocity limit in m/s
--iterations 250            number of generations
--population 120            designs per generation
--seed 7                    repeatable random seed
--output results            latest run output directory
--ledger arc-runs.csv      cumulative run history
```

## What it measures

The optimizer scores apogee proximity, maximum velocity, estimated stability in calibers, and total mass. It uses a transparent 1-D vertical-flight screening model and a genetic search. `arc-runs.csv` preserves the timestamp, run ID, settings, rank, score, and flight metrics from every execution.

## Important limitations

This is an early design-space searcher, **not a flight-certification or safety tool** and not a replacement for OpenRocket. Its aerodynamic, motor, drag, recovery, weather, and stability models are intentionally simplified. Import the top candidates into OpenRocket, select the exact certified motor, model recovery deployment, check launch-rod departure, verify structural margins, and have a qualified adult/team mentor review every design against the current official ARC handbook before building or flying.

OpenRocket reference: https://github.com/openrocket/openrocket

# rocket-simulator

A lightweight, repeatable rocket-design iteration tool for American Rocketry Challenge (ARC) concept exploration.

## Run one batch

Requires Python 3.10+ and no third-party packages:

```bash
python arc_optimizer.py --iterations 250 --population 120 --seed 7
```

## Run until a design is stable and successful

Use the continuous runner when you want it to keep searching until the same rocket is the best feasible result three times in a row:

```bash
python run_until_success.py \
  --iterations 250 \
  --population 120 \
  --required-best-runs 3 \
  --seed 7
```

The success condition is:

1. The best candidate is feasible: within the target altitude tolerance, under the velocity limit, above the minimum stability, and below the mass limit.
2. The same design parameters are the best feasible candidate for the required number of consecutive batches.

Press `Ctrl+C` to stop. The last completed batch is preserved. To prevent an unlimited run, use `--max-batches 100`. Every batch appends ranked results to `arc-runs.csv` and refreshes the latest files in `results/`.

Useful continuous-run options:

```text
--required-best-runs 3      confirmations required before stopping
--max-batches 0             0 means unlimited until success
--pause-seconds 5           optional delay between batches
--seed 7                    starting seed; each batch uses a different seed
```

## Outputs

Each execution writes the latest candidates to `results/results.json` and `results/results.csv`, and appends every ranked candidate to the cumulative `arc-runs.csv` ledger.

## Important limitations

This is an early design-space searcher, **not a flight-certification or safety tool** and not a replacement for OpenRocket. Its aerodynamic, motor, drag, recovery, weather, and stability models are intentionally simplified. Import the top candidates into OpenRocket, select the exact certified motor, model recovery deployment, check launch-rod departure, verify structural margins, and have a qualified adult/team mentor review every design against the current official ARC handbook before building or flying.

OpenRocket reference: https://github.com/openrocket/openrocket

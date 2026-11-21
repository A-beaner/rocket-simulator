# rocket-simulator

A lightweight, repeatable rocket-design iteration tool for American Rocketry Challenge (ARC) concept exploration.

## What it does

`arc_optimizer.py` generates and evaluates many candidate designs using a transparent 1-D vertical-flight model, then ranks them by:

- apogee proximity to a configurable target altitude;
- maximum velocity;
- estimated stability in calibers; and
- total mass.

It uses a small genetic search so you can rerun hundreds or thousands of iterations with a fixed seed and compare results.

## Run it

Requires Python 3.10+ and no third-party packages:

```bash
python arc_optimizer.py --iterations 250 --population 120 --seed 7 --output results
```

Useful options:

```text
--target-altitude 259       target apogee in metres
--altitude-tolerance 12     acceptable target band in metres
--max-velocity 230          screening velocity limit in m/s
--iterations 250            number of generations
--population 120            designs per generation
```

The tool writes `results/results.json` and `results/results.csv` and prints the best candidates. The default values are placeholders: set them to the current ARC rules, event altitude, payload, motor, and launch conditions for your team.

## Important limitations

This is an early design-space searcher, **not a flight-certification or safety tool** and not a replacement for OpenRocket. Its aerodynamic, motor, drag, recovery, weather, and stability models are intentionally simplified. Import the top candidates into OpenRocket, select the exact certified motor, model recovery deployment, check launch-rod departure, verify structural margins, and have a qualified adult/team mentor review every design against the current official ARC handbook before building or flying.

The repository is intentionally independent of OpenRocket's source code. OpenRocket is the authoritative detailed simulator to use for finalist verification: https://github.com/openrocket/openrocket

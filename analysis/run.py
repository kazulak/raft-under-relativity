"""Compute every number in analysis/magnitudes.typ and write analysis/results.json.

Run from the repository root:  python analysis/run.py
"""

import json
import math
import random
from pathlib import Path

import rates as r
from spacetime import Event, Inertial, PiecewiseInertial, doppler_inertial, lease_round

OUT = Path(__file__).with_name("results.json")
SEED = 20261008


def clean(x):
    """JSON has no infinity: map it to null."""
    if isinstance(x, float) and math.isinf(x):
        return None
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [clean(v) for v in x]
    return x


def validation():
    return {
        "gps_orbit_rate": r.orbit_rate(r.GM_EARTH, r.A_GPS),
        "geoid_rate": r.geoid_rate(),
        "gps_vs_geoid": r.gps_vs_geoid(),
        "gps_vs_geoid_us_per_day": r.per_day(r.gps_vs_geoid()),
        "gps_published": 4.4647e-10,
        "moon_us_per_day": r.per_day(r.moon_surface_rate() - r.geoid_rate()),
        "moon_published_us_per_day": 56.02,
        "mars_us_per_day": r.per_day(r.mars_surface_rate_helio() - r.earth_surface_rate_helio()),
        "mars_published_us_per_day": 477,
        "mars_published_variation_us_per_day": 226,
    }


def random_polyline(rng, x0, t0=-5.0, t1=60.0, vmax=0.9):
    knots, t, x = [Event(t0, x0)], t0, x0
    while t < t1:
        dt = rng.uniform(0.5, 8.0)
        t, x = t + dt, x + rng.uniform(-vmax, vmax) * dt
        knots.append(Event(t, x))
    return PiecewiseInertial(knots)


def conjecture(n=2000):
    rng = random.Random(SEED)
    worst = math.inf
    for _ in range(n):
        leader = Inertial(0.0, rng.uniform(-0.9, 0.9))
        follower = random_polyline(rng, rng.uniform(-20, 20))
        lr = lease_round(leader, follower, rng.uniform(0, 5), rng.uniform(0.1, 20))
        worst = min(worst, lr.max_lease_causal / lr.t_e)

    twin = lease_round(PiecewiseInertial([Event(0, 0), Event(5, 4), Event(10, 0)]), Inertial(0, 0), 0.0, 10.0)

    receding = []
    for name, beta in [("Ground-LEO", 2.25e-5), ("Earth-Mars", 4.65e-5), ("Fast pair", 0.6)]:
        lr = lease_round(Inertial(0, 0), Inertial(0, beta), 1.0, 1.0)
        receding.append({"name": name, "beta": beta, "k": doppler_inertial(beta),
                         "max_lease_every_frame": lr.max_lease_every_frame,
                         "max_lease_causal": lr.max_lease_causal})
    return {
        "random_trials": n,
        "seed": SEED,
        "causal_inertial_worst_ratio": worst,
        "twin_leader_speed": 0.8,
        "twin_t_e": twin.t_e,
        "twin_max_lease_causal": twin.max_lease_causal,
        "receding": receding,
    }


def main():
    results = {
        "validation": validation(),
        "oscillators": r.OSCILLATORS,
        "configurations": [r.lease_terms(c) for c in r.configurations()],
        "conjecture": conjecture(),
    }
    OUT.write_text(json.dumps(clean(results), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

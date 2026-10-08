"""Identities of the 1+1D model, and numerical tests of the lease conjecture.

Passing tests are evidence, not proof; the proofs are Step 2 (Lean).
"""

import math
import random

import pytest

from spacetime import (Event, Hyperbolic, Inertial, PiecewiseInertial, Worldline, doppler,
                       doppler_inertial, interval2, lease_round, max_doppler, precedes)

N = 2000


def random_polyline(rng, x0, t0=-5.0, t1=60.0, vmax=0.9):
    knots, t, x = [Event(t0, x0)], t0, x0
    while t < t1:
        dt = rng.uniform(0.5, 8.0)
        t, x = t + dt, x + rng.uniform(-vmax, vmax) * dt
        knots.append(Event(t, x))
    return PiecewiseInertial(knots)


# --- Identities -----------------------------------------------------------------


def test_precedes_is_reflexive_and_transitive():
    rng = random.Random(1)
    for _ in range(N):
        e = Event(rng.uniform(-5, 5), rng.uniform(-5, 5))
        f = Event(e.t + rng.uniform(0, 5), 0.0)
        f = Event(f.t, e.x + rng.uniform(-1, 1) * (f.t - e.t))
        g = Event(f.t + rng.uniform(0, 5), 0.0)
        g = Event(g.t, f.x + rng.uniform(-1, 1) * (g.t - f.t))
        assert precedes(e, e)
        assert precedes(e, f) and precedes(f, g) and precedes(e, g)
        assert interval2(e, g) >= -1e-12


def test_closed_form_arrival_matches_root_finding():
    rng = random.Random(2)
    for _ in range(N):
        w = Inertial(rng.uniform(-10, 10), rng.uniform(-0.95, 0.95))
        e = Event(rng.uniform(-10, 10), rng.uniform(-10, 10))
        assert Worldline.light_arrival(w, e) == pytest.approx(w.light_arrival_closed_form(e), rel=1e-12, abs=1e-12)


@pytest.mark.parametrize("w", [
    PiecewiseInertial([Event(0, 0), Event(3, 2), Event(7, -1), Event(9, 0)]),
    Hyperbolic(0.0, 0.3),
    Inertial(1.0, -0.4),
])
def test_proper_time_is_additive_and_inverted_by_time_after(w):
    rng = random.Random(3)
    for _ in range(200):
        a, b, c = sorted(rng.uniform(-5, 15) for _ in range(3))
        assert w.proper_time(a, c) == pytest.approx(w.proper_time(a, b) + w.proper_time(b, c), rel=1e-12)
        assert w.time_after(a, w.proper_time(a, c)) == pytest.approx(c, rel=1e-9, abs=1e-9)


def test_static_pair_round_trip():
    lr = lease_round(Inertial(0, 0), Inertial(3.0, 0), 0.0, 2.0)
    assert lr.max_lease_causal == pytest.approx(2.0 + 2 * 3.0)
    assert lr.max_lease_every_frame == pytest.approx(2.0)


@pytest.mark.parametrize("beta", [-0.6, -0.1, 2.25e-5, 0.3, 0.9])
def test_inertial_pair_matches_bondi_k_calculus(beta):
    # Leader at rest at x = 0, follower through the origin at velocity beta; S at leader time tau_S.
    k = doppler_inertial(beta)
    tau_s, t_e = (2.0, 3.0) if beta > 0 else (-50.0, 3.0)
    lr = lease_round(Inertial(0, 0), Inertial(0, beta), tau_s, t_e)
    assert lr.max_lease_causal == pytest.approx((k * k - 1) * tau_s + k * t_e, rel=1e-9)
    assert lr.max_lease_every_frame == pytest.approx(t_e / k, rel=1e-12)
    assert doppler(Inertial(0, 0), Inertial(0, beta), tau_s) == pytest.approx(k, rel=1e-12)


def test_hyperbolic_deficit_against_geodesic():
    # Twin-paradox deficit of uniform acceleration a over coordinate time T: about a^2 T^3 / 24.
    for a, t in [(1e-2, 10.0), (1e-3, 30.0)]:
        h = Hyperbolic(0.0, a)
        deficit = math.sqrt(interval2(h.event(0), h.event(t))) - h.proper_time(0, t)
        assert deficit == pytest.approx(a * a * t ** 3 / 24, rel=0.02)


# --- Conjecture checks ----------------------------------------------------------


def test_causal_reading_inertial_leader_never_loses_lease_time():
    """Conjecture (survey, Discussion): with an inertial leader, tau_L(S -> A) >= T_e."""
    rng = random.Random(4)
    worst = math.inf
    for _ in range(N):
        leader = Inertial(0.0, rng.uniform(-0.9, 0.9))
        follower = random_polyline(rng, rng.uniform(-20, 20))
        lr = lease_round(leader, follower, rng.uniform(0, 5), rng.uniform(0.1, 20))
        worst = min(worst, lr.max_lease_causal / lr.t_e)
    assert worst >= 1 - 1e-12


def test_causal_reading_accelerated_leader_can_lose_lease_time():
    """Twin paradox: a leader that leaves and returns has less proper time than T_e."""
    leader = PiecewiseInertial([Event(0, 0), Event(5, 4), Event(10, 0)])
    lr = lease_round(leader, Inertial(0, 0), 0.0, 10.0)
    assert lr.max_lease_causal == pytest.approx(6.0)
    assert lr.max_lease_causal < lr.t_e


def test_every_frame_reading_is_bounded_by_doppler_factors():
    """Hypothesis: T_e / k_max <= max lease <= T_e / k_min for an inertial leader."""
    rng = random.Random(5)
    for _ in range(300):
        leader = Inertial(0.0, rng.uniform(-0.9, 0.9))
        follower = random_polyline(rng, rng.uniform(-20, 20))
        lr = lease_round(leader, follower, rng.uniform(0, 5), rng.uniform(0.1, 20))
        ks = [doppler(leader, follower, lr.S.t + (lr.D.t - lr.S.t) * i / 4000) for i in range(4001)]
        assert lr.max_lease_every_frame >= lr.t_e / max(ks) * (1 - 1e-9)
        assert lr.max_lease_every_frame <= lr.t_e / min(ks) * (1 + 1e-9)


def test_every_frame_reading_loses_first_order_lease_time_when_receding():
    """For a receding inertial pair the safe lease is T_e / k < T_e, at first order in beta."""
    beta = 2.25e-5                                    # ground-LEO, analysis/rates.py
    lr = lease_round(Inertial(0, 0), Inertial(0, beta), 1.0, 1.0)
    assert 1 - lr.max_lease_every_frame == pytest.approx(beta, rel=1e-3)
    assert max_doppler(Inertial(0, 0), Inertial(0, beta), lr.S.t, lr.D.t) == pytest.approx(doppler_inertial(beta))

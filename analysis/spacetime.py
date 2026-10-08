"""Flat 1+1D spacetime with c = 1: worldlines, light signals and the lease round.

This is the executable prototype of the Step 2 Lean model: the names here
(Event, precedes, interval2, proper_time, light_arrival, ...) are the objects the
Lean definitions will formalise.

The lease round (Ongaro 2014, p. 92): the leader sends heartbeats at S and starts
its lease there; a follower receives at R and refuses to vote for T_e of its own
proper time, until V. Light from V reaches the leader at A. The lease expires at
E, T_L of leader proper time after S.

- Causal reading (E not in the causal future of V): safe iff E is before A.
- Every-frame reading (E in the causal past of V): safe iff E is no later than
  the leader event whose light reaches V.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    t: float
    x: float


def precedes(e, f):
    """e is in the causal past of f (or equal): f lies in the closed future light cone of e."""
    return f.t - e.t >= abs(f.x - e.x)


def interval2(e, f):
    """Squared Minkowski interval (t^2 - x^2) from e to f; >= 0 for causally related events."""
    return (f.t - e.t) ** 2 - (f.x - e.x) ** 2


def _root_increasing(g, lo, step):
    """Root of a nondecreasing function with g(lo) <= 0, by bracketing then bisection."""
    hi = lo + step
    while g(hi) < 0:
        lo, hi = hi, hi + 2 * (hi - lo)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if mid in (lo, hi):
            break
        if g(mid) < 0:
            lo = mid
        else:
            hi = mid
    return hi


class Worldline:
    """A timelike worldline x(t) with |v| < 1, parametrised by coordinate time t."""

    def position(self, t):
        raise NotImplementedError

    def velocity(self, t):
        raise NotImplementedError

    def proper_time(self, t0, t1):
        """Proper time elapsed along the worldline from t0 to t1 (t0 <= t1)."""
        raise NotImplementedError

    def time_after(self, t0, dtau):
        """Coordinate time at which dtau of proper time has elapsed since t0."""
        raise NotImplementedError

    def event(self, t):
        return Event(t, self.position(t))

    def light_arrival(self, e):
        """Earliest t >= e.t at which a light signal sent at e reaches this worldline."""
        g = lambda t: (t - e.t) - abs(self.position(t) - e.x)
        return _root_increasing(g, e.t, abs(self.position(e.t) - e.x) + 1.0)

    def light_departure(self, e):
        """Latest t <= e.t at which a light signal from this worldline reaches e."""
        f = lambda u: u - abs(e.x - self.position(e.t - u))     # u = e.t - t >= 0
        return e.t - _root_increasing(f, 0.0, abs(e.x - self.position(e.t)) + 1.0)


class Inertial(Worldline):
    """x(t) = x0 + v t."""

    def __init__(self, x0, v):
        assert abs(v) < 1
        self.x0, self.v = x0, v

    def position(self, t):
        return self.x0 + self.v * t

    def velocity(self, t):
        return self.v

    def proper_time(self, t0, t1):
        return (t1 - t0) * math.sqrt(1 - self.v ** 2)

    def time_after(self, t0, dtau):
        return t0 + dtau / math.sqrt(1 - self.v ** 2)

    def light_arrival_closed_form(self, e):
        gap = self.position(e.t) - e.x
        if gap == 0:
            return e.t
        s = 1.0 if gap > 0 else -1.0           # direction of the light ray
        return (e.t + s * (self.x0 - e.x)) / (1 - s * self.v)


class PiecewiseInertial(Worldline):
    """Polyline through events (t_i, x_i), extended inertially beyond both ends."""

    def __init__(self, knots):
        self.knots = sorted(knots, key=lambda e: e.t)
        self.vs = [(b.x - a.x) / (b.t - a.t) for a, b in zip(self.knots, self.knots[1:])]
        assert all(abs(v) < 1 for v in self.vs)

    def _segment(self, t):
        for i in range(len(self.vs) - 1):
            if t < self.knots[i + 1].t:
                return i
        return len(self.vs) - 1

    def position(self, t):
        i = self._segment(t)
        return self.knots[i].x + self.vs[i] * (t - self.knots[i].t)

    def velocity(self, t):
        return self.vs[self._segment(t)]

    def proper_time(self, t0, t1):
        cuts = [t0] + [k.t for k in self.knots if t0 < k.t < t1] + [t1]
        return sum((b - a) * math.sqrt(1 - self.velocity(0.5 * (a + b)) ** 2)
                   for a, b in zip(cuts, cuts[1:]))

    def time_after(self, t0, dtau):
        t = t0
        for k in self.knots:
            if k.t <= t:
                continue
            step = self.proper_time(t, k.t)
            if step >= dtau:
                break
            dtau -= step
            t = k.t
        return t + dtau / math.sqrt(1 - self.velocity(t) ** 2)


class Hyperbolic(Worldline):
    """Uniform proper acceleration a, at rest at x0 when t = 0."""

    def __init__(self, x0, a):
        assert a != 0
        self.x0, self.a = x0, a

    def position(self, t):
        return self.x0 + (math.sqrt(1 + (self.a * t) ** 2) - 1) / self.a

    def velocity(self, t):
        return self.a * t / math.sqrt(1 + (self.a * t) ** 2)

    def proper_time(self, t0, t1):
        return (math.asinh(self.a * t1) - math.asinh(self.a * t0)) / self.a

    def time_after(self, t0, dtau):
        return math.sinh(math.asinh(self.a * t0) + self.a * dtau) / self.a


def doppler(emitter, receiver, t_emit):
    """k = d(tau_receiver)/d(tau_emitter) for a light signal sent at t_emit.

    Along a light ray moving in direction s, u = t - s x is constant; each clock
    crosses u-surfaces at rate gamma (1 - s v) per unit of its proper time.
    """
    e = emitter.event(t_emit)
    t_r = receiver.light_arrival(e)
    s = 1.0 if receiver.position(t_r) >= e.x else -1.0
    ve, vr = emitter.velocity(t_emit), receiver.velocity(t_r)
    return ((1 - s * ve) / math.sqrt(1 - ve ** 2)) / ((1 - s * vr) / math.sqrt(1 - vr ** 2))


def doppler_inertial(beta):
    """Bondi k for an inertial pair receding at speed beta (approaching: beta < 0)."""
    return math.sqrt((1 + beta) / (1 - beta))


@dataclass(frozen=True)
class LeaseRound:
    S: Event
    R: Event
    V: Event
    A: Event
    D: Event          # leader event whose light reaches V
    t_e: float
    max_lease_causal: float
    max_lease_every_frame: float


def lease_round(leader, follower, t_s, t_e):
    S = leader.event(t_s)
    R = follower.event(follower.light_arrival(S))
    V = follower.event(follower.time_after(R.t, t_e))
    A = leader.event(leader.light_arrival(V))
    D = leader.event(leader.light_departure(V))
    return LeaseRound(S, R, V, A, D, t_e,
                      max_lease_causal=leader.proper_time(S.t, A.t),
                      max_lease_every_frame=leader.proper_time(S.t, D.t))


def max_doppler(leader, follower, t0, t1, samples=200):
    """Largest leader-to-follower Doppler factor over emissions in [t0, t1]."""
    return max(doppler(leader, follower, t0 + (t1 - t0) * i / samples)
               for i in range(samples + 1))

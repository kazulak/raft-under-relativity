"""Clock rates and lease terms for realistic node configurations (SI units).

Weak-field, first-order model: a clock moving at speed v at Newtonian potential
Phi ticks at  d(tau)/dt = 1 + Phi/c^2 - v^2/(2 c^2)  relative to the coordinate
time t of the chosen frame (Ashby 2003, Eq. 30). Rates below are the fractional
offsets d(tau)/dt - 1. Simplifications: monopole fields, circular coplanar
orbits, no Shapiro delay, no tidal terms.
"""

import math
from dataclasses import dataclass

import numpy as np

# IERS Conventions (2010), Table 1.1 (TCG/TCB-compatible values).
C = 299_792_458.0                 # m/s, defining
L_G = 6.969290134e-10             # 1 - d(TT)/d(TCG), defining (IAU 2000 B1.9)
GM_EARTH = 3.986004418e14         # m^3/s^2
GM_SUN = 1.32712442099e20         # m^3/s^2
AU = 1.49597870700e11             # m
R_EARTH = 6_378_136.6             # m, equatorial radius
G_EARTH = 9.7803278               # m/s^2, mean equatorial gravity
# IERS Conventions (2010), Table 3.1 (DE421 mass parameters).
GM_MOON = 4.902800076e12          # m^3/s^2
GM_MARS = 4.2828375214e13         # m^3/s^2
# IERS Conventions (2010), Table 1.2 (GRS80 nominal angular velocity).
OMEGA_EARTH = 7.292115e-5         # rad/s
# NASA planetary fact sheets.
R_MOON = 1_737.4e3                # m, mean radius
A_MOON = 384_400e3                # m, mean Earth-Moon distance
R_MARS = 3_389.5e3                # m, volumetric mean radius
A_MARS = 227.956e9                # m, semi-major axis
# Ashby 2003, p. 16.
A_GPS = 26_561.75e3               # m, GPS orbit semi-major axis

DAY = 86_400.0


def per_day(frac):
    """Fractional rate offset expressed in microseconds per day."""
    return frac * DAY * 1e6


def rate(potential, speed):
    """Fractional clock rate d(tau)/dt - 1 for a potential (m^2/s^2, <= 0) and speed (m/s)."""
    return potential / C**2 - speed**2 / (2 * C**2)


def circular_speed(gm, r):
    return math.sqrt(gm / r)


def orbit_rate(gm, r):
    """Clock in a circular orbit of radius r: -3 GM / (2 r c^2)."""
    return rate(-gm / r, circular_speed(gm, r))


def geoid_rate():
    """Clock on the rotating geoid, relative to TCG: -L_G (includes the centrifugal term)."""
    return -L_G


def ground_rate(height=0.0):
    """Clock at a height above the geoid, relative to TCG (uniform-gravity approximation)."""
    return geoid_rate() + G_EARTH * height / C**2


def moon_surface_rate():
    """Clock on the Moon's surface, relative to TCG (no solar tidal terms)."""
    v = circular_speed(GM_EARTH + GM_MOON, A_MOON)
    return rate(-GM_MOON / R_MOON - GM_EARTH / A_MOON, v)


def earth_surface_rate_helio():
    """Clock on Earth's geoid, relative to heliocentric coordinate time."""
    return orbit_rate(GM_SUN, AU) + geoid_rate()


def mars_surface_rate_helio():
    """Clock on Mars's surface, relative to heliocentric coordinate time (rotation neglected)."""
    return orbit_rate(GM_SUN, A_MARS) - GM_MARS / (R_MARS * C**2)


def gps_vs_geoid():
    """Net fractional rate of a GPS satellite clock relative to a geoid clock."""
    return orbit_rate(GM_EARTH, A_GPS) - geoid_rate()


# --- Geometry: bodies on circular coplanar orbits about a common centre --------


@dataclass(frozen=True)
class Circle:
    radius: float     # m
    omega: float      # rad/s, signed (negative = retrograde)
    phase: float = 0.0

    def pos(self, t):
        a = self.phase + self.omega * t
        return np.stack([self.radius * np.cos(a), self.radius * np.sin(a)], axis=-1)

    def vel(self, t):
        a = self.phase + self.omega * t
        s = self.radius * self.omega
        return np.stack([-s * np.sin(a), s * np.cos(a)], axis=-1)


def above_horizon(station, target, t):
    """Target is above the horizon of a station on the surface (elevation >= 0)."""
    p_s = station.pos(t)
    return np.einsum("ij,ij->i", target.pos(t) - p_s, p_s) >= 0.0


def clear_of_body(a, b, t, body_radius):
    """The straight line between a and b does not pass through a central body."""
    p, q = a.pos(t), b.pos(t)
    d = q - p
    s = np.clip(-np.einsum("ij,ij->i", p, d) / np.einsum("ij,ij->i", d, d), 0.0, 1.0)
    closest = p + s[:, None] * d
    return np.linalg.norm(closest, axis=1) >= body_radius


def range_stats(a, b, visible=None, samples=400_000):
    """Min and max distance and max |range rate| over one synodic period, visible samples only."""
    rel = abs(a.omega - b.omega)
    period = 2 * math.pi / rel if rel > 0 else 1.0
    t = np.linspace(0.0, period, samples, endpoint=False)
    d = b.pos(t) - a.pos(t)
    dist = np.linalg.norm(d, axis=1)
    rr = np.einsum("ij,ij->i", d, b.vel(t) - a.vel(t)) / dist
    mask = np.ones_like(dist, dtype=bool) if visible is None else visible(t)
    return float(dist[mask].min()), float(dist[mask].max()), float(np.abs(rr[mask]).max())


# --- Configurations -----------------------------------------------------------


@dataclass(frozen=True)
class Config:
    name: str
    short: str
    d_min: float      # m
    d_max: float      # m
    beta_max: float   # max |range rate| / c
    delta: float      # fractional rate offset between the two clocks


def configurations():
    n_leo = circular_speed(GM_EARTH, R_EARTH + 400e3) / (R_EARTH + 400e3)
    n_leo2 = circular_speed(GM_EARTH, R_EARTH + 550e3) / (R_EARTH + 550e3)
    n_gps = circular_speed(GM_EARTH, A_GPS) / A_GPS
    n_moon = circular_speed(GM_EARTH + GM_MOON, A_MOON) / A_MOON
    n_earth = circular_speed(GM_SUN, AU) / AU
    n_mars = circular_speed(GM_SUN, A_MARS) / A_MARS

    station = Circle(R_EARTH, OMEGA_EARTH)
    leo = Circle(R_EARTH + 400e3, n_leo)
    # Counter-rotating second orbit: the coplanar stand-in for crossing orbital planes.
    leo_retro = Circle(R_EARTH + 550e3, -n_leo2)
    gps = Circle(A_GPS, n_gps)
    moon = Circle(A_MOON, n_moon)
    earth = Circle(AU, n_earth)
    mars = Circle(A_MARS, n_mars)

    out = []
    out.append(Config("Two floors, same building (10 m)", "Floors", 10.0, 10.0, 0.0,
                      ground_rate(10.0) - ground_rate(0.0)))
    out.append(Config("Ground-ground (1000 km, 1 km height difference)", "Ground-ground", 1e6, 1e6, 0.0,
                      ground_rate(1000.0) - ground_rate(0.0)))

    d0, d1, rr = range_stats(station, leo, lambda t: above_horizon(station, leo, t))
    out.append(Config("Ground-LEO (400 km)", "Ground-LEO", d0, d1, rr / C,
                      orbit_rate(GM_EARTH, R_EARTH + 400e3) - geoid_rate()))

    d0, d1, rr = range_stats(leo, leo_retro, lambda t: clear_of_body(leo, leo_retro, t, R_EARTH))
    out.append(Config("LEO-LEO (400 km and 550 km, crossing)", "LEO-LEO", d0, d1, rr / C,
                      orbit_rate(GM_EARTH, R_EARTH + 550e3) - orbit_rate(GM_EARTH, R_EARTH + 400e3)))

    d0, d1, rr = range_stats(station, gps, lambda t: above_horizon(station, gps, t))
    out.append(Config("Ground-GPS", "Ground-GPS", d0, d1, rr / C, gps_vs_geoid()))

    d0, d1, rr = range_stats(station, moon, lambda t: above_horizon(station, moon, t))
    out.append(Config("Earth-Moon", "Earth-Moon", d0, d1, rr / C, moon_surface_rate() - geoid_rate()))

    d0, d1, rr = range_stats(earth, mars)
    out.append(Config("Earth-Mars", "Earth-Mars", d0, d1, rr / C,
                      mars_surface_rate_helio() - earth_surface_rate_helio()))
    return out


# --- Oscillator classes: accuracy incl. environment and one year of aging -----
# Vig 2004, slide 2-8 ("Hierarchy of Oscillators"); upper end of each range.

OSCILLATORS = {
    "XO": 1e-4,
    "TCXO": 1e-6,
    "OCXO": 1e-8,
    "Rb": 1e-9,
    "Cs": 1e-11,
}


def election_timeout(d_max):
    """An election timeout that meets Raft's timing requirement: about ten times the
    one-way latency (Ongaro 2014, p. 150), and no less than 150 ms (p. 152)."""
    return max(0.150, 10 * d_max / C)


def lease_terms(cfg):
    """Terms of the lease condition for one configuration.

    Causal reading: slack = round trip - |delta| * T_e; unsafe only beyond T_e*.
    Every-frame reading: the lease must shrink by the Doppler factor k_max, about
    1 + beta_max + |delta|; reported as a share of the classical drift budget 2 rho.
    """
    t_e = election_timeout(cfg.d_max)
    rtt = 2 * cfg.d_min / C
    k_minus_1 = cfg.beta_max + abs(cfg.delta)
    return {
        "name": cfg.name,
        "short": cfg.short,
        "d_min_m": cfg.d_min,
        "d_max_m": cfg.d_max,
        "rtt_min_s": rtt,
        "beta_max": cfg.beta_max,
        "delta": cfg.delta,
        "delta_us_per_day": per_day(cfg.delta),
        "t_e_s": t_e,
        "delta_t_e_s": abs(cfg.delta) * t_e,
        "beta_t_e_s": cfg.beta_max * t_e,
        "causal_crossover_t_e_s": rtt / abs(cfg.delta) if cfg.delta else math.inf,
        "causal_safe": abs(cfg.delta) * t_e < rtt,
        "k_max_minus_1": k_minus_1,
        "doppler_share": {name: k_minus_1 / (2 * rho) for name, rho in OSCILLATORS.items()},
        # With perfect clocks and the classical rule, the window by which the lease
        # outlives the every-frame bound (0 when the drift budget covers Doppler).
        "exposure_s": {name: max(0.0, k_minus_1 - 2 * rho) * t_e for name, rho in OSCILLATORS.items()},
    }

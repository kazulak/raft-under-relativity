// When could relativity break a Raft lease? Orders of magnitude.
// Build from the repository root:  typst compile --root . analysis/magnitudes.typ
// Every number comes from results.json, produced by  python analysis/run.py

#set document(title: "When Could Relativity Break a Raft Lease?", author: "Tomasz Kazulak")
#set page(paper: "a4", margin: (x: 2.4cm, y: 2.6cm), numbering: "1")
#set text(font: "New Computer Modern", size: 10.5pt, lang: "en")
#set par(justify: true, leading: 0.62em, first-line-indent: 1.2em, spacing: 0.62em)
#set heading(numbering: "1.1")
#show heading: set block(above: 1.3em, below: 0.7em)
#show heading.where(level: 1): set text(size: 12pt)
#show figure.caption: set text(size: 9pt)
#show figure.where(kind: table): set figure.caption(position: top)
#set table(stroke: (x, y) => (top: if y <= 1 { 0.6pt } else { 0pt }, bottom: 0.6pt), inset: (x: 5pt, y: 4pt))
#show table: set text(size: 9pt)
#show table: set par(justify: false)

#let r = json("results.json")
#let val = r.validation
#let cj = r.conjecture
#let cfgs = r.configurations

// Number formatting. fix: d decimals, trailing zeros kept. sci: scientific notation.
// num: fixed notation between 0.01 and 10^4, scientific otherwise.
#let fixs(x, d) = {
  let s = str(calc.round(x, digits: d))
  if d == 0 { return s }
  let parts = s.split(".")
  let frac = if parts.len() > 1 { parts.at(1) } else { "" }
  parts.at(0) + "." + frac + "0" * (d - frac.len())
}
#let fix(x, d: 2) = [#fixs(x, d)]
#let sci(x, d: 2) = {
  if x == none { return [∞] }
  if x == 0 { return [0] }
  let e = calc.floor(calc.log(calc.abs(x)))
  let m = calc.round(x / calc.pow(10.0, e), digits: d)
  if calc.abs(m) >= 10 { m = m / 10; e += 1 }
  if e == 0 { [#fixs(m, d)] } else { $#fixs(m, d) times 10^(#e)$ }
}
#let num(x, d: 2) = {
  if x == none or x == 0 { return sci(x) }
  let a = calc.abs(x)
  if a >= 0.01 and a < 1e4 {
    let digits = calc.max(0, d - calc.floor(calc.log(a)))
    fix(x, d: digits)
  } else { sci(x, d: d) }
}
#let year = 365.25 * 86400

#align(center)[
  #text(size: 16pt, weight: "bold")[When Could Relativity Break a Raft Lease?\ Orders of Magnitude]
  #v(0.6em)
  #text(size: 11pt)[Tomasz Kazulak] \
  #text(size: 9.5pt)[Independent study · technical note to the survey "Raft under Physical Communication Models"]
]

#v(0.8em)
#block(inset: (x: 1.8em))[
  #set par(first-line-indent: 0em)
  #text(weight: "bold")[Abstract.]
  The survey found one Raft mechanism whose safety rests on clocks, the leader
  lease, and no frame-invariant statement of its safety condition. Before
  proving such a statement, this note asks which physical effects could matter
  and how large they are. Which condition counts as "safe" depends on the
  correctness notion. If a stale read only has to be causally undetectable, the
  lease gains a full round trip of slack. Gravitational and motional rate
  offsets of order $10^(-10)$ could then exhaust that slack only after election
  timeouts of months to millennia; every realistic configuration is safe by
  several orders of magnitude. If the read must be correct in every reference
  frame, the notion Raft itself satisfies, the slack disappears and the lease
  must shrink by the Doppler factor between leader and follower. That effect
  is first order in $beta = v\/c$, between $10^(-6)$ and $10^(-4)$ for
  satellite and planetary links. On those links it exceeds the drift budget of
  every oscillator from an oven-controlled crystal upward, and on low-orbit and
  Mars links even that of a temperature-compensated crystal. A numerical model
  in flat 1+1D spacetime supports both statements; proofs are left to the next
  step.
]

= Question and setup

Ongaro's lease rule reads: once a majority acknowledges a round of heartbeats,
the leader extends its lease to "start + election timeout / clock drift bound",
where _start_ is when it sent the round, because followers ignore vote requests
for an election timeout after hearing from the leader @ongaro2014[p. 92]. The
rule assumes that no server's clock advances more than the drift bound times
any other's over a given period. Comparing distant clocks over "the same"
period presupposes a simultaneity convention, which is the gap the survey
identified.

The lease round can be stated with events instead (@fig:round). The leader sends
the heartbeat round at $S$ and starts its lease there. A follower receives it at
$R$ and refuses to vote for $T_e$ of its own clock, until $V$. Light from $V$
reaches the leader at $A$. The lease expires at $E$, $T_L$ of leader time after
$S$. Write $D$ for the last leader event whose light reaches $V$.

#figure(
  placement: bottom,
  box(width: 200pt, height: 215pt, {
    let lx = 60pt
    let fx = 130pt
    let ys = 205pt
    let yr = 135pt
    let yv = 80pt
    let ya = 10pt
    let yd = 150pt
    let ye = 110pt
    place(line(start: (lx, 215pt), end: (lx, 0pt), stroke: 1.2pt))
    place(line(start: (fx, 215pt), end: (fx, 0pt), stroke: 1.2pt))
    place(dx: lx - 40pt, dy: 205pt, text(size: 8pt)[leader])
    place(dx: fx + 6pt, dy: 205pt, text(size: 8pt)[follower])
    let light = (paint: gray, thickness: 0.8pt, dash: "dashed")
    place(line(start: (lx, ys), end: (fx, yr), stroke: light))
    place(line(start: (fx, yv), end: (lx, ya), stroke: light))
    place(line(start: (lx, yd), end: (fx, yv), stroke: light))
    place(line(start: (fx, yr), end: (fx, yv), stroke: 2.5pt + blue.lighten(40%)))
    let dot(x, y, name, side) = {
      place(dx: x - 2.2pt, dy: y - 2.2pt, circle(radius: 2.2pt, fill: black))
      place(dx: if side == "l" { x - 14pt } else { x + 5pt }, dy: y - 5pt, text(size: 9pt, name))
    }
    dot(lx, ys, $S$, "l")
    dot(fx, yr, $R$, "r")
    dot(fx, yv, $V$, "r")
    dot(lx, ya, $A$, "l")
    dot(lx, yd, $D$, "l")
    dot(lx, ye, $E$, "l")
    place(dx: fx + 5pt, dy: 103pt, text(size: 9pt, fill: blue.darken(20%))[$T_e$])
    place(dx: 0pt, dy: 0pt, text(size: 8pt, fill: gray.darken(30%))[time ↑])
  }),
  caption: [One lease round for two nodes at rest, light signals dashed. The
    follower's no-vote window (blue) runs from $R$ to $V$. Under the causal
    reading the lease may last until just before $A$; under the every-frame
    reading only until $D$. The expiry $E$ as drawn is safe under the first
    reading and not under the second.],
) <fig:round>

A new leader needs a vote from some follower that acknowledged the round, so its
first write completes at an event in the causal future of that follower's $V$.
Assume the worst case, where a new majority and its client sit next to the
follower, so the write can complete arbitrarily soon after $V$. A read served
by the old leader at $E$ is stale with respect to that write. Whether this
violates correctness depends on which relativistic linearizability is required
@gilbert2014:

- *Causal reading.* A stale read violates correctness only if the write's
  completion is in the causal past of the read. The pairwise condition is that
  $E$ is not in the causal future of $V$, so $E$ must come before $A$. This is
  the condition behind R1-linearizability (linearizable in some frame).
- *Every-frame reading.* R2- and R3-linearizability require linearizability in
  every total order that extends causality. For two spacelike-separated events,
  some such order puts either one first, so the read must causally precede the
  write. The pairwise condition is that $E$ is in the causal past of $V$: $E$
  must come no later than $D$. Raft without leases is R3-linearizable
  @aeini2026, so this is the reading under which leases keep Raft's guarantee.

Both are necessary pairwise conditions, not proofs of R1 or R3 for whole
histories.

= Clock rates

To first order in the weak field, a clock moving at speed $v$ at Newtonian
potential $Phi$ ticks at $d tau \/ d t = 1 + Phi\/c^2 - v^2\/(2 c^2)$ relative to
the coordinate time of the chosen frame @ashby2003. In a circular orbit of
radius $r$ this gives $-3 G M\/(2 r c^2)$; a clock on the rotating geoid runs at
$-L_G$ relative to geocentric coordinate time, with the defining constant $L_G$
and all mass parameters from the IERS Conventions @petit2010. Planetary
dimensions come from NASA's fact sheets @williams2024 @williams2025. The model
neglects higher multipoles, orbital eccentricity, Shapiro delay and tidal
terms. @tab:validation checks it against published values.

#figure(
  table(columns: (1fr, auto, auto),
    table.header[Clock pair][This model][Published],
    [GPS orbit vs. geoid, fractional], [#sci(val.gps_vs_geoid, d: 4)], [#sci(val.gps_published, d: 4) @ashby2003],
    [Moon surface vs. Earth, µs/day], [#fix(val.moon_us_per_day)], [#fix(val.moon_published_us_per_day) @ashby2024],
    [Mars surface vs. Earth, µs/day, mean], [#fix(val.mars_us_per_day, d: 0)], [#val.mars_published_us_per_day ± #val.mars_published_variation_us_per_day @ashby2025],
  ),
  caption: [Validation of the rate model. The Mars difference comes from the
    circular-orbit approximation; the published value varies by
    ±#val.mars_published_variation_us_per_day µs/day over a Mars year.],
) <tab:validation>

= Lease terms in realistic configurations

@tab:configs lists seven configurations. Distances and the largest range rate
$beta_"max" c$ come from circular coplanar orbits sampled over one synodic
period, counting only times when the two nodes can see each other. The
crossing LEO pair is modelled as two counter-rotating orbits; ground–GPS
geometry is equatorial and understates the range rate of the real inclined
orbits. The election timeout $T_e$ is the smallest that satisfies Raft's timing
requirement: about ten times the worst one-way latency and at least 150 ms
@ongaro2014[pp. 150, 152].

#figure(
  table(columns: (1fr, auto, auto, auto, auto, auto, auto),
    table.header[Configuration][$d_"min"$ (m)][$d_"max"$ (m)][$beta_"max"$][$delta$][$T_e$ (s)][$T_e^*$ (years)],
    ..cfgs.map(c => (
      c.short,
      num(c.d_min_m), num(c.d_max_m), num(c.beta_max), num(c.delta),
      num(c.t_e_s), num(c.causal_crossover_t_e_s / year),
    )).flatten()
  ),
  caption: [Configurations: two servers on floors 10 m apart; two ground
    stations 1000 km apart at heights differing by 1 km; a ground station and a
    satellite at 400 km; satellites at 400 km and 550 km on crossing orbits; a
    ground station and a GPS satellite; Earth and Moon surfaces; Earth and Mars
    surfaces. $delta$ is the fractional rate offset between the two clocks;
    $T_e^*$ is the election timeout at which the rate term would use up the
    round-trip slack of the causal reading.],
) <tab:configs>

*Causal reading.* To first order the leader's proper time from $S$ to $A$ is
$T_e (1 - delta) + "RTT"$, where $delta$ is the follower's rate relative to the
leader's. The lease can be unsafe only if $|delta| T_e > "RTT"$, that is for
$T_e > T_e^* = "RTT"\/|delta|$. Across the table $T_e^*$ is at least
#num(calc.min(..cfgs.map(c => c.causal_crossover_t_e_s)) / year) years, against
election timeouts of at most #num(calc.max(..cfgs.map(c => c.t_e_s))) s. Under
this reading relativity never threatens a lease that respects Raft's own timing
requirement, and Ongaro's rule needs no change.

*Every-frame reading.* Here the slack is gone: the follower receives the leader's
signals stretched by the Doppler factor $k$, so the latest safe expiry $D$ comes
$T_e \/ k$ of leader time after $S$. For an inertial pair $k = sqrt((1+beta)\/(1-beta))$
@dinverno1992, and in general $k_"max" - 1 approx beta_"max" + |delta|$ to first
order. Ongaro's rule spends a drift budget of about $2 rho T_e$, where $rho$ is
the clock's rate tolerance. @tab:share compares the two using oscillator
accuracies from Vig's tutorial @vig2004[slide 2-8], including environment and
one year of aging. A share above 1 means the lease is unsafe under this reading
even with perfect clocks.

#let classes = r.oscillators.keys()
#figure(
  table(columns: (1fr,) + classes.map(_ => auto) + (auto,),
    table.header([Configuration], ..classes.map(k => [#k]), [TCXO window (s)],
      [$rho$], ..classes.map(k => sci(r.oscillators.at(k), d: 0)), []),
    ..cfgs.map(c => (
      (c.short,) + classes.map(k => num(c.doppler_share.at(k))) + (num(c.exposure_s.at("TCXO")),)
    )).flatten()
  ),
  caption: [Share of the classical drift budget consumed by the Doppler factor,
    $(k_"max" - 1)\/(2 rho)$. The last column is how long a TCXO-timed lease
    outlives the every-frame bound with perfect clocks, $(k_"max" - 1 - 2 rho) T_e$.],
) <tab:share>

Doppler consumes up to a quarter of a commodity quartz budget on the fastest links,
exceeds the whole budget of a temperature-compensated oscillator for LEO and
Mars links, and dominates every better clock by orders of magnitude. The
exposure windows are short, microseconds for Earth-orbit links, but reach
#num(cfgs.last().exposure_s.at("TCXO")) s for an Earth–Mars lease. A cluster with its
leader on Earth and a majority on Mars could elect a new leader within such a
window.

= Numerical test of the survey's conjecture

The survey conjectured that an inertial leader cannot lose lease time, because
by the reverse triangle inequality its proper time from $S$ to $A$ is at least
$T_e$, so that first-order Doppler effects cancel. A small model of flat 1+1D
spacetime with $c = 1$ (`analysis/spacetime.py`) tests this. It represents
worldlines as inertial, piecewise inertial or uniformly accelerated, and finds
light-signal events by root finding.

- In #cj.random_trials random lease rounds with an inertial leader and a
  piecewise-inertial follower at speeds up to $0.9 c$, the smallest ratio of the
  causal-reading lease bound to $T_e$ was #fix(cj.causal_inertial_worst_ratio, d: 3).
  It was never below 1.
- A leader that flies out at $#cj.twin_leader_speed c$ and returns to a resting
  follower accumulates #fix(cj.twin_max_lease_causal, d: 1) units of proper time
  while the follower's $T_e = #fix(cj.twin_t_e, d: 1)$ elapses: the twin paradox,
  and a counterexample for non-inertial leaders.
- For a receding inertial pair the every-frame bound equals $T_e\/k$:
  #cj.receding.map(x => [#x.name, $beta = #num(x.beta)$: #fix(x.max_lease_every_frame, d: 7) $T_e$]).join("; ").

The conjecture therefore holds, so far numerically, for the causal reading only.
Under the every-frame reading first-order Doppler does not cancel. That
corrects the survey's remark that "first-order Doppler effects cancel": they
cancel only when correctness is required in some frame, not in every frame.

= What Step 2 must prove

Measuring each clock's drift against its own proper time makes the drift bound
frame-invariant. With that, two statements survive the tests above:

+ *Causal reading.* In 1+1D Minkowski spacetime, with an inertial leader and a
  piecewise-inertial follower whose clocks stay within $rho$ of proper time,
  the lease $T_L <= T_e (1-rho)\/(1+rho)$ ends before $A$.
+ *Every-frame reading.* With a Doppler bound $k_"max"$ between leader and
  follower, the lease $T_L <= T_e (1-rho)\/((1+rho) k_"max")$ ends no later than $D$.

The first is the reverse triangle inequality applied to the chain $S -> R -> V -> A$.
The second needs only the Doppler factor, which the follower could measure by
comparing heartbeat spacing with its own clock.

= Limitations

The rates are weak-field and first order, and the orbits are circular and
coplanar. The lease conditions are pairwise and assume the fastest possible new
leader. The spacetime model is flat and one-dimensional, so gravity enters only
through the rate offsets of @tab:configs. The numerical tests are evidence, not
proofs.

#bibliography(("../paper/refs.bib", "pending.bib"), style: "ieee", title: "References")

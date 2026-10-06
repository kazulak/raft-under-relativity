# Raft under Relativity

**Raft under Physical Communication Models: What Relativity Changes, and What It Does Not.**
A structured literature survey by Tomasz Kazulak. [Read the paper (PDF)](paper/main.pdf).

## Origin

This project began as a question I asked myself during a lecture on distributed
consensus: would Raft still work if its nodes were far apart and moving relative
to each other, so that signals take real time to arrive, clocks tick at
different rates, and the nodes cannot agree on what happens "at the same time"?
I wanted to know whether anyone had answered it, and where the answer would
actually matter. This survey is how I found out.

## Findings

The survey covers 41 studies, all checked against their full texts.

1. **Raft's safety needs no clocks.** It depends on no timing assumption, and it
   has recently been proved to survive relativistic causality.
2. **Delay, loss and partitions affect only liveness.** The large literature on
   Raft under faulty networks concerns liveness and performance. Relativity adds
   a lower bound on delay and makes delay change over time, and nothing more.
3. **The leader lease is the one open point.** It is the only Raft mechanism whose
   safety depends on clocks, and it has only ever been analysed against a common
   reference time. No study states its safety condition frame-invariantly or
   examines clock-based coordination in relativistic spacetime.

## Open questions

The paper ends with three questions that follow from finding 3:

1. What is the frame-invariant condition under which a Raft leader lease is safe?
2. In which realistic configurations (satellites, ground–orbit links,
   interplanetary distances) does that condition differ measurably from the
   classical bounded-drift rule?
3. Does a lease-based read satisfy the strongest relativistic linearizability
   condition that Raft satisfies without leases?

## Repository contents

| Path | Contents |
|---|---|
| `paper/main.typ`, `paper/main.pdf` | The paper. Build with `typst compile paper/main.typ`. |
| `paper/refs.bib` | Bibliography, auto-exported from Zotero by Better BibTeX. Don't edit it by hand. |
| `review/studies.csv` | One row per screened record: screening and eligibility decisions with reasons. |
| `review/cards.md` | Data-extraction cards for the included studies. |
| `review/blind-check.csv` | Blind re-screening sample used to check the screening decisions. |
| `review/litmaps-forward.bib` | Forward-citation export used for snowballing. |

Full texts were kept locally and are not redistributed. The paper's method,
AI-use and threats-to-validity sections describe how the survey was done and
where its limits are.

## History

An earlier version of this repository was a Raft simulator in Julia. An internal
audit found defects that voided its results, and I restarted the project from
the literature: first establish what is known, then decide what is worth
building. The simulator code remains in the git history, before commit
`396b3c8`.

## License

MIT, see [LICENSE](LICENSE).

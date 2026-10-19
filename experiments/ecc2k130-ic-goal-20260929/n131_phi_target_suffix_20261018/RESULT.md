# Public-target backward partial sums and a joint end cut

The archived Q1358 formula supports an exact target-conditioned end cut. For
each verified public-point fiber endpoint, subtracting three signed suffix
points fixes the 131-bit `partial10..12` coordinates. Pinning those vectors,
the endpoint selector, and a previously audited three-leaf forward prefix
grounds five nonlinear chain links while leaving nine middle leaves free. An
inconsistent final partial-sum bit reported UNSAT in 0.252 s. Eight ordinary
joint branches remained unresolved under the frozen 25 s per-arm cap, so this
cut did not deliver a fast terminal relation on the tested branch panel.

## Exact construction

The curve is `EC1N131Ckb1heb5f1998f20b`, and the one-public-point workload is
`3c1992b7c92f`. The original Q1358 d10/m15 XCNF SHA-256 is
`0a2f4b3e3acc8e26049921567b3c3b04b2a1eace4e86ccb8a193bd4cca29fd41`.
The frozen leaf codes `[637,989,110]` occupy positions 0–2 and 12–14. The
prefix uses sign choice `000` and its two independently audited partial-sum
coordinates. For suffix sign choice `000`, each of the four verified cofactor
fiber endpoints `E` is considered in both group orientations. The exact
backward recurrence is `partial12 = E - P14`,
`partial11 = E - P14 - P13`, and
`partial10 = E - P14 - P13 - P12`; the same recurrence is evaluated from
`-E` for the second orientation. These are necessary values for a chain
solution with the selected signed suffix. The group equivalence is
[proved in Lean](PROOF_MAP.md) for every additive commutative group. The
[freeze audit](freeze_sage.py)
verified all eight endpoint coordinates and phi masks, rebuilt the original
formula byte for byte, and checked the primary variables for leaves 12–14,
partials 10–12, and the endpoint selector.

Each joint query appends 717 unit clauses: 60 leaf code bits, 262 forward
partial bits, 393 backward partial bits, and two endpoint-selector bits. The
suffix code-only control appends 30 units. The deliberately inconsistent
control flips bit zero of `partial12` for endpoint 0, orientation 0. One
CryptoMiniSat worker ran at a time with [frozen settings](protocol.json):
25 s parent wall per arm, 300 s campaign parent cap, and 4 GiB combined RSS
cap. The checked Sage runtime is saved in
[sage_runtime_info.json](sage_runtime_info.json).

## Measured observations

| Arm | Exact observation | Parent wall | Sampled combined RSS |
| --- | --- | ---: | ---: |
| Suffix code-only | `BOUNDED_UNKNOWN_ARM_WALL_CAP` | 25.084 s | 1,318,617,088 B |
| Wrong `partial12` bit | `UNSAT_REPORTED_NEEDS_PROOF_AUDIT` | 0.252 s | 143,179,776 B |
| Endpoints 0/1, both orientations; endpoint 2 orientation 0 | `BOUNDED_UNKNOWN_ARM_WALL_CAP` | 25.057–25.143 s each | up to 1,265,451,008 B |
| Endpoint 2 orientation 1; endpoint 3, both orientations | `BOUNDED_UNKNOWN_SOLVER_TIME_LIMIT_NO_TERMINAL` | 21.395–24.668 s | up to 1,289,977,856 B |

All three solver-time-limit exits had code 15 and a `Total time (this thread)`
line but no terminal `s` state. The sum of parent arm intervals was 220.777 s.
The [receipt replay](verify.py) independently reconstructed all ten query
hashes from the archived XCNF and exact unit lists, checked the source and
raw log hashes, and returned `REPLAY_PASS`. Failed and capped arms remain
distinct. The backward cut is exact for each chosen endpoint orientation and
signed suffix; this eight-arm sample does not exhaust the sign choices for
the last three leaves.

## Next experiment

The formula leaves nine middle leaves unconstrained even after both ends are
grounded. The next cheap gate is an exact middle-sum membership test: compute
the group difference between the fixed forward partial point and each
backward partial point, and test whether the nine remaining position-specific
factor-base domains can represent it using a staged meet in the middle with
Frobenius quotienting. Freeze a smaller field instance first to establish
completeness and count retained partial sums, then estimate the full N131
index size and memory before building it. This moves target dependence into
an explicit group constraint rather than asking the full SAT solver to
propagate through nine unconstrained leaves.

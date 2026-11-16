# Bounded-product two-fold reduction: frozen component panel

Publish this source and protocol before generating fixture indices30..35.
The baseline is the current default field pipeline. A second arm enables only
f2m-karatsuba3; the third enables f2m-karatsuba3,f2m-fixed-reduction. Compare
all three on the same public inputs. This isolates the reduction addition
within each pair while retaining a current default reference.

Cases are field degrees113,131,155,163,233 using the existing polynomial
constructors. The three-limb cases are the primary component cases;113/233
retain the generic reducer as controls. Six fresh fixtures balance all six
backend orders. Each arm uses1m dependent multiplies with construction,
independent initial schoolbook check and checksum encoding outside the timer.
Runtime dispatch, reduction, scratch clearing and result handling are timed.
No full IC or relation-throughput claim follows from this component interval.

Use the same isolated crate/main.rs and locked dependencies as the preceding
field panels, separate release target directories per variant and all field
tests before timing. Record source hashes, rustc, binaries, every arm and
checksum. Pin one allowed CPU on one L4 allocation with4 requested CPUs,8GiB
and900-second cap. The workload runs on the CPU. Run before/after baseline
131-bit fixture0 calibrations per triple and retain failures outside0.85..1.15.
The driver freezes seed generation and returns raw ratios for default/combined
and six-product-only/combined. Keep all control shifts and regressions.

Host placement remains unqualified on the known gVisor allocation. Qualified
values stay null and the benchmark record stays invalid for promotion. The
source must remain opt-in pending controlled full-pipeline measurement.

## Mechanism and scope

For a masked m-bit element product P of degree at most2m-2, m=128+B, split
P=L+X^m H. With modulus X^m+r, first form F=L+H*r. A one-word r and m>128
make the remaining overflow times r have degree below126<m, so a second fold
ends reduction. Only canonical131/155/163 polynomial tails are dispatched.
For m131 the top H word has at most two bits and uses two masked XOR terms.
General reduction remains the fallback, including mismatched element/field
sizes. Tests cover every input monomial through degree2m-2 plus4096 random
bounded inputs per selected field, comparing every output word to bitwise
reduction. Existing mul/square/inverse tests remain required.

This is an adaptation of known two-fold reduction, not a novelty claim.
KB receipt: revision9141e386254340a9bdba3036f2bb706a; source:4aeae310bd8926130ee38d08ce3d9da5,
crypto:docs/perf/RESULTS.md at d390e84ab2973372534120fc4207fb65e52d4f3f,
section gf2-fold-reduce, read from the original Git object. That implementation
and its historical measurements concern smaller Gf2 fields; their ratios are
not measurements of this three-limb implementation. Four mechanism/negative/
application/adjacent queries were consulted; ranking is not evidence.

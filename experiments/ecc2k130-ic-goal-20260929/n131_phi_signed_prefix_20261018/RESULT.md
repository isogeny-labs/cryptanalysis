# Exact signed three-leaf partial-sum pins on the N131 public point

The archived Q1358 formula admits an exact signed-prefix intervention: fixing
the first three leaf codes and the first two 131-bit partial-sum phi coordinates
pins 292 formula inputs while preserving every decomposition with those signed
points. The inconsistent partial-sum control reported UNSAT in 0.219 s.
Eight genuine sign arms, representing four distinct partial-sum pairs, remained
unresolved within the frozen 25 s per-arm cap. This result identifies the
specific forward-chain pinning gate as insufficient for cheap ordinary-prefix
rejection under the tested solver settings.

## Frozen method

The curve is `EC1N131Ckb1heb5f1998f20b`, with the one-public-point workload
`3c1992b7c92f`. The original Q1358 d10/m15 XCNF has SHA-256
`0a2f4b3e3acc8e26049921567b3c3b04b2a1eace4e86ccb8a193bd4cca29fd41`.
The first prefix `[637,989,110]` comes from the prior frozen 16-prefix panel.
Each leaf code uses ten input bits, and each `partial0`/`partial1` value uses
131 input bits. The [freeze audit](freeze_sage.py) rebuilt the archived formula
byte for byte, checked the exact input maps `leaf0..2 = 2..31`,
`partial0 = 152..282`, `partial1 = 283..413`, and independently reproduced the
planted control's first two partial-sum masks by curve addition. It then
enumerated all eight sign choices before solver execution. The all-sign
reversal pairs `(000,111)`, `(001,110)`, `(010,101)`, `(011,100)` yield four
distinct coordinate pairs.

The control changes bit zero of `partial0` for sign `000` while retaining its
three leaf codes and exact `partial1`. Each ordinary arm appends 292 unit
clauses to the original public-point formula; the endpoint selector and the
remaining twelve leaves stay free. One CryptoMiniSat worker ran at a time with
the [frozen flags and limits](protocol.json): 25 s parent wall per arm, 300 s
campaign parent cap, and 4 GiB combined RSS cap. The checked Sage runtime is
in [sage_runtime_info.json](sage_runtime_info.json). The source, solver,
formula, and workload hashes are pinned in the protocol.

## Observations

| Arm | Exact observation | Parent wall | Sampled combined RSS |
| --- | --- | ---: | ---: |
| Wrong `partial0` bit | `UNSAT_REPORTED_NEEDS_PROOF_AUDIT` | 0.219 s | 149,536,768 B |
| Signs `000,001,100,101,110,111` | `BOUNDED_UNKNOWN_ARM_WALL_CAP` | 25.043–25.155 s each | up to 1,321,107,456 B |
| Signs `010,011` | `PRODUCER_FAILURE_NO_TERMINAL_STATE` | 23.224, 21.032 s | up to 1,341,276,160 B |

The latter two exits had code 15 and a solver `Total time (this thread)` line
near its 20 s `--maxtime` setting, but no `s` status line. Their exact raw
state is retained in their receipts and logs; it is not a contradiction.
The sum of parent arm intervals was 194.994 s. The prior code-only arm on the
same public point and `[637,989,110]` reported
`BOUNDED_UNKNOWN_ARM_WALL_CAP` at 25.045 s. Extra forward partial-sum pins
did not produce a terminal answer within that matched cap. These ordinary-host
stage observations do not form a verified single-target IC/rho comparison.

[verify.py](verify.py) recomputes every augmented-query hash from the original
XCNF and unit literals, checks source and log hashes, validates exact arm
inputs and statuses, and returned `REPLAY_PASS` for all nine arms. The run
retains each capped arm and the solver time-limit exits as distinct outcomes.

## Next cut

Ground the final three links from the public target backward: choose valid
codes for leaves 12–14, enumerate sign choices and the four verified target
fiber endpoints, compute `partial10..12` by exact subtraction on the curve,
and pin those three phi vectors together with the endpoint selector. A small
frozen branch panel can test whether a target-conditioned suffix makes the
nonlinear constraints propagate farther than this forward-only gate. Compare
against a code-only suffix arm at identical solver settings, and replay any
terminal model by group arithmetic.

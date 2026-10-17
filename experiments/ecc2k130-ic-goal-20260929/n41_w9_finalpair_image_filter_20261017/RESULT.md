# A direct target-conditioned final-pair image test on N41

## Contribution

The N41 five-pair final link admits an exact **last-code recovery test**
once the reciprocal x-coordinate `w` of the first four-pair sum is known.
Its resultant is `a(w)p²+b(w)p+q(w)=0`, where `p` is a binary-linear
function of the final pair's eight source-code bits. The field equation
has at most two product roots in the nondegenerate chart. Testing those
roots against the 71 allowed source codes recovers the final code without
enumerating it inside the filter. The archived ordinary relation returns
code **95**, and independent checked Sage replays its five signed pair
states against the public point.

The panel distinguishes two sources of rejection. On **1,024 distinct
field-sampled `w` values**, 520 had two field product roots and 504 had
none. On **256 distinct, admissible four-pair sums**, all 256 had two
field roots. None of the 1,280 sampled nonpositive inputs had a product
in the eight-dimensional code image. The field-root test therefore
rejected none of the sampled reachable partial sums; source-image
membership supplied all observed rejection. A checked algebraic theorem
and a separate Sage group bridge explain why an unrestricted product
exists for every nonexceptional target residual, before the sparse
factor-base policy is imposed.

## Exact instance and recovery method

The curve is `EC1N41Ckb1h7d5e80d3c4d0`,
`y²+xy=x³+1` over `GF(2)[u]/(u^41+u³+1)`, with subgroup order
`549756390943` and cofactor four. The public point is
`(1936680952394,910597499030)`. Five aligned W9 pair slots have
Frobenius rotations `(0,0,12,12,24)`; the final slot has 71 permitted
canonical product codes and four signed source states per code. The
[predecessor circuit](../n41_w9_code_linear_tower_20261017/RESULT.md)
already proves and audits its split-root resultant. This experiment
uses the same frozen source and public point.

With public reciprocal `t`, final pair constants `C,H`, and
`A=1+(tw)²`, `B=tw`, `D=t²+w²`, `M=AH+CD`, put
`a=AD`, `b=BM`, `q=M²+CHB²`. For `a,b≠0`, substitute
`p=(b/a)h` into `ap²+bp=q`; the resulting equation is
`h²+h=qa/b²`. Its trace test and halftrace produce the two field
roots. Linear and square-root charts cover `a=0` and `b=0`. The
computed product is mapped back through the exact eight-bit source
basis, then filtered to the 71 allowed codes. The [proof map](PROOF_MAP.md)
states the algebraic theorem, exceptional conditions, checked Lean
declarations, and the remaining curve-law formalization bridge.

The [frozen protocol](protocol.json) binds the producer, exact source
files, SHA-256 sample laws, one worker, a 120-second wall cap, and a
4-GiB RSS cap. It requested 1,024 distinct SHA-256-derived field values
and 256 distinct reachable `w` values from four independently selected
signed pair states with eight distinct folded columns. The archived
relation is a positive correctness control, not an input to the
sampled queries.

| Panel | Inputs | Two field roots | Rank-8 map | Code-image hits | Allowed-code hits |
| --- | ---: | ---: | ---: | ---: | ---: |
| Field-sampled `w` | 1,024 | 520 | 1,024 | 0 | 0 |
| Reachable four-pair `w` | 256 | 256 | 256 | 0 | 0 |
| Archived ordinary relation | 1 | 1 | 1 | 1, code 95 | 1, code 95 |

The [producer receipt](result.json) records all 1,280 sampled values,
their source state IDs where applicable, exact root/code decisions,
charts, ranks, phase costs, and the positive control. The producer took
**14.624884 seconds** of wall time, with **25,001,984 bytes** self peak
RSS. Its exclusive phase costs were source preparation 0.006652 s,
positive group control 0.006837 s, field-sample decode 8.436397 s,
reachable generation and decode 6.118852 s, and special-chart checks
and summary 0.056145 s. These ordinary-host times are correctness and
cost diagnostics; they do not provide a solved-target online interval.

The independent [checked-Sage replay](audit_sage_result.json) recomputed
the field coefficients, brute-forced all 256 code products for each of
**1,285** rows, independently ranked each binary map, and rebuilt all
256 reachable four-pair point sums. It also verified the positive
five-pair group relation. Its arithmetic interval was **8.310743 s**
with 200,916,992 bytes self peak RSS. A second [group bridge](group_bridge_result.json)
recomputed `Q−P` and `Q+P` for every reachable partial sum: all 256
had two nonexceptional target residual products satisfying the field
equation. Its arithmetic interval was **3.981221 s**. Both audits ran
through the repository's checked Sage launcher after the saved
[runtime receipt](sage_runtime_info.json). The [terminal verifier](verify.py)
checks all frozen hashes, rows, phase sums, audits, Lean axiom output,
and resource limits; its [output](verification.stdout) passes.

## Consequence and next experiment

For a reachable point `P` with a nonzero residual coordinate, the
target link has a field root `e=1/x(Q−P)`. Taking
`p=(C e²+H)/e` makes the unrestricted source quadratic vanish. The
Lean result proves this algebraic implication; the checked Sage bridge
verifies its curve-point premise on the measured panel. Thus the
Artin–Schreier trace alone cannot reject those nonexceptional partial
sums. The sparse source-code image remains the useful condition.

This implementation applies the condition **after** a four-pair sum has
been supplied, so the measured rejection does not establish early
family pruning or an N131 search path. The next exact gate is a
target-conditioned table of `(w, final_code)` pairs obtained by
translating every signed final-pair state by the public target. Encode
that finite relation before enumerating four-pair sums, keep all source
codes and folded-column checks, and compare its full N41 circuit and
unpinned search with the native join under one shared budget. Only a
verified ordinary relation and source-bound N131 cost projection can
promote that encoding to the frozen N131 public-point run.

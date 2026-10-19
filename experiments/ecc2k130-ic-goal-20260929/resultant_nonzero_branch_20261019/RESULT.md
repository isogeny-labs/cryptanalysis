# Nonzero-branch cubic solve and exact W33 root recovery

Fixing the low first-code bit to one makes the cubic equation `pF(p,q)=0`
equivalent to the original two-pair resultant on the tested N131 block, while
leaving all 32 second-code bits free. The one-worker solver recovered the
constructed N131 source codes **`(3,16722)` in 178.791 seconds** with
1,178,959,872 bytes of sampled peak combined RSS. Its paired frozen public
raw-point branch returned a unit ideal in 156.748 seconds with 1,010,843,648
bytes of sampled peak combined RSS. Both completed within the frozen
600-second and 4-GiB caps. The result is a width-four two-pair component,
identified as `candidate_id: null` until the full IC pipeline is specified.

An independent checked-Sage W33 subspace-GCD audit tested first codes
`0..15` on both N131 point rows. The constructed row had exactly one
surviving first code, `3`, with GCD degree one; all 16 public-row first codes
had GCD degree zero. Direct root extraction recovered second code `16722`,
then replayed the source points on the curve and matched the constructed
point. The audit took 4.654 seconds for 32 exact first-code decisions, and
root extraction plus curve replay took 0.716 seconds. These timings are
algorithmic diagnostics on an ordinary shared host; the repository's
existing native W29 quartic filter is the relevant high-throughput baseline
for bulk first-code scanning.

## Instance and method

The N131 field is `GF(2)[u]/(u^131+u^13+u²+u+1)` and the curve is
`y²+xy=x³+1`, ID `EC1N131Ckb1heb5f1998f20b`. The frozen W33 source has
seed mask `898618`, 32 free code bits, and pair rotations `(0,18)`. The first
block has codes `0..15`; its odd-code branch contains eight assignments.
The second code remains a free 32-bit variable. The positive point and
public raw point are the two exact rows in the [coefficient receipt](../n131_w33_freecode_resultant_20261018/coefficients.json).

For the 13-term bidegree-`(4,4)` resultant `F(p,q)`, multiplication by the
first product `p` lowers the Boolean code degree to three. The prior
[degree-fall proof and finite checks](../resultant_degree1_syzygy_20261019/RESULT.md)
establish the transformation. The current solver adds the linear Boolean
condition `bit_0(first_code)=1`; it checks all eight corresponding first
products are nonzero, so the field equivalence `pF=0 ↔ F=0` applies on the
branch. The Gröbner computation uses degrevlex on 36 code variables and 132
equations, with 2,314 ANF monomials in the N131 public and positive blocks.

The independent audit constructs the exact 32-dimensional second-product
subspace vanisher `L_V(Z)` by basis adjunction. For each first code it forms
the specialized quartic `H_p(Z)`, reduces `L_V` modulo `H_p`, and computes
`gcd(H_p,L_V mod H_p)`. Degree zero rejects that entire second-code family.
For the sole degree-one positive case, the root is mapped back through a
full-rank `131×32` binary basis matrix to the second code. Every recovered
code is checked against the product map, and the source point signs are
replayed against the target curve point.

## Frozen runs and controls

All Sage jobs used the [checked repository launcher](sage_runtime_info.json)
with its runtime receipt saved before measurement. Each Gröbner run had one
child process and monitored combined RSS. The N41 gate completed the positive
and ordinary width-five branches under a 120-second cap and matched an
independently replayed five-pair public relation. The N131 positive gate
checked the curve replay before the public branch was launched.

| Frozen case | Solver status | Parent wall | Sampled peak combined RSS | Exact check |
| --- | --- | ---: | ---: | --- |
| N41 positive, width-five odd branch | `GB_COMPLETE` | 31.499 s | 339,361,792 B | codes `(253,63)`; independent prior relation replay |
| N41 ordinary, same branch | `GB_UNIT_IDEAL` | 27.556 s | 335,904,768 B | complete finite N41 control |
| N131 constructed, width-four odd branch | `GB_COMPLETE` | 178.791 s | 1,178,959,872 B | codes `(3,16722)`; direct W33 root and point replay |
| N131 frozen public raw point, same branch | `GB_UNIT_IDEAL` | 156.748 s | 1,010,843,648 B | all eight branch codes independently rejected by W33 GCD |

The N131 W33 GCD audit additionally covered the eight even first codes in
`0..15`, so its public-row result is a source-level no-root certificate for
that **finite 16-code block**. The Gröbner unit ideal by itself has no
separately checkable Gröbner certificate; the GCD audit supplies the
independent finite-block check. The [terminal receipt](verification_result.json)
hash-binds all input, output, stdout, stderr, run protocol, and prior replay
artifacts. Its first verifier attempt failed because the verifier expected a
list where the producer had written a keyed code object; the [failure](verification_attempt1_failure.txt)
and frozen first protocol are retained, and the corrected second protocol
passed.

## Consequence for the next iteration

The odd-code branch is an effective bounded correctness and solver control,
but its eight first-code families take about 157–179 seconds per N131 point
row. The existing native W29 quartic/subspace filter scanned `2^20` raw
first codes in 7.204 seconds for one fixed public two-pair query under its
separate protocol. Thus the cubic form should be carried forward as a joint
constraint across several pair slots, while the native GCD path handles
fixed-residual filtering. The next experiment must construct one shared
target-conditioned constraint that rejects groups of three-pair residuals
before separate two-pair queries. It should prove the pruning is exact on
the independently replayed N41 five-pair relation, then freeze an N131
public-point run with all residual generation, source checks, and rank
accounted for under the one-worker 600-second, 4-GiB gate.

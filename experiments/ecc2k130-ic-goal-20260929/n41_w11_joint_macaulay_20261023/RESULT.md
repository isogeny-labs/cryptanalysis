# A degree-six certificate rejects a 16-code N41 first-family block

A Boolean Macaulay row combination rejects the complete raw product
space for a 16-code first-family block and the frozen public N41
two-pair residual. It covers **16,384 raw first/second code pairs**
with one 1,961-row constant-one identity. The block contains seven
source-valid first codes. An independent evaluator checked that
identity on every raw assignment, so the rejection is exact for the
entire block and retains the constructed relation on the paired
positive residual.

## Exact input and method

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[u]/(u^41+u^3+1)`. The W11 fixed-seed source has 281 valid
canonical codes per pair and ten free bits per code. The two pair
slots use Frobenius rotations 12 and 24. The 13-term bivariate
resultant `H_T(p,q)` is taken from the archived free-code experiment.
Residual index 0 is the constructed positive with source codes
`(253,63)`; residual index 1 is the first frozen ordinary public
residual. The independent full census found one source-valid root on
index 0 and zero on index 1.

Because each source product is binary-linear, the 13-term resultant
has Boolean degree at most four in the 20 raw code bits. Each of its
41 field-bit equations is multiplied by monomials whose product stays
within the declared Macaulay degree. A row combination equal to the
constant polynomial one proves that no raw code assignment can solve
the field equation. For blocks, the high first-code bits are fixed to
the positive code's aligned block, while the low `k` bits and all ten
second-code bits remain free.

| Raw first-code block | Source-valid first codes | Lowest public rejection degree | Public certificate rows | Matrix time | Raw pairs independently replayed |
| --- | ---: | ---: | ---: | ---: | ---: |
| `253` | 1 | 3 | 101 | 0.003 s | 1,024 |
| `252..253` | 1 | 4 | 166 | 0.006 s | 2,048 |
| `252..255` | 2 | 6 | 768 | 0.171 s | 4,096 |
| `248..255` | 3 | 6 | 1,322 | 0.281 s | 8,192 |
| `240..255` | 7 | 6 | 1,961 | 0.477 s | 16,384 |

Every positive block retained `(253,63)`. On the public row, the
independent audit found zero raw roots in each tested block and
evaluated the saved certificate to one on every raw pair. Source
validity was checked separately: the block experiment directly
evaluated all 281 allowed second codes for every allowed first code
in each block and matched the prior full census.

The unrestricted two-family experiment used all ten first-code and
ten second-code bits. At degrees 4, 5, and 6, both residuals had full
Macaulay row rank and no constant-one combination. At degree six,
each matrix had 8,651 rows and 60,460 monomials; its reduction took
4.975 s on the positive row and 5.085 s on the public row. The
public source-valid domain has no root by the independent census,
so this is a degree-six certificate boundary rather than a missed
known witness.

## Transfer and performance boundary

The N41 result is a whole-family rejection, but its current Python
degree-six matrix takes 0.477 s for a block containing seven allowed
first codes. The prior per-code N41 degree-three Macaulay panel
processed 7,025 families in 34.668 s, about 0.0049 s per family on
its ordinary host. Those separate-host diagnostic intervals do not
establish a speedup for the block method.

For an N131 W29 first-code block of width four, the analogous raw
degree-six matrix would have 32 Boolean variables, 69,299 generated
rows, and 1,149,017 monomials. A dense bitset for every generated
row requires about **9.27 GiB** before pivot storage, beyond the
4-GiB worker envelope. This is a storage calculation for the direct
construction, not a lower bound for sparse or structured methods.
The next useful algorithmic test is to exploit the low-degree
source-product structure to reject **three or more free pair families**
without dense matrices or serial first-code specialization, then
measure total residual generation and rejection on an unpinned N41
public point. A two-pair block certificate alone does not close the
five-pair N131 search.

This is a component with `candidate_id: null`. The frozen caps are
120 s and 4 GiB self RSS on an ordinary host; the producer used
10.657 s and 145 MB raw peak RSS for the unrestricted panel, and
the block producer used 4.492 s and 32 MB raw peak RSS. The audit
used 3.961 s and 23 MB raw peak RSS. These intervals are stage
diagnostics; complete single-target online IC and matched rho timing
remain downstream of the public relation and full pipeline gates.

## Reproduction

`protocol.json`, `block_protocol.json`, and `audit_protocol.json`
freeze code, inputs, caps, and the prior census before their runs.
`result.json`, `block_result.json`, and `audit_result.json` retain
every tested degree and status. `PROOF_MAP.md` maps the generic
Lean theorem and concrete field audit. From this directory, run
`lean MacaulayBlockSound.lean` and `python3 verify_archive.py`.

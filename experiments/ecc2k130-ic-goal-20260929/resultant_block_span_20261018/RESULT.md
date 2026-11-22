# Exact affine-span filter for target resultant code blocks

An exact block filter now rejects whole families of source-code pairs by
testing whether zero lies in the affine span of their resultant values.
The checked [Lean theorem](AffineSpanSound.lean) proves that a rejected
block contains no zero output. The 185-case frozen probe retained the
known positive N41 and N131 code pairs and replayed all ranks from the
source coefficients. It also located the filter's practical boundary:
the sampled N131 blocks with five free bits on each source filled the
131-bit field, so this affine test rejected none of them.

## Method

For a block of source codes with base output `v0`, let `v_i` be every
other resultant value in the block. Reject exactly when Gaussian
elimination shows `v0` outside the binary span of `v_i XOR v0`.
If some `v_i=0`, then `v_i XOR v0=v0`, so that block is retained.
The evaluator includes all raw code assignments in each block; source
validity and distinctness are deferred, making the filter a sound
superset test. The actual code pairs remain unpinned within their
tested blocks.

The N41 control uses `GF(2)[u]/(u^41+u³+1)`, the frozen 25-target
13-term resultant and its 281 valid source codes. All 281 exported
source products match the independent binary-field implementation.
The N131 probe uses `GF(2)[u]/(u^131+u^13+u²+u+1)`, the frozen
constructed and ordinary public target coefficients, and W33 source
products with rotations `(0,18)`. The positive source products satisfy
the exact resultant in both fields. `candidate_id: null` remains the
appropriate identity at this filter stage.

## Frozen results

Each width has eight deterministic random block bases per target, hence
16 random cases, plus the block containing the known positive code pair
on each target. The N41 positive-code family was also checked against
all 24 ordinary target rows at width two. The random panel is a probe
of rank behavior, not a population estimate.

| Field degree | Free bits per source | Random block ranks | Random blocks rejected | Positive block retained |
| ---: | ---: | ---: | ---: | --- |
| 41 | 1 | 3 | 16/16 | yes |
| 41 | 2 | 15 | 16/16 | yes |
| 41 | 3 | 41 | 0/16 | yes |
| 41 | 4 | 41 | 0/16 | yes |
| 131 | 1 | 3 | 16/16 | yes |
| 131 | 2 | 15 | 16/16 | yes |
| 131 | 3 | 48 | 16/16 | yes |
| 131 | 4 | 120 | 16/16 | yes |
| 131 | 5 | 131 | 0/16 | yes |

The N131 positive-code family itself had ranks 3, 14, 45, 114, and
131 at widths one through five. On the frozen ordinary point, the same
family was rejected at widths one through four and retained by the
width-five affine test, with no zero among its enumerated pairs.
At N41 width two, the positive-code family was rejected for all 24
ordinary target rows and retained for the constructed positive.
The complete probe took 15.222 seconds on this ordinary host;
`python3 verify.py` recomputes all 185 cases and checks the proof log.

At width four, the N131 32-bit-per-source space has `2^56` block pairs
under this low-bit partition. At width five, the tested spans were
already full and gave no pruning. Thus the measured linear filter by
itself does not bring this partition near the one-worker 600-second
ordinary-point gate. A stronger nonlinear condition must prune at
larger blocks or share work across their bases.

## Proof map

`AffineSpanSound.rejected_block_has_no_zero` states that rejection by
the exact XOR-span predicate implies the base and every other listed
block output are nonzero. It is checked with Lean 4.34.1 in
`lean_check.log`; `#print axioms` lists only `propext` and `Quot.sound`.
The code contains no sorry, admit, custom research axiom, native proof
shortcut, or kernel bypass. `lean4checker --fresh` was unavailable.
The conversion from resultant outputs to field-bit integers is checked
by the pinned source products and full case replay; the Gaussian basis
implementation is checked computationally rather than formalized in
Lean.

# Equality-adaptive public collision trace: exact candidate set

**Theorem.** When the only target-dependent feedback after each new public
group expression is one bit saying whether it equals any earlier expression
with a different scalar slope, every pre-hit transcript is the same all-miss
transcript. The checked Lean theorem identifies the target scalars that can
produce a first hit among `n` generated expressions with the image of the
informative pair-candidate map on that trace. Consequently its success set
has size at most the number of informative pairs, at most `n²`.

Each expression is represented by `aQ+bG=(aw+b)G`, with `Q=wG`. Equality
between distinct slopes gives the one candidate
`w=(b_j−b_i)/(a_i−a_j)`. Equal-slope distinct expressions cannot collide.
The strategy may choose the next `(a,b)` from all prior collision bits;
before its first hit those bits are necessarily all false. The group-level
Lean bridge states the needed injectivity of scalar multiplication at `G`.
The p=313 exact-order certificate in the ancestor public-first PR supports
that premise for this replay.

## Complete checked-curve replay

The frozen protocol uses `E/F₃₁₃: y²=x³−x−2`, `G=(2,2)` of order 331,
every `Q=wG` for `0≤w<331`, and at most 24 forms per target. The first two
forms are `G` and `Q`; subsequent coefficient pairs come from SHA-256 of
the prior Boolean transcript. After each form, the producer compares its
actual finite-curve point against earlier unequal-slope points and stops at
the first equality. The independent audit reconstructs all modular forms,
pair candidates, first-hit positions, and operation counts.

| Exact metric across all 331 targets | Value |
| --- | ---: |
| Maximum forms per target | 24 |
| Informative pairs on the negative trace | 276 |
| Distinct pair candidates | 192 |
| Targets with a first group collision | 192 |
| Forms constructed across the complete census | 6,299 |
| Group equality tests across the complete census | 61,484 |

The observed success set is exactly the 192 candidate scalars, within the
Lean pair bound of 276. Repeated pair candidates account for the gap. These
are exhaustive event and operation counts, not a wall-time comparison or a
same-target rho measurement. The prior one-bit relation test names at most
one scalar per query; checking each new form against all previous ones
creates the quadratic collision mechanism familiar from
[Shoup's generic-group analysis](https://www.shoup.net/papers/dlbounds1.pdf).
This theorem handles equality-bit adaptation and fixed external randomness.
It does not include random-label coupling or selection from concrete point
coordinates.

## Reproduction

The checked `/Volumes/SSD990/cryptanalysis/sage` launcher saved its runtime
receipt before `run_sage.py`. Reproduce with that launcher's `-python` mode,
then `python3 audit.py`; from `formal/`, run `lake build AdaptiveCollision`.
`python3 verify.py` checks the sealed inputs, complete result, independent
audit, and Lean build receipt. The next proof step is to model generic
random encodings with a coupling that makes pre-collision labels independent
of the target, then separately test any concrete coordinate-based selection
rule with its full computation cost.

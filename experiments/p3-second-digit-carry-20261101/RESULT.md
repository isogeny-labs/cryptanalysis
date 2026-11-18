# H112 — `p^3` second-digit halving carry: measured result

![Best selected accuracy by curve](h112-p3-second-digit-carry-results.png)

Editable vector source: `h112-p3-second-digit-carry-results.svg`.

## Outcome

The higher-depth carry is algebraically well formed, but the frozen parity
bridge did not appear. All 9,096 target cases passed the `p^3` lift, public
halving, kernel, formal-coordinate, digit-recombination, and two-layer torsion
checks. A standalone implementation replayed every target and score. None of
the 144 preregistered predicates was exact on any of the 28 curve/generator
rows, so no repeated-halving decoder was eligible to run.

This is a scoped null result. It rejects the frozen second-digit depth channels
and cross-digit XOR predicates; it does not reject every function of a
two-digit carry and does not establish a generic lower bound.

## Mechanism tested

For `Q=[k]G`, the experiment computes the public half

```text
H = [(r+1)/2]Q
```

and, for the canonical two-digit Hensel section `s_00`, the normalized word

```text
C_3(Q) = [2]s_00(H) - s_00(Q)
K(Q)   = t(C_3(Q))/p mod p^2
       = kappa_0(Q) + p*kappa_1(Q).
```

The frozen family contains 72 predicates of `kappa_1`,
`kappa_0+kappa_1`, or `kappa_1-kappa_0`, and 72 XOR predicates combining
offset bits of both digits. It deliberately contains no low-digit-only
predicate already tested by H111.

## Measurements and controls

| Evidence | Best accuracy after 144-way selection | Exact rows |
|---|---:|---:|
| 28 canonical rows | 0.530120–0.685185; median 0.569820 | 0/28 |
| 16 randomized-section controls | 0.592593–0.670732; median 0.610434 | 0/16 |
| 16 symmetry-matched-label controls | 0.585366–0.694444; median 0.621161 | 0/16 |
| coordinate-isomorphic E101/E127 | 0.658537, 0.601852 | 0/2 |

The canonical fits overlap both controls. The largest canonical fit, 68.5185%,
is below the 69.4444% matched-label maximum and does not persist as the field
size grows. These selected accuracies are therefore not evidence for a
uniform parity law.

The complete replay has stable scientific digest:

```text
3f0d58b381df5d308537942c29f80e826217105bdd7c8db4129885c4e91ea832
```

The recovered raw JSON SHA-256 is
`304d84d1602b8278436775719a2b235506b613df907c4540a418c9b80698e759`;
its deterministic gzip SHA-256 is
`5263425a61d4d5062fd8c5c5b15d6b95f4f403849f9e918b0027b1649725ce76`.
The PR attachment uses the smaller deterministic xz representation:

```text
553742acc024e8d463275f7b2e32adbfb604ab69082cb7e69df7ad731d714d6d
```

Decompression reproduces the raw JSON hash above.

## Charged work

The canonical candidate path used 18,192 Hensel lifts, 9,096 lifted
doublings, 9,096 mixed kernel sums, and 9,096 formal extractions. Charged ring
work was 209,208 modular additions, 418,416 modular multiplications, and
54,576 modular inversions. It also used 9,096 public group-halving scalar
multiplications, evaluated 1,309,824 frozen predicate instances offline, and
stored 18,192 field digits. Torsion and control work is recorded separately in
the raw artifact.

No recovery cost is reported as executed: the exactness gate failed. Had a
single uniform exact predicate existed, the conditional decoder would have
made `O(log r)` oracle queries with polynomial bit complexity; this experiment
does not supply that premise.

## Proof and verification boundary

`H112P3SecondDigitCarry.lean` compiles with Lean 4.34.1 and pinned mathlib. It
proves reduction-kernel membership, zero carry for a homomorphic section,
digit recombination and bounds, the conditional exact-predicate interface,
recursive parity reconstruction, uniqueness after EC verification, and the
charged cost interface.

Lean does **not** assert that one of the 144 predicates is exact. The empirical
run found zero. `h112_reference_verify.py` imports no H112 experiment code and
independently rebuilt the `p^3` arithmetic, frozen predicates, controls,
isomorphisms, summaries, and scientific digest.

## Recovery provenance

The first result workspace was lost after its deterministic run. The original
scientific digest and file hashes had already been recorded, but the 23 MB raw
artifact had not reached the draft PR. The implementation was reconstructed
from the frozen protocol and H111 dependency and rerun over the complete
cohort. The scientific digest matched the original exactly. Raw byte hashes
differ because raw JSON includes timing and environment fields that the
scientific digest intentionally excludes. `RECOVERY_PROVENANCE.json` preserves
both hash sets rather than presenting the replay as the original byte stream.

## Claim boundary

The bounded prior-art screen retained Smart's anomalous-curve attack
([DOI](https://doi.org/10.1007/S001459900052)), Huang–Kueh–Tan's lifting work
([DOI](https://doi.org/10.1007/10722028_22)), Silverman's lifting survey
([DOI](https://doi.org/10.1007/978-3-642-04159-4_6)), and Yasuda's formal-group
analysis ([DOI](https://doi.org/10.1007/978-3-642-12827-1_9)). The exact H112
screen was not located there; external novelty is not established.

H112 supplies no generic, subexponential, or polynomial-time ECDLP algorithm.
It does supply a reproducible rejection of one new higher-depth candidate and
a proof of what an exact candidate would have implied.

# A fixed two-image shift grid preserves zero rational relation yield

A frozen 81-variant coordinate grid produced **3,969 valid rational curves** for the 17 public-hit vectors and 32 nonrelation controls from the larger-order xedni panel. Every candidate retained both specified public point images and good reduction. **None of the 1,377 variants of a public-hit vector satisfied its rational relation**; the 2,592 control variants likewise had zero relations. The public search supplying these events contained **6,656 vector tests**, including 17 hits. The checked theorem in [PR #1672](https://github.com/isogeny-labs/cryptanalysis/pull/1672) rules out the controls' public nonrelation vectors for every compatible lift; this grid tests the remaining public-hit vectors.

## Frozen selection and construction

The [protocol](protocol.json) pins the [parent public transcript from PR #1671](https://github.com/isogeny-labs/cryptanalysis/pull/1671) and the centered [two-image query transcript from PR #1672](https://github.com/isogeny-labs/cryptanalysis/pull/1672) by SHA-256. It selects all 17 public-relation attempts plus the first public nonrelation attempt for each of the 32 field-target pairs. All selected events have different finite `x` coordinates. This selection uses only the public relation flag; the shift grid and its order were fixed before rational outcomes were computed.

For each event, center the finite points as integer pairs `(x₁,y₁)` and `(x₂,y₂)`. The 81 shifts in lexicographic `{-1,0,1}⁴` order add multiples of `p` independently to `x₁,y₁,x₂,y₂`. Each shift determines one rational curve:

```text
fᵢ=yᵢ²−xᵢ³,   A=(f₁−f₂)/(x₁−x₂),   B=f₁−Ax₁,
E: y²=x³+Ax+B,   P=(x₁,y₁),   R=(x₂,y₂).
```

The runner checks nonsingularity, `p`-integral coefficients with `A≡−1` and `B≡−2`, both point reductions, and the exact rational sum `aP+bR`. It charges every candidate, including failures. The `(0,0,0,0)` variant matches the parent centered curve for all 49 events.

| Arm | Events | Shifted curve attempts | Valid curves | Rational relation hits |
| --- | ---: | ---: | ---: | ---: |
| Public-hit vectors | 17 | 1,377 | 1,377 | 0 |
| First-nonhit controls | 32 | 2,592 | 2,592 | 0 |
| **Total** | **49** | **3,969** | **3,969** | **0** |

The model score is the maximum numerator or denominator bit length among `A,B,x₁,y₁,x₂,y₂`. Among positive events, the median centered score is 27 bits and the median best-grid score is 23 bits; the median paired reduction is 3 bits. All 17 positive and 32 control events have a model within the predeclared 32-bit cap, including the centered positive models. This is model size, not a rational relation witness. The 1.88-second script interval is a bounded algorithmic diagnostic on this host after the checked Sage launcher started; it is not an isolated same-target online comparison.

## Verification and interpretation

The four ordered `candidates.partNN.jsonl.gz` files in [storage-amendment.json](storage-amendment.json) retains all 3,969 shifts, exact coefficients, statuses, scores, and relation flags. [run-result.json](run-result.json) records counts and raw/compressed digests. The [compression script](compress.py) splits the frozen transcript losslessly; the audit reconstructs its original bytes and gzip hash before replay. The [independent auditor](audit.py) uses Python `Fraction` and separate finite and rational group laws to reconstruct every selected event, all 3,969 rational curves and vector sums, coefficient and point reductions, discriminants, height scores, and centered matches. [audit.json](audit.json) records `PASS` with empty stderr. The [runtime receipt](sage-runtime.json) was saved before the workload, and [verify.py](verify.py) replays the audit and checks the SHA-256 seal.

The result covers the frozen 81-shift grid and selected 13-vector family. It shows that changing both affine lift coordinates by one field modulus in either direction does not turn any of these 17 public hits into its rational relation. The next construction should vary the *lift selection rule itself* before inspecting the vector outcome, then evaluate relation yield and selection cost on fresh public queries. A global impossibility theorem would require a bound over that larger adaptive search space.

Reproduce from this worktree with `/Volumes/SSD990/cryptanalysis/sage --runtime-info`, `/Volumes/SSD990/cryptanalysis/sage -python experiments/xedni-two-image-shift-grid-20261116/run.py`, `python3 experiments/xedni-two-image-shift-grid-20261116/compress.py`, `python3 experiments/xedni-two-image-shift-grid-20261116/audit.py`, and `python3 experiments/xedni-two-image-shift-grid-20261116/verify.py`.

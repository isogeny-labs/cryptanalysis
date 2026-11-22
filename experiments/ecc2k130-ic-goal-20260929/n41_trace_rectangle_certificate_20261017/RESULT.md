# Binary-linear target certificates saturate on product rectangles

**Every one of the 13,824 N41 full affine product rectangles with two low source-mask bits free per slot has coefficient-span rank 41, on both the frozen public-witness residual and its negative control.** Thus a binary linear functional cannot certify the eliminant nonzero over any of those complete 64-assignment cubes. Rank stays 41 for every full cube at three and four low bits per slot. At one low bit, the functional certifies all zero-free rectangles and correctly leaves the public witness rectangle open. This is an exact exhaustive result for the stated N41 rectangle cover and target-conditioned eliminant.

## Certificate and frozen source

The N41 curve is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t⁴¹+t³+1)`. The prior [universal eliminant](../n41_first_product_interpolated_eliminant_20261017/RESULT.md) has 213 `(q,r)` coefficient polynomials in `p`, and a zero is necessary for a three-free-product relation on the frozen four-state suffix. All three source slots use the same 40 legal eight-bit canonical masks. For width `b`, group each slot's legal masks by their high `8-b` bits and let the `b` low bits range freely. This full affine cube may include invalid source masks, so proving nonzero on it soundly rejects every legal triple in its rectangle. Each legal triple appears in exactly one rectangle.

For a rectangle with `f=3b` free bits, write the field-valued Boolean algebraic normal form

`F(x)=⊕_{S⊆supp(x)} a_S`, with `a_S∈GF(2⁴¹)`.

The affine hull of all values is `a_∅ + span_GF(2){a_S:S≠∅}`. Indeed, the displayed expansion puts every value in that affine space, and Möbius inversion expresses every nonconstant coefficient as an XOR of a value and the constant value. A binary linear functional `λ` with `λ(a_∅)=1` and `λ(a_S)=0` for all nonconstant coefficients therefore gives `λ(F(x))=1` on the entire cube, proving `F(x)≠0`. Such a functional exists exactly when `a_∅` is outside the nonconstant coefficient span. The [Lean theorem](TraceCertificate.lean) proves the final nonzero implication under an explicit additive functional; the [proof map](PROOF_MAP.md) keeps the ANF-transform and concrete curve bridges explicit.

| Low bits per slot | N41 nonempty rectangles | Full-cube certificates, witness / negative | Source-valid-only certificates, witness / negative | Source-valid triples covered by source-only certificates, witness / negative |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 42,875 | 42,874 / 42,875 | 42,874 / 42,875 | 63,999 / 64,000 |
| 2 | 13,824 | **0 / 0** | 13,823 / 13,824 | 63,992 / 64,000 |
| 3 | 2,744 | **0 / 0** | 2,405 / 2,414 | 45,010 / 45,375 |
| 4 | 512 | **0 / 0** | **0 / 0** | 0 / 0 |

The full-cube nonconstant coefficient rank is **41 for every rectangle at widths 2, 3 and 4** on both panels. At width 1 its maximum is 7. The source-valid-only column is an optimistic bound: it computes the affine hull *after enumerating all valid values in each rectangle*. It is not a cheap source-aware certificate construction. The public witness mask triple `(153,215,64)` remains in one open rectangle at every width; the frozen negative panel has no source-valid zero. Both source-valid zero counts agree with the archived full 40³ sweep.

The checked-Sage worker evaluated the 128-mask-per-slot envelope once per panel (`128³=2,097,152` field values), then analyzed every rectangle at widths 1–4. Witness grid construction took **101.83 s** and negative grid construction **80.10 s**; analysis of all four widths took **6.50 s** and **5.37 s** respectively. Peak process RSS was **268,533,760 B** under the frozen one-worker, 300-second alarm and 4-GiB observational boundary. These are ordinary-host component costs, with source setup and checked-Sage launch outside the recorded grid intervals. The [runtime receipt](sage_runtime_info.json), [protocol](protocol.json), [result](result.json), stdout and stderr retain the exact inputs and status.

The independent [field replay](verification.json) evaluates saved width-1 certificates directly using a separate shift-and-XOR multiplier, checks the archived witness zero, and recomputes rank 41 on a representative full rectangle at each larger width and on both residuals. The exhaustive rank histograms are producer measurements; the independent replay covers the saved certificates and six representative full-rank rectangles.

## Exact W20 prefix transfer screen

The selected N131 W20 source has 132,045 valid 19-bit product codes per slot. Reconstructing those codes from the frozen [support table](../n131_w20_sevenpair_gate_20261010/support_w20.tsv) gives the following nonempty high-bit groups under the analogous low-bit rule. An independent [validity-bitmap replay](n131_projection_verification.json) reproduces every group histogram and the earlier two-bit source survey.

| Low bits per slot | Nonempty W20 groups per slot | Three-slot rectangles before exclusions | Rectangle decisions/s for a 600 s pass |
| ---: | ---: | ---: | ---: |
| 1 | 115,577 | 1,543,882,527,605,033 | 2,573,137,546,009 |
| 2 | 90,055 | 730,337,316,916,375 | 1,217,228,861,528 |
| 3 | 59,163 | 207,085,916,043,747 | 345,143,193,407 |
| 4 | 32,441 | 34,141,507,942,121 | 56,902,513,237 |

The table is an exact traversal count for this fixed prefix partition, before cross-slot column exclusions and before work on the other four pair slots. It is not a lower bound on adaptive or algebraically structured covers. Even width 4 would require over **56.9 billion rectangle decisions per second** to visit every three-slot block in 600 seconds, while the N41 full-cube certificate has already saturated at width 2. This combination stops the fixed low-bit linear-certificate route. The next source-bound experiment should search for larger **all-valid affine flats or other structured covers** of the W20 code bitmap and test a joint target predicate on those blocks; its success must be measured on an unpinned N41 public relation before the frozen N131 ordinary-relation gate. `candidate_id` remains `null` for this component.

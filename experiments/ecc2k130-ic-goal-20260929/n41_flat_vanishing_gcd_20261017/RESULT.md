# Exact flat-root GCD preserves N41 decisions; direct evaluation wins the measured query

**A target-conditioned vanishing-polynomial GCD screens a complete all-valid right-source family without enumerating its members, and both tested variants exactly reproduce the frozen N41 public witness and negative control.** Combining the overlapping flats into one degree-27 polynomial reduces the GCD route from 52.36 to 31.01 seconds on the witness panel. The matched direct scan takes 0.375 seconds on that panel. Thus the exact family operation works, but its current per-pair use is substantially more expensive than direct evaluation.

For a finite field subset `A`, let `V_A(R)=∏_{a∈A}(R−a)`. The [checked Lean theorem](FlatProduct.lean) proves `V_A(r)=0` exactly when `r∈A` for a finite source list. Since `V_A` splits into distinct linear factors here, `gcd(F_{p,q},V_A)` has positive degree exactly when the target-conditioned polynomial `F(p,q,R)` has a root in `A`. The first variant tests six all-valid size-eight affine flats covering 27 of the 40 legal right masks, then evaluates the other 13 directly. The second tests their 27-mask union with one degree-27 polynomial, then evaluates the same 13 directly. Any nonconstant GCD triggers exact member checks to report the source mask.

The frozen N41 eliminant has degree at most 24 in the right product. Each panel specializes its 213-term tensor at all `40²=1,600` legal left/middle mask pairs. For each pair the runner alternates route order by mask-index parity and charges common coefficient construction, direct all-40 Horner evaluation, and each GCD route in separate exclusive intervals.

| Panel and route | Common coefficients | Query route | Family GCDs | Exact zero masks |
| --- | ---: | ---: | ---: | --- |
| Witness, direct all 40 | 0.149 s | **0.577 s** | 0 | `(153,215,64)` |
| Witness, six flats plus 13 | same | **52.360 s** | 9,600 | `(153,215,64)` |
| Negative, direct all 40 | 0.134 s | **0.372 s** | 0 | none |
| Negative, six flats plus 13 | same | **38.585 s** | 9,600 | none |
| Witness, direct in union run | 0.124 s | **0.375 s** | 0 | `(153,215,64)` |
| Witness, union plus 13 | same | **31.012 s** | 1,600 | `(153,215,64)` |
| Negative, direct in union run | 0.121 s | **0.352 s** | 0 | none |
| Negative, union plus 13 | same | **27.930 s** | 1,600 | none |

The six-flat and union setup intervals are 0.0244 and 0.0215 seconds, respectively, outside the per-pair query routes. Both checked-Sage runs completed under their one-worker, 300-second alarm and 4-GiB observational envelope; peak self RSS was 255,295,488 and 255,000,576 bytes. These are ordinary-host component timings, with launch, file loading, and the accepted Sage [runtime check](sage_runtime_info.json) outside the route intervals. They are not CPU-isolated speedup measurements. The [six-flat result](result.json), [union result](union_result.json), protocols, stdout, stderr, source hashes, and phase counts preserve the exact work.

The independent [replay](verification.json) reconstructs each vanishing polynomial with a separate binary-field multiplier and checks its zero set against all 40 legal right products. It checks the full 40³ frozen value grids and zero locations from the preceding affine-flat survey, verifies all route counts and source hashes, and directly reevaluates 40 right values for each of two left/middle pairs on each panel from the coefficient tensors. The producer also compares both routes against its own full direct scan and the prior independently audited source sweep. The [proof map](PROOF_MAP.md) records the Lean theorem and the remaining concrete polynomial/GCD formalization bridge.

## N131 source-bound decision

The W20 source has 132,045 valid codes per slot, hence `17,435,882,025` ordered left/middle pairs. A literal visit to every such pair needs **29,059,804 pair decisions per second** to finish in 600 seconds. Applying the current 4,096-block size-sixteen cover to every pair would schedule `71,417,372,774,400` GCD decisions and still leave `79,802` right codes per pair outside that partial cover. Those counts describe this literal specialized-pair architecture; target-guided elimination of left/middle families could change them. The measured N41 GCD route does not justify N131 promotion. The next design step is to constrain whole left/middle families jointly with the public target before forming per-pair right polynomials, then test an unpinned N41 ordinary relation under the same accounting boundary. `candidate_id` remains `null` for this component.

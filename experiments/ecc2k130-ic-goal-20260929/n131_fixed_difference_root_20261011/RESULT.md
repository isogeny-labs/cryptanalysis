# Degree-eight root gate for a fixed same-seed product difference

Fixing the difference `δ=p+q` between the two pair products converts the archived same-seed four-point eliminant into a **degree-eight polynomial in `T=pq`**. Each field root `T` gives at most two product roots through the Artin–Schreier equation `p²+δp=T`. On the frozen N131 W14 positive block, this extracted exactly the two ordered products **`(1112,1376)` and `(1376,1112)`**; a trace-zero field control had four product roots in the full field and **zero** in the source product image. Complete product-image scans and the independently archived four-point group witness agree.

The [protocols](protocol.json) [for both stages](quotient_protocol.json) bind the exact degree-41 and degree-131 fields, `y²+xy=x³+1`, the archived 150-term resultant, its positive/control inputs, checked Sage runtime, one worker, 120 seconds per case, and 4 GiB RSS. The N131 source is W14 with seed `s=t`, product image size **8,192**, and fixed positive difference `δ=312`. N41 uses W6, image size **32**, and `δ=80`. Both fixed differences come from the archived positive pairs; this experiment is a terminal gate with `candidate_id: null`.

## Exact reduction

The original polynomial `H(s,p,q,z)` is symmetric in `p,q`. Its exact symmetric representation `Hbar(s,P,T,z)` has 87 terms for `P=p+q` and `T=pq`, with degree at most eight in `T`. At fixed `P=δ`, solve `Hbar(s,δ,T,z)=0` over the field. A `T` root lifts to field products exactly when `Tr(T/δ²)=0`: half-trace solves `u²+u=T/δ²`, then `p=δu` and `q=p+δ`. The [terminal verifier](verification.json) expands `Hbar(s,p+q,pq,z)` as a sparse GF(2) polynomial and matches every one of the original 150 terms, then checks that the degree-eight path returns the same complete field-root set as the separately computed degree-16 specialization in all four frozen cases.

| Field and frozen case | Source image | Degree-16 roots / supported | Degree-8 quotient roots / lifted products | Degree-8 query wall | Full image scan wall |
| --- | ---: | ---: | ---: | ---: | ---: |
| N41 positive | 32 | 2 / 2 | 3 / 2 | 0.991 s | 0.034 s |
| N41 trace-zero control | 32 | 0 / 0 | 1 / 0 | 0.024 s | 0.016 s |
| N131 positive | 8,192 | 2 / 2 | 2 / 2 | **4.597 s** | 60.079 s |
| N131 trace-zero control | 8,192 | 4 / 0 | 5 / 4 | **4.633 s** | 39.439 s |

The [degree-16 producer](result.json) also checked `H(s,p,p+δ,z)` at every product in the complete source image. Its N131 root extraction took 9.817 seconds on the positive and 6.204 seconds on the control; the [quotient result](quotient_result.json) returned identical field roots after the trace test. Producer and quotient process peak RSS were 209,911,808 B and 206,323,712 B. All per-case intervals met their frozen caps. Both process stderr files are empty, and the checked [Sage runtime receipt](sage_runtime_info.json) was saved before the measured arithmetic intervals. CPU wall times are exploratory on this heavily contended host; the exact reduction in polynomial degree and root decisions is the reproducible result.

This gate requires both a proposed four-point output `z` and a product difference `δ`. Searching every difference would replace a single degree-eight call with thousands of calls per seed, so the next experiment must obtain a small target-conditioned difference domain from an upper S3 constraint while other block outputs remain implicit. Its first end-to-end gate is an unpinned N41 public relation with all failed proposals charged; a source-bound N131 projection must then fit one worker, 600 seconds, and 4 GiB before a frozen public-point query.

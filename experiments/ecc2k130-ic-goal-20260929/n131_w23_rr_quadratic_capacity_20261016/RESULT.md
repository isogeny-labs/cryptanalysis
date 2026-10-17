# N131 W23 quadratic value certificate saturates after 67 complete codes

**One quadratic Boolean functional certifies the first 67 ascending W23 first-pair codes against the frozen N131 public target, covering all 8,576 root/sign states.** Adding the 68th code makes the shared functional system inconsistent at its upper x root, sign mask 2. An explicit odd XOR dependency of **4,373** evaluated feature rows proves that inconsistency. Checked Sage independently formed and matched **all 8,704** seven-point Riemann–Roch determinants for the 68 processed codes; every value in this selected panel is nonzero. The first 68 codes have the same first 13 bits of their 22-bit canonical mask, so a single degree-two determinant-value certificate cannot reject even that full high-bit region on this fixed-five-slot panel.

This gives a direct N131 scale test of the [N41 quadratic code-region screen](../n41_rr_quadratic_value_dual_20261016/RESULT.md). Seven four-bit N41 regions admitted shared certificates there. Here the N131 8,646-dimensional quadratic feature space is nearly exhausted by 68 codes: rank rises by 128 per code through code 67, then reaches 8,642 before the first inconsistent row of code 68. A useful W23 family filter must let its condition vary with source-code information or exploit an identity beyond interpolation of a fixed quadratic score.

## Frozen source, target and calculation

The field is `GF(2)[t]/(t¹³¹+t¹³+t²+t+1)`, the curve is `y²+xy=x³+1`, and the subgroup order is `680564733841876926932320129493409985129`. The ordinary raw public target is `(752537266629515638098808075959135066805,1706656992242509891647994989162078416372)`. Five pair-code and x-root choices are the predeclared W23 sample indices `2,3,4,5,6` from the earlier [six-pair RR source panel](../n41_n131_sixpair_rr_root_span_20261016/RESULT.md). This fixed-five panel measures certificate capacity; those choices were not obtained by an unpinned search algorithm.

The checked [Sage preparer](prepare_sage.py) scanned canonical first-slot masks in ascending order, required both seed endpoints to meet the W23 reciprocal-trace source law, rejected folded-column conflicts with the five fixed pairs, and froze the first **80** eligible pair codes in [panel.json](panel.json). It examined masks `1,…,311`; the 68th accepted mask is **274**. Both x roots and all 64 y-sign assignments were retained per code. The preparer ran through the repository's checked `./sage` launcher after [saving the runtime receipt](sage_runtime_info.json). The [prepare protocol](prepare_protocol.json) fixes the exact source and scan rule.

For a determinant value `D∈GF(2¹³¹)`, let `d_i` be its binary coordinates. A quadratic certificate has the form

`Q(D)=Σ_i a_i d_i + Σ_{i<j} b_ij d_i d_j`, with `131+binom(131,2)=8,646` coefficients.

The seven-point determinant includes `−target` as its seventh row. If `Q(D)=1` for every root/sign state in a code family, then that family contains no zero determinant because `Q(0)=0`. The [rank worker](run.py) computed the determinant sign polynomial, evaluated it on all 64 signs per root, and inserted each quadratic feature row into an exact GF(2) system. Its [frozen protocol](run_protocol.json) hashes the panel and source, specifies one worker and a 600-second parent cap, and records an observational 4-GiB memory threshold. The run finished before its cap. This was a certificate-capacity diagnostic, not the ordinary N131 relation-query gate.

## Exact result and independent replay

| Frozen W23 fixed-five panel | Result |
| --- | ---: |
| Eligible first codes frozen / processed | 80 / 68 |
| Root/sign states per processed code | 128 |
| States certified by one shared quadratic score | 67 × 128 = **8,576** |
| Rank after codes 1–67 | exactly `128 × code_count` |
| First inconsistent state | code ordinal 67, mask 274, root 1, sign 2 |
| Rank before that state | **8,642 / 8,646** features |
| Explicit odd XOR dependency | **4,373** rows; feature XOR zero |
| Independent checked-Sage determinants matched | **8,704 / 8,704** |
| Zero determinants in this selected panel | **0** |
| Arithmetic worker interval / macOS process high-water RSS | 14.267 s / 31,309,824 B |

The [coefficient artifact](coefficients.json) contains both root-chart sign polynomials for every processed code. Checked Sage independently built the actual 7×7 evaluation matrix for every one of the 8,704 sign states and matched each determinant to the polynomial value; [audit_result.json](audit_result.json) retains chart digests and status. The [explicit contradiction](certificate.json) indexes 4,373 saved states. XORing their 8,646-bit feature vectors gives zero, while their required right-hand sides XOR to one. The [independent verifier](verify.py) recomputes all feature vectors and matrix rank with low-pivot elimination, checks the 67-code score on every state, checks the contradiction, and binds the Sage audit. Its [terminal receipt](terminal.json) reports `PASS_N131_W23_QUADRATIC_CAPACITY_REPLAY`.

The first 64 accepted codes have masks below 256; four more accepted masks from 256 through 274 enter the tested 68-code prefix. All 68 masks are below 512. With a 22-bit canonical mask, every high-bit prefix of depth at most 13 therefore keeps the contradictory set together. Depth 14 separates the first 64 from the next four. This is an exact obstruction for **one fixed quadratic score on that bucket**; it does not constrain a code-dependent score or a different source family.

The preparer, certificate producer, full Sage determinant audit, and terminal verifier retain separate [protocols](prepare_protocol.json), [stdout](run.stdout), [stderr](run.stderr), and results. The arithmetic worker's interval is inside the Python process and excludes launch and input loading; the checked-Sage audit took 22.442 seconds inside its process, the contradiction producer 26.792 seconds, and the terminal verifier completed under its 300-second cap. These ordinary-host times are component diagnostics. Every target-dependent construction cost would belong in a later single-target online interval. `candidate_id` remains `null` because this is a representation screen rather than a complete IC pipeline.

## Proof and next algorithmic gate

The mathematical contradiction is immediate from linearity in the feature vector `φ(D)=(d_i,d_id_j)`: for the saved odd set `I`, `⊕_{i∈I}φ(D_i)=0`. Any fixed coefficient vector `w` gives `⊕_{i∈I}⟨w,φ(D_i)⟩=0`, whereas requiring each score to be one gives parity one. [QuadraticConflict.lean](QuadraticConflict.lean) proves this structural implication for an arbitrary Boolean-linear score and XOR dependency. The [proof map](PROOF_MAP.md) records the checked theorem, concrete finite certificate, and remaining curve formalization bridge.

The next candidate should make a **target-conditioned condition depend on unresolved source-code bits** and prove whole-region rejection without enumerating its members. A cheap first falsifier is to take this same frozen N131 panel and test whether a compact code-parametric quadratic score extends far beyond 67 codes while the condition remains derivable before root/sign expansion. A passing construction must then find an ordinary relation on an unpinned N41 public query with complete target-dependent costs and a matched direct join before the frozen one-worker, 600-second, 4-GiB N131 relation query.

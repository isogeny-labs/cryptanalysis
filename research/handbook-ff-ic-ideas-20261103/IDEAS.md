# 100 index-calculus ideas from the Handbook of Finite Fields (2026-11-03)

Each row is a proposal: mechanism, falsifiable claim, preregistered prediction, cheapest discriminating test, falsifier, prior-art status in this lab, and its Lean declaration. Nothing in this table is verified, measured or an improvement; a row becomes a success only when a frozen, replayed measurement lowers cost against the named IC baseline (AGENTS.md, success criterion).

Lean status key: `proved` = a supporting theorem compiled and passed the axiom audit; `stated` = only the claim `Prop` exists; `unverified` = the module failed the mechanical check (see `formal/receipts/`).

## factor-base (18)

### H001 — Kloosterman/Walsh ranking of affine cosets for the factor base

- **Handbook**: 17.2.1 Mutually unbiased bases  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H001_claim`; theorems: `H001_partition_sum`, `H001_no_gain_without_variance`)
- **Claim**: Valid-point counts across the 2^(n-m) cosets of a fixed V exceed binomial spread; a dual-sum (Walsh) predictor ranks cosets with Spearman >= 0.6, so best-of-K gives >= 1.05x relations per factor-base element. A13 measured coset choice as near-null, so this is a predictor test only.
- **Prediction**: Spread 1.0-1.5x binomial SD; predictor rho 0.6-0.9; best-of-64 gain 1.03-1.10x, shrinking with n.
- **Cheapest test**: n=17, m=8: all 512 cosets; count valid points and S3 relations over 2000 targets; correlate with Walsh prediction; 5 random b.
- **Falsifier**: Spearman < 0.3, or best-of-64 gain < 1.02x with bootstrap CI containing 1.
- **Lean gap (assumed, not proved)**: Walsh/Kloosterman dual-sum predictor correlation (Spearman >= 0.6) with coset valid-point counts and the resulting best-of-64 gain; claim quantifies over observation records.

### H002 — Cyclic-shift window factor base: Frobenius merge factor about 2

- **Handbook**: 17.1.6.3 Linear polynomial dynamical systems  ·  **Prior art**: tried-closed  ·  **Lean**: proved (`H002_claim`; theorems: `H002_stay_count`, `H002_claim_holds`)
- **Claim**: New angle only on the closed census: for a window V=span{x,...,x^(2^(m-1))} of dim about n/2, Frobenius classes number |V|/c with c in [1.8,3] independent of n, so orbit quotient shrinks columns about 2x, not n x. The existence obstruction itself is closed.
- **Prediction**: Mean class size about 3.0; classes/|V| about 0.5 (0.33-0.56); LA B^2 term falls at most about 4x.
- **Cheapest test**: n=19,29 (also 11,13,37): enumerate window elements, compute classes by repeated squaring, report class-size distribution.
- **Falsifier**: Column reduction >= 4 for the window at n=29 or 37.
- **Lean gap (assumed, not proved)**: That Frobenius class sizes of the window span{x,...,x^(2^(m-1))} in GF(2^n) are at most 3 and sum to |V| (hypothesis of the claim); the shift action as a bit shift on window coordinates.

### H003 — Kneser/Freiman-extremal subspaces with small product span

- **Handbook**: 16.7.2 Polynomial multiplication, 16.7.3 Matrix multiplication structure  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H003_claim`; theorems: `H003_ap_sums`, `H003_claim_holds`, `H003_ap_le_generic`)
- **Claim**: Among d-dim subspaces of GF(2^n), n prime, dim(V*V)=2d-1 holds only for u*span{1,w,..,w^(d-1)}; random subspaces give min(n,d(d+1)/2). Product-span size controls the linearised-decision candidate dimension.
- **Prediction**: n=23,d=7: random V gives dim 23; interval V gives 13; no non-AP subspace in 1000 samples drops below 2d-1.
- **Cheapest test**: n=17..23, d=5..8: sample subspaces, Gaussian-eliminate pairwise products, histogram dim(V*V).
- **Falsifier**: A non-AP subspace with dim(V*V)<2d-1 at prime n, or random subspaces below the generic value at >1%.
- **Lean gap (assumed, not proved)**: Kneser/Freiman lower bound dim(V*V) >= 2d-1 and the equality characterisation (V is u*span{1,w,..,w^(d-1)}) in GF(2^n), n prime; both are hypotheses. The AP sumset count is proved on exponents only.

### H004 — Fano-factor selection of equal-size subspace factor bases

- **Handbook**: 16.2.1 Basic concepts of stream ciphers  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H004_claim`; theorems: `H004_cost_divides`, `H004_cost_antitone`, `H004_cost_improves`)
- **Claim**: Solution count N(V) over random k-dim subspaces is over-dispersed against a symmetric null, so best-of-M selection gives >= 1.2x relations per candidate at fixed |V|.
- **Prediction**: Fano factor exceeds null by >1.5; best of 300 gives 1.2-1.6x; random-b negative control 1.0+-0.05.
- **Cheapest test**: n=19,k=7,m=3: 300 random V, brute-force N(V); compare dispersion with null and Frobenius-invariant positive control.
- **Falsifier**: Dispersion within 0.9-1.1 of null, or best-of-M gain <1.05 after multiple-comparison correction.
- **Lean gap (assumed, not proved)**: Over-dispersion of the solution count N(V) over random k-dim subspaces of GF(2^n) (Fano factor vs symmetric null) and the measured best-of-M gain >= 1.2x; proved part is only the cost arithmetic.

### H005 — Trace-code rank-profile criterion for factor-base subspace shape

- **Handbook**: 15.1.2.4 Subfield and trace codes, 15.1.2.3 Reed-Muller codes  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H005_claim`; theorems: `H005_sum_counts`, `H005_best_ge`)
- **Claim**: At fixed dimension, dispersion index of decomposition counts over targets differs across V shapes (prefix, contains 1, trace-zero, random); the low-rank mass of Dickson forms B_gamma predicts which shape maximises P(N0>=1).
- **Prediction**: Random V index within 5% of 1; prefix and 1-containing V 1.15-1.6; P(N0>=1) differs >= 0.03 between shapes.
- **Cheapest test**: Exact N0(r) for all r at n=17..23 per shape via Artin-Schreier enumeration; 20 random V per shape; subfield-like degenerate positive control.
- **Falsifier**: All shapes within 5% dispersion and 0.01 in P(N0>=1), or predictor Spearman < 0.5.
- **Lean gap (assumed, not proved)**: Dickson-form low-rank (trace-code) predictor linking V shape to P(N0>=1) and the exact Artin-Schreier N0(r) enumeration; double counting is proved for an abstract pair-to-r map, not the field.

### H006 — Cyclotomic-coset factor base x^s in a Frobenius orbit

- **Handbook**: 14.7.1 Association schemes, 14.6.5 Cyclotomic classes  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H006_claim`; theorems: `H006_stable`, `H006_instance`)
- **Claim**: F={x: x^s in C}, C a Frobenius orbit in mu_M, is Frobenius-stable for any n with |F|=s*n, no table needed; yield equals a random stable set within 10%. Divisors of 2^n-1 near 2^(n/2) limit availability.
- **Prediction**: Yield ratio 0.9-1.1; membership 1.0-1.5x a hash lookup at |F| about 2^28; n=29, s=1103 gives |F|=31987.
- **Cheapest test**: n=29, s=1103: compare m=2 yield and columns against random orbit union and Hamming ball; list divisors of 2^n-1 near 2^(n/2) for n in 53..131.
- **Falsifier**: Yield ratio outside [0.8,1.25], or no divisor within 8x of 2^(n/2) for most n.
- **Lean gap (assumed, not proved)**: GF(2^n)* as Z/(2^n-1) via a primitive element, x^s as multiplication by s, ord_M(2)=n for M | 2^n-1, yield-vs-random-stable-set ratio and the existence of divisors of 2^n-1 near 2^(n/2); the |F| = s*n count is checked only by decide for N=63, s=3, n=6.

### H007 — 2-torsion translation as extra projectivity in subfield orbit quotient

- **Handbook**: 14.4.2 Collineations and coordinate frames  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H007_claim`; theorems: `H007_monotone`, `H007_half`, `H007_claim_holds`, `H007_cost_improves`)
- **Claim**: For even-order binary curves with iota-closed subfield base (sqrt b in V), quotienting by <Frobenius, iota> instead of <Frobenius> halves unknown classes and relations needed; 2-torsion saturation may already do this.
- **Prediction**: Class ratio 0.50+-0.05; relations to full rank 0.50+-0.10; dense LA x0.25-0.5.
- **Cheapest test**: y^2+xy=x^3+x^2+1 over GF(2^18), V=GF(2^6), m=3: build relation matrices on pi-classes vs (pi,iota)-classes, verify logs by brute force.
- **Falsifier**: Class ratio >0.6, a mod-l inconsistent relation, or code already quotients by iota.
- **Lean gap (assumed, not proved)**: That the 2-torsion translation iota acts freely and commutes with Frobenius on the iota-closed subfield base (sqrt b in V), giving orbit size 2d, plus mod-l consistency of relations transferred to the quotient DLP instance.

### H008 — Exponential-sum bias of S3 triple count T(V) across subspaces

- **Handbook**: 12.5.3 Bounds for rational places, 12.7.3 Case of curves  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H008_claim`; theorems: `H008_le_cube`, `H008_cost_antitone`, `H008_perm_invariant`)
- **Claim**: T(V), the count of S3 solutions in V^3, varies beyond clumped-Poisson across V; offline search beats a random V by more than noise, while structured families (polynomial basis, trace-kernel) stay within 5% of random.
- **Prediction**: std/mean of T 10-25%; best of 1000 gives 1.2-1.5x mean; structured families within 5%.
- **Cheapest test**: n=20,l=7: T(V) for 2000 random V and 6 structured families; dispersion vs Poisson with A/A split.
- **Falsifier**: Dispersion within 1.1 of clumped-Poisson and no structured family beyond 5%.
- **Lean gap (assumed, not proved)**: Exponential-sum/Weil-type bias of the S3 triple count T(V) across subspaces and the best-of-1000 gain of 1.2-1.5x; the S3 relation is an abstract Bool predicate here. Permutation invariance is proved only for a single-index count, not the full triple count.

### H009 — Artin-Schreier splitting density of cosets of V

- **Handbook**: 12.1.3 Extensions of function fields  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H009_claim`; theorems: `H009_tuples_length`, `H009_good_count`, `H009_monotone`)
- **Claim**: Only about half of V lies on E (Tr(v+a+b/v^2)=0); the best coset has density 0.5+O(sqrt(k(n-k))2^(-k/2)), raising useful fraction by (rho/0.5)^m, visible at small k and vanishing at cryptographic size. Koblitz trace-zero policy already forces density 1.
- **Prediction**: n=24,k=8,m=3: best of 10^4 cosets rho 0.60-0.70, gain 1.7-2.7x; n=48,k=16 gain <1.15x.
- **Cheapest test**: n=20..30: E-density of 10^4 random cosets; fit best density to Chernoff prediction; S3 solves on best vs median V.
- **Falsifier**: Best-of-10^4 density within 0.02 of 0.5 at n=24,k=8, or gain <1.3x useful relations per call.
- **Lean gap (assumed, not proved)**: Artin-Schreier splitting criterion Tr(v+a+b/v^2)=0 defining the on-curve predicate, the Chernoff best-coset density 0.5+O(sqrt(k(n-k))2^(-k/2)), and Koblitz trace-zero policy; the strict-improvement conjunct of the claim is stated but not proved.

### H010 — Legendre-sequence bias selection of affine cosets (odd p and binary)

- **Handbook**: 10.4.4.3 Legendre sequence and related bit sequences  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H010_claim`; theorems: `H010_claim_holds`, `H010_best_monotone`, `H010_best_ge`)
- **Claim**: Best-of-T coset selection by lift fraction raises it from 1/2 to 1/2+0.35*sqrt(ln T/|V|); gain is a toy-scale effect shrinking like 1/sqrt|V|.
- **Prediction**: |V|=2^10,T=2^10: 2.6-3% gain in B per enumerated x; under 0.1% at |V|>=2^20.
- **Cheapest test**: GF(2^17) and p about 2^20: lift fraction over 2000 cosets of a dim-10 subspace vs Gaussian and random-coset nulls, with A/A.
- **Falsifier**: Max over T cosets within one standard error of the iid-binomial null, or realised gain <0.5% at |V|=2^10.
- **Lean gap (assumed, not proved)**: That the +-1 characters are Legendre/quadratic-character values of the lift predicate on cosets of V in GF(2^n) or F_p, and the 0.35*sqrt(ln T/|V|) extreme-value gain of best-of-T selection; only the integer identity 2*lifts = |V| + sum chi and max-monotonicity are proved.

### H011 — Primitive-polynomial LFSR enumeration of factor-base abscissae

- **Handbook**: 11.1.1.3 Primitive elements, 11.1.3.2 Modular reduction in extension fields  ·  **Prior art**: untried  ·  **Lean**: proved (`H011_claim`; theorems: `H011_pow_add`, `H011_distinct_lt`, `H011_distinct`, `H011_enum_cost_ratio`)
- **Claim**: Factor base {t^i}, t primitive, is enumerated with one shift plus <=hw(f)-1 XORs, >=10x cheaper than random-x sampling, with relation yield equal to a random-x base within 10%.
- **Prediction**: Enumeration 5-15x cheaper in bit ops; yield within +-5%; end-to-end gain <2%.
- **Cheapest test**: GF(2^n), n=19,23,29: B=2^10 for both bases, 10^5 targets each, matched seeds, A/A arm, count bit ops.
- **Falsifier**: Yield differs >10%, or enumeration saving <3x in measured cycles.
- **Lean gap (assumed, not proved)**: That t is primitive in GF(2^n) (pow k != 1 for 0<k<2^n-1), that the field multiplication is associative with cancellation, and that LFSR step cost is hw(f) bit ops. The 10x saving and the yield match are not proved.

### H012 — Factor base restricted to cofactor image subgroup via character test

- **Handbook**: 10.1.4.3 Characteristic functions, 10.1.4.4 Gauss sums  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H012_claim`; theorems: `h012_pigeon`, `H012_pair_fibre_average`, `H012_pair_sum_mem`)
- **Claim**: Drawing F only from H=hE(F_q) (Tr(x)=Tr(a) for h=2, half-trace test for h=4) raises per-tuple m=3 decomposition success by h at fixed |F|; matched rho in H is cheaper by sqrt(h), so net gap closes at most sqrt(h).
- **Prediction**: Yield ratio 2.0+-0.15 (h=2), 4.0+-0.4 (h=4) on GF(2^17..21).
- **Cheapest test**: GF(2^19), a=0 and a=1 Koblitz: filtered vs unfiltered F (|F|=2^6), 2000 targets in H; check halving test against brute-force 2E membership.
- **Falsifier**: Yield ratio 95% CI upper bound <1.2 for h=4, or halving test disagrees with brute force on any point.
- **Lean gap (assumed, not proved)**: That H=hE(F_q) has size N/h and is closed under addition, and that the character or half-trace test decides membership. Pair sums are modelled as a list of labels below M.

### H013 — Valid-point fraction of Frobenius-invariant subspaces (orbit-level variance)

- **Handbook**: 9.1.2 Walsh transform, 9.1.1.2 Trace representation  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H013_claim`; theorems: `H013_valid_eq_repsum`, `H013_claim_holds`, `H013_valid_le_total`, `h013_filter_const`)
- **Claim**: For invariant V the point-existence indicator is orbit-constant, so valid fraction has spread about 0.5*sqrt(n/|V|); best-of-K invariant subspaces give yield (1+2eps)^m above median. Moment identities caution that per-curve spectra are invariant.
- **Prediction**: n=23,d=8..9,m=3: spread 0.12-0.16; best of 2000 fraction >=0.75; yield >=2.5x median; generic V <=1.5x.
- **Cheapest test**: 2000 random invariant subspaces at n=23,d about 8: valid fraction vs relations on 500 targets; regress on fraction^3.
- **Falsifier**: Spread equals iid-coin spread, yield ratio <1.3x, or R^2 <0.5.
- **Lean gap (assumed, not proved)**: That the point-existence indicator is constant on Frobenius orbits of V, that the relation count is at most validCount^m, and the spread of order 0.5*sqrt(n/|V|).

### H014 — Swap hill-climbing on exact S3 yield N(V)

- **Handbook**: 9.1.3 Parameters of Boolean functions, 9.1.1.1 Algebraic normal form  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H014_claim`; theorems: `H014_fibre_le_two`, `H014_total_le`, `h014_two_bound`, `h014_flat_len`)
- **Claim**: N(V) is overdispersed across subspaces; swap hill-climbing finds V with several times median yield in a few hundred evaluations, transferring to fresh targets.
- **Prediction**: Var/Mean >=3 at n=23,d=8; climbed V >=2x median, >=1.8x on fresh targets; <=1.5x at n=31.
- **Cheapest test**: Brute-force N(V) for 2000 random V at n=19..23; 500-step swap climbs from 20 starts; retest on 2000 fresh targets.
- **Falsifier**: Dispersion <1.5, or climbed V <1.2x median on fresh targets.
- **Lean gap (assumed, not proved)**: That S3 solutions in x3 are the fibre of an xor-additive map such as x^2+x with kernel {0,e}, and that V is duplicate-free. Overdispersion of N(V) and hill-climb transfer are not proved.

### H015 — Best-of-T scaling/translate of V by Kloosterman liftable bias

- **Handbook**: 7.1.4 Artin-Schreier hypersurfaces, 6.3.5 Incomplete character sums  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H015_claim`; theorems: `H015_sum_le_len_mul_max`, `H015_rel_antitone`, `H015_cost_improves`, `h015_le_max`)
- **Claim**: Solutions need all x_i liftable, so yield scales as (2*liftFrac)^m; best of T scalings lambda*V (or translates) raises liftFrac by about sqrt(2 ln T/2^d)/2 at unchanged solve cost. Prime-degree lift repulsion is a closed-leaning negative.
- **Prediction**: GF(2^29),d=10,T=2^10: liftFrac about 0.55, m=3 yield ratio about 1.33 (1.2-1.5); at d=20 only about 1.03.
- **Cheapest test**: n=29,d=10: 1000 random V vs best-of-1024; count S3 solutions over 50 x_R, paired.
- **Falsifier**: Yield ratio <1.1, or fails to track (liftFrac ratio)^m within 15%.
- **Lean gap (assumed, not proved)**: That yield scales as (2*liftFrac)^m, that the liftCount list comes from Kloosterman-liftable x over the scalings lambda*V, and that the gain is about sqrt(2 ln T/2^d)/2. The yield ratio c is a natural-number stand-in.

### H016 — Affine-hull dimension of S3(V^3) as subspace selection criterion

- **Handbook**: 6.4.2 Sum-product estimate  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H016_claim`; theorems: `H016_antitone`, `H016_generic_at_full`, `H016_hull_at_least_generic`, `H016_claim_holds`)
- **Claim**: Solution count over V^2 is about |V|^2*2^(-w(V))*[c0 in hull], w the hull dimension (about dim span(V*V)); K-structured V has w<n and high yield for hull-compatible x_R but risks rank collapse in E(K).
- **Prediction**: n=24,k=6: V=K+K*theta, w<=18, yield about 64x generic when c0 in hull; average over x_R unchanged unless hull is steerable.
- **Cheapest test**: n=24,k=6: random vs K-structured V; compute w by elimination, count solutions on 200 (V,x_R) draws, correlate log2 count with n-w; check relation rank mod ell.
- **Falsifier**: Corr <0.8, average yield equal to generic within 5% with no steering, or rank <90% of columns.
- **Lean gap (assumed, not proved)**: That the solution count is |V|^2*2^(-w) times [c0 in hull], that hullDim is about dim span(V*V), and that rank does not collapse in E(K). The formula for h016Rel is assumed.

### H017 — Legendre-biased multiplicative coset selection for prime-field factor bases

- **Handbook**: 7.1.5 Kummer hypersurfaces, 7.3.2 Jacobi sums  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H017_claim`; theorems: `H017_agree_ge_half`, `H017_cost_antitone`, `H017_claim_holds`)
- **Claim**: x3 in F_p iff chi(f(x1))=chi(f(x2)), so yield from coset gH goes as (2 liftFrac)^m; best of T cosets gains (1+sqrt(2 ln T/B))^3, vanishing at production size. Window families are closed; coset selection is untested.
- **Prediction**: p about 2^40,B=2^10,T=2^10: liftFrac about 0.558, gain about 1.39; gain-1 scales as B^(-1/2).
- **Cheapest test**: p about 2^40 curve; 1000 random cosets vs best-of-1024; count S3 solutions by x1,x2 enumeration; scaling over B=2^8..2^14.
- **Falsifier**: Gain <1.1 at B=2^10, or log-log slope of gain-1 outside -0.5+-0.15.
- **Lean gap (assumed, not proved)**: That x3 is in F_p iff chi(f(x1))=chi(f(x2)), the Legendre bias of the coset gH, and the gain (1+sqrt(2 ln T/B))^3. The best-of-T statement reuses the H015 abstract max-versus-average lemma.

### H018 — Rotation-closed Hamming-ball necklace factor base for primitive-root n

- **Handbook**: 5.2.1 Normal bases, 5.3.1 Low complexity normal bases, 14.9.2 Weights of multiples  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H018_claim`; theorems: `H018_wt_rot`, `H018_ball_closed`, `h018_fixed_const`, `h018_wt_const`, `H018_fixed_weight`)
- **Claim**: Where no invariant subspace exists, W_w={wt_ONB<=w} is Frobenius-closed with necklace storage |W_w|/n and popcount membership; yield equals a random closed set within 5%. Encyclopedia C6 rejected it as storage-only, so the claim is a cost, not yield, gain.
- **Prediction**: Yield ratio 0.95-1.05; necklace count exact by Burnside; membership >=1.3x faster than hash at 2^28; end-to-end <=1.1x.
- **Cheapest test**: n=29, |W_w| about 2^12-2^17: m=2 collection on a Koblitz toy vs random closed set and non-stable set of equal size; microbenchmark membership.
- **Falsifier**: Yield ratio outside [0.9,1.1], orbit count off Burnside, or popcount not faster than hashing.
- **Lean gap (assumed, not proved)**: That Frobenius acts as cyclic rotation in the ONB. Rot-by-1 fixed points are proved to be 0 or all-ones for any n. The prime-n orbit structure of rot^k (exact Burnside necklace count), the popcount speedup and the yield match are not proved.
- Merged from pool keys: P5-1

## decomposition (25)

### H019 — Groebner-fan bi-weight order for the bilinear S3 subspace system

- **Handbook**: 17.1.4.2 Groebner fan parameter estimation  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H019_claim`; theorems: `H019_zero_left`, `H019_kernel`, `H019_len_decomp`, `H019_toy_count`)
- **Claim**: On bilinear S3 with |V|=|W|=2^m, m=8..12, the best fan-selected bi-weight order cuts the largest F4 matrix >=2x vs grevlex, yet F4 stays above the 2^m lookup baseline.
- **Prediction**: Matrix ratio 0.3-0.7, shrinking with m; F4 time >=10x the lookup baseline at m>=10.
- **Cheapest test**: n=20, 50 targets: msolve/F4 under grevlex, (1^10,0^10) refined by grevlex, and 5 random fan weights; compare matrix size, dreg, time.
- **Falsifier**: Best bi-weight matrix >=0.8x grevlex, or loses a paired sign test (p<0.05).
- **Lean gap (assumed, not proved)**: That S3 restricted to V x W is xor-bilinear (additivity of squaring in char 2). Groebner-fan matrix sizes, F4 cost and the lookup-baseline comparison are not modelled.

### H020 — Canalyzing-depth pre-sieve for the post-trace decomposition predicate

- **Handbook**: 17.1.4.1 Minimal-sets algorithm, 17.1.6.1 Nested canalyzing functions  ·  **Prior art**: untried  ·  **Lean**: proved (`H020_claim`; theorems: `H020_presieve_sound`, `H020_detset_mono`, `H020_canal_is_detset`, `H020_parity3_no_canal`, `H020_and3_canal`, `H020_claim_holds`)
- **Claim**: P(a)=[x2 in W] and the S3 bit components have canalyzing depth 0 for >=99% of targets, minimal determining set >=0.9m, so no m/4-bit pre-sieve discards >5% beyond the trace test. Expected negative; closes the route.
- **Prediction**: Depth 0 in >99%; determining set 0.9-1.0m; pre-sieve discards 0-3%.
- **Cheapest test**: n=18,m=9, 500 targets: enumerate P, brute-force subsets up to 3 for canalyzing variables; random-function negative control.
- **Falsifier**: Determining set <=m/4 for >5% of targets, or pre-sieve discards >=10% losslessly.
- **Lean gap (assumed, not proved)**: That the post-trace decomposition predicate P(a) and the S3 bit components behave like the toy predicates, with canalyzing depth 0 for at least 99% of targets and determining set at least 0.9m. Only soundness and monotonicity of the pre-sieve and two 3-bit instance checks are proved.

### H021 — Frobenius-linear decision test for 2-point decomposition on interval bases

- **Handbook**: 16.7.2 Polynomial operations arithmetic, 16.3.3.12 Linearization  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H021_claim`; theorems: `H021_sound`, `H021_relCost_le`, `H021_claim_proved`, `H021_instance_n31_d9`)
- **Claim**: For V=span{1,..,t^(d-1)}, 3d-1<=n, S3 is F2-linear in bits of (pi,s) with pi reduction-free; deciding x(R)=x1+x2 costs one n x (3d-1) elimination, not 2^d, returning identical decompositions.
- **Prediction**: Per-relation cost 2^(n-2d)*n^3/64; total about 2^(2n/3) at d=n/3; >=100x speedup at n=31,d=9.
- **Cheapest test**: Koblitz n=31 (also 23,37), d=9: 2^16 targets, compare decomposition sets and time vs enumeration; fit log2 cost slope vs n.
- **Falsifier**: Any missed decomposition, speedup <10x at n=31,d=9, or slope not within 20% of 1/3.
- **Lean gap (assumed, not proved)**: S3 is F2-linear in the bits of (pi,s) on interval bases with 3d-1<=n, so the n x (3d-1) elimination decides exactly h021Decomposes; taken as the hypothesis hlin. The 2^(n-2d)*n^3/64 cost formula and the speedup are not derived.

### H022 — Block-multigraded Macaulay matrices for Weil-restricted S_{m+1}

- **Handbook**: 16.3.3.12 Direct attacks with polynomial solvers, 16.3.3.8 Rank structure  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H022_claim`; theorems: `h022Mono_pos`, `h022Mono_le_succ`, `h022Mono_mono`, `H022_bitDeg_le_two`, `H022_claim_proved`)
- **Claim**: Bit-degree popcount(e) per block makes the system multihomogeneous; at the first-fall multidegree the multigraded Macaulay matrix has >=10x fewer columns than total degree at m=3. m=2 bidegree was measured column-heavy.
- **Prediction**: Column ratio >=10 at d=7,n=21, growing with d; first fall at multidegree (1,1,1) or (2,1,1).
- **Cheapest test**: Build sparse F2 Macaulay matrices for m=3, n=21, d=7 in both gradings to degree 3; compare columns and rank at recovery.
- **Falsifier**: Column ratio <2 at first fall, or multigraded rank fails to recover the planted decomposition at smaller size.
- **Lean gap (assumed, not proved)**: Macaulay columns are modelled by squarefree monomial counts, not by the actual sparse matrix. The first-fall degree of the total-degree system (assumed at least 5) and the first-fall multidegree (1,1,1) are not derived. Matrix rank at recovery is not modelled.

### H023 — One-bit trace criterion as a dead-target sieve for 2-decompositions

- **Handbook**: 16.3.3.1 Linearization equations, 16.3.2.4 Frobenius-additive structure, 9.1.1.2 Trace representation  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H023_claim`; theorems: `H023_filter_preserved`, `H023_live_le`, `H023_partition`, `H023_claim_proved`, `H023_strict_improvement`)
- **Claim**: For V in ker Tr, targets with Tr(b/z^2)=1 (equivalently Tr(x_R)!=(m-1)Tr(a)) have no V-decomposition; live targets carry 2x yield, halving solves per relation. Leads record this as closed (<=0.2 bits, degree-2 fall); remaining angle is the m=2 loop savings.
- **Prediction**: Dead fraction 50+-2%, zero counterexamples, live mean 2.0x, additions ratio 0.50+-0.03.
- **Cheapest test**: n=17,19, b=1 and random b, k=8 subspaces inside/outside ker Tr: enumerate x1, tabulate counts against Tr(b/z^2).
- **Falsifier**: Any decomposition of a Tr=1 target for V in ker Tr, dead fraction outside 0.48-0.52, or live mean not near 2x.
- **Lean gap (assumed, not proved)**: The hypothesis h_dead: for V in ker Tr, Tr(x_R) != (m-1)Tr(a) implies no V-decomposition. The 50 percent dead fraction and the 2x live yield are not derived.
- Merged from pool keys: P12-0

### H024 — Lifted (s,p) enumeration with half-trace bit-GEMM tables

- **Handbook**: 16.3.2.5 Oil and vinegar, 16.3.3.2 Critical bilinear relations  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H024_claim`; theorems: `h024_decode_lifted`, `H024_claim_proved`, `H024_ratio`, `H024_xor_cancel`)
- **Claim**: For fixed z, S3 is affine in (s,p); enumerating s in V with precomputed half-trace and 1/s^2 tables uses <=0.6 field multiplications and no inversion per candidate vs >=4, returning the identical relation set.
- **Prediction**: Identical multiset; 0.5+-0.1 mults per candidate; 3-6x faster at n=45,k=15, <2x once tables exceed L2.
- **Cheapest test**: n=33 (m=2,k=16) and n=45 (m=3,k=15): count mults and time both loops over 1000 targets; compare relation sets.
- **Falsifier**: Relation sets differ, gain <1.5x at k<=18, or table traffic erases the saving.
- **Lean gap (assumed, not proved)**: The multiplication counts (at most 0.6 against at least 4 per candidate) are constants, not derived from half-trace and 1/s^2 table lookups. That S3 is affine in (s,p) for fixed z and that a lifted witness corresponds to Dec is not modelled. Only the pure (s,x1) re-indexing bijection on XOR-closed lists is proved, so relation-set equality holds up to the swap.

### H025 — Optimal normal basis coordinates to minimise monomials of Weil-restricted S3

- **Handbook**: 16.3.1.1 Bipolar construction, 16.3.1.3 Isomorphism of polynomials  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H025_claim`; theorems: `H025_count_invariant`, `H025_cost_scaling`, `H025_claim_proved`)
- **Claim**: Choosing S,T as consecutive ONB elements gives >=10x fewer monomials and >=3x sparser Macaulay matrices than a random basis pair at equal degree of regularity, lowering F4 time.
- **Prediction**: Monomial ratio about n/2 (10-30x at n 30-60); F4 time 2-5x; dreg unchanged.
- **Cheapest test**: n=29 (type II) and n=28 (type I): k=9 subspace S3 in random vs ONB basis; count ANF monomials; run F4 with fixed hybrid guesses.
- **Falsifier**: Monomial ratio <2 after restriction to V, or F4 time not improved despite density.
- **Lean gap (assumed, not proved)**: The ONB basis change is modelled only as an abstract left-invertible map f with left inverse g on Nat points. The monomial density ratio (monos' * c <= monos), the F4 cost proportional to monomials * columns, and the dreg-unchanged claim are hypotheses or model choices.

### H026 — Gray-code Artin-Schreier enumeration over the hyperplane Tr(s)=Tr(b/r^2)

- **Handbook**: 15.1.2.4 Trace codes, 15.1.2.1 Standard array decoding, 15.1.2.3 Reed-Muller codes  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H026_claim`; theorems: `H026_claim_proved`, `H026_identity_gf8`, `H026_iff_gf8`, `H026_gray_one_bit`, `H026_hyperplane_half`)
- **Claim**: With s=x1+x2, w^2+rw+r^2s^2+b=0 is solvable iff Tr(s)=Tr(b/r^2); Gray-code walk over V cap hyperplane finds all m=2 decompositions with >=5x fewer multiplications per relation than hash-lookup of x(R-P), same relation set.
- **Prediction**: Multiplication ratio 8-12x, wall-clock 3-6x (1/s^2 table memory-bound).
- **Cheapest test**: n=31,l=15, 10^4 targets: count multiplications and cache-missing reads in both; check set equality; repeat n=41,l=20.
- **Falsifier**: Relation sets differ, multiplication ratio <2, or wall-clock ratio <1.
- **Lean gap (assumed, not proved)**: The Artin-Schreier identity is checked by decide only over GF(8), not for general n such as 31 or 41. Solvability iff Tr(s)=Tr(b/r^2) (hypothesis hsolv), the trace map itself, and the multiplication and cache-miss counts are not modelled. The Gray walk is stated only as V.filter hyp.

### H027 — Rank profile of Weil-restricted S3 components as F4 degree predictor (invariant vs random V)

- **Handbook**: 15.1.2.3 Reed-Muller codes, 15.1.2.4 Trace codes, 15.1.3 Cyclic codes  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H027_claim`; theorems: `H027_claim_proved`, `h027Ins_length`, `h027Insert_length_le`, `h027Rank_fold_le`, `H027_rank_le_rows`, `H027_rank_instances_n7`)
- **Claim**: For m=2, n=23..31, l=n/2, Frobenius-invariant V gives F4 solving degree >=1 below random V of equal dimension, predicted by the dimension of the low-rank component subspace.
- **Prediction**: Degree drops 4->3 in >=60% at n=31,l=15; low-rank dimension >=3 higher; time 1.5-3x lower.
- **Cheapest test**: n=31 and n=21: 50 targets, rank profile of n component forms, F4 (msolve/M4GB) degree and time; invariant V vs 20 random V.
- **Falsifier**: Paired bootstrap CI of degree difference contains 0, or Spearman(low-rank dim, degree) <0.4.
- **Lean gap (assumed, not proved)**: The mechanism hypothesis (low-rank-dimension excess of at least 3 implies an F4 degree drop of at least 1) and the 60 percent dimension-excess rate are assumptions. The Weil-restricted component forms, F4 degrees and basis-change invariance of rank are not modelled; rank is only bounded by the row count and checked on n=7 examples.

### H028 — Determinantal elliptic-normal-curve system keeping y

- **Handbook**: 14.4.5 k-Arcs, 14.4.1 Projective and affine spaces  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H028_claim`; theorems: `H028_var_balance`, `H028_time_ratio_implies_faster`, `H028_balance_m3_n21`)
- **Claim**: The det[phi_j(P_i)]=0 system on |kO| keeping y, with Weil-restricted x only, has lower F4/F5 degree of regularity and solve time than S_{m+1} at equal V for m=3,4.
- **Prediction**: dreg lower by >=1 at m=3; time ratio 0.3-0.8 for n<=25, vanishing at n>=40.
- **Cheapest test**: E over GF(2^21), dim V=7, m=3: build both systems for 200 targets, run same F4, record dreg, matrix size, time, matching projected solutions.
- **Falsifier**: dreg not lower, median time ratio >=1, or solution sets differ.
- **Lean gap (assumed, not proved)**: The hypothesis hdet (sum of logs zero iff the determinant vanishes on |kO|) is not stated as a theorem. The dreg drop, time ratio and solution-set equality are measured outcomes held in a record, not derived. Only the variable count arithmetic m*(n/m+n) = (m+1)*n is proved.

### H029 — Rank-count law as null model for S3 pair matrices

- **Handbook**: 13.2.1 Matrices of specified rank, 13.3.5 Orthogonal groups, characteristic two  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H029_claim`; theorems: `H029_coset`, `H029_claim_proved`, `H029_fibres_instance`)
- **Claim**: S3 is F2-affine in x1 for fixed (x2,x3), so solution sets are cosets of a kernel; some V (invariant, trace-orthogonal) have rank-deficient M(x2,x3) at >=2x the uniform-matrix rate, raising relations per pair.
- **Prediction**: Random V within 5% of 2^-(n-m+1); best of 200 structured V gives 1.5-4x excess.
- **Cheapest test**: n=19,m=8 and n=23,m=9: 100 subspaces, all 2^16 pairs, bit-packed rank, histogram kernel dimension vs closed-form rank-count law.
- **Falsifier**: All structured V within 10% of null (bootstrap CI contains 1).
- **Lean gap (assumed, not proved)**: That S3 is F2-affine in x1 (the additivity hypothesis hadd) and that a structured V has an at least 2x excess of rank-deficient pair matrices are assumed. The coset result is proved only as an iff, and the cardinality of the kernel coset is not proved. The closed-form rank-count law is not formalised.

### H030 — Fill-triggered M4RI/PLE backend for Macaulay matrices (matched-degree test)

- **Handbook**: 13.4.1.1 Tiny finite fields, 13.4.2.2 PLE decomposition  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H030_claim`; theorems: `H030_m4ri_le_schoolbook`, `H030_trigger_mono`, `H030_instance`)
- **Claim**: Four-Russians PLE is already landed and positive; the open part is a fill trigger (>15% after 30% pivots) on binary Semaev Macaulay matrices n=19..29, giving >=2x fewer bit ops than sparse F4.
- **Prediction**: 2-5x for >=20k x 20k, <1x below 2k x 2k; decomposition total -20-40% at n=29.
- **Cheapest test**: Dump 10 Macaulay matrices at 5k..40k columns, run both backends on the same host, compare time and word-XORs, confirm equal rank.
- **Falsifier**: Speedup <1.2x at 20k x 20k, or fill stays <5%.
- **Lean gap (assumed, not proved)**: The M4RI cost model (p/k blocks, each 2^k*c+r*c) and the schoolbook model p*r*c are idealised dense counts. Sparse-F4 cost, fill dynamics, the 15 percent after 30 percent trigger actually firing, and the measured 2x speedup at 20k x 20k are not derived. H030_claim itself is a stated measurement prediction and is not proved.

### H031 — Halving-trace character appended as an explicit linear equation in the solver

- **Handbook**: 12.2.6 Torsion subgroup, 12.2.5 Twists  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H031_claim`; theorems: `H031_nsmul_psi`, `H031_combo_psi`, `H031_filter_keeps_valid`, `H031_claim_holds`)
- **Claim**: Adding psi(P)=Tr(x_P)+Tr(a) sum constraint up front and eliminating one bit removes no true decomposition and cuts F4/hybrid time at fixed (n,l,m); fall-degree records suggest F4 gets it at degree 2.
- **Prediction**: Zero decompositions lost; hybrid time ratio 0.5-0.7; dreg change <=1.
- **Cheapest test**: n=31,l=10,m=3, 200 targets: solve with/without the equation (msolve or hybrid guess loop); compare solution sets; brute-force check.
- **Falsifier**: Any decomposition violating the equation, time ratio >0.9, or F4 derives it below d_reg.
- **Lean gap (assumed, not proved)**: That the halving-trace character psi(P)=Tr(x_P)+Tr(a) is a homomorphism to Z/2 on the curve group (the h031Hom record), and that F4/hybrid time ratio and d_reg behave as predicted.

### H032 — Affine shift/scale and Montgomery-model scan to minimise S_m monomials

- **Handbook**: 12.3.7 Montgomery curves, 12.3.8 Twisted Edwards, 12.3.5 Short Weierstrass  ·  **Prior art**: untried  ·  **Lean**: proved (`H032_claim`; theorems: `H032_smoothCount_invariant`, `H032_exists_min`, `H032_min_le_origin`, `H032_claim_holds`)
- **Claim**: x->u(x-c) with c,u in the subfield keeps the base intact; nnz(S4) and F4 matrix size vary >25% over (c,u) and 2-isogenous Montgomery models, and short Weierstrass is not the minimum.
- **Prediction**: Montgomery S4 >=25% fewer monomials; min over c <=0.75x nnz at c=0; F4 time 0.8-0.9.
- **Cheapest test**: Build S4 over F_p (p=1009) in each form, scan (c,u), record nnz; msolve on Weil-restricted n=3,m=3 for 5 extremal (c,u).
- **Falsifier**: nnz spread <5%, or F4 time ratio >0.95.
- **Lean gap (assumed, not proved)**: That x->u(x-c) and 2-isogenous Montgomery models are bijections of the decomposition solution set preserving the base (the hypothesis g(f a)=a), and the actual nnz(S4) / F4 time values over the scan.

### H033 — Support and Newton-polytope structure of GF(2)-defined Koblitz S_4, S_5

- **Handbook**: 11.5.2.2 Polytope indecomposability, 11.5.2.3 Sparse bivariate Hensel lifting  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H033_claim`; theorems: `H033_S3_sym`, `H033_S3_nodup`, `H033_S3_box`, `H033_S3_density`, `H033_claim_holds`)
- **Claim**: Over GF(2) in e-coordinates, S_4,S_5 support fills <=30% of the weighted-dense set (Frobenius-closed exponent sets) with Minkowski-indecomposable polytope; density falls with m, giving sparse Macaulay rows.
- **Prediction**: S_4 density 15-40%; S_5 5-25%; polytope indecomposable at m=3,4,5.
- **Cheapest test**: Compute S_3 by hand, S_4,S_5 by resultant over GF(2); count monomials vs weighted-dense; F4 sparse vs dense row storage on S_4 toys.
- **Falsifier**: S_5 density >=60%, or a nontrivial factorization of some S_m.
- **Lean gap (assumed, not proved)**: The actual supports of S_4, S_5 over GF(2) (resultant computation), Frobenius-closure of those exponent sets, the weighted-dense reference set, and Minkowski indecomposability of the Newton polytopes (Indec is an abstract predicate).

### H034 — Linearized subspace-polynomial test L_V mod N for root membership

- **Handbook**: 11.3.3 Rabin irreducibility test, 11.4 Univariate factorization  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H034_claim`; theorems: `H034_mem_of_prod_zero`, `H034_prod_zero_of_mem`, `H034_roots_in_V`, `H034_claim_holds`)
- **Claim**: For degree d<=16 completion polynomial N, L_V mod N = 0 decides all roots in V with about k Frobenius powers, >=2x fewer multiplications than distinct-degree plus equal-degree root finding, identical decisions.
- **Prediction**: n=48,k=16,d=8: multiplication ratio 2.5-4.
- **Cheapest test**: GF(2^n), n=24..48, 10^5 random N of degree 4-16 with 1% planted V-roots; compare decisions and counted multiplications.
- **Falsifier**: Any differing decision, or counted multiplications not lower by 1.5x.
- **Lean gap (assumed, not proved)**: That GF(2^n) is an integral domain (h034Dom), that N | L_V yields L_V vanishing on roots of N, that L_V vanishes exactly on V, and the 1.5x+ multiplication-count advantage over distinct/equal-degree factoring.

### H035 — Canonical sign bit Tr(y/x) resolving x-only Semaev solutions

- **Handbook**: 11.1.9.2 Half-trace, 11.1.6.2 Squaring in characteristic two  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H035_claim`; theorems: `H035_sign_neg`, `H035_flip_all`, `H035_trials_gt_one`, `H035_claim_holds`)
- **Claim**: For odd n, s(P)=Tr(y/x) is a negation-sign bit and sum s(P_i) equals a closed form in (x1,x2,x3) (one sqrt, trace, inversion), selecting the valid sign class without 2^(m-1) trial additions.
- **Prediction**: Closed form matches brute force exactly; sign-resolution ops fall to about one inversion plus one half-trace; total change <5%.
- **Cheapest test**: 5 toy curves, n in {11,...,19}: all zero-sum triples; compare sum Tr(y_i/x_i) with closed form; time vs brute-force addition for m=3,4.
- **Falsifier**: Any triple disagreeing with the true sign class, or sign resolution <2% of decomposition time.
- **Lean gap (assumed, not proved)**: Field trace additivity and Tr(1)=1 for odd n (h035Tr record), negation being (x,y+x) on the binary curve, and the closed form for sum s(P_i) in (x1,x2,x3).

### H036 — Extraneous diagonal factor of S_4(x,x,y,z)

- **Handbook**: 10.5.3 Degree growth  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H036_claim`; theorems: `H036_deg_factor`, `H036_degree_drop`, `H036_quarter_drop`, `H036_S3_degree2`, `H036_diag_S3`, `H036_claim_holds`)
- **Claim**: S_4(x,x,X3,X4) contains an extraneous square factor from the degenerate P+P=O branch; its squarefree part has lower degree and removing it lowers F4 dreg by >=1 for some (m,l).
- **Prediction**: Squarefree degree about 25% lower; F4 time -20-50% on diagonal subsystem; no effect off-diagonal.
- **Cheapest test**: Singular over GF(2^k), k=7..13: build S_3,S_4, substitute x1=x2, factor; F4 on diagonal Weil-restricted systems with/without the factor.
- **Falsifier**: Substituted polynomial squarefree of full degree, or time and dreg unchanged within A/A.
- **Lean gap (assumed, not proved)**: That S_4(x,x,y,z) actually factors as f^2*g with deg f>0 from the degenerate P+P=O branch (hypothesis s = f*f*g), and the F4 d_reg/time effect of removing the factor.

### H037 — Sparse relative defining polynomial for Weil restriction on composite n

- **Handbook**: 11.1.3.2 Modular reduction, 11.1.1.2 Extension field generation  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H037_claim`; theorems: `H037_dreg_invariant`, `H037_time_le`, `H037_claim_holds`)
- **Claim**: On composite n=l*m (55,57,91,93,95), a sparse relative defining polynomial lowers F4 time by a constant factor while dreg stays identical to a dense choice.
- **Prediction**: dreg identical; time ratio dense/sparse 1.2-2x at n=57,l=19,m=3; no exponent change.
- **Cheapest test**: n=55 and n=57: restricted S_3 with 5 random irreducibles and the best sparse one; record monomials, dreg, F4 time, randomised order, A/A.
- **Falsifier**: Runtime ratio within A/A noise, or dreg differing across choices.
- **Lean gap (assumed, not proved)**: That the degree-d Macaulay predicates of the dense and sparse relative-polynomial systems coincide (invertible linear substitution invariance), and the measured constants cs<=cd with the 1.2-2x time ratio.

### H038 — Dembowski-Ostrom rank spectrum of the fixed-s S_3 system (MinRank screen)

- **Handbook**: 9.5.5 Planar DO polynomials, 10.1.4.2 Nonlinearity  ·  **Prior art**: tried-open  ·  **Lean**: proved (`H038_claim`; theorems: `H038_expansion_diff`, `H038_expansion_mod2`, `H038_exponents_pow2`, `H038_low_rank_exists`, `H038_claim_holds`)
- **Claim**: With x2=x1+s, S_3 is a DO quadratic map; for structured V (subfield-adjacent, Frobenius-stable) the min component rank is >=2 below the random-map null, giving cheaper per-s rank-aware solves than generic F4 hybrid. Open lead, unrun.
- **Prediction**: n=21,d=7: random V matches null (KS p>0.05); structured V min rank lower by >=2 in >=30% of cases.
- **Cheapest test**: n=21,d=7: all 2^21 mu, 14x14 bilinear form ranks; histogram for random V, structured V, 200 random quadratic maps.
- **Falsifier**: No V family differs from null at 5%, or F4 dreg unchanged when low-rank components are added.
- **Lean gap (assumed, not proved)**: Reduction of the Z-identity mod 2 to GF(2^n) (char-2 expansion), the S_3 form (x1x2+x1x3+x2x3)^2+x1x2x3+b for the binary curve, the rank bound <=2d, and the empirical rank spectrum vs random-map null (>=30% structured cases).

### H039 — Heavy Walsh coefficient of the decomposability indicator as target prefilter

- **Handbook**: 9.1.2 Walsh transform, 9.3.2 Bent functions  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H039_claim`; theorems: `H039_list_sum_le`, `H039_floor`, `H039_parseval_instance`, `H039_claim_holds`)
- **Claim**: The decomposability indicator D of a subspace base has a normalised Walsh coefficient several times the random null near V-perp-related u; targets selected by that parity decompose more often. Trace and learned prefilters were null; this tests the full spectrum.
- **Prediction**: Max coefficient >=3x null on >=70% of curves; favoured-class success >=1.2x; else <=1.5x (null).
- **Cheapest test**: n=20: exact D on all targets, FWHT; compare to 200 random equal-density sets and the trace-parity positive control.
- **Falsifier**: Max within 1.5x null on >=70% of curves, or favoured-class gain <1.1x.
- **Lean gap (assumed, not proved)**: Parseval sum_u W(u)^2 = N|D| from character orthogonality on F_2^n (taken as hypothesis hP; only verified by decide on one n=3 instance), and the actual decomposability indicator D of a curve's subspace base.

### H040 — Low-degree annihilators of the decomposability indicator

- **Handbook**: 9.1.6.3 Optimal algebraic immunity  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H040_claim`; theorems: `H040_mon_succ_le`, `H040_mon_mono`, `H040_instance14`, `H040_instance16`, `H040_annihilator_of_count`, `H040_count_persists`, `H040_claim_holds`)
- **Claim**: For subspace or invariant V at toy scale, algebraic immunity of D is >=2 below ceil(n/2), and the annihilator test rejects a constant fraction of undecomposable targets; degree e may track F4 dreg.
- **Prediction**: AI(D)<=ceil(n/2)-2 for >=80% of (curve,V); rejects >=20% of undecomposable targets; random sets AI >= ceil(n/2)-1.
- **Cheapest test**: Exhaustive D for n=14..18; find AI by F2 linear algebra on monomials of degree <=e; 100 random equal-density sets; compare e with F4 dreg.
- **Falsifier**: AI within 1 of ceil(n/2) on >=80% of cases, or rejection <5%.
- **Lean gap (assumed, not proved)**: The GF(2) linear-algebra step that more degree-<=e monomials than |supp D| yields a nonzero annihilator (hypothesis hlin), the identity sum_{i<=e}C(n,i)=2^n at e=n, the actual |supp D| of curve indicators, and the rejection-rate/F4 d_reg link.

### H041 — Trace-form isotropic block pairs giving free linear equations

- **Handbook**: 7.2.3 Trace forms  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H041_claim`; theorems: `H041_reduction_factor`, `H041_strict`, `H041_claim_holds`, `H041_mono`)
- **Claim**: S3 coordinates are Tr(mu s t) bilinear forms; choosing V1 in (mu V2)^perp for a subspace M of mu kills the bilinear part on dim M coordinates, so first-fall degree drops >=2 and F4 time >=4x vs random pairs. MinRank family is open.
- **Prediction**: n=26,d1=d2=13: random dim M about 0; isotropic pairs 4-8; F4 ratio about 5x (2x-30x).
- **Cheapest test**: n=26: random and isotropic V1,V2; rank of 26 Gram matrices; msolve/F4 on 30 x_R each with matched solution counts.
- **Falsifier**: dim M no larger than random, or F4 ratio <1.5x.
- **Lean gap (assumed, not proved)**: That the isotropic choice V1 in (mu V2)^perp actually yields k = dim M independent affine equations (Gram-matrix rank over F_2 for the trace forms) and that F4 time scales with the enumeration bound. The Lean file proves only the 2^u -> 2^(u-k) arithmetic under k <= u.

### H042 — Exact character-sum yield ranking of cyclic-code subspaces

- **Handbook**: 6.2.2 Additive character sums, 6.2.4 Generic estimates, 6.3.3.3 Dual BCH distance  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H042_claim`; theorems: `H042_orthogonality_4`, `H042_indicator_expansion_4`, `H042_ratio_needs_eps`)
- **Claim**: Frobenius-invariant subspaces of equal dimension m about n/3 on one Koblitz curve have yield N(V) differing by >=3 sigma_binomial; top decile is >=1.2x median and the ranking transfers between a=0 and a=1 curves. Coset indicators were random-level.
- **Prediction**: n=35: best/median 1.15-1.6; Spearman across curves >0.5.
- **Cheapest test**: n=35 (or 21,45): all divisors g with dim 10-13; exact N(V) on 3 Koblitz toys; ranked table with binomial intervals; A/A split.
- **Falsifier**: All N(V)/E within 2 sigma, or cross-curve Spearman <0.2.
- **Lean gap (assumed, not proved)**: The Weil/binomial sigma for the cyclic-code subspace yields on Koblitz curves, the exact N(V) as a character sum over the curve, and the cross-curve (a=0 vs a=1) rank transfer. Orthogonality and indicator expansion are checked only by decide on 4-bit strings.

### H043 — Sparse Gauss-period normal basis for the restricted Semaev system

- **Handbook**: 5.3.2 Gauss periods, 5.3.1 Optimal normal bases  ·  **Prior art**: tried-open  ·  **Lean**: proved (`H043_claim`; theorems: `H043_complexity_d5`, `H043_complexity_d7`, `H043_terms_le_two`, `H043_cx_le`)
- **Claim**: In a type-II ONB the multiplication tensor has about 2d-1 nonzeros, so restricted S3 has <=0.5x monomials and F4 time falls, with dreg unchanged; G3 sparse-ONB hypothesis is open and unmeasured.
- **Prediction**: Monomial ratio 0.3-0.6 at d=5..7,q=2^5; F4 time ratio 0.4-0.9.
- **Cheapest test**: d=5,q=2^5 (n=25): 3d-variable S3 in polynomial vs ONB basis, same F4 and seeds, interleaved, 20 repeats.
- **Falsifier**: Monomial ratio >0.8 or F4 time ratio >1.0 at d=5 and d=7.
- **Lean gap (assumed, not proved)**: That the abstract fold model (b_1*b_j = b_{j+1}+b_{j-1}, zero index drops) is the real type-II ONB multiplication tensor for F_{2^d} with 2d+1 prime and 2 primitive, the general equality complexity = 2d-1 (only decided for d=5,7; the general upper bound 2d is proved), and the monomial and F4 time ratios of the restricted Semaev system.

## relation-collection (12)

### H044 — Order-6 automorphism-orbit quotient for j=0 curves, q=1 mod 3

- **Handbook**: 16.6.5 Endomorphisms, 16.6.4 Restriction of scalars  ·  **Prior art**: tried-open  ·  **Lean**: proved (`H044_claim`; theorems: `H044_twisted_consistent`, `H044_order6`, `H044_ratio`, `H044_claim_holds`, `H044_total_improves`)
- **Claim**: For y^2=x^3+b, S_m is weighted-homogeneous so F_q-subspace bases are closed under x->wx and negation; quotienting by order 6 needs B/6 relations vs B/2, cutting relations and LA size 3x. Matches unrun DGM-01 ablation.
- **Prediction**: q=97,n=3: relations ratio (negation-only)/(order-6) = 3.0+-10%; dreg not increased.
- **Cheapest test**: Existing Diem-style IC on a j=0 toy twice (negation-only vs order-6 reps), same V; compare relations to full rank.
- **Falsifier**: Ratio <2.5, or lambda-twisted signs make logs inconsistent mod l.
- **Lean gap (assumed, not proved)**: That for y^2=x^3+b with q = 1 mod 3 the Semaev summation basis is closed under x -> wx and negation, the automorphism of order 6 acts on logs by multiplication by lam with lam^6 = 1 mod n (taken as a hypothesis), and the quotiented relations remain independent (full rank) with dreg not increased.

### H045 — Stop collection at orientability threshold; target-only left-kernel extraction

- **Handbook**: 15.3 LDPC and Gallager codes, 15.5.1 Tornado codes, 17.3.8 Coding over networks, 15.5.2 LT and fountain codes  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H045_claim`; theorems: `H045_extract`, `H045_claim_holds`, `H045_determined_mono`)
- **Claim**: t=log_P Q is determined at the first left-kernel vector y of the factor-base part with y.b nonzero, at N/B about 0.918 (m=3), 0.5 (m=2), below B+1; online echelon stopping at target-determined (N_det vs N_full) is the same rule. Solver contract exists, N_det unmeasured.
- **Prediction**: N_dep/B = 0.92+-0.03 (m=3), about 0.52 (m=2); about 8% saving for m=3, about 2x for m=2.
- **Cheapest test**: Koblitz n=23..29, m=3, Frobenius-orbit columns: prefix ranks mod ell on real relations; first N with rank<N and y.b!=0; check recovered t; 20 seeds.
- **Falsifier**: Median N_dep/B outside [0.88,0.96], wrong t, or left-kernel solve costs more than relations saved.
- **Lean gap (assumed, not proved)**: The hypothesis (Ya + Yb*x) = 0 mod n, i.e. summing the relations along a left-kernel vector (swap of the double sum over rows and columns of the factor-base logs), that real Koblitz orbit relations reach a dependency at N/B about 0.92 (m=3), and that left-kernel solving costs less than the relations saved.
- Merged from pool keys: P1-5, P3-7

### H046 — Cayley-graph walk candidate generation with lambda_2-selected generators

- **Handbook**: 14.10.3 Expander graphs, 14.10.4 Cayley graphs  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H046_claim`; theorems: `H046_walk_sound`, `H046_claim_holds`, `H046_ops_per_relation`)
- **Claim**: Walking R_{i+1}=R_i+s_j on Cay(Z_N,S) with r=8-16 generators yields relations per candidate equal to iid (a,b) within 3% at >=5x fewer group-op equivalents per relation for m=2; no gain if the baseline already walks.
- **Prediction**: Yield ratio 0.97-1.03; lag-1 autocorrelation <0.01; duplicates <0.1% over 10^7 steps; ops 5-9x fewer.
- **Cheapest test**: Prime-field curve of order about 2^24: iid control, walks r=4,8,16 with random S, r=16 with lambda_2-minimised S; count relations, rank at R=B+20, ops.
- **Falsifier**: Yield ratio <0.9, rank deficient in >1% of runs, or autocorrelation >0.05 at r>=8.
- **Lean gap (assumed, not proved)**: The expander mixing property (yield ratio within 3% of iid, lag-1 autocorrelation, duplicate rate) from lambda_2 of Cay(Z_N,S), encoded only as the hypothesis h046Mixing, and the group-op cost model (iid candidate at least 6 ops versus 1 mixed addition).

### H047 — Koblitz tau-adic Gray-code enumeration with a_0=1 orbit-duplicate filter

- **Handbook**: 14.8.5 Digital (t,s)-sequences, 14.8.6 Gray-code enumeration  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H047_claim`; theorems: `H047_gray_injective_6`, `H047_gray_onebit_8`, `H047_gray_closed_8`, `H047_filter_half_6`, `H047_gray_cost`)
- **Claim**: Gray-code enumeration of tau-adic strings with a_0=1 costs one mixed addition per candidate, orbit-duplicate rate 0 (50% unfiltered), and yield equal to iid within 3%.
- **Prediction**: Duplicates 50+-1% unfiltered at k=20, 0% filtered; yield ratio 0.97-1.03; about 1 addition vs 2n/3 per candidate.
- **Cheapest test**: Koblitz a=1, n=17,19: enumerate 2^20 strings both ways; count distinct orbits and m=2 relations over a stable base; compare iid tau-adic digits.
- **Falsifier**: Duplicates >1% after filter, yield ratio outside [0.9,1.1], or rank growth lower by >1%.
- **Lean gap (assumed, not proved)**: The general-k statement (gray injective, one-bit steps, closed on 2^k, half of strings with a_0=1) is only decided for k=6 or 8; the identification of the tau-adic orbit-duplicate structure (a_0=1 removes Frobenius duplicates) and the incremental point update equal to the closed form tau-adic expansion on a Koblitz curve; yield equal to iid within 3%.

### H048 — Walsh-bias audit of the decomposable-target indicator for linear prefilters

- **Handbook**: 14.2.3 Directions and Redei polynomials, 14.2.4 Sets determining few directions  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H048_claim`; theorems: `H048_parseval_3`, `H048_floor`)
- **Claim**: For random V the max normalised Walsh coefficient of D_V stays within random-set fluctuation; bias beyond that exists only for inversion- or Frobenius-closed V (e.g. alpha=1). Trace and weight prefilters were null.
- **Prediction**: Random V max |W|/|D| about 0.01-0.02 at n=22; inversion-closed V 0.02-0.1; yield gain <=1.02-1.1x, likely null.
- **Cheapest test**: n=20-22: FFT of D_V for 20 random, 20 invariant, 20 inversion-closed V vs random sets of equal density; planted-correlation positive control.
- **Falsifier**: No coefficient above the 4-sigma null band for any family, or detector fails the planted control.
- **Lean gap (assumed, not proved)**: That the decomposable-target indicator D_V of a curve (Semaev summation polynomial solvability on V) is a set to which Parseval applies, the random-set Walsh fluctuation band, and the existence of bias for inversion- or Frobenius-closed V. Parseval is decided only for all subsets of the 3-bit cube; the floor lemma is proved for arbitrary lists.

### H049 — Streaming PLE rank certificate to stop at rank B-1 versus fixed excess

- **Handbook**: 13.4.2.2 PLE decomposition, 13.4.4.2 Rank, determinant, characteristic polynomial  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H049_claim`; theorems: `H049_stop_le_fixed`, `H049_net_improvement`, `H049_priced_saving`)
- **Claim**: Certifying rank B-1 online stops collection 4-12% below a fixed 1.05-1.1 B excess and always solves; the incremental interface exists but the saving is unmeasured.
- **Prediction**: Median saving about 7%; relations phase falls the same fraction.
- **Cheapest test**: Replay stored toy streams; rank mod ell per 1% increment; first count with rank=B-1 vs 1.1B; 30 seeds per curve, paired; charge probe cost at 0/0.1/1 GAE.
- **Falsifier**: Median saving <2%, or probe cost exceeds saved relation cost.
- **Lean gap (assumed, not proved)**: That rankAt (rank mod ell of the first k collected relations) reaches B-1 below the fixed 1.05-1.1 B excess, i.e. the hypothesis B-1 <= r K at the fixed time K, with a streaming PLE probe whose cost is the separate priced field; the 4-12% saving is empirical.

### H050 — Fano factor of solution counts: Frobenius clumping of yield per call

- **Handbook**: 11.2.3.2 Factorization patterns, 11.2.3.5 Permutations and integers  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H050_claim`; theorems: `H050_solutions_le`, `H050_orbits_le`, `H050_claim_holds`)
- **Claim**: On invariant V, solutions per target are compound-Poisson with Fano factor about n, so independent relations per call are orbits, not solutions; yield accounting must divide by orbit multiplicity.
- **Prediction**: n=23,m=3: Fano 15-23 invariant, 0.9-1.2 non-invariant; mean orbits per call within 20% of non-invariant mean.
- **Cheapest test**: S_3 for 2000 targets with normal-basis-span V vs random V of equal dimension; record solutions, orbits, variance/mean.
- **Falsifier**: Invariant-V Fano below 3, or non-invariant Fano above 2.
- **Lean gap (assumed, not proved)**: That solutions on a Frobenius-invariant V decompose into orbits of size dividing n (orbit sizes taken as the input list with 1 <= s <= k), and the compound-Poisson Fano factor about n and non-invariant Fano about 1, which are not formalised.

### H051 — Low-discrepancy lattice sweeps over (a,b) at high saturation

- **Handbook**: 10.4.5.5 Discrepancy, 10.4.5.2 Lattice test  ·  **Prior art**: untried  ·  **Lean**: proved (`H051_claim`; theorems: `H051_dups_zero_of_nodup`, `H051_korobov_nodup`, `H051_korobov_dups_zero`, `H051_dups_instance`)
- **Claim**: A Korobov rank-1 lattice over (a,b) has fewer duplicate relations and faster rank growth than iid when relations needed are >=10% of the effective space; no difference below 1% saturation.
- **Prediction**: At 20% saturation duplicates 10%->under 3%, relations to full rank -5-8%; at 1% difference <0.5%.
- **Cheapest test**: Toy curve of order about 2^16, B=64: iid vs Korobov vs Sobol, interleaved seeds, A/A, 100 repetitions, paired bootstrap.
- **Falsifier**: Relations-to-full-rank intervals overlap at 20% saturation, or lattice arm has lower rank.
- **Lean gap (assumed, not proved)**: Relation-rank growth and the 10%->3% duplicate rate at 20% saturation are empirical (h051Prediction); the proofs assume the decomposition is a deterministic function of (a,b), so distinct (a,b) give distinct relations. The second conjunct of H051_claim is not provable from the model.

### H052 — Multiplier-closed table via commuting x-only maps (Dickson analogue)

- **Handbook**: 9.6.1 Dickson polynomials basics, 9.6.2.2 Maps Phi_a, Psi_a  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H052_claim`; theorems: `H052_relation_scale`, `H052_four_le_sq`, `H052_cost_lower_bound`, `H052_claim_holds`)
- **Claim**: A table {x(kF_j): k in K} built by composing R_2,R_3 raises relations per tuple by about |K| without enlarging the matrix; cost follows K*B+N/K, optimum 2*sqrt(NB) (BSGS-IC hybrid), still above rho.
- **Prediction**: GF(2^20),B=2^7,|K|=16: relations per 10^6 tuples x16+-3; rank >= B-2; cost 2^14.5 vs 2^20.
- **Cheapest test**: GF(2^20), m=3, B=128: K=1,4,16,64; relations per tuple, table cost, rank; compare against a plain base of size K*B at equal budget.
- **Falsifier**: Yield gain <|K|/2, rank deficiency >3, or total cost at optimal K not >=4x below K=1.
- **Lean gap (assumed, not proved)**: That the table entries x(kF_j) have logs k*log F_j (commuting Dickson R_2/R_3 maps acting as scalar multiplication on the x-line), and the relations-per-tuple gain of about |K| and rank >= B-2. Only the exponent-side coefficient sum and the (K*B+M)^2 >= 4NB bound are proved.

### H053 — Consecutive-scalar sampling with pseudorandomness (C_2) guard

- **Handbook**: 6.3.5.2 Measures of pseudorandomness, 6.3.5 Incomplete character sums  ·  **Prior art**: untried  ·  **Lean**: proved (`H053_claim`; theorems: `H053_seq_le_indep`, `H053_seq_lt_indep`, `H053_speedup`, `H053_claim_holds`)
- **Claim**: Scanning k,k+1,... with R_{k+1}=R_k+P gives hit rate [x(kP) in V] within 3% of independent scalars with no excess correlation, at one addition per candidate instead of a scalar multiplication.
- **Prediction**: Hit-rate ratio 1.00+-0.03; lag-1 correlation within 4/sqrt(hits); candidate cost drop about 20x, end-to-end 5-10x.
- **Cheapest test**: 2^24 consecutive points vs 2^24 independent; hit counts, autocorrelation to lag 16, Mauduit-Sarkozy C_2 for windows 2^6..2^12.
- **Falsifier**: Hit-rate ratio outside 0.95-1.05, lag z-score >4, or pair-collision rate differing >5%.
- **Lean gap (assumed, not proved)**: Equal hit rate of consecutive scalars k, k+1, ... versus independent scalars (Mauduit-Sarkozy C_2 pseudorandomness, lag correlation) is assumed via the shared expectedTrials count. The addition-cost versus scalar-multiplication-cost gap is a hypothesis (add < mul).

### H054 — Cubic/sextic Jacobi-sum j=0 panels with mu_3/mu_6 factor-base quotient

- **Handbook**: 6.1.2 Jacobi and Gauss sums of small orders  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H054_claim`; theorems: `H054_cols_exact`, `H054_cube_action`, `H054_rewrite`, `H054_la_ninth`, `H054_claim_holds`)
- **Claim**: On j=0 toys, quotienting by mu_3 on top of negation (log lifted by lambda^2+lambda+1=0) cuts relations, search cost and LA size 3x; Jacobi sums choose prime-order test curves. Overlaps order-6 idea; this adds lambda-lifted logs.
- **Prediction**: Relation time to full rank falls 2.5-3.2x vs negation-only at p 2^28..2^36; rank deficiency <2; logs match baseline 100/100.
- **Cheapest test**: p about 2^30, p=1 mod 3, prime-order b via Jacobi sum: baseline orbit key vs mu_3 key with lambda in the matrix; 10 seeds interleaved; validate vs rho.
- **Falsifier**: Relations fall <2x, any wrong log, or baseline already uses mu_3.
- **Lean gap (assumed, not proved)**: That the j=0 curve has a mu_3 automorphism acting on points with log(act P) = lam*log P and lam^3 = 1 mod n (and the primality and order facts from the Jacobi sum). The orbit action being free on the factor base and the 2.5-3.2x relation-time gain are assumed or empirical.

### H055 — Gray-code incremental products over a subspace factor base

- **Handbook**: 5.3.5 Fast arithmetic using normal bases  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H055_claim`; theorems: `H055_incremental_eq`, `H055_mult_saving`, `H055_gray_visits_once_m4`, `H055_gray_single_flip_m4`, `H055_claim_holds`)
- **Claim**: Enumerating x1 in V in Gray order updates p=x1*x2 and s=x1+x2 by XOR, cutting inner-loop multiplications from about 5 to 4 per pair and time 10-20% at m>=16; same relation list.
- **Prediction**: Counted mults 4.0 vs 5.0; throughput 1.1-1.25x independent of n in [53,131].
- **Cheapest test**: n=53,m=16: pair loop with/without Gray enumeration; instrumented field type; 20 interleaved repeats; identical relation lists.
- **Falsifier**: Mult reduction <10%, differing relation lists, or wall-clock gain <1.05x.
- **Lean gap (assumed, not proved)**: That the field multiplication by a fixed element (and the Frobenius or trace maps used) is an XOR-linear map f on bit vectors in the chosen basis, and the real 5 versus 4 multiplication count and wall-clock gain. Gray bijectivity is only checked by decide for m=4, not proved for all m.

## relation-filtering (8)

### H056 — Overlap-bounded degree-balanced relation selection before filtering

- **Handbook**: 17.3.5 Sequences with small Hamming correlation  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H056_claim`; theorems: `H056_finSum_zero`, `H056_finSum_single`, `H056_dot_unit`, `H056_zero_coverage_kernel`, `H056_RS_design_q5`, `H056_RS_overlap_q3`, `H056_claim_holds_fragment`)
- **Claim**: At fixed B, RS-profile greedy selection (balanced column coverage, capped pairwise overlap) needs >=5% fewer relations for full column rank than uniform subsampling of the same pool, with no heavier matrix.
- **Prediction**: 3-12% fewer (central 6%); gain shrinks with pool size; zero when pool equals needed count.
- **Cheapest test**: n=23, subspace FB dim 11 (B about 2000), pool 6000 weight-3 relations, 200 seeds: smallest N for rank B-1 mod 31-bit prime, uniform vs greedy; A/A shuffle.
- **Falsifier**: Paired mean reduction <2%, or CI includes 0 while A/A centres at 0.
- **Lean gap (assumed, not proved)**: Relations are modelled as integer row vectors; rank over a 31-bit prime field and the real RS-profile greedy selector, the 5-6% reduction in relations needed, and the gain shrinking with pool size are empirical. RS design properties are checked by decide for q=5 (coverage) and q=3 (overlap) only. H056_claim's second conjunct is only the weak fragment N_greedy <= N_uniform.

### H057 — Density-evolution threshold for filtering overhead (non-uniform degrees)

- **Handbook**: 16.3.3.12 Sparse linear solving, coding-theory cross-over  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H057_claim`; theorems: `H057_cost_transfer`, `H057_claim_holds`, `H057_peel_sound`, `b06_peel_solvable`)
- **Claim**: Core size after peeling matches the density-evolution fixed point within 5% using measured column degrees (2-core at c*=0.818 for m=3); the cost-optimal overhead c is predictable without running LA and differs from the current default.
- **Prediction**: m=3 uniform: core fraction 0.45-0.60 at c=1.02; within 3% at c=1.2; measured-degree prediction within 5%.
- **Cheapest test**: Archived toy sets n=23..29: sweep c 0.8-1.3 by subsampling, measure core after peeling, compare with recursion using measured degrees.
- **Falsifier**: Core deviates >15% from prediction, or filtering already within 2% of optimal c.
- **Lean gap (assumed, not proved)**: The density-evolution recursion and its fixed point (c* = 0.818 for m=3) and the match of measured core size within 5% are not formalised; they enter as the hypothesis h057Within 5 core pred. Only the transfer of core-size error to dense-phase cost, peel soundness and the termination measure are proved.

### H058 — Closed-form 2-core as a hidden-structure diagnostic

- **Handbook**: 15.5.2 LT and fountain codes, 15.5.3 Raptor codes  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H058_claim`; theorems: `H058_core_le`, `H058_claim_holds`, `H058_classify_sound`, `H058_classify_instance`, `H058_peel_preserves`)
- **Claim**: On real m=3 matrices post-peeling core fraction equals density evolution (0.72 at c=1.0, 0.85 at c=1.2) within 3 points; deficits measure engineerable structure (orbits, symmetrisation), excess measures hidden bias.
- **Prediction**: Core 0.72+-0.03 at c=1.0, 0.85+-0.03 at c=1.2; orbit-merged columns >=5 points smaller.
- **Cheapest test**: n=31 Koblitz, m=3, B about 2000: run singleton filter and compare with formula; 20 seeds.
- **Falsifier**: Core within +-1 point (nothing to engineer), or >5 points off both ways without cause.
- **Lean gap (assumed, not proved)**: The closed-form core fractions (0.72 at c=1.0, 0.85 at c=1.2) and the interpretation of deficits as orbit or symmetrisation structure and excess as hidden bias are empirical. The bound 100*core <= f*B is a hypothesis. Peeling is modelled for unit-coefficient singleton columns over Int mod m only.

### H059 — Closed-form peeling core with max-degree inactivation ordering

- **Handbook**: 15.5 Raptor codes, 15.5.1 Tornado codes, 15.3 LDPC density evolution  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H059_claim`; theorems: `H059_wiedemann_gain`, `H059_claim_holds`, `H059_peel_backsub`, `H059_inactivate_max`, `b06_backsub_unique`)
- **Claim**: For m=3 the core is 0.635B at N=0.918B and 0.723B at N=B; peel plus Raptor inactivation then Wiedemann on the core costs >=1.5x fewer modmuls than on the unfiltered matrix. Risk: relabels structured elimination.
- **Prediction**: Core within 3% (random), 8% (real); core Wiedemann 0.4-0.7 of unfiltered count.
- **Cheapest test**: Peeler on saved toy relations (n about 27, B 2^12..2^14): core after peeling and inactivation; block Wiedemann modmuls vs structured GE at equal weight.
- **Falsifier**: Core off by >8% on real data, or core-only modmuls not below 0.9 of structured-GE + Wiedemann.
- **Lean gap (assumed, not proved)**: The core fractions 0.635B at N=0.918B and 0.723B at N=B (here 1000*core <= 723*B is a hypothesis), the Wiedemann cost model d*d*w versus the real block Wiedemann modmul count, and the claim that inactivation does not just relabel structured elimination.

### H060 — Inactivation-decoding order replacing greedy singleton/clique removal

- **Handbook**: 14.4.6 k-Arcs and linear MDS codes  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H060_claim`; theorems: `H060_dense_cubic`, `H060_inactivation_perm`, `H060_claim_holds`, `H060_unit_peel`, `b06_perm_solvable`)
- **Claim**: Inactivating the max-residual-weight column when peeling stalls leaves a dense core >=10% smaller than singleton-plus-clique filtering at oversampling 1.1, lowering Lanczos cost; Markowitz pivoting is the nearest prior art.
- **Prediction**: Core -15-40% at row weight 4-6; dense-phase cost -30-60%; whole-solve effect small.
- **Cheapest test**: Toy matrices n=20-24 orbit-quotiented: singleton-clique vs max-weight inactivation; compare dense core dimension, total ops, rank mod l.
- **Falsifier**: Core not >=10% smaller, or rank differs after filtering.
- **Lean gap (assumed, not proved)**: That max-residual-weight inactivation yields a core at least 10% smaller than singleton-plus-clique filtering (10*dIn <= 9*dSC is a hypothesis) at oversampling 1.1, and the dense-phase cost being cubic in the core dimension. Only the cost monotonicity, solution-set invariance under column permutation and unit-coefficient peel soundness are proved.

### H061 — Z/4 torsion character from halving to prune sign patterns and reject corrupt rows

- **Handbook**: 12.2.6 Torsion and Tate module, 12.2.7 Weil and Tate pairing  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H061_claim`; theorems: `H061_relation_character`, `H061_patterns_length`, `H061_survivors_m3`, `H061_survivors_m4`, `H061_survivors_half_m3`)
- **Claim**: On cofactor-4 curves psi4: E(F_q)->Z/4 (two halvings) is a homomorphism; checking sum eps_i psi4(P_i)=psi4(R) mod 4 prunes about half the sign patterns and rejects corrupt or twist-contaminated rows with probability 3/4 before group ops or LA.
- **Prediction**: Survivors 0.35-0.6 of 2^m; sign-resolution additions down 1.5-2x; corrupt rows rejected about 0.75.
- **Cheapest test**: a=0 Koblitz n=31: homomorphism check on random pairs; 10^5 brute-force m=3 relations, true vs corrupted; a=1 (h=2) control.
- **Falsifier**: Homomorphism fails, survivors >0.6, corrupt rejection <60%, or psi4 cost exceeds saving.
- **Lean gap (assumed, not proved)**: Existence of the Z/4 homomorphism psi4 via two halvings on cofactor-4 curves (modelled as h061Hom). The general 2^(m-1) survivor count for odd psi4 is stated in the claim but only proved for m=3 and m=4 instances by decide.

### H062 — Coupon-collector relation count and orbit-quotient coverage law, with rare-column steering

- **Handbook**: 11.6.10 Sparse linear systems, 11.2.3.5 Permutations and integers  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H062_claim`; theorems: `H062_flatten_len`, `H062_cover_bound`, `H062_orbit_cover_bound`, `H062_claim_holds`)
- **Claim**: Relations to full rank follow (B/m)(ln B+c), and after orbit quotient (B_orb/m)ln B_orb, so saving is n*lnB/ln(B/n), not n (subfield arm measured closed). Fixing x1 to a rare column may lower total solver calls; the Koblitz arm and steering are open.
- **Prediction**: n=24-30,m=3: 3-5B relations to full rank; steering 1.3-2x fewer solver calls or cancelled; quotient saving within 15% of n*lnB/ln(B/n).
- **Cheapest test**: 3-5 curves, n in {22,24,26}: log column sets in arrival order, incremental rank mod group order, fit B/m(lnB+c); folded matrix; steered arm, 20 seeds, count solver calls.
- **Falsifier**: Full rank at <=1.15B unsteered, steering needs >= unsteered solver calls, or quotient saving equals n within 5%.
- **Lean gap (assumed, not proved)**: The coupon-collector (B/m)(ln B + c) law and the steering gain are empirical. Not modelled: that relations are random m-column supports, that a surjective fold from the curve's automorphism or Frobenius action gives B/k orbit columns, and that rank mod the group order equals support coverage.
- Merged from pool keys: P9-1

### H063 — Run-structure canonicalisation of normal-basis necklaces in filtering

- **Handbook**: 10.2.4 Run property of LFSR sequences, 10.3.2 Autocorrelation of sequences  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H063_claim`; theorems: `H063_rot_length`, `H063_lexLe_lz`, `H063_claim_holds`, `H063_instance`)
- **Claim**: The minimal rotation starts at a maximal zero run, so clz/ctz plus 1-2 comparisons canonicalise 131-bit necklaces >=10x faster than naive and 3x faster than Booth, identical outputs. A related arm gave an unresolved 8% instruction saving.
- **Prediction**: Mean candidates 1.6+-0.4; 15-40x over naive, 3-8x over Booth.
- **Cheapest test**: C microbenchmark, 10^7 random 131-bit vectors: naive, Booth, run-based; assert identical outputs; cycles and candidate histogram; real toy x-coordinates.
- **Falsifier**: Any output differing from naive, mean candidates >4, or speedup over Booth <1.5x.
- **Lean gap (assumed, not proved)**: That normal-basis x-coordinates are 131-bit necklaces under Frobenius rotation. The proved result is that a lexicographic minimum has a maximal leading zero run. The candidate-count (about 1.6) and speedup over Booth are not proved.

## linear-algebra (4)

### H064 — Sparse fountain-coded SpMV for block Wiedemann on Spot

- **Handbook**: 17.3.8 Coding over networks  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H064_claim`; theorems: `H064_cost_lt_replication`, `H064_decode_any_two`, `H064_claim_holds`)
- **Claim**: Sparse-coded SpMV with redundancy 1.25 keeps expected iteration time <=1.15x no-failure and at preemption q=0.1 beats 2x replication and checkpoint-restart in core-seconds; orchestration saving, not a mathematical speedup.
- **Prediction**: Flops 1.3-1.6x; break-even q about 0.03-0.08; gain <=1.4x at q=0.1, none at q<0.03.
- **Cheapest test**: Simulate B=20000,w=6,k=16 mod 61-bit prime, n=20 workers, q in {0.01,0.03,0.1,0.3}; compare restart, replication, dense RS, sparse fountain; verify decode.
- **Falsifier**: Coded cost >= min(replication,restart) at q=0.1, or decode failure >1e-3.
- **Lean gap (assumed, not proved)**: Full column rank of any received selection of sparse fountain-coded rows (hdec), the decode-failure probability below 1e-3, the preemption model q, and the restart and checkpoint costs. Only the flop-factor versus replication arithmetic and a 2+1 parity decode are proved.

### H065 — Block Wiedemann early stop by confirmed linear-complexity profile

- **Handbook**: 17.2.4 Period finding, 17.3.1 Sequences  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H065_claim`; theorems: `H065_first_ge`, `H065_first_le`, `H065_first_mono`, `H065_linComp_mono`, `H065_linComp_le`, `H065_saving`, `H065_claim_holds`)
- **Claim**: Online Berlekamp-Massey with a stability window delta stops at about 2L*+delta; on filtered IC matrices L* is >=3% below N/m+N/n, saving >=3% of SpMVs with failure probability <1e-6.
- **Prediction**: Savings 0-4% (central 1%); null most likely.
- **Cheapest test**: B=3000 weight-3 matrix mod 31-bit prime after clique filtering; scalar and block (m=n=4) Wiedemann with online BM; compare iterations over 100 matrices; verify kernel vector.
- **Falsifier**: Median saving <2%, or an early-stopped run returns a wrong kernel vector.
- **Lean gap (assumed, not proved)**: That ok t L (a recurrence of order L explains the first t terms) is prefix-closed for the actual Wiedemann or Berlekamp-Massey sequence, that the minimal-polynomial degree is at most N, that the stability window delta gives failure below 1e-6, and that L* is at least 3% below N/m+N/n on filtered IC matrices (empirical).

### H066 — Functional-only Wiedemann reading kernel coordinates from the BM sequence

- **Handbook**: 16.2.1 LFSR synthesis, linear complexity, Berlekamp-Massey  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H066_claim`; theorems: `H066_functional_comb`, `H066_matvec_count`, `H066_claim_holds`)
- **Claim**: Recovering log(Q) via coordinate functionals u=e_i and a normaliser uses 2N+O(1) matvecs instead of 3N, a 33% cut with identical output.
- **Prediction**: Matvec ratio 0.67+-0.02; log(Q) identical in 100% of 200 runs.
- **Cheapest test**: 3000x3000 weight-3 matrix mod 40-bit prime from an n=31 curve: standard Wiedemann kernel vs functional variant; matvecs and log(Q).
- **Falsifier**: Scalar BM fails to give the minimal polynomial in >5% of runs, or ratio >0.8.
- **Lean gap (assumed, not proved)**: That the BM minimal polynomial of the scalar sequence u(A^j b) is the true annihilator, that the coordinate functionals u=e_i with a normaliser recover log(Q) for the actual relation matrix mod the group order, and the 2N+O(1) count of the O(1) overhead. Only linearity of u over a combination and the matvec arithmetic are proved.

### H067 — Displacement-rank solve of the un-quotiented Frobenius-twisted relation matrix

- **Handbook**: 13.4.5.2 Structured matrices and displacement rank, 13.2.6 Hankel and Toeplitz  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H067_claim`; theorems: `H067_count_le`, `H067_claim_holds`, `H067_instance`)
- **Claim**: After full orbit expansion, M-ZMD has constant generator rank (<=8) independent of B, enabling O(alpha^2 B) Toeplitz-like solves; relation supports chosen by smoothness may carry no shift structure.
- **Prediction**: Median displacement rank <=8 for n in {17,19,23}, B 2^8..2^11; random control >=0.45B; solve cost down >=10x at B=2^11.
- **Cheapest test**: Un-quotient toy Koblitz runs, reduce mod ell, compute rank(M-ZMD) over F_ell; shuffled-support control; seconds for B<=2048.
- **Falsifier**: Rank grows linearly (slope >=0.2) and matches the shuffled control.
- **Lean gap (assumed, not proved)**: That the un-quotiented Frobenius-twisted relation matrix is shift-invariant away from orbit boundaries (the twist-closure hypothesis), that smoothness-selected supports keep that structure, and that rank(M-ZMD) is at most the number of nonzero displacement rows. Matrix rank over F_ell is not defined here, only the nonzero-row count.

## descent (7)

### H068 — Waring-type coverage threshold for descent steps

- **Handbook**: 13.1.6 The Waring problem over finite fields  ·  **Prior art**: untried  ·  **Lean**: proved (`H068_claim`; theorems: `H068_tuples_length`, `H068_cover_count`, `H068_necessary`, `H068_claim_holds`)
- **Claim**: Representing a target as a sum of k cubes from {v^3: v in V} is complete once km>=n+2log2(n)+O(1); below it a fraction exp(-2^(km-n)) is uncovered, so descent retries are 1+exp(-mu), not geometric.
- **Prediction**: n=17,19,23,m=n/3+2: uncovered fraction matches exp(-mu) within 20% for km-n in [-2,3] and is 0 at about 5.
- **Cheapest test**: n=17,m=8,k=3: N_3(t) for all t by Walsh-Hadamard convolution; compare to Poisson(mu); smallest km-n with zero uncovered.
- **Falsifier**: Variance >1.5x Poisson, or full coverage needs km-n>10.
- **Lean gap (assumed, not proved)**: That the cube set V has 2^m elements and that sums of cubes in F_{2^n} are indexed by t < 2^n. The Poisson law exp(-2^(km-n)) for the uncovered fraction and the sharp threshold km >= n + 2log2(n) are empirical and not proved. Only the necessary condition km >= n is proved.

### H069 — Riemann-Roch counting threshold on descent level size

- **Handbook**: 12.1.2 Divisors and Riemann-Roch theorem  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H069_claim`; theorems: `H069_subsets_length`, `H069_threshold`, `H069_claim_holds`, `H069_instance`)
- **Claim**: An m-term descent step succeeds with probability 1-exp(-C(|V'|,m-1)/q), sharp at |V'|^(m-1)=(m-1)!q; for m=3 the first level needs about sqrt(2q) (rho scale), so descent is cheap only for m>=4. Yield law measured, sharp threshold not.
- **Prediction**: n=24,m=3: 50% crossing near d=12-13; m=4 near d=8-9.
- **Cheapest test**: n=24 toy: all pairs/triples from V' of dim 8..14 into a hash of x-sums; fraction of 10^4 random targets decomposed vs Poisson curve.
- **Falsifier**: Measured threshold dimension differs from the formula by >=1.5 at m=3 or m=4.
- **Lean gap (assumed, not proved)**: That a descent step is an (m-1)-subset sum from V' hashed into the targets, and the Poisson success law 1-exp(-C(|V'|,m-1)/q) with its sharp threshold. The relation to dimension d is also missing: |V'|=2^d. Only the pigeonhole necessity N <= C(|V'|,m-1) is proved.

### H070 — Kloosterman/Weil yield bound for codimension-c descent targets

- **Handbook**: 10.1.4.4 Gauss sums, 10.1.3 DFT  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H070_claim`; theorems: `H070_indicator_expansion`, `H070_single_bit`, `H070_claim_holds`)
- **Claim**: Descent yield from V1 to V' is |V1|^2*2^(-c)(1+eps) with |eps|<=C*2^c*sqrt(q)/|V1|^2, C<=4; at |V1|=q^(1/3) bias decays like q^(-1/6), so exploitable bias exists only at toy sizes.
- **Prediction**: n=19..23,d=6..8,c=1..3: |eps| below the bound; >10% only when the bound exceeds 10%; median |eps|<3% at d>=n/3.
- **Cheapest test**: Exhaustive counts of (x1,x2) in V1^2 with x3 in V' for 300 random (V1,V',beta) triples at n=19..23.
- **Falsifier**: Any |eps| above the C=4 bound, or persistent bias >10% at d>=n/3 for structured V1.
- **Lean gap (assumed, not proved)**: The Weil/Kloosterman bound on the non-trivial character sums (C <= 4, |eps| <= C*2^c*sqrt(q)/|V1|^2), identification of the parity bits with trace-form characters of the subspace V', and the pair-sum structure of N over V1^2. Only the product-of-characters indicator expansion of a codimension-c parity condition is proved.

### H071 — Bilinear dreg and time of the 2-point descent system

- **Handbook**: 9.1.1.1 Algebraic normal form, 9.2.7 Quadratic APN functions  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H071_claim`; theorems: `H071_affine_in_x2`, `H071_descent_bound`, `H071_cost_total`, `h071XorSum_xor`)
- **Claim**: With r fixed, S_3 is bilinear in the two bit blocks; F4 dreg <=d+1 is below the generic-quadratic prediction and time per decomposition scales with a smaller base than 2^d enumeration. The bound is published; the measured slope on descent systems is untried.
- **Prediction**: n=17..29, d=ceil(n/2)+2: dreg <=d+1 and >=1 below semi-regular at n>=21; log2 time slope about 0.35n vs 0.5n.
- **Cheapest test**: msolve/F4 on Weil-restricted descent systems for n=17..27 (50 targets); compare with random bilinear, generic quadratic, and enumerate-over-x1 plus F2 algebra.
- **Falsifier**: dreg matches the semi-regular prediction, or time slope per bit >= enumeration at n>=25.
- **Lean gap (assumed, not proved)**: That the Weil-restricted descent system is the bilinear form modelled here, and the measured F4 dreg, semi-regular prediction and log-time slopes (supplied as fields of h071Measure).

### H072 — Descent chain chosen by per-level valid-point fraction

- **Handbook**: 9.1.2 Walsh transform, 9.1.3 Parameters of Boolean functions  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H072_claim`; theorems: `H072_monotone`, `H072_cost_total`)
- **Claim**: Among nested invariant chains V_0<...<V_k of fixed dimensions, per-level success varies beyond binomial noise; the best chain has >=2x fewer expected trials per full descent than the median. A null on the factor-base twin predicts a null here.
- **Prediction**: n=23, dims (6,8,10,12,14), m=2: per-level spread >=1.5x; best-of-500 product of trials <=0.5x median; non-invariant <=0.8.
- **Cheapest test**: 500 random nested invariant chains at n=23; per-level success on 2000 points via exhaustive 2-decomposition; compare with the product of valid fractions.
- **Falsifier**: Per-level spread within binomial noise, or best/median trials ratio >0.8.
- **Lean gap (assumed, not proved)**: Per-level valid-point counts of random nested invariant chains and the median-chain statistic are hypotheses. The Prop assumes the best-of-500 chain exists with at least 2x fewer trials; Lean does not derive per-level spread from curve structure.

### H073 — Per-level liftable-bias selection of descent sets

- **Handbook**: 7.1.4 Artin-Schreier hypersurfaces, 6.3.4.2 Inversive congruential pseudorandom numbers  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H073_claim`; theorems: `H073_biased_le`, `H073_work_mono`)
- **Claim**: Selecting each descent level's V by best-of-T liftable bias cuts attempts per node by (2*liftFrac)^(-m) and total descent cost by the product over levels, with no linear algebra. Shrinks as 2^(-d/2); expected to fail if the factor-base twin fails.
- **Prediction**: n=29, levels d=(8,11,14), T=2^8: liftFrac 0.58, 0.55, 0.53; total cost ratio about 2.5x (1.5-3.5x).
- **Cheapest test**: n=29: 200 random targets, chosen vs random level sets, m=2 closed-form pair enumeration; mean attempts per level, paired bootstrap.
- **Falsifier**: Total attempts ratio <1.15, or per-level ratio not within 20% of (2*liftFrac_measured)^m.
- **Lean gap (assumed, not proved)**: That best-of-T selection raises the liftable fraction above 1/2 and that attempts per node scale as (2 liftFrac)^(-m). Per-level liftFrac, attempts and nodes are record fields; the 1.15x total ratio is asserted.

### H074 — Completely normal element for conversion-free subfield-tower descent

- **Handbook**: 5.4.1 Complete normal basis theorem, 5.4.3 Cyclotomic modules and complete generators  ·  **Prior art**: untried  ·  **Lean**: proved (`H074_claim`; theorems: `H074_normal_of_cn`, `H074_nonzero_of_cn`, `H074_six`, `H074_six_zero_not`, `H074_conv_saving`)
- **Claim**: A completely normal beta is normal over every F_{2^d}, d|n, so successive Weil restrictions need zero basis-conversion maps (vs about n^2/64 word ops each) and invariant subspaces nest as kernels ker g_d(sigma). Composite n only; prime n such as 131 excluded.
- **Prediction**: Conversion cost 0; total descent saving <3% at n=36; yield unchanged.
- **Cheapest test**: n=12,36 over F_2: find completely normal beta by checking circulant rank of Tr_{n/d}(beta) at each d | n; count conversions in a three-level descent script vs independent normal elements.
- **Falsifier**: No completely normal element within 1000 trials at n=36 (bug), or descent time differs >5% from baseline.
- **Lean gap (assumed, not proved)**: The model is a GF(2) circulant-rank proxy over the group ring. Real normality of Tr_{n/d}(beta) over F_{2^d} (F_{2^d}-linear independence of conjugates) is not formalised. Existence of a completely normal element at n=36 and the <3% saving are hypotheses. The n=6 instance beta=1 is trivial under the proxy.

## cost-model (9)

### H075 — Hankel rank spectrum of the trace-component pencil and yield overdispersion

- **Handbook**: 16.3.3.8 Rank attacks, 16.3.3.9 MinRank  ·  **Prior art**: untried  ·  **Lean**: proved (`H075_claim`; theorems: `H075_geom`, `H075_daykin_sum`, `H075_count_zero_two`, `H075_hist_two`, `H075_hist_three`)
- **Claim**: On interval V the component bilinear forms are Hankel with Daykin rank counts 3*2^(n-2d+2r-1); decomposition counts per target are overdispersed vs Poisson(2^(2d-n)) by the low-rank Walsh spectrum, and low-rank combinations become linear after r branchings.
- **Prediction**: n=19,d=8: rank-1 count 48, rank-2 count 192; Var/Mean>1 by a computable amount at n=17..21.
- **Cheapest test**: n=19,d=8: Hankel rank histogram over all 2^19 delta vs formula; brute-force decomposition counts for all 2^19 targets vs Walsh-sum prediction.
- **Falsifier**: Histogram deviates from 3*2^(n-2d+2r-1) beyond the 2x kernel factor, or Var/Mean equals 1 within error.
- **Lean gap (assumed, not proved)**: Daykin counts for general d are asserted, not proved: the brute-force count equals the formula is proved only by decide at d=2,3. The link from Hankel ranks of the trace-component pencil to per-target decomposition counts, and the Var/Mean>1 overdispersion, are hypotheses.

### H076 — Batch-target marginal cost: left-kernel growth about 0.75 per extra relation

- **Handbook**: 15.5.1 Tornado codes, 15.3 LDPC rank above ML threshold  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H076_claim`; theorems: `H076_batch_le_separate`, `H076_k64`, `H076_adjugate`, `H076_unique`)
- **Claim**: Above the orientability threshold left-kernel dimension grows about 0.74 per extra relation, each dependency giving an equation in the unknown target logs; k targets need about c_3 B+2k relations, so extra targets cost about 2 attempts. Must be priced against matched batch rho.
- **Prediction**: Slope 0.70-0.78 for N/B in [0.92,1.0]; 1.3-2.0 relations per extra target; k=64, B=2000: about 1968 vs 64x1840.
- **Cheapest test**: Random 3-uniform hypergraphs B=2000..8000 mod 61-bit prime: left-kernel dimension vs N, then k=1..64 target-carrying rows; repeat on real Koblitz relations with planted Q_j.
- **Falsifier**: Slope outside [0.55,0.9], >4 relations per target, or real-vs-simulation mismatch >15%.
- **Lean gap (assumed, not proved)**: The kernel-growth slope 0.70-0.78 of random 3-uniform hypergraphs above the orientability threshold, the relation count c3*B, and the bridge from real Koblitz relations to the random model are assumed. Only the k=2 adjugate step is proved, not general k.

### H077 — Strength-2 covering array screening of the autolab configuration space

- **Handbook**: 14.7.4 Covering arrays  ·  **Prior art**: untried  ·  **Lean**: proved (`H077_claim`; theorems: `H077_covers`, `H077_main_effects`, `H077_budget`)
- **Claim**: A 6-run binary (or 9-run ternary) strength-2 covering array plus a pairwise model finds a configuration within 10% of the exhaustive best on >=80% of toy curves using <5% of 128 runs; a process-cost tool for finding measured improvements.
- **Prediction**: Within 10% on 80-95% of 50 curves; failures on three-way interactions.
- **Cheapest test**: Full 2^7 grid on 50 toy curves (n=17..23 binary, 20-bit prime) as ground truth; replay the preregistered 6-row array offline with a pairwise model.
- **Falsifier**: <60% of curves within 10%, or median regret >25%.
- **Lean gap (assumed, not proved)**: That the pairwise model fitted on the 6 array rows picks a configuration within 10% of the exhaustive best on at least 80% of curves. This depends on the real cost functions having small three-way interactions; the claim takes pick and best as hypotheses.

### H078 — Sidon-defect of Carlitz-torsion and spread-element factor bases

- **Handbook**: 14.5.3 Difference families and BIBDs, 14.4.4 Singer cycles, 13.5.5 Carlitz torsion, 14.3.3 Desarguesian spread  ·  **Prior art**: tried-closed  ·  **Lean**: proved (`H078_claim`; theorems: `H078_pairs_length`, `H078_distinct_le`, `H078_distinct_eq_iff`, `H078_coverage_le`, `H078_coverage_eq_iff`, `H078_tri_two_mul`, `H078_sidon_example`)
- **Claim**: General sumset-coverage and energy were measured null (Sidon base 1.107x only); the untested families are Carlitz/Drinfeld torsion ker(C_a) and spread elements mu*GF(q), predicted to show >3% coverage deficit from structure-induced collisions.
- **Prediction**: Random and spread V within 1% of Poisson; Carlitz-torsion V 0-5% excess collisions, direction uncertain.
- **Cheapest test**: n=20-22, dim-7 subspaces, 50 per family, 5 curves: exhaustive pair-sum x-image size vs Poisson; random-subset negative control; planted AP positive control.
- **Falsifier**: All families within 1% of Poisson, or the positive control shows no defect.
- **Lean gap (assumed, not proved)**: That Carlitz torsion ker(C_a) and spread elements mu*GF(q) subspaces yield x-images with a coverage deviation of at least 1% from Poisson. Mean coverage and expectation are Nat inputs, and the x-coordinate image map is not modelled.

### H079 — Delayed-reduction PLE dense core moving the hybrid switch point

- **Handbook**: 13.4.6.1 Hybrid sparse-dense methods, 13.4.1.2 Word size prime fields, 13.4.2.2 PLE decomposition  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H079_claim`; theorems: `H079_mono_d`, `H079_cost_down`, `H079_argmin_up`)
- **Claim**: With 2-3 limb ell, delayed modular reduction in blocked PLE cuts dense per-entry cost near the block size, moving the optimal dense core >=1.5x larger and total LA cost down >=15%.
- **Prediction**: Core 0.05B->0.09B; LA cost -15-30% at B=2^16..2^20; kernel 3-6x fewer cycles per MAC.
- **Cheapest test**: Microbenchmark 3-limb mul-add reduce-each vs delayed (k=8,16) in blocked PLE of 2048x2048; plug constants into the hybrid cost model, recompute argmin core.
- **Falsifier**: Dense kernel speedup <1.5x, or optimum core moves <1.2x.
- **Lean gap (assumed, not proved)**: The 3-6x delayed-reduction kernel speed-up (3*d' <= 2*d), the sparse cost curve being convex, and the 1.5x core shift and 15% LA cost drop. The strict single-crossing theorem needs a strictly increasing dense cost, while the Prop's 1.5x shift and 15% drop are empirical.

### H080 — Hamming-weight degree and mixed-volume predictor for F4 cost

- **Handbook**: 11.5.2.1 Ostrowski's theorem, 11.5.2.2 Polytope indecomposability  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H080_claim`; theorems: `h080Pop_eq`, `H080_pop_le`, `H080_pop_one`, `H080_pop_add`, `H080_weight_le_total`, `H080_weight_mul`, `H080_hits_le`)
- **Claim**: Bit-degree popcount of exponents plus BKK mixed volume of Weil-restricted supports predicts the F4 maximum degree within +-1 on >=85% of toy instances vs <=65% for the semi-regular bound.
- **Prediction**: Weight predictor 85-95% hit rate; semi-regular 50-65% (n=15..24, m=3, k=n/3, 100 systems).
- **Cheapest test**: 100 Weil-restricted S_3,S_4 systems: run F4, record max degree and matrix size; compute both predictors; compare hit rates (testable from existing degree data).
- **Falsifier**: Weight predictor within 5 points of semi-regular, or hit rate <70%.
- **Lean gap (assumed, not proved)**: The link from the bit-degree weight (and the BKK mixed volume, not modelled) to the F4 maximum degree, plus the hit-rate numbers 85% vs 65%, which come from F4 runs on Weil-restricted systems (hypothesis fromWeilF4Runs).

### H081 — Correlation measure C_2 of the decomposability indicator along an additive sweep

- **Handbook**: 10.4.5.3 Correlation measure of order k  ·  **Prior art**: untried  ·  **Lean**: proved (`H081_claim`; theorems: `H081_corr_identity`, `H081_dis_le`, `H081_corr_abs_le`, `H081_C2_abs_le`, `H081_claim_holds`)
- **Claim**: For generic shifts C_2 stays within 3*sqrt(L ln L), but for tau-multiple shifts on Koblitz curves it exceeds it, understating yield variance in the cost model.
- **Prediction**: Generic: sqrt(L) scaling; tau shift excess 2-5x, yield variance 1.5-3x binomial; non-Koblitz no excess.
- **Cheapest test**: Koblitz GF(2^17), B=100: indicator for L=2^16 and order-2 correlation for shifts {1,2,tau-multiples,random}; random-curve null; planted positive control.
- **Falsifier**: C_2 for tau-shifts within the random-curve null band with the positive control detected.
- **Lean gap (assumed, not proved)**: That the decomposability indicator of a Koblitz GF(2^17) additive sweep has the stated generic sqrt(L ln L) band and a tau-shift excess is a measured fact, not proved; the band hypothesis is an explicit premise.

### H082 — Multihomogeneous Bezout/mixed-volume predictor of F4 time for split systems

- **Handbook**: 7.1.3 Toric hypersurfaces  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H082_claim`; theorems: `H082_prod_mono`, `H082_total_sum`, `H082_claim_holds`)
- **Claim**: log F4 time correlates with log B_mh at Spearman >=0.9 vs <=0.6 for total-degree Bezout, so a B_mh-driven model picks the best (d,m,split) more often; counts only if chosen parameters measurably cut time.
- **Prediction**: Spearman 0.9+-0.05 vs 0.55+-0.15; argmin agreement >=70% vs <=40%.
- **Cheapest test**: 200 systems, n in 18..26, d in n/3..n/2, m in {2,3}: msolve/F4 with timeouts; compute both predictors symbolically; Spearman with bootstrap CI.
- **Falsifier**: Spearman gap <0.1 with CI overlapping zero, or argmin agreement no better than Bezout.
- **Lean gap (assumed, not proved)**: Monotonicity of F4 running time in the multihomogeneous Bezout bound (the Spearman >= 0.9 correlation) is a hypothesis; the true mixed-volume bound is replaced by a block-degree product.

### H083 — Variance-to-mean (Poisson) audit of decomposition counts via log-domain spectrum

- **Handbook**: 6.3.6.3 Thin sets with small DFT, 6.3.6.4 Character sums over arbitrary sets  ·  **Prior art**: tried-closed  ·  **Lean**: proved (`H083_claim`; theorems: `H083_sums_length`, `H083_coverage_step`, `H083_coverage_mono`, `H083_coverage_le`, `H083_claim_holds`)
- **Claim**: Spectrum ratio max|F_hat|/sqrt(B) was measured generic (closed); the unrun angle is variance-to-mean of decompositions per target equalling 1.00+-0.03 for subspace and orbit bases, with any peak showing as overdispersion.
- **Prediction**: ell about 2^28,B=2^12: ratio 6.2+-0.5 for random and structured; variance/mean 1.00+-0.03.
- **Cheapest test**: Toy order about 2^28: BSGS logs, subspace/orbit/random FBs, sampled-t FFT, decomposition counts for 10^5 targets.
- **Falsifier**: Structured spectrum ratio >1.25, or variance/mean >1.1.
- **Lean gap (assumed, not proved)**: Variance/mean of decomposition counts equal to 1 and the flat Fourier spectrum of subspace/orbit bases on a real curve group are not proved; only the counting skeleton of m-fold sums on the exponent side is.

## curve-selection (6)

### H084 — Koblitz twin-curve amortisation: S3 independent of a

- **Handbook**: 16.4.1.3 Special curves, 16.4.2.2 Pairings and twists  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H084_claim`; theorems: `H084_partition`, `H084_amortised`, `H084_claim_holds`)
- **Claim**: One S3 solve over V gives relations for E_0 and E_1: about 50% pure E_0, 50% pure E_1, mixed <1%, so a paired workload amortises 2x; single-curve use only filters. Amortisation, not a single-instance gain.
- **Prediction**: n=23,a=1,b=1: split 50+-2%, mixed <1%; two-instance throughput 2.0x.
- **Cheapest test**: n=23,d=8: enumerate V^2, roots of S3, classify types by trace test, tabulate counts.
- **Falsifier**: Mixed >1%, split off 50/50 by >5%, or no two-instance workload exists in the protocol.
- **Lean gap (assumed, not proved)**: The no-mixed-solution hypothesis (mixed < 1%) and the 50/50 E0/E1 split from the trace test on Koblitz n=23 are curve facts assumed as hypotheses; the S3 solution set is an abstract list with a type tag.

### H085 — Select GHS/Weil-descent covers by maximal rational-point count

- **Handbook**: 14.8.3 Niederreiter-Xing function fields  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H085_claim`; theorems: `H085_choose_step`, `H085_choose_mono`, `H085_choose_small`, `H085_surj_card`, `H085_claim_holds`)
- **Claim**: Relation probability per divisor class scales as N^g/(g!#J); top-decile-N genus-g covers yield >=3x the bottom decile, so choose covers by N_q(g) rather than at random.
- **Prediction**: 2000 genus-3 curves over F_8: Pearson r>0.95 with N^g/(g!#J); top/bottom decile 3-10x; q=16,g=4 upper bound about 69x.
- **Cheapest test**: Enumerate y^2+hy=f over F_8 (g=3); N and #J from L-polynomial; sumset of g-point sums via Cantor arithmetic; covered fraction vs formula.
- **Falsifier**: r<0.8, decile ratio <1.5, or the real GHS family offers no choice of N for the target.
- **Lean gap (assumed, not proved)**: The relation to the actual probability N^g/(g! #J) via L-polynomials and Cantor arithmetic, and surjectivity of the g-point sum map onto the Jacobian, are assumed; only binomial monotonicity and a surjection-cardinality bound are proved.

### H086 — Invariant-dimension screen 3m>n+4 with rotation-only membership

- **Handbook**: 13.2.3 Matrix representations of finite fields, 13.2.4 Circulant matrices  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H086_claim`; theorems: `H086_orbit_closed`, `H086_countP_or`, `H086_countP_reps`, `H086_card_le`, `H086_claim_holds`)
- **Claim**: Primes n in 53..131 with ord_n(2)<=n/3 (73, 89, 113, 127) admit invariant subspaces of dimension m with 3m>n+4; orbit-distinct S3 counts there match generic subspaces within 10% while membership costs a few rotations/XORs instead of a matrix product.
- **Prediction**: n=23 (m=11,12) and n=31 (m=10,15): counts within +-10% of random V; membership 5-20x fewer word ops.
- **Cheapest test**: n=23,m=11: S3 over V^3 with x3 fixed on a few hundred values for invariant g vs 50 random V; time membership.
- **Falsifier**: Invariant count deviates >25% from random V, or membership gain <2x.
- **Lean gap (assumed, not proved)**: Existence of Frobenius-invariant subspaces of dimension m with 3m>n+4 for n=73,89,113,127, and that the orbit-distinct S3 count matches generic subspaces within 10%, are not proved; the orbit-size bound and orbit-key cover are hypotheses.

### H087 — Volcano ascent to a j=0 or 1728 crater for an Aut-6 or Aut-4 quotient

- **Handbook**: 12.2.3 Isogenies, 12.2.8 Endomorphism ring and automorphism group, 12.2.9 Ordinary curves  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H087_claim`; theorems: `H087_orbit_six`, `H087_orbit_four`, `H087_transport`, `H087_claim_holds`, `H087_relation_ratio`)
- **Claim**: For smooth-conductor floor curves, walking to the crater (Aut order 6 or 4) lets the factor base close under zeta, cutting relations and LA size about 3x at equal base size; rho cost is level-independent, and random-curve targets are not covered.
- **Prediction**: p about 2^30..2^40, f=2 or 4: relations ratio (crater/floor) 0.33+-0.05; LA ratio about 0.11 dense; walk cost <1e-3.
- **Cheapest test**: 5 toy floor curves D=-12 or -48; Velu walk to j=0; same m=2 small-x IC with orbit quotient on both; random curve control.
- **Falsifier**: Relation ratio >0.5, transported log fails, or base cannot be made orbit-closed.
- **Lean gap (assumed, not proved)**: Existence of the Velu isogeny walk to a j=0/1728 crater, free action of Aut of order 6 or 4 on the factor base, and that the isogeny is a homomorphism of cyclic groups with image order dividing the source order are assumed (divisibility is a hypothesis of the transport lemma).

### H088 — Invariant-subspace dimension menu from x^n-1 as a curve-size selector with yield test

- **Handbook**: 10.2.1 LFSR sequences, 10.2.3 Maximal period sequences, 15.1.3 Cyclic codes, 14.9.2 Weights of multiples of polynomials, 5.4.3 Cyclotomic modules  ·  **Prior art**: tried-closed  ·  **Lean**: proved (`H088_claim`; theorems: `H088_trivial_stable`, `H088_zero_rot_11_13`, `H088_dims_primitive`, `H088_ord_values`, `H088_claim_holds`)
- **Claim**: The census (2 primitive mod n gives only dims 0,1,n-1,n, including n=131) is closed. New angle: the explicit near-n/2 and near-n/3 dimension and count table for n=53..131, plus a measured yield and partial-stability (coordinate subspace column ratio >=0.97) test where such subspaces exist.
- **Prediction**: At most 25% of primes admit dim within 1 of n/3; n=127 has 7j and 7j+1 dims; coordinate subspaces at n=23 give columns/|V_I| in [0.97,1.0]; invariant yield equals generic within 10%.
- **Cheapest test**: Factor x^n-1 over F_2 for n=53..131; subset-sum divisor degrees; n=73 (d=24,25) invariant vs generic yield on a toy curve; n=23 coordinate-subspace orbit counts.
- **Falsifier**: A primitive-root prime with a stable subspace of dimension in [2,n-2], or columns/|V_I|<0.9 at n=23.
- **Lean gap (assumed, not proved)**: Semisimplicity of F_2[x]/(x^n-1) and the identification of stable subspaces with unions of cyclotomic cosets are taken as the hypothesis StableDim d <-> d in h088Dims sizes; the measured yield and column-ratio tests are not modelled.
- Merged from pool keys: P4-3, P14-0, P5-0

### H089 — Berlekamp-Massey linear-complexity screen of Tr(x(kG)) for weak curves

- **Handbook**: 10.4.2 Linear complexity analysis, 10.4.4.1 Explicit sequences  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H089_claim`; theorems: `H089_lc_mono`, `H089_fold_congr`, `H089_determined`, `H089_bands`, `H089_claim_holds`)
- **Claim**: For smooth curves over GF(2^n) in ecdb, BM linear complexity of N=2048 terms of Tr(x(kG)) lies in N/2+-8; a nodal cubic gives L<=3n, validating the screen. An anomaly would be a lead.
- **Prediction**: At least 1000 smooth curves fall in [1016,1032]; nodal b=0 cubic over GF(2^21) gives L<=63; expected null.
- **Cheapest test**: For each ecdb curve with n<=40 and 5 generators: 2048 multiples, trace bit, BM over GF(2); nodal and supersingular controls; shuffled-sequence null.
- **Falsifier**: Positive control not detected (L>3n), or smooth curves outside the band above the 2^-16 rate.
- **Lean gap (assumed, not proved)**: Berlekamp-Massey itself is not implemented; only the soundness skeleton (an order-r recurrence is determined by r terms, complexity bound monotone) is proved. That Tr(x(kG)) on smooth curves has complexity N/2+-8 and nodal cubics have L<=3n is a curve fact not proved.

## hardware (11)

### H090 — ONB canonical orbit key with trace as parity (type-II n=53,131)

- **Handbook**: 16.7.4 Normal bases, 16.7.5 Optimal normal bases  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H090_claim`; theorems: `H090_canon_idem`, `H090_check_five`, `H090_order_131`, `H090_cost_gain`, `H090_claim_holds`)
- **Claim**: In a type-II ONB Frobenius is a bit rotation and Tr is parity, so orbit canonicalisation is the least rotation in about n bit-ops vs about n-1 squarings; only an end-to-end measured saving counts (repricing alone is accounting).
- **Prediction**: Canonicalisation 5-20% of collection cost in polynomial basis, <1% in ONB; end-to-end 1.05-1.25x at n=131; <5% share at n=53 means no gain.
- **Cheapest test**: Instrument the Frobenius-orbit IC at n=53,131: squarings and mults spent canonicalising as a fraction of per-relation cost at 0/0.1/1 GAE vs the ONB bit-op count.
- **Falsifier**: Canonicalisation <3% of per-relation cost at all prices, or ONB multiplication overhead gives end-to-end ratio <1.0 at 1 GAE.
- **Lean gap (assumed, not proved)**: That a type-II ONB at n=53,131 makes Frobenius a bit rotation and trace parity is assumed; rotation-invariance of the least-rotation canon is proved by decide only for n=5 and in general only as a hypothesis-based idempotence lemma, and the end-to-end measured saving (canonicalisation share of per-relation cost) is not modelled beyond Cost arithmetic.

### H091 — GF2P8AFFINEQB bit-matrix applies for the linear maps of the lifted loop

- **Handbook**: 16.2.6 AES (Rijndael)  ·  **Prior art**: untried  ·  **Lean**: proved (`H091_claim`; theorems: `h091_xor_xor`, `H091_apply_linear`, `H091_comp_linear`, `H091_blocks_64`, `H091_blocks_131`, `H091_blocks_quadratic`, `H091_blocks_mono`, `H091_instr_mono`)
- **Claim**: On GFNI+AVX-512 hosts the linear-map part of the lifted loop reaches >=2x the candidates per cycle of 8-bit table lookups at n=64..131 (throughput- not load-bound); block count is quadratic in n/8.
- **Prediction**: Ratio 1.5-3x at n=64, below 1x at n>=131.
- **Cheapest test**: One n=64 and one n=131 F2-linear map over 2^20 vectors, table vs VGF2P8AFFINEQB, perf stat cycles on a GFNI host via isolab-eks; report the crossover n.
- **Falsifier**: Table lookup faster at n=64 or crossover below n=48; host without GFNI voids, not refutes.
- **Lean gap (assumed, not proved)**: Measured cycles per GFNI instruction vs per table lookup on a GFNI+AVX-512 host (throughput- not load-bound); H091_claim takes the 2x cycle ratio as a hypothesis.

### H092 — Longest-zero-run canonicalisation of Frobenius orbits (bit-parallel)

- **Handbook**: 14.9.2 Cyclic structure F_2[X]/(X^n-1), necklaces  ·  **Prior art**: tried-open  ·  **Lean**: proved (`H092_claim`; theorems: `H092_le_lz`, `H092_min_has_max_run`, `H092_fast_eq_naive_upto6`, `H092_ops_131`, `H092_ops_ratio`)
- **Claim**: Minimal rotation starts at a maximal zero run; clz/ctz plus about 2 comparisons canonicalise a 131-bit word in O(n/64) ops, identical to naive. An earlier arm saved 8% instructions but did not resolve against the native limit.
- **Prediction**: At least 10x fewer cycles than naive; end-to-end >=1.2x if canonicalisation was >=20% of candidate cost; ties 1.3-2.2.
- **Cheapest test**: C microbenchmark on random 131-bit words, 10^8 calls; verify equality with naive on 10^7 words and all words for n<=24; count ties; perf-ipc where a PMU exists.
- **Falsifier**: Any output differing from naive, speedup <3x, or mean tied starts >4.
- **Lean gap (assumed, not proved)**: General-n proof that the fast run-start canonical form equals the naive minimum rotation is only exhaustive for n<=6 plus the exchange lemma (min rotation has max zero run); the word-op model is not measured cycles.

### H093 — MDS-arc checksum protection for block Lanczos/Wiedemann on Spot

- **Handbook**: 14.4.6 k-Arcs and linear MDS codes  ·  **Prior art**: untried  ·  **Lean**: proved (`H093_claim`; theorems: `H093_cks_add`, `H093_cks_single`, `H093_detect_of_mds`, `H093_single_fault_detect`, `H093_overhead_le_2pct`, `H093_cheaper_than_duplicate`)
- **Claim**: With r=4 Vandermonde checksum rows c^(j)A, every corruption of <=4 coordinates per matvec is detected and <=2 corrected at <2% extra cost, vs about 100% for duplicate verification. Engineering saving.
- **Prediction**: Overhead 0.01-0.1% extra multiplies at dimension 2^16; detection 100% within bound; beats checkpoint-only by 1.2-2x at 5%/hour preemption.
- **Cheapest test**: Block Lanczos mod 31-bit l on a 2e4-dim sparse matrix, 20 nonzeros per row; inject 1-5 faults per 1000 matvecs; four arms: none, checkpoint, duplicate, MDS checksum.
- **Falsifier**: Any undetected corruption inside the bound, a miscorrection, or overhead >2%.
- **Lean gap (assumed, not proved)**: The Vandermonde/MDS property (any nonzero error pattern of weight 1..4 is seen by some checksum row mod l) and unit weights mod l are hypotheses; correction of <=2 faults is not modelled; overhead ratio depends on the measured check period q and row weight.

### H094 — Latin-square XOR-skewed storage for conflict-free pair-sum table access

- **Handbook**: 14.1.1 Prime powers, 14.1.5 Affine and projective planes  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H094_claim`; theorems: `h094_xor_cancel`, `h094_xor_eq_zero`, `H094_row_conflict_free`, `H094_skew_injective`)
- **Claim**: Banking entry (i,j) at i XOR j over GF(2^5) gives conflict-free access along rows, columns and all slopes a!=1, removing shared-memory bank conflicts in the pair-sum kernel; odd-stride padding is already used elsewhere.
- **Prediction**: Replays drop from 2-4 per warp access to 0; kernel 1.1-1.3x if memory-bound.
- **Cheapest test**: CUDA kernel, B=2^12: row-major, padded, XOR-skewed layouts; ncu l1tex bank-conflict counters; cycles per pair.
- **Falsifier**: Speedup <5% or non-zero conflicts after skewing.
- **Lean gap (assumed, not proved)**: The GF(32) multiplication table is an abstract structure h094GF32 (distributivity, one, no zero divisors) rather than a concrete table; kernel bank-conflict counters and speedup are measured on GPU, not proved.

### H095 — Projective-plane block design to shard all-pairs decomposition

- **Handbook**: 14.5.1 Block designs basics, 14.4.1 Projective spaces, 14.5.3 Singer difference sets  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H095_claim`; theorems: `H095_line_pairs`, `H095_work_sum`, `H095_total_work`, `H095_transfer_le`, `H095_p7_transfer`, `H095_claim_holds`)
- **Claim**: Placing shard pairs by lines of PG(2,p) (lambda=1) gives zero redundant pair work and per-worker transfer B(p+1)/M vs B for all-gather; total work identical.
- **Prediction**: p=7 (M=57): per-worker memory down about 7x; wall-clock 1.0-1.5x on Spot clusters.
- **Cheapest test**: Simulate 57 workers at B=2^14: bytes moved and work per worker for all-gather, random 2-D tiling and Singer design; check coverage equals C(M,2) exactly.
- **Falsifier**: Wall-clock gain <10%, or any shard pair covered zero or twice.
- **Lean gap (assumed, not proved)**: Existence of the PG(2,p) line blocks with lambda=1 (pair cover) is a hypothesis; the total-work and transfer arithmetic is proved from block count and block size; wall-clock gain on Spot clusters is empirical.

### H096 — Reverse Cuthill-McKee reordering for block-Wiedemann matvec locality

- **Handbook**: 13.4.5.1 Reordering, 13.4.4.1 Wiedemann  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H096_claim`; theorems: `h096_finSum_ofFn`, `H096_finSum_perm`, `H096_relation_invariant`, `H096_cycles_ratio`)
- **Claim**: For B>=2^20 and 130-bit ell, RCM plus heavy-column grouping cuts L2 misses per nonzero >=30% and cycles per nonzero >=1.25x vs insertion order; a cycle-level, not op-count, gain.
- **Prediction**: 1.25-1.8x lower cycles per nonzero; <1.1x at B=2^16; IPC 0.6->0.9.
- **Cheapest test**: Synthetic B=2^14..2^22, row weight 6, Zipf(1) column weights: insertion vs RCM vs degree sort, perf stat cycles and L2 misses on an isolab host, 20 paired repeats.
- **Falsifier**: Ratio <1.1 at B=2^22 with CI excluding 1.25, or no PMU and simulated miss reduction <10%.
- **Lean gap (assumed, not proved)**: The 30% L2-miss reduction from RCM ordering and the memory-bound fraction (2*compute <= miss stall) are measured hypotheses; only permutation invariance of relations and the cycle-model implication are proved.

### H097 — Batch-affine vs projective candidate generation, binary vs prime split

- **Handbook**: 12.3.3 Coordinate systems, 12.3.4 Explicit formulas, 12.3.6 Char-2 short Weierstrass  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H097_claim`; theorems: `H097_mixed_le`, `H097_batchInv_le`, `H097_affine_le_proj`, `H097_ledger_ratio`)
- **Claim**: With k>=64 walks, batch-affine addition is >=1.6x faster per candidate than projective plus batch conversion in GF(2^131) with CLMUL, and <=1.1x on 255-bit Edwards. Prime side measured against batching; binary side unmeasured.
- **Prediction**: GF(2^131): 1.8-2.3x at k=64..256; GF(2^53): 1.3-1.6x; 2^255-19: 0.95-1.1x.
- **Cheapest test**: C microbenchmark, 1e7 additions per scheme with matched tables and seeds on isolab-eks; M/S/I ledger matching formulas; A/A arm; perf-ipc cycles.
- **Falsifier**: Binary speedup <1.15x at k=64, or prime-field speedup >1.3x.
- **Lean gap (assumed, not proved)**: Cycle cost is assumed proportional to the M/S/I ledger (CLMUL multiplication/squaring/inversion costs S<=M/10, I<=25M); the prime-field (<=1.1x) arm and real cycle ratio are unmeasured here.

### H098 — Booth/Duval canonical key at n=131 against squaring chains

- **Handbook**: 12.2.8 Frobenius on Koblitz, 12.3.6 Char-2 arithmetic  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H098_claim`; theorems: `H098_orbit_count`, `H098_orbit_count_div`, `H098_key_rotation_invariant_upto6`, `H098_key_le_word_upto6`, `H098_orbits_n5`, `H098_orbits_n7`)
- **Claim**: Normal-basis keys are integrated (8.6x at degree 61); open is Booth/Duval at n=131: one basis change plus Booth is >=1.5x fewer cycles than min-over-squarings, with identical orbit partition.
- **Prediction**: n=131 AVX2: polynomial basis 1.3e3-2e3 cycles vs 4e2-8e2; speedup 1.6-3x; 1.0-1.3x at n=53.
- **Cheapest test**: C benchmark, 1e6 random x for n in {53,83,131}: min over squarings vs Booth on a normal-basis image; orbit ids via hash map; perf-ipc cycles; A/A.
- **Falsifier**: Speedup <1.15x at n=131, any orbit-partition mismatch, or basis change exceeds the saving.
- **Lean gap (assumed, not proved)**: H098_claim (key rotation invariance and key<=w for all words) is proved only exhaustively for n<=6; Booth/Duval equals naive minimum rotation, the free prime-order action at n=131, and the 1.5x cycle gain after basis change are not proved.

### H099 — Itoh-Tsujii plus Montgomery batching as the affine-add primitive of the collection loop

- **Handbook**: 11.1.8.2 Inversion in extension fields, 11.1.5.2 Multiplication in extension fields  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H099_claim`; theorems: `H099_itoh_131`, `H099_itoh_83`, `H099_itoh_53`, `H099_batchInv_20`, `H099_breakeven_131`, `H099_batch_beats_ld_131`, `H099_claim_131`)
- **Claim**: Batched affine addition (about 5 mults) with Itoh-Tsujii (8 mults at n=131) beats Lopez-Dahab mixed addition (8-11 mults) per point-sum at batch >=16 for n in 53..131, no Z coordinate.
- **Prediction**: 1.3-1.8x at batch 16-64 at n=131; break-even batch 4-8 when squaring is about 0.1 mult.
- **Cheapest test**: GF(2^n), n in {53,83,131}: affine+batch+Itoh-Tsujii vs LD mixed add, interleaved, A/A, batch 1,4,16,64; ns and mults per add.
- **Falsifier**: LD mixed add at least as fast at batch 16 for n=131, or break-even batch >64.
- **Lean gap (assumed, not proved)**: The Itoh-Tsujii multiplication count formula (floor(log2(n-1)) + wt(n-1) - 1) and the LD mixed-add cost 8M+5S are assumed; H099_claim for general n in 53..131 is stated, only n=131 is proved; real ns per add is empirical.

### H100 — Rotation-based membership test g(sigma)x=0 with sparse generator

- **Handbook**: 5.3.5 Fast arithmetic using normal bases, 5.2.1 Normal bases  ·  **Prior art**: partially-tried  ·  **Lean**: proved (`H100_claim`; theorems: `H100_rotPow_eq`, `H100_rot_pow_n`, `H100_apply_rot`, `H100_apply_xor`, `H100_kernel_xor_closed`, `H100_kernel_rot_invariant`, `H100_cost_ratio`, `H100_claim_holds`, `H100_divides_x7`, `H100_divides_x15`)
- **Claim**: Membership in V=ker g(sigma) costs wt(g) XORs of rotations (normal basis), 8-15x cheaper than the polynomial-basis matrix test, but whole-loop gain is only 1-5% since roots and inversions dominate; likely null.
- **Prediction**: Membership 8-15x fewer cycles; loop 1-5%; net <1.05x or negative if multiplication must run in the normal basis.
- **Cheapest test**: n=127, V dim 63 or 7*9: membership microbenchmark in both bases (1e8 candidates), then the n=31 toy S3 pair loop; perf-ipc where available.
- **Falsifier**: Full-loop speedup >1.2x (then it matters), or membership speedup <3x.
- **Lean gap (assumed, not proved)**: Normal-basis representation of Frobenius as rotation, g | x^n-1 for the chosen n=127 generator (checked by decide only for n=7 and n=15), and the whole-loop speedup (1-5%, likely null) are not proved.

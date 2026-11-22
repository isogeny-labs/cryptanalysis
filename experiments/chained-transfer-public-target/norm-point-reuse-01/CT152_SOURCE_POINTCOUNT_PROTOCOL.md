# CT152 protocol — independent exhaustive original q223 source point census

16 November 2026 UTC. [pcc:unverified]. Root crypto #3877; stacked cryptanalysis #1589.

## Target, fixed *before the controlled follow-up source replay*

Independently reconstruct the exact original-source elliptic curve selected by `CheckedInstance::construct()`, whose original engine calls `Inst::search(223,1,200000)`. The original source is over K = F_223[z]/(z^3-3), with z^223 = 183z. The seed1 expected constructor accepts trial 91, source order 11,092,292=4*2,773,073, short model coefficients
`a2=[127,56,199]; a4=[152,35,36]; a6=[212,109,150]` and selected G = (x=[162,197,140], y=[45,11,207]). These values are **pre-existing target parameters**; their reproductions do not constitute independent validation of raw custody.

**Exploratory disclosure:** a first developer-local Python reconstruction and C++ exhaustive x-census were run *before* this protocol was committed, so those runs are explicitly retrospective. This protocol governs the controlled replay after publication, its source checks, and the verification status; do not relabel the exploratory work as prospectively preregistered.

## Independent evidence tests

1. A standalone Python reconstruction with no imports from the Rust producer reconstructs the source field, deterministic xorshift64* RNG, Frobenius, source curve, and group law, including seeded group-order prefilter. Require exact original trial, curve coefficients, generator, reported subgroup and total order. Confirm generator belongs to the curve and has exact prime order. Prove irreducibility of z^3-3 using the noncube criterion.
2. A separately written, bounded C++17 program using a *generic five-coefficient convolution* for the cubic field enumerates each of all 223^3 field elements as y, builds a full square-residue membership table, then examines each of the 223^3 x values independently. Classify RHS as 0 / nonzero square / nonsquare; compute N=1+#zero+2#nonzero_square.
3. The result must be exactly N=11,092,292, with expected zero=3, nonzero_square=5,546,144 and nonsquare=5,543,420; the residue roster must have (223^3+1)/2 entries. Verify all classification partitions and count independently.
4. Reject deliberately modified source coefficients, malformed generator/field and requested expected-point-count mismatch. Run ordinary and optimized Python, compare deterministic JSON and hashes, execute C++ twice and require identical integer counters (timing fields are descriptive only). Bound the local experiment to one field/canonical original source, <=128MiB peak RAM and <=180s; no EKS, GPU or paid cloud instance.
5. Keep all arithmetic and emitted canonical source constants in committed source. Include reproducible commands; no dependence on external credentials, untracked artifacts or producer Rust crates for the point counter.

## Interpretation / non-goals

A complete exact point census removes CT151's **reported-order premise** for the *original* selected q223 curve if the deterministic source binding holds. The fixed-nu12 alternative's N=11,086,844 remains independently uncounted. The separate K/k Weil-restriction identity, k-defined polarized quotient/isogeny and all original-vs-reuse 695/701 native Jacobian records are not established by this census. Neither primitive C169/C13/D timings nor full same-target cold ECDLP is measured. A producer-run and hosted code check are not a PCC signature; standing remains [pcc:unverified].

## Sources inspected

cryptanalysis `experiments/chained-transfer-public-target/native/original/{common.rs,ghs.rs}`; `native/src/lib.rs`; `fixed-jacobian-chain-01/src/lib.rs`; CT149–CT151 reports; original crypto #3877 and #4215; concurrent native pricing #1562 and genus/LP work. Research-KB MCP/Conductor unavailable in this runtime; no novelty or prior-art absence claim.

## Exit

Commit standalone source, controlled replay receipt, test failures, exact-head source CI; independent scientific validation/PCC remains a separate gate. No original evidence/ledgers/CI gates/paid compute modified.

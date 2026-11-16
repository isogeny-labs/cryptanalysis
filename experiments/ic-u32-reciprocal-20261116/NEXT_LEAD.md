# Exact reciprocal reduction for bounded matrix coefficients

Current incremental dense Gauss uses a generic u128 modular product for every
multiply/subtract. All five registered scaling subgroup moduli fit in32bits.
The standalone Rust prototype computes mu=floor(2^64/m) once for2<=m<=2^32-1.
For any u64 x, q=floor(x*mu/2^64) underestimates floor(x/m) by at most one:
0<=x/m-x*mu/2^64<1. Therefore q*m<=x and0<=r=x-q*m<2m. One subtraction when
r>=m returns the exact canonical residue. Every u32 product fits in u64.
Unsupported moduli must retain the original arithmetic. Preserve pivot order,
row statuses, recovered columns, row-operation accounting and defaults.

[pcc:unverified] The standalone prototype passes exhaustive numerators0..65535
for moduli2..255, plus1500000 deterministic full-width numerators and1500000
u32 products across15 moduli including near-u32-limit values, quotient boundaries
and invalid-constructor rejection. These are arithmetic correctness checks only.
An opt-in incremental-gauss-u32 matrix caller is now implemented, preserving the generic default and falling back for larger moduli/noncanonical rows. There is no performance result. Current five-field
prefix scaling uses the frozen earlier binary and is unaffected.

[pcc:unverified] Differential checks now compare complete row states, pivots, all pinned columns, statuses and work after4000 rows across ten moduli and five widths, including large-modulus fallback. The existing end-to-end pipeline check also passes with the new matrix and identical scalar, rank, row and work counts. Strict library Clippy passes.

Next: inspect emitted hot-loop assembly, then freeze a fresh complete-pipeline comparison with existing matrix controls.
Charge constructor/preparation and all work; report row counts separately from
native wall. Do not substitute this prototype into a running or frozen panel.

The frozen scaling phase breakdown also limits the expected complete-pipeline
benefit: N27 prefix setup14.44ms, query14.38ms, matrix1.84ms medians. A matrix
component gain alone cannot explain or promise a large complete-pipeline gain.
Future broad improvements should also address query/walk and preparation costs.

[pcc:unverified] Local aarch64 assembly audit of the standalone multiply wrapper emits umull, umulh, msub, cmp/csel and sub in the hot function, with no division or helper call there. The generic comparison emits a call to ___umodti3. This is static code generation, not runtime performance or a pipeline result; reciprocal construction still performs its one-time division.

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
There is no production caller and no performance result. Current five-field
prefix scaling uses the frozen earlier binary and is unaffected.

Next: inspect emitted hot-loop assembly, add an opt-in matrix implementation,
differentially compare complete row states and all pinned columns to the existing
implementation across independent/dependent/inconsistent rows and modulus edges,
then freeze a fresh complete-pipeline comparison with existing matrix controls.
Charge constructor/preparation and all work; report row counts separately from
native wall. Do not substitute this prototype into a running or frozen panel.

# Mask and half-trace generation exactly covers the frozen pair source

**Seven source-mask bits and two endpoint-sign bits per slot reconstruct all 960 frozen N41 pair outputs without storing point rows in the SAT formula.** The same arithmetic law reproduces all 32 signed outputs of eight archived Sage-audited N131 W23 seed edges. This establishes an exact compact source representation for the next target-conditioned search design. Two unpinned N41 Riemann–Roch queries, one using a 40-code sign ANF and one generating points by field and curve arithmetic, each reached its 185 s solver bound with status `BOUNDED_UNKNOWN`.

## Frozen N41 source and target

The instance is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t³+1)`, with curve `y²+xy=x³+1`, six source rotations `(0,6,12,18,24,30)`, and raw public target `Q=(2026560328086,1928332930914)`. The [source](../n41_sixpair_shared_target_20261017/join_input.tsv) has 40 canonical pair codes and four signed states per code in each slot; SHA-256 is `7fc0362121ecc510d9ec9ea62a17c1efc878cd96fed7292246675c1951f006fb`. The query enforces twelve distinct folded columns and seven distinct x coordinates including `−Q`. The known state IDs `(12,122,116,47,128,34)` serve only as an assignment control; all source masks and signs are free in both public queries.

The code/sign design writes each seven-coordinate `L(7O)` evaluation row as the exact two-bit algebraic normal form

`R(sa,sb)=R00 + sa(R00+R10) + sb(R00+R01) + sa·sb(R00+R01+R10+R11)`

with addition in `GF(2^41)`. It selects one of 40 codes and then evaluates the row. [SignANF.lean](SignANF.lean) proves the four sign cases bitwise, and the [independent audit](audit_result.json) checks all `960×7=6,720` coordinate cases with separate field arithmetic. The [degree screen](degree_result.json) checked 5,904 output bits across the six nonconstant row coordinates and four sign terms: 2,949 require degree three on the 40-code selector domain. Degree-three monomials already span all 40 samples, so that fit does not establish a compact N131 interpolation.

The arithmetic design derives each endpoint from its mask `a` or `b=a XOR 56`. If `u` is the linear half-trace-basis coordinate, set `x=1+u⁻¹`, solve `z²+z=x+x⁻²` by half-trace, and choose `y=x(z+sign)`. It adds the two endpoints on the binary curve, applies the slot's Frobenius rotation, and evaluates the seven RR function rows. Its only N41 source-code table is the 40 allowed masks and folded-column exclusions; it contains no point-row table. The frozen [geometry preflight](implicit_result.json) matches every one of the 960 generated pair points to the archived source, allowing for its independent sign-label convention. The [independent field/group auditor](implicit_audit_result.json) repeats all 960 point sums with separate multiplication and inversion, checks the known six-pair group sum, and recounts the serialized formula.

| Same N41 source and public target | Variables | CNF clauses | XOR rows | AND gates | XCNF bytes | Build wall | Public query |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 40-code, two-sign ANF rows | 62,309 | 113,788 | 24,542 | 36,981 | 2,828,563 | 0.459 s | `BOUNDED_UNKNOWN`, 185.012 s |
| Seven-bit mask and arithmetic point generation | 161,025 | 301,717 | 60,333 | 99,108 | 7,528,896 | 0.987 s | `BOUNDED_UNKNOWN`, 185.019 s |

Both one-worker queries used the same hashed CryptoMiniSat binary, `--threads=1`, `--maxtime=180`, a 185 s parent cap, and a 4 GiB memory boundary on the ordinary local host. Their observed child peak RSS values were 265,601,024 B and 225,378,304 B. Both known assignments satisfied every CNF and native-XOR row. The raw solver outputs, protocols, formula hashes and statuses are retained; neither transcript contains a terminal solver result. These are point-decomposition stage measurements with `candidate_id: null`.

## N131 source-law transfer and search decision

For the archived W23 source on `EC1N131Ckb1heb5f1998f20b`, the mask is a 23-bit `w`, eligibility requires `Tr(w)=Tr(w⁻¹)=0`, and the fixed seed is `898618`. The [frozen transfer replay](n131_transfer_result.json) independently computed `u=halftrace(w)`, both endpoint signs, and four pair sums for each of eight [Sage-audited source edges](../n131_w23_sixpair_density_20261016/sage_audit_result.json). It matched both archived pair x roots on every edge: **8 edges and 32 signed outputs**. This sample validates the arithmetic source law on the N131 field; it does not measure full-domain coverage or a target relation.

The arithmetic generator removes the explicit signed-point table, but it increases the N41 Boolean circuit from 2.83 MB to 7.53 MB and leaves the same unpinned target search unresolved at its cap. The archived exact N41 three-plus-three join found a relation on this public target in 6.927 s under its separate ordinary-host run, so the next improvement must act on search, not only source encoding. The immediate experiment is an exact target-conditioned filter on **families of mask/code choices before endpoint signs and row products are expanded**. Freeze the filter, measure rejected families and surviving ordinary relations on this N41 source against the join, then preflight its N131 domain and resource use before the 600 s, 4 GiB public-point gate. The [proof map](PROOF_MAP.md) records the checked Lean results and the open curve-to-circuit bridge.

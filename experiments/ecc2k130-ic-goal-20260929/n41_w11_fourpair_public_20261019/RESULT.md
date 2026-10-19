# Four-pair public relations with 520 usable base points

An exact two-plus-two join found ordinary four-macro-pair relations for the frozen N41 public point at both W11 and W10. The W10 construction uses 520 distinct cofactor-projected, subgroup-usable base points and 255 signed/Frobenius-folded columns. Independent checked Sage reconstruction verified all eight source leaves, eight distinct columns within each relation, the raw group sum, inverse Frobenius transport, and cofactor-four projection. A W9 scan exhausted all 41 target-orbit orientations for the same source selector and four rotations with status `COMPLETE_NO_HIT`.

The instance is `EC1N41Ckb1h7d5e80d3c4d0`, `GF(2)[u]/(u^41+u^3+1)`, `y^2+xy=x^3+1`, subgroup order `549756390943`, cofactor four, with raw point `(1936680952394, 910597499030)`. The four slots use source seed mask 56 and Frobenius rotations `[0,12,24,36]`. W11 source choices were frozen from the audited five-pair table before the search. The W10 and W9 variants were frozen as nested code restrictions before each run. W11 found codes `[525,479,7,803]` at orientation 3; W10 found `[177,16,267,284]` at orientation 29.

| Width | Eligible codes | Actual usable base points | Folded columns | Native target-orbit result | Parent wall | Sampled peak RSS |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| W11 | 281 | 1,124 | 557 | Hit at orientation 3 after 4,373,459 lookups | 6.371 s | 140,214,272 B |
| W10 | 130 | 520 | 255 | Hit at orientation 29 after 7,876,637 lookups | 5.356 s | 50,167,808 B |
| W9 | 71 | 284 | 139 | `COMPLETE_NO_HIT`, 41 orientations, 3,256,384 lookups | 2.287 s | 33,144,832 B |

Each run used one worker, a 600 s parent cap, and a 4 GiB sampled RSS cap. W11 target-dependent native lookup took 3.893 s; its right table was ready at 1.339 s and both tables by 2.175 s from native start. W10 target-dependent lookup took 4.871 s after its table construction. These are point-decomposition components; a complete IC pipeline and paired rho measurement are separate work. `candidate_id` stays `null` until factor-base logs, relation rank, and target recovery are specified. The first W11 native compile failed because the linker used a full temporary filesystem; `compile_attempt1.txt` is retained. Two W11 Sage audit launches failed before computation because of cache storage and sandbox placement; `audit.stderr` and `audit_v2.stderr` are retained. The third launch used the checked Sage runtime recorded in `sage_runtime_info_v3.json` and completed with empty stderr. The W10 independent audit passed in 0.140 s internal time, as recorded in `w10/audit_result.json`. The checked Sage base audit in `base_audit_result.json` enumerated every source mask, both point signs, and every cofactor-four image; it confirmed the actual base sizes and folded-column counts above.

## N131 source-support experiment

The exact N131 curve is `EC1N131Ckb1heb5f1998f20b`, `GF(2)[u]/(u^131+u^13+u^2+u+1)`, `y^2+xy=x^3+1`, with group order `4r=2^131`, where `r=680564733841876926932320129493409985129`. The source seed mask is 898618. A frozen Python diagnostic sampled 8,192 distinct nonzero codes separately at widths 33 and 34, then applied the exact source trace and two inverse-trace filters from `output_first_math.py`.

| Width | Valid / sampled | Valid fraction, Wilson 95% | Estimated eligible codes | Estimated signed pair states |
| --- | ---: | ---: | ---: | ---: |
| W33 | 2,009 / 8,192 | 0.2452 [0.2360, 0.2547] | 1.053 billion | 4.213 billion |
| W34 | 1,999 / 8,192 | 0.2440 [0.2348, 0.2534] | 2.096 billion | 8.384 billion |

The independent code samples and eligibility outcomes are in `n131_density_protocol.json` and `n131_density_result.json`. Their counts estimate source support only. The uniform-group heuristic `S^4/2^131` gives 0.116 W33 or 1.815 W34 four-pair witnesses per target orientation; those numbers are predictions, not relation measurements, and Frobenius orientations need not behave independently. A literal two-plus-two table requires about `S^2`, or `1.78e19` W33 and `7.03e19` W34 pair entries. The estimated number of folded columns before overlaps is `2C`, approximately 2.11 billion for W33 and 4.19 billion for W34. Exact actual base sizes, orbit overlaps, rank, and final linear algebra remain to be measured.

The next concrete test is an N41 target-coupled four-pair encoding that prunes joint code families before pair materialization. Freeze the public target, source masks, and resource cap; compare its ordinary-query output and complete charged work against these exact joins. Promote it to N131 only if its measured pruning removes the `S^2` table boundary while preserving independently audited witnesses. Test W33 before W34 because its estimated column count is half as large; use all target-orbit orientations only after one-orientation correctness is established. The W9 `COMPLETE_NO_HIT` row is an exact result for the frozen code restriction and four rotations, rather than an assertion about other W9 constructions.

## Replay and proof

Run `python3 archive_verify.py` in this directory. It checks the frozen source hashes with path relocation, output hashes, caps, source codes, all eight relation columns, both relations again with an independent pure-Python curve implementation, and the W9 41-orientation terminal receipt. For a new checked-Sage audit, restore the archived directory to the original `/private/tmp/ecc2k130-w34-fourpair-20261019` path or create a new versioned protocol with updated paths and hashes; invoke `/Volumes/SSD990/cryptanalysis/sage -python audit_sage_v3.py` and the corresponding W10 and base-audit scripts. The original protocols and raw outputs are immutable records of the completed runs.

The group-theoretic Frobenius pullback step is already covered by `SixPairTargetOrbit.relation_pullback` in `../n41_sixpair_target_orbit_20261016/OrbitTransport.lean`. Its theorem is quantified over the relation-list length, so it covers these four pair outputs. The proof assumes an additive automorphism and inverse, a base closed under inverse Frobenius, and the raw-to-public cofactor relation. The checked Sage audit supplies the concrete curve and point checks; the concrete curve-to-Lean bridge remains open. Rechecking the pinned Lean 4 v4.34.1 module returned only `propext` and `Quot.sound` from `#print axioms`.

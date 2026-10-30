# Result verification and formalization map

| Result | Lean declaration | Current verification |
| --- | --- | --- |
| Prescreen selects the first eligible 40-point class at p78157 | None | Checked-Sage producer and independent Sage audit re-evaluate primality, curve order, eligible cases, class points and projection |
| Base-plus-direct relation rank is 32 over (F_{1303}) | None | Independent Sage point enumeration and matrix rank; exact 40-column matrix formalization remains open |
| All 40 source equations and 194 Hecke relation rows are valid | None | Independent Sage curve-group replay; Lean definitions for this concrete curve and degree-13 source maps remain open |
| Every frozen checkpoint rank ends at 33, below the rank-39 gate | None | Independent Sage matrix rebuild and rank checks for both orders; full finite-field rank theorem remains open |
| The 194 Hecke candidate supports have four increasing source indices; 193 use two residue-1 sources, one uses zero, and none uses four | `ResidueSupport.supports_strict`, `mixed_support_count`, `zero_support_count`, `all_one_support_count` | Exact audited support list and class residues; Lean kernel checked, no axioms |

The contribution here is a measured prospective holdout with complete source and checkpoint receipts. `formal/ResidueSupport.lean` proves the feasible finite support-composition result from audited data. A faithful Lean proof of the numeric ranks would also require the p78157 curve model, its 40 point constants, the degree-13 source equations, the enumerated row matrix over (F_{1303}), and a checked rank certificate for each checkpoint. Those definitions and certificates are not yet present, so rank formalization remains partial. The source scripts and independent audit retain the finite data needed for that next step. Lean 4 `v4.35.0-rc4` is pinned, `lake build` passes, and `#print axioms` reports no axioms for the four checked declarations; `lean4checker --fresh` is unavailable here.

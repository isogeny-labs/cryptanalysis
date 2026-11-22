# Proof map

| Result | Declaration or replay | Exact scope | Status |
| --- | --- | --- | --- |
| Degree-two cubic root counts | `X011P941Degree2Roots.exact_root_counts` and `root_count_histogram` | 112 pinned cubics, all 941 field residues; 56 one-root and 56 three-root | Lean checked, no axioms |
| Degree-three quartic root counts | `X011P941Degree3Roots.exact_root_counts` and `all_have_two_roots` | 112 pinned quartics, all 941 field residues; two roots each | Lean checked, no axioms |
| Polynomial identity with Hecke moments | `audit_sage.py` | Rebuild archived source and apply closed-form Newton identities at every frozen source point | Independent Sage replay passed; Lean modular-function bridge open |
| Complete rational neighbors and closed rows | `audit_sage.py` | All x/xy moments, group sum, modular polynomial, membership and row identity for 56 degree-two sources | Independent Sage replay passed; point/Hecke formalization open |
| Direct rows and ranks | `audit_sage.py` | Pair-index enumeration of signed support 1–3 and matrices over `QQ`, `F_2`, `F_3`, `F_5` | Independent Sage replay passed; Lean matrix-rank formalization open |

`generate_formal.py` checks the frozen producer-result hash against `post-run.json` and `audit.json` before writing the coefficient lists. Both modules build with `lean <module>.lean` under pinned Lean `v4.34.1` and no third-party dependency. Their retained build outputs show the `#print axioms` audit. Neither contains `sorry`, `admit`, a research axiom, or native-evaluation bypass.

# Proof map

| Result | Declaration or check | Exact scope | Status |
| --- | --- | --- | --- |
| 84 listed cubics | `X011P1009.certificate_size` | Length of the generated coefficient list | Lean checked, no axioms |
| One rational x root per listed cubic | `X011P1009.each_cubic_has_one_root` | For each listed coefficient tuple, exactly one `x ∈ {0,…,1008}` satisfies the cubic modulo 1009 | Lean checked, no axioms |
| Each cubic is the degree-two neighbor-x polynomial of its recorded source | `audit_sage.py` source-by-source rebuild | Corrected X011 ledger, archived regularized Hecke source, p1009 | Independently replayed in Sage; formal bridge open |
| Direct relation counts and ranks | `audit_sage.py` exhaustive replay | Signed supports 1–3, `QQ` and `F_17` | Independently replayed in Sage; Lean rank formalization open |

Lean command: `lean P1009Degree2.lean` in this directory. `build-output.txt` contains the `#print axioms` output. The pinned core toolchain is `leanprover/lean4:v4.34.1`; no third-party Lean dependencies are loaded. The generated coefficient tuples are bound to `polynomial-certificates.json` by the digest in `audit.json` and checked by `generate_formal.py`. The mathematical bridge from the archived modular implementation to those coefficients and the matrix ranks is explicit above rather than assumed in the Lean theorem.

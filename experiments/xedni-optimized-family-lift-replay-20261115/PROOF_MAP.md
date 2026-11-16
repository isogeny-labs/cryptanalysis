# Proof and verification map

The imported structural source is `experiments/xedni-first-hit-dominance-20261115/formal/FirstHitDominance.lean` at SHA-256 `d7983175cfc7845b60799c36edb16f5823652e2c6450de1320e5504d85393245`. Its saved checked build output is SHA-256 `4200858c7d1092621bd3e8ca6cd7de5af9227ae0eba802e858edbb44ee6ea7ab`.

| Result | Formal or executable check | Exact scope | Status |
| --- | --- | --- | --- |
| Rational relation reduces to the same public relation | `XedniFirstHitDominance.relation_reduces` from PR #1611 | Compatible reduction homomorphism, same query and coefficient list | Checked Lean in parent artifact; not rebuilt here |
| Selected public relation rows | `run.py` public group tests; `audit_sage.py` fixture equation and group replay | Eight archived prime-order fields, 13 frozen selected vectors, all 30,008 ordered queries per arm | Independently checked |
| Zero selected rational relation rows | `audit_sage.py` rational elliptic-curve group tests | Exactly 4,844 accepted tests under each saved centered/shifted CRT curve law | Independently checked Sage; Lean formalization partial |
| Positive rational control | `audit_sage.py` checks parent `(1,2)` witness | Both arms at `p=47`, archived query 239 | Independently checked Sage |
| Probe and failure accounting | Archived raw row hashes, row status and attempts; `verify.py` seal | Every archived query in both arms | Checked |

The missing Lean bridge for the zero-yield census is a formal definition of the rational CRT curve/point constructions in the 16 field-arm cells, their exact point laws and all 9,688 arithmetic decisions. The checked structural implication does not itself decide rational existence. The full finite result remains supported by saved raw rows and independent checked-Sage replay.

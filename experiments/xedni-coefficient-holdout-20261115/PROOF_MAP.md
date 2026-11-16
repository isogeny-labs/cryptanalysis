# Proof map

The formal model fixes `Q = 17G`, the first query coordinate `t₁ = 0`, and a generator of order `q`. Its `equation q c t` is the exact modular coefficient condition for `c₁Q + c₂(Q−tG) = O`. The checked Sage audit supplies the bridge to the specified curve and public points in each field, including generator order, admission, and independent scalar replay.

| Result | Lean declaration in `formal/FirstFamilyHit.lean` | Hypotheses and scope | Status |
| --- | --- | --- | --- |
| The indexed vector order enumerates the frozen 14-element family | `vector_image_eq_family` | Exact `Fin 14` index and `family` definitions | Checked |
| `(1,1)` relates at offset 34 | `relation_at_34` | Every modulus `q`; `Q=17G`, `t₁=0` | Checked |
| No earlier admitted relation | `no_relation_before_34_751`, `_883`, `_983`, `_1103`, `_1153`, `_1453`, `_1459` | Each stated modulus; every `t : Fin 34` except `t=0` (duplicate point) and `t=17` (identity); every `j : Fin 14` | Checked |

`lake build FirstFamilyHit` completed 3,138 jobs with pinned Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. All nine declarations have `#print axioms` output in `formal/build-output.txt` with only `propext`, `Classical.choice`, and `Quot.sound`. The group-law bridge is checked by `audit.py`, rather than formalized as a Lean elliptic-curve theorem. The 452 vector tests and 3,065 group-add calls are independently audited executable counts, not Lean theorems.

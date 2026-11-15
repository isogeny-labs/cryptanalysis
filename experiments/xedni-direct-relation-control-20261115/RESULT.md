# Direct reduced-relation control for the two-point CRT panels

The publicly computable relation `P₁+2P₂=O` appears within the first 3–66
ordered target queries in every field of the frozen eight-field panel. The
first rational-lift relation occurs at query 239 for `p=47` in both lift
policies, and at query 571 for `p=251` in the shifted policy. The direct
relation supplies the scalar at its first occurrence: with `Q=wG` and
`Pᵢ=Q−tᵢG`, it is equivalent in the prime-order subgroup to
`3w=t₁+2t₂ (mod r)`. All eight subgroup orders lie in `[43,79]`, so 3 is
invertible. The direct test uses only the public points; the fixed scalar
17 is used afterward for fixture replay.

| Base prime `p` | Subgroup `r` | First direct `t` | First direct query | First centered rational query | First shifted rational query | Coefficient probes to first centered / shifted rational hit |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 47 | 43 | `(0,4)` | 5 | 239 | 239 | 41,466 / 43,777 |
| 101 | 53 | `(0,52)` | 53 | — | — | — |
| 191 | 53 | `(0,52)` | 53 | — | — | — |
| 211 | 79 | `(0,65)` | 66 | — | — | — |
| 251 | 61 | `(0,56)` | 57 | — | 571 | — / 102,212 |
| 281 | 73 | `(0,62)` | 63 | — | — | — |
| 347 | 47 | `(0,2)` | 3 | — | — | — |
| 349 | 71 | `(0,61)` | 62 | — | — | — |

There are exactly `r−1` admissible reduced-relation rows per field, 472 in
all. The omitted solution in each field has both sampled points at the
identity. The audit recomputes the first direct event using independent
finite-field group arithmetic, then checks that both saved raw streams give
the same first event and uncompressed row hash. It independently replays
scalar recovery on every first direct hit. The rational-hit probe prefixes
come from the saved per-row candidate counts. These counts retain all
queries before a hit, including failed construction rows.

## Algebra and scope

In any abelian group, substituting `Pᵢ=Q−tᵢG` and `Q=wG` gives

`P₁+2P₂=(3w−t₁−2t₂)G`.

In scalar coordinates of a prime-order subgroup, zero is equivalent to
`3w=t₁+2t₂`. Thus checking the reduced group relation on the same fixed
query schedule gives the scalar at or before any rational relation with the
coefficient vector `(1,2)`. A rational relation that reduces at the base
prime must lie in this reduced event. The original xedni method can choose
other coefficient vectors, lift laws, and curves; this control addresses
the measured two-point template and its exact public query order.

The pinned Lean module proves the additive-group identity and scalar-field
recovery implication under their exact hypotheses. `PROOF_MAP.md` maps the
abstract reduction-homomorphism step and its status. The earlier structural
xedni development studies finite coefficient families more generally.

## Reproduction

`protocol.json` pins both input result digests, arithmetic sources, field
list, query law, and 30,008-query cap. Run
`python3 experiments/xedni-direct-relation-control-20261115/audit.py` to
replay the control. The independent audit and its zero-length stderr are
retained with the result. `SEAL.sha256` binds the files. These are exact
query-rank and coefficient-probe diagnostics, with no CPU isolation or
same-target wall-time comparison attached.

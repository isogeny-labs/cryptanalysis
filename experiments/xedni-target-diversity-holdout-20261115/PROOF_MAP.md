# Proof map

The formal equation is `((a+b)d−bt)=0` in `ZMod q` for `Q=dG`, `R₁=Q`, and `R₂=Q−tG`. The eight field rows in `result.json` supply `(q,d,t)` and the successful coefficient vector. The checked Sage audit confirms that this equation matches the specified elliptic-curve group law and admission rule.

| Field | Hit theorem | Earlier-offset theorem | Hypotheses and status |
| ---: | --- | --- | --- |
| 773 | `relation_at_hit_773` | `no_relation_before_hit_773` | `q=751`, `d=496`, every `t : Fin 241` except `0` and `d`, every `j : Fin 14`; checked |
| 863 | `relation_at_hit_863` | `no_relation_before_hit_863` | `q=883`, `d=671`, every `t : Fin 35` except `0` and `d`, every `j : Fin 14`; checked |
| 883 | `relation_at_hit_883` | `no_relation_before_hit_883` | `q=883`, `d=260`, every `t : Fin 130` except `0` and `d`, every `j : Fin 14`; checked |
| 983 | `relation_at_hit_983` | `no_relation_before_hit_983` | `q=983`, `d=671`, every `t : Fin 47` except `0` and `d`, every `j : Fin 14`; checked |
| 1049 | `relation_at_hit_1049` | `no_relation_before_hit_1049` | `q=1103`, `d=775`, every `t : Fin 119` except `0` and `d`, every `j : Fin 14`; checked |
| 1153 | `relation_at_hit_1153` | `no_relation_before_hit_1153` | `q=1153`, `d=530`, every `t : Fin 93` except `0` and `d`, every `j : Fin 14`; checked |
| 1423 | `relation_at_hit_1423` | `no_relation_before_hit_1423` | `q=1453`, `d=342`, every `t : Fin 114` except `0` and `d`, every `j : Fin 14`; checked |
| 1433 | `relation_at_hit_1433` | `no_relation_before_hit_1433` | `q=1459`, `d=430`, every `t : Fin 87` except `0` and `d`, every `j : Fin 14`; checked |

`formal/lean-toolchain` pins Lean `v4.35.0-rc4`; `formal/lake-manifest.json` pins Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. `formal/build-output.txt` records the successful build and `#print axioms` output for all 16 declarations. The group-law bridge and operation counts are independently checked by `audit.py`; those are not claims of the Lean module.

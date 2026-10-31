#set page(paper: "a4", margin: (x: 18mm, y: 17mm))
#set text(font: "DejaVu Sans", size: 9pt)
#set par(justify: true)
#show heading: set text(fill: rgb("162541"))

= Cryptanalysis Lean source-tree reconciliation

_Frozen cryptanalysis commit_ `d3673ee089dd2a3a4ba15da087b95ebf2fb8e123` · 2026-10-31

The source-tree inventory contains *184 tracked Lean files*. Its 97-source corpus receipt leaves 87 files outside that particular receipt. An exact-commit hosted `corpus` job accounts for the 87 paths by separate machine gates and verifier roles. These are file and machine-check counts, not proof-coverage or experiment-validity percentages.

#image("scope.svg", width: 100%)

== Observation

- *39* paths passed dedicated source-bound native module audits: 153 theorems total, with zero failing and zero trusted exceptions.
- *37* paths passed native builds and declared theorem/lemma axiom-output checks through the generic current-source gate. This route is narrower than the dedicated exhaustive module audit.
- *One* Hasse squared-bound source passed its separate pinned build and transitive audit. Its prior independent review validates the conditional arithmetic implication.
- *Seven* paths are verifier self-test fixtures. The two expected pass cases and five expected fail cases had their specified outcomes. *Three* further paths are verifier implementation sources, not research theorem claims.

== Evidence binding

The terminal successful `corpus` job `124428817573` ran on the exact frozen commit and reported `native added theorem modules checked: 77`. Its log has 39 named audit rows, 37 matched compile/axiom-output pairs, and seven fixture rows. The 77 total is 39 + 37 + one Hasse source. `reconciliation.json` gives all 87 paths and the relevant log lines. The job log SHA-256 is `9e0c9a0acb5184add97faf84129024327904a5c7d98e33bce6e9d78008463916`; the gate source SHA-256 is `0a3e5f4fa78ba768ff36ce0628a9b17f17152fd8f23d1bb9ffda2eb36116842d`.

== Interpretation and next check

The file-level gap in the 97-source receipt is reconciled at this frozen commit. The machine results do not compare theorem types against historical research claims or replay the experiments. The four known-label ring identities and seven pair-index lemmas pass named native audits; independent elaborated-type comparison for the former and semantic/concrete-subgroup review for the latter remain open. The three verifier implementation files need their own software review. Next, bind each historical claim to a theorem type and execution record, review its concrete bridges, and repeat the inventory at the new main head.

_Source links and a reproduction checklist are in `README.md`. No performance number or dashboard value changes in this packet._

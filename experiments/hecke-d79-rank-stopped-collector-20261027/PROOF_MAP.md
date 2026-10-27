# Proof map and executable bridge

| Result | Proof or check | Status |
| --- | --- | --- |
| Two-, three-, and four-term complement identities underlying the signed-pair index | `PairIndexCancellation.two_cancel_iff`, `.three_cancel_iff`, `.four_cancel_iff` in the pinned parent pair-index PR | Lean build and axiom audit passed there; only `propext` reported |
| Each source append emits relations whose largest source index is that source, and all retained-prefix relations are present | `IncrementalPrefix.prefix_step` plus the ordered split argument in the parent `PROOF_MAP.md` | Lean recurrence checked; exact Python loop bridge audited on ten sealed traces and nine live cases |
| Incremental F_q rank equals the matrix rank of baseline plus emitted rows after every append | `validate_existing_sage.py` and `audit_sage.py` | Ten prior complete traces and all 355 live source steps checked by independent Sage matrices |
| At rank 39 one q-projection anchor determines and replays all 40 class logs | `audit_sage.py` | p103357 control checked pointwise over F_197 |

The mathematical prefix recurrence and pair-complement identities are general statements. The curve-group equations, exact source-lift outputs, rank matrices, and Python loop behavior are checked by Sage against frozen inputs, not encoded as Lean elliptic-curve objects. The formal toolchain/dependency revisions and `#print axioms` output are retained under `formal/`.

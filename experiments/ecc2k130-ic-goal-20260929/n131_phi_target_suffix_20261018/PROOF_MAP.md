# Backward cut proof map

The exact group recurrence used to generate target-conditioned backward pins
is checked in [BackwardCut.lean](BackwardCut.lean). The toolchain is pinned to
Lean 4.34.1, commit `5045d0056413266e57c625dcd7c365b10e377c52`; only
the bundled `Std` and Lean `Init.Grind.Ring.Basic` modules are imported.

| Mathematical statement | Lean declaration | Hypotheses | Check |
| --- | --- | --- | --- |
| If a prefix sum plus three fixed signed suffix points equals the chosen endpoint, the prefix sum is the three-step backward subtraction. | `BackwardCut.necessary` | Any `AddCommGroup G`; exact endpoint group equality. | Built, no axioms. |
| The backward value gives the exact four-part group sum. | `BackwardCut.sufficient` | Same group and explicit backward equality. | Built, no axioms. |
| The endpoint equation is equivalent to the backward lookup equality. | `BackwardCut.exact_cut` | Same group. | Built, no axioms. |

Run `lean BackwardCut.lean` from this directory. The actual command output is
in [lean_check.log](lean_check.log), including `#print axioms` for all three
theorems. `lean4checker --fresh` was not used. The theorem speaks about the
curve's group law abstractly; the bridge from group points to archived
131-bit phi coordinates and XCNF variable positions is separately checked by
[freeze_sage.py](freeze_sage.py), whose rebuilt formula hash matches the
archived source. The Lean theorem does not encode that concrete bridge.

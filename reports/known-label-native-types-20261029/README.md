# Native type evidence for known-label identities

T-790 addresses the missing elaborated-type evidence identified by the historical claim matrix and the prior known-label review. This is evidence collection infrastructure; no scientific promotion is made.

## Requirements and current status

| Requirement | Status and evidence |
| --- | --- |
| Preserve four frozen producer proofs and build pins | SHA-256 bindings in bindings.json; original Algebra.lean unchanged |
| Collect exact types from newly built module | Implemented: isolated CollectedTypes.lean imports the fresh original .olean and runs explicit, fully qualified #check commands |
| Refuse native failure or incomplete output | 32 Python tests pass; missing, duplicate, wrong-namespace, empty, changed-wrapper and command-failure controls included |
| Establish actual native types | Pending hosted Lean gate; synthetic test output is not evidence of elaboration |
| Independently compare claims to types | Pending actual native output and independent review |
| Complete historical validation | Open; these four ring identities do not establish graph/group, probabilistic or execution bridges |

## Prior evidence and implementation

The source is docs/known-label-next-leads-20261028/Algebra.lean, SHA-256 d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d. The existing pinned native corpus gate compiles those original bytes into an isolated directory and audits the exact four theorem names and transitive axioms. This change imports that same compiled module from the isolated LEAN_PATH and prints all four elaborated types. Universe, explicit binder and full-name options are enabled. Header completeness checks are an output gate, not a semantic proof.

The wrapper source, its SHA-256, actual stdout, and stdout SHA-256 are printed between named markers in the native log. Source and workspace hashes remain checked around native work. Old reports and receipts are preserved. No local native Lean build or experiment was run; the shared heavy-build reservation remains owned by another task.

Reproduce software controls: `PYTHONDONTWRITEBYTECODE=1 python3 tools/lean/test_current_corpus_gate.py -v`. Full native evidence must come from the existing lean-proof-gate workflow at the final PR head. This change is separate from T765/T786's archival-only approval and does not consume or extend that authorization.

## Review and graph scope

Independent review must inspect the fresh-module import, exact names, failure propagation, isolation and output retention, then compare the native types to each intended ring identity. Existing independent mathematical reviews remain historical scoped inputs; they do not certify this new instrumentation. No claim is marked validated_scoped here. The diagram shows the missing evidence link; no performance graph changes are justified.

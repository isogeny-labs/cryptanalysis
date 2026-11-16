# Continue CI without unrelated S3 restoration

The user authorized proceeding without S3. Head `77c4a311` corrected the N83
unit job. Its initial current-head read then found eight other failures at
S3 restore, before the actual checks: artifact validation, binary-genus-two
native/Lean, and five analysis jobs. Their complete provider logs are retained
here. Preserve every real check and frozen input.

Extend opt-in job-scoped inference to these three workflows. Event path
filters select runs; they do not declare runtime data inputs. Shared runtime
environment and dispatch defaults remain conservative inputs. Remove only
generated restores whose remaining job contents have no moved-data reference.
Actual consumers retain required restoration.

Move the existing clang-format exclusion expression unchanged into a tracked
configuration file, so the dependency scanner no longer mistakes excluded
historical source paths for data reads. Validate exact selection equivalence
against all tracked paths and additional positive/negative examples.

Acceptance: preserve non-bootstrap checks/triggers/timeouts/commands, all
format exclusions, original IC/native/Lean source and frozen evidence. Run
the complete artifact regression suite (including event-selector versus
runtime-default controls) and global workflow wiring. Retain failed logs and
source-scoped validation, append unsigned evidence and push the concrete fix.
Hosted correctness results remain pending until those checks actually run.
No benchmark or measured runtime advantage follows from this CI correction.

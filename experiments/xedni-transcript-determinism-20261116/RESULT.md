# Visible labels determine adaptive affine forms

The checked `dlp_forms_from_transcript` theorem establishes that a complete
visible label tuple fixes the affine form trace of any finite
label-adaptive addition/subtraction program begun at `G,Q=wG`. Its
`dlp_group_from_transcript` companion equates each actual group point with
evaluation of that fixed form at `w`. For an informative equality of two
actual group points, the checked `dlp_collision_mem_candidates` theorem
places `w` in the transcript's symbolic collision-candidate set;
`transcript_candidate_bound` caps that set at `m²` for `m` stored forms.
The scalar-to-generator map must be injective for the collision implication.

The frozen Z/7 replay from PR #1637 contains **30,240** executions with
five stored forms each. Grouping by complete visible labels produced
**4,686** distinct transcripts, **720** of them shared by more than one
scalar. Reconstructing commands and forms solely from each label prefix
matched every source execution. An independently audited amendment then
enumerated the informative candidate set for every transcript. Its set
sizes were 3 (21 transcripts), 4 (60), 5 (1,305), 6 (1,500), and 7
(1,800). All **25,920** executions with an informative group equality had
their scalar in the corresponding candidate set, with zero mismatches.
The independent audit enumerated all seven field values for each
transcript and checked every saved candidate set exactly.

The per-transcript candidate bound is now linked to the actual adaptive
program. The next theorem must count how often each transcript can occur
under the uniform target and random-bijection laws before the first
informative collision. A bound on each transcript's candidate set alone
does not determine the total success probability. Public curve-coordinate
observations remain a separate xedni mechanism.

`protocol.json` froze the complete-label reconstruction before its run.
`candidate-protocol.json` records the later candidate-set amendment and
pins the prior result and transcript-row hashes. `SEAL.sha256` binds both
receipts, sources, raw transcript rows, results, independent audits, and
the Lean build. Lean v4.35.0-rc4 and Mathlib
021c46bdd042f67b538b9f9871d556a93713a9a9 are pinned; `lake build
TranscriptDeterminism` passed 3,143 jobs with only standard foundational
axioms in the nine new declarations.

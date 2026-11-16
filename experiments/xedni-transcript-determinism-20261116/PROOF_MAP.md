# Visible-transcript form determinism proof map

Lean toolchain v4.35.0-rc4; Mathlib revision
021c46bdd042f67b538b9f9871d556a93713a9a9.

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Initial trace embeds in final trace | `programLe` | Typed finite adaptive add/sub program |
| Read initial labels from a final label tuple | `prefixLabels` | Same program and complete visible label tuple |
| Construct all affine forms from labels alone | `formsFromTranscript` | Field; program; complete visible labels; initial forms |
| Actual group execution preserves its initial points | `runGroup_prefix` | Additive group; bijective encoding; program |
| Executed forms equal transcript-reconstructed forms | `runForms_eq_transcript` | Initial point/form evaluation invariant; complete labels equal actual encoded output |
| Specialize form equality to public `G,Q=wG` | `dlp_forms_from_transcript` | Field/module; complete labels of actual program execution |
| Actual group trace equals evaluation of transcript forms | `dlp_group_from_transcript` | Same |
| Informative group equality puts scalar in candidate set | `dlp_collision_mem_candidates` | Finite field; injective scalar-to-`G` map; distinct forms; pair order; matching actual group points |
| Candidate set has at most `m²` elements | `transcript_candidate_bound` | Finite field; `m` final stored forms |

The construction `formsFromTranscript` takes no target scalar or group
encoding. At each recursive node it reads the appropriate prefix of the
complete label tuple and applies the program's command chooser to that
prefix. The `runForms_eq_transcript` induction uses `runGroup_prefix` to show
that these are exactly the labels the actual execution saw at the node.
The public-seed specialization then identifies every actual group point
with evaluation of the transcript's fixed affine form. For distinct forms,
group equality reflects scalar equality under the stated injectivity
premise; equal slopes cannot give an informative equality, and unequal
slopes identify one candidate scalar. The imported symbolic theorem bounds
the candidate set for each fixed transcript.

This is a per-transcript bound. The observed transcript itself depends on
the target scalar and random encoding. A total success-probability theorem
requires a checked coupling/counting recurrence over transcript fibers up
to the first informative collision. Symbolically identical forms contribute
no target information and need explicit handling in that recurrence.
Concrete elliptic-curve coordinates are outside this abstract-label model.

`lake build TranscriptDeterminism` completed 3,143 jobs. All nine new
`#print axioms` reports list only standard Lean foundations (`propext`,
`Classical.choice`, `Quot.sound` where applicable). The source contains no
placeholder or custom research axiom. `lean4checker --fresh` was unavailable
on this host. Lean emitted an advisory style warning that `programLe`, a
proposition-valued definition used in the computable prefix reader, could
be declared as a theorem; it does not affect kernel checking.

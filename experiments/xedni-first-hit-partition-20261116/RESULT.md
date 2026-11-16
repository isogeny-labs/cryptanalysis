# First-hit partition for adaptive group traces

An adaptive add/sub program with public points `G` and `Q = w • G` has an
exact first-hit description under an injective scalar-to-group map. For
each scalar and bijective encoding, `execution_first_hit_iff_eligible_next`
identifies the earliest group equality between distinct reconstructed
affine forms with membership in the old prefix's eligible set and the new
form's candidate-root set. The result uses the actual visible labels to
reconstruct forms, so the form list may depend on earlier labels. The
initial `G = Q` equality is included at stage 1.

The proof defines the finite set of raw hit stages and selects its minimum.
Its first-hit characterization gives a hit at the selected stage and no
earlier hit. A separate prefix lemma identifies the absence of earlier
raw equalities with eligibility of all old forms, including known repeats.
The actual group/form correspondence then transports that statement to
the scalar-and-encoding execution space. `execution_stage_mass_flow` and
`execution_total_mass_identity` give exact first-hit conservation over
that space.

The frozen `Z/7Z` control evaluated all seven scalars, all 5,040 bijective
encodings, and stages 1 through 5 of one adaptive program. Every one of
the 35,280 executions had matching first raw, staged, and predicted hit
times. The follow-up audit checked live/eligible equivalence at six prefix
lengths for every execution (211,680 checks).

| First hit | Executions |
| --- | ---: |
| Initial stage 1 | 5,040 |
| Stage 2 | 7,560 |
| Stage 3 | 2,520 |
| Stage 4 | 0 |
| Stage 5 | 7,560 |
| Survives through stage 5 | 12,600 |

| Prefix length | Live executions | Eligible executions |
| ---: | ---: | ---: |
| 1 | 35,280 | 35,280 |
| 2 | 30,240 | 30,240 |
| 3 | 22,680 | 22,680 |
| 4 | 20,160 | 20,160 |
| 5 | 20,160 | 20,160 |
| 6 | 12,600 | 12,600 |

The next formal step is to partition these exact live and hit sets by
visible prefix labels and identify each bucket's cardinality with the
corresponding encoding fiber. That will discharge the bucket-mass
hypotheses in `aggregate_bucket_bound`. The present theorem concerns
generic labels and bijective encodings; a coordinate-guided calculus
requires its own model and cost argument.

Reproduce the finite records with `python3 run.py` and `python3 audit.py`.
Build the proof from `formal/` with `lake build FirstHitPartition`.

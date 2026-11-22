# Controlled relation-system comparison — plan before new data

2026-11-18; user-authorized experiment, tracking PR #1767. Status: design/source preparation; scientific execution not started. [pcc:unverified]

## Requested comparison

Compare Montgomery, Edwards, torsion-invariant and retained-intermediate-point polynomial systems on the same growing toy instances. Include cofactor-1 controls; record time per accepted point-checked usable relation, peak RSS, candidate rejection and timeout rates, relation-matrix rank, and total complete or censored collection cost. No prior term-count result substitutes for this experiment. [pcc:unverified]

## Design to freeze

- Six prime fields: 101, 229, 461, 929, 1861, 3733. Choose the first admissible Montgomery coefficient A>=3 with complete twisted-Edwards parameters and order 8*r, r>=11 prime; bounds and selection rule are fixed in the harness. Existing exploratory data are in-sample design evidence, not new measurements. [pcc:unverified]
- Three summands throughout. Elimination arms use S4 and identical base/target constraints. The retained-point arm uses two S3 constraints with an intermediate x-coordinate, plus an explicit infinity branch, so cancellation is not silently omitted. [pcc:unverified]
- Factor bases: the same k sign classes on each source curve, k=min(5,ceil(cuberoot(r))), chosen by public coordinate scan and subgroup membership, then transported exactly across models. Distinguish 2*k actual signed points from k matrix columns. No coordinate-dependent reselection in the primary comparison. [pcc:unverified]
- Add one same-field cofactor-1 short-Weierstrass control and one exact-subgroup-order cofactor-1 control over a different nearby prime field. The first changes group order; the second changes field. Neither comparison isolates torsion alone. Edwards/Montgomery/torsion-quotient arms are not applicable on cofactor-1 controls; use universal Weierstrass elimination and retained-point systems there. [pcc:unverified]
- Two fixed seeds/replicates. Same public target and ordinary query stream across applicable arms; A/A is a second copy of the baseline. Alternate arm order by seeded shuffle. Fresh worker process per collection, one pinned exposed CPU, thread count one. Warmup is separate from recorded work. [pcc:unverified]
- Per collection: at most 24 ordinary nonidentity queries; up to 2 seconds per polynomial solve and 60 seconds per collector. Retain every timeout, error and rank-deficient collection; report full-collection time as null when the stopping rank was not reached. No retries for mathematical/solver failures. [pcc:unverified]
- All systems use the same SymPy finite-field Groebner backend and lex order. Equation construction, solving, root extraction, sign lifting, relation checks, rank updates/recovery and setup are recorded separately. Uneliminated variables are not allowed to vanish merely because their system is expensive. [pcc:unverified]
- Positive controls: planted three-summand decompositions and the cancellation path B+(-B)+R. Negative controls: exact point-enumeration oracle certifies an unsatisfiable fixed-base query, or records that the base has no such query. No planted control enters ordinary-query yield estimates. [pcc:unverified]
- Peak RSS comes from OS child accounting; successful and killed workers both retain resource data. Report process CPU time and wall time separately. Ordinary-host timings remain exploratory and cannot decide a qualified speedup; no asymptotic or Curve25519-size claim. [pcc:unverified]

## Admission

The current repository requires an S3 resume checkpoint before a run and a CUDA GPU host for IC runs; its ordinary-host diagnostic allowance does not itself grant qualified timing status. The selected computer has no admitted isolation receipt. [pcc:unverified]

The normal bucket check again returned AllAccessDisabled on 2026-11-18. No checkpoint token is configured locally. Before measurement, either restore normal checkpoint/host admission, or obtain the user's explicit exception for committed Git/PR checkpoints and a CPU-only exploratory panel. A generic historical S3 exception for another task is not reused. No paid allocation is proposed by the CPU option. [pcc:unverified]

## Prior work and scope

The 2019 model-comparison paper's publisher abstract, the 2016 prime-field paper's author full text, and the 2020 method-specific conditional analysis were checked again. The 2019 full text remains subscription restricted. Links and the previous research bundle are cited in protocol.json. No novelty claim is made. [pcc:unverified]

## Delivery

Freeze the source, protocol and analysis before new affected data; commit/push the record. After admission, execute the fixed panel, produce the unified export and preserve failures. Deliver a source-linked report/PDF with measured panels and qualified limitations. Until then, this plan and a source implementation are not the requested experimental result. [pcc:unverified]

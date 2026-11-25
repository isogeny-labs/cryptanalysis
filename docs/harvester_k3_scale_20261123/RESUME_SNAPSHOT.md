# Resume: cryptanalysis @ claude/harvester-k3-scale-20261123

## Goal
Extend the gain-forest harvester k=3 ladder (PR #1901: S 0.31-0.57x the eliminator, exponent 0.428 -> 0.332 on p=271..2083) to p = 4159, 8317, 16657 (n up to 2^42); decide if 0.332 holds, drifts back or improves; audit that S charges harvesting work; report distance to rho.

## Lead / hypothesis
Lead: RES-harvester-k3, workspace docs/notes/graph-theory-ic-20261121/followups/next/harvester/RESULTS.md. Confirmed if B exponent CI over extended ladder contains 0.332 with paired B-A below -0.05; killed/drifted if lower bound above 0.332.

## Spec
docs/harvester_k3_scale_20261123/PROTOCOL.md (frozen before data), runner docs/harvester_k3_scale_20261123/run_cells.sh. Seeds 1..6; arms A (eliminator --max-lp 2) and B (--harvester cycles --max-lp 3); A at p=16657 only seeds 1,2. Baseline rho = run_rho3 in the same JSON.

## State
Worktree /home/user/wt/harvester-k3-scale (git needs GIT_WORK_TREE=$PWD exported because the submodule's core.worktree is relative). Build done: suite/target/release/examples/gaudry_cubic_bench. Draft PR isogeny-labs/cryptanalysis#1940. Calibration (p=4159 seed 1): A S=2508.3 169 s, B S=824.5 54 s. No ladder data yet.

## Next steps
1. Launch two runner processes (see Runs in flight). 2. Analyse with docs/harvester_k3_scale_20261123/analyze.py. 3. Write results note, push, tick ACTIVE line, mark PR ready.

## Runs in flight
Data dir /home/user/wt/h3s-data/{p1,p2}; progress.log in each; none until launched. Collect by rerunning analyze.py on those dirs.

## Stop and success conditions
About 90 min wall, 2 single-thread processes. Success = full ladder cells recovered and group-checked; killed cells are reported, not imputed.

## Open questions
Does the exponent of B drift upward; is the uncounted non-multiplication harvest work material.

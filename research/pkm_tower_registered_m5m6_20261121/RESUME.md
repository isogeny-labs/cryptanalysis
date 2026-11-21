# Resume: cryptanalysis @ codex/pkm-high-arity-phase1-20261121

## Goal
Run the frozen phase-1 PKM tower comparison, including feasible m=5,6, with raw-presentation baseline and planted/random controls. Determine whether the reduced tower engine lowers the widest F4 matrix on matched cells. This is a component measurement, not an ECDLP complexity claim.

## Lead / hypothesis
`research/pkm_tower_registered_m5m6_20261121/lead.json`; prior art is pinned there. The earlier m=5,t=2 attempt could not choose five distinct base abscissae because |V|=4; it did not measure F4. The registered sweep sets t_min=ceil(log2 m). The lead predicts narrower F4 matrices than raw presentation at same p,m,t and targets across tower kinds. A failed planted control or missing comparable rows makes a cell inconclusive; larger or equal matrices rejects the proposed gain at that cell.

## Spec
`/Volumes/SSD990-2/workspace/docs/lead-testing/PROTOCOL.md` and `/Volumes/SSD990-2/workspace/docs/lead-testing/registry.json` (sha256 prefix e840213ad5cf); lead spec above. Phase 1: p=786433, seed=1347112276, 3 planted and 3 random targets, m=2..9 one process per m, t_min=max(1,ceil(log2 m)), t_max=8, budget=60 seconds per solver, wall=3600 seconds per cell, memory ceiling=12 GiB with host floor. Raw f4 is baseline, f4_fp_tower is lead, controls tower/null/naive. m>=7 declared unsupported by this engine. Rho is distance only, not a gate.

## State
Draft PR aburan28/cryptanalysis#1883; Conductor T-607. Clean isolated worktree at `/Volumes/SSD990-2/.codex/worktrees/cryptanalysis-pkm-high-arity-20261121`. Lead spec validates with `python3 tools/lead_sweep.py check`. No registered measurement has run yet. Build remains to do. Workspace PR #45 holds earlier scope correction and construction-only diagnostics. Crypto PR #4884 holds fail-fast curve preflight fix, still draft.

## Next steps
1. In this cryptanalysis worktree, build with `RUSTC=/Users/adamburan/.rustup/toolchains/1.97.0-aarch64-apple-darwin/bin/rustc rustup run 1.97.0 cargo build --release --locked --bin ca-ic --example pkm_tower_pilot` in `suite/`.
2. In `/Volumes/SSD990-2/workspace`, run `python3 tools/lead_sweep.py plan /Volumes/SSD990-2/.codex/worktrees/cryptanalysis-pkm-high-arity-20261121/research/pkm_tower_registered_m5m6_20261121/lead.json --phase 1 --cryptanalysis /Volumes/SSD990-2/.codex/worktrees/cryptanalysis-pkm-high-arity-20261121`.
3. Run `scripts/checkpoint.sh gate` in this worktree. Then in workspace run `python3 tools/lead_sweep.py run /Volumes/SSD990-2/.codex/worktrees/cryptanalysis-pkm-high-arity-20261121/research/pkm_tower_registered_m5m6_20261121/lead.json --phase 1 --cryptanalysis /Volumes/SSD990-2/.codex/worktrees/cryptanalysis-pkm-high-arity-20261121`, monitoring the live process and recording run path. Push checkpoint after launch and result.
4. Review statuses and raw rows, create scoped report with correct evidence labels, commit/push to PR #1883 and update workspace PR #45. Do not mark the overall goal complete from component data.

## Runs in flight
none.

## Stop and success conditions
Stop an individual cell on the registry 12 GiB ceiling, host memory floor or 3600-second wall limit, recorded as a resource limit. m>=7 unsupported. Report PASS/FAIL/INCONCLUSIVE only from the frozen gate; no promotion beyond phase 1 without protocol PASS. Full run may take hours; preserve live process and checkpoint across interaction boundaries.

## Open questions
Whether m=5,6 can construct valid planted targets for every tower kind at registered t_min and whether the reduced presentation changes matrix width before resource limits.

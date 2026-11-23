# Resume: cryptanalysis @ claude/pkm-aux-curve-odd-isogeny-20261123

## Goal
Test the untested branches of the Petit–Kosters–Messeng §3.4 auxiliary-curve
(isogeny-tower) factor base for prime-field ECDLP index calculus: (A) isogeny
towers with odd and mixed prime degrees (3, 5, 2·3) instead of only degree 2;
(B) the m = 2..9 frontier and larger fields; (C) solvers that use the
two-stage structure (eliminate tower variables by resultant / chain root
finding) against F4 and enumeration. Owner request 2026-11-23 ("try all the
things"). Tracking: cryptanalysis PR #1927, workspace PR #86.

## Lead / hypothesis
Leads in `research/pkm_aux_curve_odd_isogeny_20261123/leads/pkm-iso-deg{3,5,23}.json`
(`lead-testing.lead/v1`). Hypothesis: at equal log2|V|, odd-degree Vélu levels
cut F4 work >= 2x versus degree-2 isogeny levels at m = 2 and lose no cell at
m >= 3. Prior: crypto `research/pkm_odd_tower_f4_20261114` found 3-8x for
Kummer odd degrees at m = 2 and isogeny = Kummer within 0.76-1.47x (m <= 3, ad
hoc). Killed if the equal-|V| ratio is within [0.5, 2] or the lead loses cells.

## Spec
Workspace protocol `docs/lead-testing/PROTOCOL.md`, registry
`docs/lead-testing/registry.json` (sha256 e840213ad5cf...). Runner
`tools/lead_sweep.py` in the workspace trunk. Pilot flag `--iso-degrees`
in `suite/examples/pkm_tower_pilot.rs` (commit 36fb74f08). Baseline: raw
presentation on f4_fp, controls tower/null/naive, kinds kummer/dickson/isogeny.

Build: main does not compile (C and Rust merge breakage from the 2026-11-21
`mt-work` merges, e59dda7e..1ed7de57). Built in `/home/user/ca-build` =
`git archive 9824fb08` (last commit before the breakage) + this branch's
`suite/examples/pkm_tower_pilot.rs`. Runs set
`LEAD_SWEEP_CRYPTANALYSIS=/home/user/ca-build`.

## State
- Pilot change committed and pushed (36fb74f08); unit tests pass: the F_61
  worked example of the auxiliary-curves guide reproduces exactly (maps,
  V = {5,11,15,16,17,19,25,37,58}, chi = 60), towers of degrees 3, 5, 7, 2,3,
  3,2 build at t = 1..3, BSGS point count equals exact count.
- Smoke run, degree 3, m = 2, p = 786433, t = 1..4 (|V| up to 81): 16/16
  rows, planted solutions found, max_cols 15/105/409/2577 (random targets).
- Nothing else measured yet.

## Next steps
1. Phase 1 of each lead, in the workspace trunk:
   `LEAD_SWEEP_CRYPTANALYSIS=/home/user/ca-build python3 tools/lead_sweep.py run repos/cryptanalysis/research/pkm_aux_curve_odd_isogeny_20261123/leads/pkm-iso-deg3.json --phase 1 --jobs 2`
   then deg5, deg23.
2. Equal-|V| analysis from the rows (`log2_V`, `max_cols`, `ms`) against the
   reference arm's degree-2 isogeny rows; script to be written in the study dir.
3. Branch C: structure-aware solver (eliminate tower variables by resultants
   or chain root finding) on the exported systems vs F4 and enumeration.
4. Write-up in the study dir, bench record, results-index record in the trunk.

## Runs in flight
none (phase 1 of pkm-iso-deg3 about to start on this container: 4 vCPU, 15 GiB;
output under /home/user/workspace/runs/lead-testing/pkm-iso-deg3/).

## Stop and success conditions
Lead-sweep gate as frozen (PROTOCOL.md section 6) plus the equal-|V| reading.
Success: a verified measured reduction of F4 work at equal |V| that holds or
grows with |V|. Failure: ratio within [0.5, 2] or decaying. Resource kills are
limits, never negatives. No claim about rho, larger sizes or deployed curves.

## Open questions
- The frozen gate pairs by t, which is unequal information for odd degrees;
  the equal-|V| reading is reported beside it.
- The S3 checkpoint push needs CHECKPOINT_UPLOAD_TOKEN, which this session
  does not have.

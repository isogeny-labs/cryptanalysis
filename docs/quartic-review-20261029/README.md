# Quartic review repairs, 2026-10-29

The 27 original author heads are already included in main through PR #1257. Their original stacked PRs remain open pending review reconciliation. This follow-up preserves all 1,404 frozen input hashes and adds portable integer replay, a safe field-index successor runner, indexed open proof bridges, and dated explanatory reports with editable diagrams and PDFs.

All 42 original integer auditors passed in a new disposable canonical-layout container; the source checkout was read-only and every frozen hash was checked before and after replay. Thirteen local refusal/preparation/execution I/O controls pass. The previous integrated proof map covers 37 original modules and 142 theorems under the pinned project; the new diagrams do not expand those theorem claims. No new Sage experiment or benchmark was run.

Publication of protocol and result together is retrospective/exploratory unless an earlier independent publication witness exists. In particular the six-row sqrt(2) holdout and the 62/62 simple-root correctness result retain their exact values with this qualification. Archived PASS_PROSPECTIVE labels remain historical receipt strings.

## Portable replay

Hydrate the exact manifest inputs through the existing artifact reader, then run from any checkout with Docker:

```sh
python3 tools/ci/quartic_portable_replay.py --out /tmp/quartic-replay-new-run
```

The output path must be new. Docker builds the pinned Python/SymPy verifier, then replays without network access, mounting the source read-only. The managed-cloud proxy CA is supplied as a build secret when configured. The 42 original scripts run only in the disposable historical layout.

For field-index producer preparation:

```sh
python3 tools/ci/quartic_successor.py field --out /tmp/quartic-field-new-run --prepare-only
python3 tools/ci/quartic_successor.py basis --out /tmp/quartic-basis-new-run --prepare-only
```

Preparation copies exact sources and protocols into distinct originals/worktree trees. Field mode removes old attempt, partial and final result files from its working copy; basis mode retains its pinned field-result input and removes only the old basis outputs. Executing a successor additionally requires this repository's checked Sage launcher and its successful runtime check, uses the original timeout, kills its process group on timeout, and retains stdout/stderr and output hashes. Preparation is not a scientific replay. Apply the repository's experiment/backend/protocol rules before a new producer run.

Evidence: [portable-evidence.json](portable-evidence.json), [all 42 results](portable-replay/results.json), both [first](portable-replay-1.zip) and [second](portable-replay-2.zip) attempt archives, [control output](portable-controls.log), [graph review](graph-review.json), and [plot sources](quantitative-sources.json). Reports cite their original source heads and exact census inputs. Rebuild the deliverables with `python3 docs/quartic-review-20261029/build_reports.py`; Graphviz, Matplotlib and ReportLab are required.

The new indexed bridge problems remain open. Recording them does not prove the field/ideal/local/Galois claims, and neither retrospective replay nor finite census verifies an ECDLP attack.

## Study reports

| PR | Report and PDF | Original study |
| --- | --- | --- |
| #1162 | [Certify j1728 quartic-octic resolvent factorization](1162.md), [PDF](1162.pdf) | [experiments/hecke-432-j1728-resolvent-field-20261026](../../experiments/hecke-432-j1728-resolvent-field-20261026/REVIEW_20261029.md) |
| #1163 | [Prove square-three obstruction for j1728 source fiber](1163.md), [PDF](1163.pdf) | [experiments/hecke-432-j1728-quadratic-extensions-20261026](../../experiments/hecke-432-j1728-quadratic-extensions-20261026/REVIEW_20261029.md) |
| #1164 | [Certify sqrt2 Frobenius factor swap at j1728](1164.md), [PDF](1164.pdf) | [experiments/hecke-432-j1728-sqrt2-split-20261026](../../experiments/hecke-432-j1728-sqrt2-split-20261026/REVIEW_20261029.md) |
| #1165 | [Certify bounded √2 reduction gate and exceptional primes](1165.md), [PDF](1165.pdf) | [experiments/hecke-432-j1728-sqrt2-resultants-20261026](../../experiments/hecke-432-j1728-sqrt2-resultants-20261026/REVIEW_20261029.md) |
| #1166 | [Classify √2 reduction gate below one million](1166.md), [PDF](1166.pdf) | [experiments/hecke-432-j1728-sqrt2-million-20261026](../../experiments/hecke-432-j1728-sqrt2-million-20261026/REVIEW_20261029.md) |
| #1167 | [Audit source-fiber exception below ten million](1167.md), [PDF](1167.pdf) | [experiments/hecke-432-j1728-octic-collision-holdout-20261026](../../experiments/hecke-432-j1728-octic-collision-holdout-20261026/REVIEW_20261029.md) |
| #1168 | [Add fast local polynomial-gcd gate for C–E fibers](1168.md), [PDF](1168.pdf) | [experiments/hecke-432-j1728-fast-local-root-gate-20261026](../../experiments/hecke-432-j1728-fast-local-root-gate-20261026/REVIEW_20261029.md) |
| #1169 | [Certify norm powers and an 83-bit quartic collision prime](1169.md), [PDF](1169.pdf) | [experiments/hecke-432-j1728-norm-power-20261026](../../experiments/hecke-432-j1728-norm-power-20261026/REVIEW_20261029.md) |
| #1170 | [Certify two octic-norm primes and their rational source fibers](1170.md), [PDF](1170.pdf) | [experiments/hecke-432-j1728-octic-factor-search-20261026](../../experiments/hecke-432-j1728-octic-factor-search-20261026/REVIEW_20261029.md) |
| #1171 | [Identify repeated-root branch zeros and source Frobenius gate](1171.md), [PDF](1171.pdf) | [experiments/hecke-432-j1728-fiber-overlap-20261026](../../experiments/hecke-432-j1728-fiber-overlap-20261026/REVIEW_20261029.md) |
| #1172 | [Prove cubic common-root branch collision and replay exceptional fibers](1172.md), [PDF](1172.pdf) | [experiments/hecke-432-j1728-derivative-ideal-20261026](../../experiments/hecke-432-j1728-derivative-ideal-20261026/REVIEW_20261029.md) |
| #1173 | [Certify exact -16 resultant projection on the source-j field](1173.md), [PDF](1173.pdf) | [experiments/hecke-432-j1728-resultant-projection-20261026](../../experiments/hecke-432-j1728-resultant-projection-20261026/REVIEW_20261029.md) |
| #1174 | [Certify sixth-power discriminant norms of j=1728 factors](1174.md), [PDF](1174.pdf) | [experiments/hecke-432-j1728-discriminant-norms-20261026](../../experiments/hecke-432-j1728-discriminant-norms-20261026/REVIEW_20261029.md) |
| #1175 | [Certify common prime support of j=1728 discriminant roots](1175.md), [PDF](1175.pdf) | [experiments/hecke-432-j1728-root-prime-support-20261026](../../experiments/hecke-432-j1728-root-prime-support-20261026/REVIEW_20261029.md) |
| #1176 | [Certify j=1728 source-field discriminant and index gate](1176.md), [PDF](1176.pdf) | [experiments/hecke-432-j1728-field-index-gate-20261026](../../experiments/hecke-432-j1728-field-index-gate-20261026/REVIEW_20261029.md) |
| #1177 | [Certify prime-ideal overlap of j=1728 discriminant factors](1177.md), [PDF](1177.pdf) | [experiments/hecke-432-j1728-relative-ideal-overlap-20261026](../../experiments/hecke-432-j1728-relative-ideal-overlap-20261026/REVIEW_20261029.md) |
| #1178 | [Certify unramified local quadratic factors and order indices](1178.md), [PDF](1178.pdf) | [experiments/hecke-432-j1728-relative-quadratic-local-20261026](../../experiments/hecke-432-j1728-relative-quadratic-local-20261026/REVIEW_20261029.md) |
| #1179 | [Classify split and inert j=1728 quadratic factor places](1179.md), [PDF](1179.pdf) | [experiments/hecke-432-j1728-quadratic-residue-class-20261026](../../experiments/hecke-432-j1728-quadratic-residue-class-20261026/REVIEW_20261029.md) |
| #1181 | [Certify local maximal-order indices of j=1728 relative quartics](1181.md), [PDF](1181.pdf) | [experiments/hecke-432-j1728-relative-quartic-local-order-20261026](../../experiments/hecke-432-j1728-relative-quartic-local-order-20261026/REVIEW_20261029.md) |
| #1182 | [Certify quartic simple-factor splitting components at four primes](1182.md), [PDF](1182.pdf) | [experiments/hecke-432-j1728-relative-quartic-splitting-20261026](../../experiments/hecke-432-j1728-relative-quartic-splitting-20261026/REVIEW_20261029.md) |
| #1184 | [Resolve selected j=1728 quartic prime splitting locally](1184.md), [PDF](1184.pdf) | [experiments/hecke-432-j1728-relative-quartic-local-factor-20261026](../../experiments/hecke-432-j1728-relative-quartic-local-factor-20261026/REVIEW_20261029.md) |
| #1185 | [Independently resolve the p23 quartic quadratic clusters](1185.md), [PDF](1185.pdf) | [experiments/hecke-432-j1728-relative-quartic-p23-local-replay-20261026](../../experiments/hecke-432-j1728-relative-quartic-p23-local-replay-20261026/REVIEW_20261029.md) |
| #1186 | [Identify Klein-four Galois groups and Kummer generators for relative quartics](1186.md), [PDF](1186.pdf) | [experiments/hecke-432-j1728-relative-quartic-galois-resolvent-20261026](../../experiments/hecke-432-j1728-relative-quartic-galois-resolvent-20261026/REVIEW_20261029.md) |
| #1187 | [Prospectively verify Kummer splitting at five new primes](1187.md), [PDF](1187.pdf) | [experiments/hecke-432-j1728-kummer-prime-holdout-20261026](../../experiments/hecke-432-j1728-kummer-prime-holdout-20261026/REVIEW_20261029.md) |
| #1188 | [Prove sqrt2 conjugacy of the two quartics and pair their prime splitting](1188.md), [PDF](1188.pdf) | [experiments/hecke-432-j1728-quartic-conjugacy-20261026](../../experiments/hecke-432-j1728-quartic-conjugacy-20261026/REVIEW_20261029.md) |
| #1189 | [Transfer quartic splitting from one side at five new primes](1189.md), [PDF](1189.pdf) | [experiments/hecke-432-j1728-single-sided-splitting-20261026](../../experiments/hecke-432-j1728-single-sided-splitting-20261026/REVIEW_20261029.md) |
| #1190 | [Classify V4 quartic splitting from one simple residue factor](1190.md), [PDF](1190.pdf) | [experiments/hecke-432-j1728-simple-root-shortcut-20261026](../../experiments/hecke-432-j1728-simple-root-shortcut-20261026/REVIEW_20261029.md) |

# Independent raw-row recomputation: GLV table-budget held-out confirmation

**2026-11-07.** The content-addressed `rows_main.jsonl.gz` and `rows_c12.jsonl.gz` match the committed `.artifacts.json` digests. An independent parser recomputed 80,000 paired rows per arm, 80,000 recorded rho references, the full 2-family × 8-size × 200-curve × 25-target grid, all 16 cell ratios, and both geometric-mean primary statistics. Every published point value in `results.json` matches to absolute tolerance 1e-15. The 45,700 equal-table identity-control rows have zero differing operation counts.

## Custody and chronology

- `rows_main.jsonl.gz`: SHA-256 `46237cc3602ff7582aacf43b3fa7c8de3d38e0330ae85c9b97ef985196178b30`, 1,674,663 compressed bytes.
- `rows_c12.jsonl.gz`: SHA-256 `4bb57c61f156a3871cd757460cce17223fd91950534f4c41d693f4b50531805a`, 1,295,953 compressed bytes.
- Both were downloaded read-only from `s3://setec-astronomy-artifacts/store/sha256/<first-two-digest-characters>/<full-digest>` and hashed locally. The raw files remain outside Git; the two recomputation scripts and their derived JSON are committed here.
- PR #1065 shows protocol/source/analysis commit `f630cc30baa97eff39b9fa88d57fd273bae7d735` at 2026-10-22 08:13:55 UTC, then held-out result commit `d433d5f9b9c1534bc04e671aa9d53e41922d0268` at 08:47:14 UTC. The first commit lists only `PROTOCOL.md`, `PROTOCOL.sha256`, `analyze.py`, `run.py`, and `src/curve.c`; no result file. This supports the recorded protocol-before-result chronology. It does not independently establish when the first trial process started.

## Independent arithmetic

| Family | Recomputed geometric mean, 28–34 bits | Separate 10,000-resample 97.5% interval | Published interval |
|---|---:|---:|---:|
| j=1728 | 0.9565397206 | [0.948088, 0.964908] | [0.948003, 0.964895] |
| j=0 | 0.9670782595 | [0.958173, 0.976202] | [0.958117, 0.976189] |

The separate bootstrap uses a new, recorded seed (20261107) and resamples the 200 curves within each of the four primary cells. Both intervals retain upper bounds below 1, consistent with the frozen decision rule. The small endpoint differences are Monte Carlo variation. All 16 c12/main, main/rho, and c12/rho cell point ratios match the producer `results.json`; their exact totals are in `independent-point-recompute.json`. `cell-ratios.svg` is drawn from those derived values.

All rows mark `correct=true`; all main-arm rows mark `rho_correct=true`. These flags are producer records, not a fresh independent group-law or solver replay. The native arm libraries named in `PROTOCOL.md` were not available by their pinned digests for this review, so no operation counter or answer was rerun. The protocol uses an identity control and rho reference; it does not specify an A/A arm. This review therefore supports the recorded row arithmetic and control consistency, while independent execution fidelity remains open. No cloud or new trial was launched. This is a supplemental raw-row audit, not an `experiment.review/v1` export review because this 2026-10-22 experiment has no `experiment.export/v1` bundle.

## Reproduce this review

With read-only access to the content-addressed store, download the two digest paths above as `rows_main.jsonl.gz` and `rows_c12.jsonl.gz` beside the committed `recompute.py` and `bootstrap.py`. Verify both compressed SHA-256 values against `.artifacts.json`, then run `python3 recompute.py` and `python3 bootstrap.py`. The latter uses a separate seed, so its interval endpoints differ slightly from the frozen producer analysis. The scripts require only Python standard library modules.

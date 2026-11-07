# Local smoke of the frozen schedule (diagnostic)

`run_schedule.py --one-per-arm` on the shared cloud-agent VM, CPU 2, with the
locally built binaries (`online/` for side A and rho, `online-b/` for side B)
ran the first run of every arm in every segment: 102 processes, every one
valid, `verified=1` and with no issues (cM10FO 1, cM10RF 1, cM38FO 13, cM38FOX 12, cM38FOaa 12, cM38RF 13, cPFO 1, cPRF 1, kM38FO 12, kM38FOaa 12, kM38RF 12, rT 12) `[pcc:unverified]`.

`verify_receipt.py` on that partial receipt (`verify_smoke.json`) passes 17
checks, among them one layout and index digest set per base, identical rank
relations, probe vectors and root calls per seed across kM38RF, kM38FO and
kM38FOaa, the planted index check, and both pipeline gates. The checks it
fails are the ones a partial smoke must fail: all_aa_pairs_complete, all_planted_pairs_complete, all_primary_pairs_complete, every_scheduled_row_present, receipt_matches_schedule, runner_identity_matches_frozen_files. Timings from this VM are
not evidence.

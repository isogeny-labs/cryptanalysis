# Local smoke of the frozen schedule (diagnostic)

`run_schedule.py --one-per-arm` on the shared cloud-agent VM, CPU 2, with the
locally built binaries (`online/` for side A and rho, `online-b/` for side B)
ran the first run of every arm in every segment: 102 processes, every one
valid, `verified=1` and with no issues (cM10FO 1, cM10R1 1, cM38FO 13, cM38R1 13, cM38R1X 12, cM38R1aa 12, cPFO 1, cPR1 1, kM38FO 12, kM38R1 12, kM38R1aa 12, rT 12) `[pcc:unverified]`.

`verify_receipt.py --correctness-only` on that partial receipt
(`verify_smoke.json`) passes 19 checks, among them one layout and index digest
set per base, identical rank relations, probe vectors and root calls per seed
across kM38FO, kM38R1 and kM38R1aa, and both pipeline gates; the check it
cannot decide on a smoke is `pre_timing_tables_and_closure_bases_verified`. Timings from this VM are not evidence.

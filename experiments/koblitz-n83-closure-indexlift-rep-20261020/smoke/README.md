# Local smoke (correctness only, not timing evidence)

Host: the cloud-agent VM (Intel Xeon @ 2.10 GHz, KVM, 4 vCPUs, kernel
6.18.44), CPU 0. Run on 2026-10-20 after the protocol and schedule were
frozen. No file was changed after the smoke.

Binaries: `ic_online_closure_indexlift_r770` and `rho_tuned_r770` came from
a local build of the parent's crate. Its derived source has the same SHA-256
(`1d328b2e...`) as this experiment's, which `restore.py` checks, and the
crate files are byte-identical. The binary digests differ from any runner
build because the build paths differ. The Tier 1 job builds its own
binaries.

Commands:

```sh
python3 restore.py                       # all pins, parent digests included
python3 check_log_table.py --out ../log-table-check.json   # PASS: K600, M38, M10 (log-table-check.json here)
python3 run_schedule.py --bin-dir <local build> --receipt-dir <dir>/panel --cpu 0 \
    --segments O1,P5 --one-per-arm
python3 verify_receipt.py <dir>/panel --correctness-only    # correctness_smoke.json here
python3 -m unittest test_verify_receipt  # 23 tests, OK
```

The smoke ran 10 rows: Q0 on cPI and cM38I, and in P5 the first process of
every arm (kPI, cPI, kM38I, cM38I, rT, kM38IX, kM38Iaa, cM38Iaa). All 10 are
valid. Every check that can be evaluated on this subset passes:

- one scalar per point, replayed in the oracle;
- one relation and one probe count per point and base;
- one index and layout digest set per base, equal to the frozen one;
- Q0 equal to the archived and frozen identities;
- every rank table equal to its frozen table;
- identical rank digests and probe vectors for seed 1213 (kM38I and
  kM38Iaa);
- placement on CPU 0 for every process;
- the same CPU record at the start and the end;
- rows in schedule order;
- binaries unchanged;
- the receipt matches the schedule;
- the runner files equal the frozen ones.

Two checks are false here, as expected:

- **The probe-law band.** Two kM38I blocks (32 attempts) give 1.31. The gate
  pools 480 attempts. The parent's single-block smoke gave 1.566, and its
  Tier 1 pool gave 1.0304.
- **No smoke subset.** It fails only in the full verifier, because the smoke
  used one.

A full verifier pass over a copy of this receipt returned `invalid`, as it
must: there were missing rows, a smoke subset and incomplete pairs. That
pass exercised every statistics path. Its timing values come from this VM
and are not reported.

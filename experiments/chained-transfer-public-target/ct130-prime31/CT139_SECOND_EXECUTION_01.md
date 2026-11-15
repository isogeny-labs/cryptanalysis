# CT139 no-cost separate-container replay and transfer cost headroom — 2026-11-15 [pcc:unverified]

**Primary status:** repeated the previously frozen CT138 3,840-record complete toy-curve benchmark under a distinct container ID and exact unchanged published source/archive. Both the existing independent EC arithmetic verifier and a separately implemented fail-closed timing auditor pass in Python normal and optimized modes. This is a second execution, not a verified independent *physical host* (both report EPYC 9V74, GCC 14.2.0 and 4-vCPU quota), and not a signed PCC result. [pcc:unverified]

## Evidence and source custody

- Prospective add-on protocol published *before this execution* as [CT139_CROSS_HOST_PROTOCOL.md](CT139_CROSS_HOST_PROTOCOL.md), commit 8fc9a3c8cb95523a7b12206a1db62a851bf5d351. [pcc:unverified]
- Frozen CT138 first-run archive SHA-256: 4fadd60f98c72b571dc1683bd030695a7527eafa19a508524e9fbcd96e2823fe; untouched. Frozen C++/Python generator and verifier source SHA values recorded in protocol; new execution reconstructed from archive, not rewritten.
- New distinct-container raw bundle includes 12 per-seed/width CSV outputs, stderr, wall/RSS receipts, host and source/binary digests, generated C++ and compiled executables, both independent EC audits, an additional separate timing-accounting script and its normal/-O reports. SHA-256 bundle: **1590e7692cffb5fff036674ce24f81c45dc141fb952d1e5bb4d3cf1e44394d68**, 226073 bytes, 57 paths including SHA256 manifest. Bundle produced in the user-facing runtime; durable remote evidence store upload and PCC signature **not established**. Do not mistake the hash alone for execution attestation. [pcc:unverified]
- Source code, raw logs and audits are inside the same new bundle; the plain report alone is insufficient for independent custody. Source archive and new report do not modify original 695/701 fixtures, Rust evaluators, graph source, ledger or proposed math maps.
- Host: Linux 6.18.57, AMD EPYC 9V74 virtual machine, GCC Debian 14.2.0, Python 3.13.5, 4-vCPU cgroup quota. Original host container ac9c3bcad2e3, new container 58438f925cec. The underlying physical host might be shared. No EKS, Spot or paid compute.

## Exact reproducer

In an empty directory extract frozen CT138 archive and run:

~~~sh
python3 -S ct138_generate.py generated2
for w in 16 32 64; do
  g++ -O3 -std=c++17 -Wall -Wextra -Werror -I . "generated2/ct138_width$w.cpp" -o "replay-width$w"
done
# Follow the immutable sequence.txt ordering exactly.
while IFS=: read -r s w; do
  timeout 120 /usr/bin/time -f 'wall_seconds=%e maxrss_kb=%M' \
     -o "results/width${w}-${s}.time" "./replay-width$w" 32 "$s" \
     > "results/width${w}-${s}.csv" 2> "results/width${w}-${s}.stderr"
done < sequence.txt
python3 -S ct138_verify.py results > audit-normal.json
python3 -O -S ct138_verify.py results > audit-optimized.json
cmp audit-normal.json audit-optimized.json
python3 -S ct139_headroom.py OLD_ARCHIVE_ROOT . > ct139-headroom.json
python3 -O -S ct139_headroom.py OLD_ARCHIVE_ROOT . > ct139-headroom-optimized.json
cmp ct139-headroom.json ct139-headroom-optimized.json
~~~

The Python EC arithmetic auditor accepted all 12×32×10 = **3,840 complete scalar-recovery records** and rejected all 33 historical synthetic mutations plus three invalid width labels, with byte-identical normal/-O outputs. Independently written CT139 timing auditor checks raw schemas/arm counts/scalars/timing and source-target cohort equality, rejects six additional synthetic corruptions in each Python mode, and reconstructs the timing totals from raw CSV. Exact source and generated C++ SHA digests are in archive manifest. All 12 processes exited successfully; stderr files are empty. [pcc:unverified]

## Measured results, fixed 128-source-target cohort [pcc:unverified]

| Metric | Original CT138 local | CT139 second container |
| --- | ---: | ---: |
| Best fixed source solver | batch16 | batch16 |
| Source cohort total | 632,943,762 ns | 630,658,197 ns |
| Best fixed transferred solver | batch16 | batch16 |
| Transferred cohort total | 475,069,239 ns | 478,000,261 ns |
| Source / transferred ratio | 1.332319× | **1.319368×** |
| Paired-bootstrap 95% *descriptive* interval | [1.175809,1.469367] | [1.178925,1.461970] |
| Source − transferred per public target | **1.233395 ms** | **1.192640 ms** |

The last line is the maximum *additional* per-target transfer/setup/verification time that the observed toy solver can tolerate before the measured ratio becomes 1. These baseline timed target arms **already include** both 2-isogeny maps (source generator and public point) and source scalar verification. The ~1.193ms remaining headroom is arithmetic from complete timed toy solver totals, not an observed cost of original-prime Jacobian or C169/C13a/C13b/D. [pcc:unverified]

CT139 second-container width-specific ratios / remaining extra headroom: width16 1.319368× / 1.192640 ms; width32 1.301622× / 1.148584 ms; width64 1.211456× / 0.913975 ms. All use a fixed whole-cohort arm, with no target-by-target oracle selection. Differences against prior local result are not a paired controlled host-change estimate. [pcc:unverified]

## Decisions and open obligations

No performance promotion, paper or leaderboard row, paid compute, workflow dispatch or merge. Best repeatable scoped lead remains a 31-bit **deliberately selected** CM-isogenous toy pair; all costs from choosing a curve and the true original-prime 695/701 Jacobian transfer remain external to it. Prior #1523 result that all three prepared norm generator points equal already available source generator points must be used as a *stronger* full-cost reference, never priced as newly saved precomputation. The proposed headroom check is a screening tool, not the owner's acceptance metric.

**Next decisive computation** remains native paired original-prime CT126/137 C169,C13a,C13b,D pricing (two Rust evaluators presently type-check but not benchmarked), full 695/701 exceptional-path parity, and verified single-target cold rho/BSGS/IC (source optimizations, setup, isogeny, linear algebra, checks, maximum RSS, same-host A/A, uncertainty, independent PCC). If measured original-prime overhead consumes all headroom, log the negative and redirect to strongest unblocked algebraic index-calculus lead; do not generalize from this toy headroom. [pcc:unverified]

## Worklog

### What was done
Read PR metadata/source CI/session logs/AGENTS and checked concurrent PRs in crypto, cryptanalysis and crypto-autoresearcher. Wrote immutable add-on prospective protocol; reconstructed and rebuilt unchanged native algorithms; ran all 12 trials; passed normal/-O independent EC audits and additional 6 negative timing controls; computed exact sensitivity ceiling. [pcc:unverified]

### Decisions made
Preserved original report and frozen fixture, separated same-model distinct-container repetition from verified physical-host independence; kept raw evidence and its manifest and did not launch paid jobs or merge. [pcc:unverified]

### Open threads
PCC signing, stable long-term raw archive custody, original-prime actual primitive prices, strongest complete cold comparisons and admission remain open. [pcc:unverified]

### Errors
First draft of secondary auditor rejected valid raw rows because 13 fields were assumed instead of 14; corrected to 14 before accepting either run. Both failed attempts retained in this report, no scientific source changed. Physical-host independence cannot be established. [pcc:unverified]

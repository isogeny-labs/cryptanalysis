# `mitm-prime-batched` under the lead-testing protocol (2026-11-22)

Raw `ic bench` arm reports (`cells/*/baseline.json`, `lead-m2.json`,
`lead-m3.json`, the runner's `*.status.json`), the runner's `SUMMARY.md`,
`verdict.json` and `manifest.json` for the three phases of
`LEAD-prime-batched-mitm-20261121` (`lead.json`), run with the workspace
runner `tools/lead_sweep.py run --phase auto` against `registry.json`
(sha256 `e840213ad5cf…`, frozen 2026-11-19) on cryptanalysis commit
`225cd56` (this branch), host: 4 vCPU / 15 GiB cloud container, no other
load during the run.

`validator-report.json` is an independent recomputation from the raw arm
reports (pairing by planted seed, geometric mean of baseline S over lead S,
95 % percentile bootstrap with 10,000 resamples, seed 20261119, every row's
`[d]G = Q` check flag read): it agrees with the runner's verdicts to bootstrap
noise. It is unsigned; the claim is `PCC-20261122-ae5817` and its standing is
whatever `pcc standing` says (unverified at the time of writing) [pcc:unverified].

An earlier run of the same sweep (2026-11-22T00:04Z, commit `31d8f2f`, not
copied here) was taken while `cargo clippy` and `cargo test` were compiling on
the same 4 vCPU host. Its natively priced arms carry that load (one 16-bit
m = 3 repeat priced at S = 142 against ~12 for the others); it passed phases
1-3 at m = 2 but is not cited.

The baseline arm is the registry's `prime-abscissa` + `mitm` (full table,
m = 2); the lead arms are `mitm-prime-batched:m=2` and `:m=3` with the
default pricing (preparation and m = 3 candidate arithmetic charged as
measured nanoseconds at the host's ns per addition; lookups and hit
verification counted as for `mitm`). The matched rho is the negation walk
priced in the baseline process; `lead S / matched rho` in the summaries is
the distance remaining, not a gate.

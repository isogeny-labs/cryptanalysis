# M31 target-blind known-log pair-table comparison

Status: exploratory local five-public-target validation, 2026-11-27. The
prospective protocol was written before the five-target launch but is first
published with the results, so this is retrospective evidence for a PR claim.
This is an existing
generic known-log table/search method transplanted into the current native
`PairIndex`; it is not a new index-calculus construction or a new ECDLP
complexity result. The base and all scalar multiplications were rebuilt in
each child. Its known coefficients bypass relation collection and elimination,
so this comparison isolates their cost rather than improving those phases.

## Frozen workload and source

Curve: p=2147483647, y²=x³+2x+14, G=(1,814455902), subgroup order
2147505293. The five public targets are the previously published
`fresh-public.json` (SHA256
`dc724fc613d9c2b824b90d59c876f1f7f84b3273d8d607c648e1ba3fbc089252`).
The development screen used a different frozen public Q and three seeds; the
prespecified known256 candidate passed its screen gate, after which the
five-target validation was frozen in `PROTOCOL.md` before execution. Validation
used 15 target/seed blocks, four arms per block, rotating order. Source and
binary identities are in `validate.py`, `validation-raw.csv`, and
`ct322-source.sha256`; the known-log validation binary has SHA256
`5bbb1cab0ed20e55baca1e54ad6668d5a77298c7b92121efbd16290f27f4f570`.

| Cold arm | Median charged wall | Median charged CPU | Completed |
|---|---:|---:|---:|
| Known-log pair table, B=256 | 6.382 ms | 6.154 ms | 15/15 |
| Integrated index calculus, interval B=384 | 29.228 ms | 28.673 ms | 15/15 |
| Archived C++ rho | 11.064 ms | 10.790 ms | 15/15 |
| Existing CT322 generic BSGS source on this exact curve | 15.742 ms | 15.389 ms | 15/15 |

Median of 15 paired other/known256 ratios: integrated IC 4.414 wall and
4.622 CPU, rho 1.785 wall and 1.908 CPU, BSGS 2.112 wall and 2.245 CPU.
Known256 won 14/15 IC wall comparisons and 15/15 CPU; 13/15 rho wall and
CPU; 15/15 BSGS wall and CPU. Per-target median charged wall times in target
order were known256 [6.382, 6.007, 6.275, 7.451, 6.073] ms; IC384
[30.674, 28.148, 35.516, 28.706, 31.926] ms; rho
[11.064, 9.948, 9.818, 15.105, 17.273] ms; BSGS
[12.639, 19.164, 15.742, 13.969, 16.167] ms.

Known256 median internal base generation, pair-index build, online, and
main-entry-to-report were 0.243, 1.377, 0.967, and 2.653 ms. The IC384
corresponding medians were 0.099, 3.073, 21.743, and 25.201 ms. External
charged timings include process startup, output parsing, and an independent
public group-equation check. The same target/seed-2/1 block had large wall
outliers across multiple arms: 108.56 ms known256 versus 7.23 ms CPU,
114.79 ms rho versus 17.00 ms CPU, and 192.35 ms BSGS versus 16.04 ms CPU.
These are retained; the CPU and per-target medians are less sensitive to that
host scheduling event. The source is an arm64 macOS host; native x86 behavior
is unmeasured here.

`audit.py` independently checked the public group equation for all 60 saved
answers and every known-log base label, signed pair relation, offset, and
scalar for 15/15 known-log reports. `KnownLog.lean` kernel-checks the group
identity: from Q+[a]G=[s]G+[t]G, infer Q=[s+t-a]G. It does not verify Rust
lookup completeness, machine-code arithmetic or empirical timings. Raw CSV
SHA256 is `5c7028c05f308c0396c4edc93491040926011ff9c0bb0a1a41e60859baa94585`.

## Interpretation and next falsifier

Known256 is a local cold improvement over these specific implementations.
The CT322 BSGS source is a generic, unoptimized affine reference with 46,342
full-point baby entries; known256 has 65,536 pair entries. Peak per-process
RSS was not measured, so table-entry counts do not prove byte-matched memory.
The rho implementation is the archived C++ control, not a strongest known
implementation. This panel therefore does not establish a novel algorithmic
breakthrough. A stronger generic-method comparison should impose the same
measured memory cap, use optimized BSGS/rho, and repeat on an independent
host. For the original IC question, the next falsifier is to acquire genuine
factor-base logs through charged relations and elimination, then test whether
the pair table still provides a cold single-target advantage.

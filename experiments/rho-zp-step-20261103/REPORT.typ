#set page(paper: "a4", margin: 1.7cm)
#set text(size: 9.5pt)
#set par(justify: true)

= The native $(ZZ\/p ZZ)^*$ rho step inline

*Date:* 2026-11-03. *Repository:* `aburan28/cryptanalysis`, study `experiments/rho-zp-step-20261103/`. *Class:* engineering. *Instrument:* Callgrind instruction counts (deterministic) and the performance index's paired wall comparison on a shared 4-vCPU cloud VM, CPU 3 pinned, L0 (not Tier 0 or Tier 1). Every solve returns the same logarithm, operation count, iteration count and table: $S$ and every reported constant are unchanged.

== What changed

For the native $(ZZ\/p ZZ)^*$ group, `rho_thread_main` multiplies each walk's residue word by its multiplier's in place and hashes inline (`ca_zp_hash_word`, which the vtable's `zp_hash` now calls), instead of staging every multiplier and point and dispatching `zp_batch_op` and `zp_hash` through the vtable. The group has no negation map. Every other group keeps the vtable path. The EC walk has had its own inline step since `rho-ec-step-20261101`.

#figure(image("figures/ir_and_wall.svg", width: 100%),
  caption: [Recorded values (`data/measurements.json`): whole-solve Ir per group operation (seed 2), perfindex `c_rho_zp40` Ir, and the paired wall speedups with 95% CIs (7 rounds).])

== Measurements

#table(
  columns: (auto, auto, auto, auto),
  [*measurement*], [*`main` 0045cfa09*], [*this change*], [*ratio*],
  [whole $ZZ_p$ rho solve, seed 2, Ir], [1,834,275,912], [1,563,271,817], [*0.852*],
  [per group operation], [125.6], [107.0], [0.852],
  [perfindex `dlp/c_rho_zp40` Ir], [273,556,841], [233,308,726], [*0.853*],
  [perfindex `dlp/c_rho_ec36` Ir], [189,530,435], [190,785,114], [1.007 (neutral)],
  [perfindex compare `c_rho_zp40` wall], [32.75 ms], [29.19 ms], [*1.111×* (CI 1.092–1.135)],
)

Identical `x`, `ops`, `iterations` and `table_entries` against `main` on seeds 1–3; `ctest` 19/19 with a new check that the inline product and hash equal the vtable's; every `dlp` and `field_ec` perfindex fingerprint identical. The EC kernel's 0.7% is code layout (same calls and inlining in `rho_thread_main`; an out-of-line `Z_p` step left it unchanged and cost the `Z_p` kernel 0.8%).

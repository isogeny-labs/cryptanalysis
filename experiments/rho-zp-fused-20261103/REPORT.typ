#set page(paper: "a4", margin: 1.7cm)
#set text(size: 9.5pt)
#set par(justify: true)

= The native $(ZZ\/p ZZ)^*$ rho round, fused: under 100 instructions per step

*Date:* 2026-11-03. *Repository:* `aburan28/cryptanalysis`, study `experiments/rho-zp-fused-20261103/`. *Class:* engineering. *Instrument:* Callgrind instruction counts (deterministic) and the performance index's paired wall comparison on a shared 4-vCPU cloud VM, CPU 3 pinned, L0 (not Tier 0 or Tier 1). *Target:* fewer than 100 Callgrind instructions per group operation; it was 107.0 after `rho-zp-step-20261103`. *Result:* 67.2. Every solve returns the same logarithm, operation count, iteration count and table: $S$ and every reported constant are unchanged.

== What changed

After \#1380 the native $ZZ_p$ round still had the generic shape: one pass formed every product into a staging array (a 32-byte copy of the point in), a second copied it back and did the bookkeeping, with the group dispatch and the negation-map tests per walk, and the shared constants reloaded for every walk because the pass's `uint64_t` stores may alias `*sh`. For the native group without the negation map (it has none), a round is now one pass in walk order: index, Montgomery product in place, hash, exponent update, `since_dp`, then the distinguished-point event (out of line, the bookkeeping pass's code statement for statement) or the abandon test, with every constant in a local. A walk's product reads only that walk's state, so computing it just before its commit is the same walk; the round adds its $W$ operations up front as the staged pass did. `CA_RHO_TRACE` builds and every other group keep their paths.

#figure(image("figures/ir_and_wall.svg", width: 100%),
  caption: [Recorded values (`data/measurements.json`): Ir per group operation across the two rounds (seed 2), per seed, and the paired wall speedups with 95% CIs (7 rounds).])

== Measurements

#table(
  columns: (auto, auto, auto, auto),
  [*measurement*], [*`main` fbabd9df6*], [*fused round*], [*ratio*],
  [whole $ZZ_p$ rho solve, seed 2, Ir], [1,563,271,818], [981,122,494], [*0.628*],
  [per group operation, seeds 1 / 2 / 3], [107.3 / 107.0 / 107.4], [*67.5 / 67.2 / 67.5*], [0.628],
  [perfindex `dlp/c_rho_zp40` Ir], [233,308,726], [146,925,023], [*0.630*],
  [perfindex `dlp/c_rho_ec36` Ir], [190,785,114], [190,186,983], [0.997 (neutral)],
  [perfindex compare `c_rho_zp40` wall], [29.22 ms], [23.92 ms], [*1.240×* (CI 1.204–1.269)],
)

Identical `status`, `x`, `ops`, `iterations`, `table_entries`, `collisions` and `bytes_peak` against `main` on seeds 1–6. `ctest` 19/19, with a new test that runs six solves on the native group and on the same group behind a copied (non-native) vtable, which takes the staged path; it covers the mask and fastmod indices and a capped run, and fails under a perturbed update. Every perfindex fingerprint is identical and the gate is valid (index 1.015, CI 1.008–1.029). The loop body is 63 instructions, roughly: index 5, product 12, hash 15, two exponent updates 14, the rest stores, tests and loop control.

== Next

The arithmetic is what is left. Recording the multiplier indices between distinguished points and rebuilding $(a, b)$ only at one would remove the updates, at a replay per distinguished point; that changes what a step does and needs its own protocol.

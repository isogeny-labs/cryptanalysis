#set page(paper: "a4", margin: 1.7cm)
#set text(size: 9.5pt)
#set par(justify: true)

= Cofactor projection of the factor base: one product per Frobenius orbit

*Date:* 2026-11-04. *Repository:* `aburan28/cryptanalysis`, production Rust crate `suite/`; study `experiments/proj-orbit-fast-20261104/`. *Class:* engineering. The same projected points come out, and every perfindex fingerprint matches `main` (d3a0f1320) [pcc:unverified].

#figure(image("figures/proj.svg", width: 100%), caption: [Callgrind Ir ratios (main / change) and paired wall speedups over 15 rounds.])

== What changed

`projected_signed_orbit_map_fast` computed `[h]P` for every factor-base point: 15,264 scalar multiplications at degree 53, which is 32% of the four-target descent kernel. `[h]` commutes with the Frobenius, so `project_by_cofactor` now multiplies once per orbit and steps the Frobenius along it, about 290 products. A new test checks every point against its own product at degrees 15 to 53.

== Result

- Descent k0n53: 1.276× fewer instructions [pcc:unverified], 1.254× wall.
- Rung k0n31: 1.142× fewer instructions [pcc:unverified], 1.151× wall.
- All other kernels: unchanged.

The wall verdicts are "neutral" because the A/A noise on the shared VM was ±13–15%; the instruction counts are deterministic. This is a setup cost, so it shrinks with the number of targets one solver serves. It is not a complete-solve row and makes no matched-rho claim.

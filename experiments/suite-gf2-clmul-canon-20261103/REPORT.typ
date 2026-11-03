#set page(paper: "a4", margin: 1.7cm)
#set text(size: 9.5pt)
#set par(justify: true)

= Rust suite: $"GF"(2^n)$ products inlined, Frobenius canon tightened

*Date:* 2026-11-03. *Repository:* `aburan28/cryptanalysis`, production Rust crate `suite/`; study `experiments/suite-gf2-clmul-canon-20261103/`. *Class:* engineering; every perfindex fingerprint identical to `main`'s. *Instruments:* Callgrind instructions (scalar paths: Valgrind does not emulate AVX-512) and the native paired wall comparison (AVX-512 kernels on; L0, CPU 3). *Target:* half the instructions of the index-calculus code. *Outcome:* 1.07–1.27× on the Koblitz index-calculus kernels; not half.

== What changed

`clmul_u64` is a `pclmulqdq` target-feature function, which a portably built caller cannot inline, so every field product was a call; `batch_inv`, `inv` and `add_many_lazy` now dispatch to `pclmulqdq`-enabled copies of their bodies in which the product, the table fold and the loop inline. `FrobeniusCanon::coords` walks eight zero-padded byte tables, fully unrolled; the least rotation's zero-run search advances by one constant rotation a step. A Barrett reduction by carry-less multiplication cut instructions further (descent 1.46×) but ran slower natively (signed rho 0.76×: three dependent products against overlapping table loads) and was dropped.

#figure(image("figures/ir_and_wall.svg", width: 100%), caption: [Instruction ratios and paired wall speedups (`data/measurements.json`).])

== Remaining cost

Natively, the Koblitz hot loops already run the AVX-512 kernels, so scalar savings reach wall time only where scalar code remains (wall index 1.033; `pair_table_build` 1.088×, `fast_mul` 1.063×; nothing slower). The linear-algebra kernels are unchanged: about 45% is a 64×64→128 multiply-accumulate per entry and lane on uniform 45-bit values, and 30–37% the approximant basis's full residual updates, which a divide-and-conquer or lazily evaluated residual would roughly halve with the same output.

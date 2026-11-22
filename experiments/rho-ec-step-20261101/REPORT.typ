#set page(paper: "a4", margin: 1.7cm)
#set text(size: 9.5pt)
#set par(justify: true)

= The EC rho step without the vtable, with four interleaved inversion chains

*Date:* 2026-11-01. *Repository:* `aburan28/cryptanalysis`, study `experiments/rho-ec-step-20261101/` (README with the full
text, raw rounds and performance-index outputs in `data/`). *Class:* engineering. *Instrument:* Callgrind instruction counts
(deterministic) and descriptive wall time on a shared 4-vCPU cloud VM, one CPU pinned, L0 in this repository's tiers (not
Tier 0 or Tier 1). Every solve returns the same logarithm with the same group-operation count, iteration count and
distinguished-point table on the same seed: $S$ and every reported constant are unchanged, and there is no ECDLP cost change
and no rho comparison.

== What changed

For the native $E(FF_p)$ group, `ca_rho_solve`'s batched step (`src/rho.c`) now reads each walk's point and multiplier where
they lie, computes the denominators and sums with inline functions in `src/ca_internal.h` that restate the element
arithmetic of `ec_batch_op` (`ec_batch_op` itself is unchanged: its shared-helper form is invisible to clang's static
analyzer at the depth it is reached, and the by-value and temporary forms that satisfy the analyzer cost 8% in
`c_ec_batch_add`; the study README lists every variant), runs Montgomery's simultaneous inversion over four interleaved chains with suffix products (one field
inversion per batch as before, plus $3 dot 4 - 2 = 10$ multiplications to join the chains, of about 770 at 256 walks), and
canonicalises and hashes with the inline functions behind the vtable's `ec_canonicalize` and `ec_hash`. The coefficient
negation under the negation map is selected rather than branched. Generic groups keep the vtable path. A first variant with
one chain (inline dispatch, no copies) saved the same 7% of instructions and no wall time, which is what pointed at the
serial multiplication chain.

#figure(image("figures/ir_and_wall.svg", width: 100%),
  caption: [Left: Callgrind Ir per group operation on the 44-bit curve ($p = 17592186044399$, $a = p - 3$, $b = 95$, prime
  order $n = 17592192476281$, seed 1, 4,907,163 operations) for the baseline (`main` 8a93e468d), the variants tried
  (the by-value one hatched, rejected) and the kept code. Right: the solver's own seconds for the same solve, nine
  interleaved rounds baseline / kept variant / baseline, CPU 3 pinned (`data/wall_ab_final_rounds.txt`).])

== Identical outputs

Baseline and candidate binaries compared field by field (`x`, `ops`, `iterations`, `table_entries`): the 44-bit curve for
seeds 1–4; a 36-bit prime-order curve ($p = 68719476731$, $a = p - 3$, $b = 33$, $n = 68719022539$) for seeds 1–4 and for
`--walks` 1, 2, 3, 5, 7 (chains of 1 to 4 with a ragged tail); a $ZZ_p^*$ subgroup ($p = 4503599627372423$,
$q = 2251799813686211$, the generic path) for seeds 1–3. All identical. `ctest`: 19 of 19, with new checks that the inline
arithmetic agrees with `ca_group_op` on the doubling, inverse-pair, identity and in-place cases and that the inline
canonicalisation and hash agree with the vtable's. The performance index's validity gate (`perfindex.py instr`): every
`dlp` and `field_ec` kernel's fingerprint identical between the two `ca_perfbench` builds.

== Measurements

#table(
  columns: (auto, auto, auto, auto),
  [*measurement*], [*baseline*], [*this change*], [*ratio*],
  [`ca solve --alg rho`, 44-bit, seed 1, Callgrind Ir, whole process], [1,530,505,869], [1,436,152,339], [*0.938*],
  [per group operation], [311.9], [292.7], [0.938],
  [perfindex `dlp/c_rho_ec36` Ir (4 targets, 36-bit)], [199,957,434], [189,530,435], [*0.948*],
  [perfindex `dlp/c_rho_zp40` Ir ($ZZ_p^*$, generic path)], [270,988,160], [273,556,841], [1.009 (neutral)],
  [perfindex `field_ec/c_ec_batch_add` Ir (`ca_group_batch_op`)], [233,479,793], [233,479,793], [1.000],
  [every other `dlp` and `field_ec` kernel], [—], [—], [1.000 (`c_ec_count_points` 1.004)],
  [wall, 44-bit seed 1, median of 9 interleaved rounds (L0, quiet host)], [0.219 s (A/A arm 0.217 s)], [*0.192 s*], [0.88],
)

The wall time is latency-bound rather than instruction-bound (about 82 cycles per step for about 293 instructions at
2.1 GHz); the two baseline arms differ by 1% and the candidate sits 12% below both on a quiet host (an earlier pass over
the v3 code on a busy host read 17%: the baseline ran slower there, the candidate did not). The performance index's paired wall comparison (five rounds, CPU 3, `data/perfindex-compare.md`): `dlp/c_rho_ec36` 1.180× (95% CI 1.052–1.282, A/A noise ±7.5%), `c_rho_zp40` 1.031× (neutral), `c_ec_batch_add` 0.997× (±1.1%), index over every kernel 0.999×. No
end-to-end or cross-host claim is made from it. What is left in a step: about 115 instructions of
field arithmetic, 30 of hash and canonicalisation, 20 of coefficient updates, the rest bookkeeping. Next levers, not started:
the Euclidean inversion's 64-bit divisions (about 4–5 cycles per step amortised) and a 52-bit-radix AVX-512 IFMA step for
$p < 2^52$.

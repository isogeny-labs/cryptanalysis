#set page(paper: "a4", margin: 1.7cm)
#set text(size: 9.5pt)
#set par(justify: true)

= Folded pair table: two-bit presence filter (and a dropped reduction)

*Date:* 2026-11-04. *Repository:* `aburan28/cryptanalysis`, production Rust crate `suite/`; study `experiments/pair-filter-two-bit-20261104/`. *Class:* engineering. The decompositions are the same; only the filter's stored bits change [pcc:unverified]. *Host:* session VM without VPCLMULQDQ or IFMA; single thread, CPU 3, L0.

#figure(image("figures/wall.svg", width: 100%), caption: [Paired wall speedups against `main` a08cbbef7. Left: the two-bit filter (15 rounds). Right: the dropped pentanomial shift fold (9 rounds; the n = 53 field and pipeline kernels).])

== Two-bit presence filter (adopted)

A CPU-built folded table now sets a second bit, `(h >> 32) & 63`, of each key's filter word, and a lookup needs both: one load as before, with false positives falling from `1 − e^{−ρ}` to about `(1 − e^{−2ρ})²`. The device layout of `gpu/ecc2k` keeps one bit: `build_folded_within_one_bit_filter` builds it, the parity tools use it, and `FoldedParts` carries a `two_bit_filter` flag.

- `koblitz_collect_k0n53_w477_u1024`: *1.136×* (95% CI 1.093–1.162, verdict faster) [pcc:unverified].
- The k0n53 descent: 1.085×, neutral.
- Other kernels: neutral; instruction counts unchanged.

A test checks that both tables give the same decompositions.

== Pentanomial shift fold (dropped)

Folding `z^53 + z^6 + z^2 + z + 1` by shifts measured quicker in isolation, but `gf2_n53_mul_sqr_1m` ran at 0.794× in the kernels (index 0.991×). This matches the 0.84× measured on the other host, so the change was reverted. The AVX-512 batched add showed no gain in the phase profile because this host lacks VPCLMULQDQ: the scalar path ran either way.

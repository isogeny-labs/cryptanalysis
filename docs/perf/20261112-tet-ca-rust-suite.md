# Rust suite WALL-only optimisation pass (tet offensive, slug `ca-rust-suite`)

Date: 2026-11-12. Branch `perf/ca-rust-suite`, base commit
`cea0f68f3313d272725c8917a17782d216268693` (the base of the four code
commits below). Scope: `suite/`
(crate `cryptanalysis_suite`) and `crates/hashed-ecdl-tensor` (not touched).
Class: **engineering**, WALL-only. No pcc claim, benchmark record or
leaderboard row is made here; every wall number is **local, unisolated,
[pcc:unverified]**, host load average 3.0 on a shared 4-vCPU VM
(Intel Xeon @ 2.10 GHz, no PMU, rustc 1.97.0, valgrind 3.22.0). Primary evidence is deterministic Callgrind `Ir` from
`scripts/perf/perfindex.py instr` (restricted to the measured region, one
thread). Valgrind has no AVX-512, so the AVX2/scalar paths are what is
counted.

Prior audit read first: `docs/perf/rust-hotpaths-2026-10-15.md` (bsgs_fast
REDC, preprocessing_rho low byte), `docs/perf/PERFORMANCE_INDEX.md`
("Changes tried and rejected"). Nothing there is undone.

## Commits and instruction counts

Base binary sha256 `0fd2c1cb61c7a2a65836d3021b0c8a81276509b1c691d2b5eb7a95862e75478c`
(cea0f68f), final binary
`7879d58d723640aebd7ce708591917798de11cdf1df2d476a85c3858e99a4c9b`
(`705a3172`), both `cargo build --release --example perfbench` with
`CARGO_PROFILE_RELEASE_DEBUG=line-tables-only`.

| commit | change | kernel | base Ir | cand Ir | Ir ratio |
|:--|:--|:--|--:|--:|--:|
| `adc4a353` | `suite/qs` and `factoring::arith::big_mod_u64`: digit-wise `big_mod_u64` (no `BigUint` per call); `% p` replaced by one conditional subtraction in the sieve root updates and start offsets (operands already reduced); sieve inner loop without bounds checks (`j1 < j2 < len`); survivor scan by 32-byte vectorised max; `c = (b^2-kn)/a` only for polynomials with a survivor; trial division by `v mod p` plus in-place `v /= p` instead of `div_rem(&BigUint::from(p))` | `relation/qs_semiprime_20d` | 77,211,969 | 72,187,644 | 1.070x |
| | | `relation/qs_semiprime_30d` | 98,657,566 | 86,902,952 | 1.135x |
| | | `relation/qs_semiprime_40d` | 527,977,317 | 463,836,866 | 1.138x |
| | | `relation/gnfs_semiprime_30d` | 1,543,656,720 | 1,538,881,667 | 1.003x |
| | | `relation/qs_semiprime_50d` | not captured in the paired `instr` run | | wall below |
| `76439a1a` | `ecc::point::Point::add_vartime/double_vartime` (word-sized affine law, Euclid inverse via `utils::mod_inverse_u64`, falls back to `Point::add` above 64 bits); used by `EcGroup::add/dbl/batch_add` and the collaborative-rho `step`. `Point::add/double` (constant-time users) untouched; counters bumped where they were | `dlp/gaudry_schost_negation_demo32` | 2,221,969,516 | 302,765,045 | 7.34x |
| | | `dlp/collab_walkers_demo32_x8` | 1,529,143,594 | 166,300,066 | 9.20x |
| `280adc67` | `weak_curves::fixed` (new): `[u64; N]` CIOS Montgomery arithmetic, N = 1..4; `Ec::mul` (Jacobian ladder) and `Ec::add_batch` run on it, `BigUint` fallback outside the contract | `dlp/weak_pohlig_hellman_smooth_128` | 1,300,781,379 | 447,286,425 | 2.91x |
| | | `dlp/weak_smart_anomalous_256` | 105,692,572 | 88,704,079 | 1.19x |
| `705a3172` | `Fpk::mul`: lazy reduction (fold with `c*(p-f_j)`, reduce the folded coefficient and the low `k` once) | `dlp/weak_mov_supersingular_k2_160` (measured jointly with `280adc67`: one binary) | 1,753,138,710 | 1,312,778,735 | 1.34x |

The paired `instr` runs were made commit by commit against the previous
commit's binary for the first two commits and against `76439a1a` for the
last two. The `instr` subcommand reported identical fingerprints for every
kernel it ran. Kernels not named above changed by under 0.1% Ir (hash seed
jitter), for instance `dlp/bsgs_fast_toy40_w1_x4` 581,161,789 both sides.

Wall (local, unisolated, [pcc:unverified], load average about 3.1, one
thread, 3 interleaved base/cand pairs, median of 3 samples each, ms):

| kernel | base | cand |
|:--|:--|:--|
| `relation/qs_semiprime_50d` | 503, 552, 519 | 455, 410, 420 |
| `relation/qs_semiprime_40d` | 62, 62, 77 | 66, 73, 57 (inside noise) |
| `dlp/gaudry_schost_negation_demo32` | 210, 183, 189 | 40, 39, 37 |
| `dlp/collab_walkers_demo32_x8` | 129, 130, 130 | 19, 26, 20 |
| `dlp/weak_pohlig_hellman_smooth_128` | 102, 121, 121 | 44, 41, 43 |
| `dlp/weak_mov_supersingular_k2_160` | 133, 147, 133 | 106, 129, 100 |
| `dlp/weak_smart_anomalous_256` | 9.4, 9.2, 8.7 | 8.1, 7.1, 7.6 |

## Identity checks

* All 148 Quick-tier perfbench kernels (every area), one thread, base binary
  vs final binary: fingerprints compared pairwise, **0 differences**.
* `perfindex.py instr` (which refuses on differing answers) ran on
  `relation/qs_*`, `nfs`, `gnfs`, `pm1`, `rho_factor`, all of `dlp/`,
  `weak`, `field_ec/ecdsa|point`, `bsgs|orbit|fastfield`.
* Unit tests of the touched modules, release lib test binary built from
  `705a3172`: `cryptanalysis::factoring` 56 passed; `ecc::point::vartime_tests`
  1 (new, word path vs `BigUint` path on generic, doubling, opposite and
  identity operands of toy40); `weak_curves` 34 (includes the new
  `fixed::tests`: add/sub/mul vs `BigUint` at N = 1, 2, 3, 4 on edge
  values and 400 random pairs each); `ecdlp_variants` 14;
  `pollard_collab` 35; `bsgs_fast` 13. All passed.
* Counters: `group_ops` and `field_inversions` are incremented at the same
  places in `EcGroup` (`add`, `dbl`, `batch_add`, degenerate pairs); the
  collaborative-rho DP records and dead-trail step counts are in the
  kernel fingerprint and are unchanged.

## Tried and reverted

| idea | measurement | decision |
|:--|:--|:--|
| `FastField::inv` with a 4-bit sliding window over odd powers | `fastfield_p61_inv` 26,882,725 -> 26,784,245 Ir (-0.4%); `bsgs_fast_toy40_w1_x4` 581.2M -> 611.7M (+5.2%), `_w4_interval38_x8` 824.8M -> 908.1M (+10.1%), `orbit_rho_baseline_40bit_x4` 850.3M -> 886.9M (+4.3%): the table build and window scan cost as much as the saved multiplications at 40-bit exponents | reverted |
| `FastCurve::scalar_mul` in Jacobian coordinates with one final inversion (seeding of chains) | `bsgs_fast_toy40_w1_x4` 581.2M -> 593.9M (+2.2%), `_w4_` 824.8M -> 843.1M (+2.2%); `orbit_rho` -0.5%, `orbit_ic_j0_34bit_x8` -0.8% (seeding is under 2% of the kernel) | reverted |
| binary extended-GCD inversion for `FastField` (analysed, not built) | about 65 iterations of ~25 instructions each is more `Ir` than Fermat's ~1,500 and its coefficient chain is latency-bound at about 13 cycles per iteration against Fermat's multiply chain, a gain at most 25% of an inversion that is a third of the work | not built |

`bsgs_fast` is therefore unchanged: its inner loop is at the multiplication
floor (the 128-bit product, REDC and conditional subtraction are about 13 `Ir`
per field multiplication, about 12 million multiplications in
`..._w1_x4`).

## Not done in this pass (WALL-only, left for later)

* `pq_wiedemann::mat_vec_into` (68% of `relation/pq_wiedemann_m127_c160`):
  a fixed 128-bit accumulator path for `n < 2^128` would remove one
  `BigUint` product allocation per matrix entry.
* `Fpk` / `mov::ExtCurve` on fixed limbs (the MOV kernel is still 74% in
  `Fpk::mul` through `BigUint`); `fixed::ModN` is the building block.
* `weak_curves::Ec::add/double` (single, affine, one `modinv` each) and
  `BigUint::modinv` itself (22% of the Pohlig kernel before this change).
* `koblitz_*` kernels: `FrobeniusCanon::canon_in_place` is already
  AVX-512 vectorised in the wall path, which Callgrind cannot see.

## Deferred method changes (would alter a counter, RNG draw or output)

* `bsgs_fast`: more `chains_per_worker` amortises the Fermat inversion over
  more chains, but it is a plan input and changes chain step counts and the
  fingerprint.
* `pollard_collab::walk::step`: sharing one inversion across a trail batch
  (Montgomery trick across walkers) would change the order of walker
  advancement and `field_inversions`-style accounting.
* `qs`: any change to the multiplier, factor-base size or `a`-selection
  order changes the relation order and so the dependency found.

## Housekeeping

Build dirs were created under `/home/user/tgt-ca-rust-suite` and
`/home/user/bin-ca-rust-suite` (about 0.9 GB) and removed at the end; the
disk was already near 1.5 GB free from other agents' builds while this ran.
Binary hashes are recorded above. `hashed-ecdl-tensor` and the
proof-pinned `ca_addmod` were not touched; no Python implementations were
added.

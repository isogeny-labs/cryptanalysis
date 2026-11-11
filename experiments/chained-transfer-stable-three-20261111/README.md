# Galois-stable rational degree-3 kernels — bounded exhaustive implementation

Status: **producer development evidence; [pcc:unverified]**.
Owner scope: cryptanalysis issue #1470; chained-transfer queue crypto issue #3904.

## Reconciliation and prior art (before edits)

- Existing `suite/src/isogeny/velu.rs` constructs kernels from rational points using `(#E(Fp)/ell)P`. The comment claiming that `ell ∤ #E(Fp)` rules out *all* Fp-defined ell-isogenies is false.
- Pizzo, Pomerance, Voight, *Counting elliptic curves with an isogeny of degree three* (2019), §2, Lemma 2.4, https://www.math.dartmouth.edu/~carlp/3isog-070319.pdf : the degree-3 division-polynomial root is equivalent to a rational cyclic kernel; their proof over Q uses Galois stability and transfers to perfect finite fields of characteristic >3.
- Banegas, Gilchrist, Le Dévéhat, Smith, *Fast and Frobenius: Rational Isogeny Evaluation over Finite Fields* (2023), https://arxiv.org/abs/2306.16072 : established extensions when kernel generators are not Fp-rational; no novelty claim here.
- Related current work: crypto PR #3877, #3907, #3909; cryptanalysis PR #1469 (merged), #1471 (merged). Lead atlas in crypto-autoresearcher is encrypted and could not be read. Shared research-KB MCP and CLI are unavailable in this environment, so no KB receipt exists.

## Mathematical contract

For `E/Fp : y²=x³+ax+b`, nonsingular, p>3 prime, a rational cyclic 3-subgroup is `{O, ±P}`. Frobenius fixes the subgroup, hence `Fr(P)=±P` and the coordinate `r=x(P)` lies in Fp. Conversely any Fp root of

`psi_3(r) = 3r^4 + 6ar^2 + 12br - a^2`

provides a Frobenius-stable order-three subgroup, even when `r³+ar+b` is a nonsquare. No rational y-coordinate is required. With `u=4(r³+ar+b)` and `v=2(3r²+a)`, Vélu gives

`A=a-5v, B=b-7(u+rv)` and `X=x+v/(x-r)+u/(x-r)^2`,
`Y=y(1-v/(x-r)^2-2u/(x-r)^3)`.

`suite/src/isogeny/stable_three.rs` models the kernel with its **rational x-coordinate**, not a fabricated rational point. It scans all r in Fp, enumerating exactly the rational degree-3 kernels on valid small-prime inputs when `p<=scan_limit`. It does not generalize to all odd degrees, large p, or composite modulus inputs. The prior pointwise-kernel routine and graph/volcano traversals remain explicitly partial.

## Local independent check (Python stdlib scratch oracle, not Rust CI)

A separate finite-field implementation enumerated every affine point and infinity on each input and codomain, checked order preservation and all ordered source-point homomorphism pairs for all rational roots.

| p | a | b | #E | roots of psi3 in Fp | per-root ordered pairs |
|---:|---:|---:|---:|---|---:|
| 103 | 0 | 3 | 124 | 0 | 15,376 |
| 101 | 0 | 2 | 102 | 0, 99 | 10,404 |
| 101 | 0 | 1 | 102 | 0, 31 | 10,404 |
| 103 | 1 | 3 | 120 | 39 | 14,400 |
| 101 | 1 | 1 | 105 | 17, 28 | 11,025 |
| 109 | 2 | 7 | 112 | 69 | 12,544 |

**Producer check: 105,986 ordered-point comparisons passed**, including infinity; not signed or independently certified. The actual **Rust code has not been compiled** in this runtime: no `rustc`/`cargo` binary and GitHub is unreachable from the container. Rust unit tests are committed but their execution must be checked through exact-head CI. Do not equate the scratch oracle with verified Rust execution.

Especially, F103 E(0,3) has 124 points and no nontrivial rational 3-torsion, yet psi3 has the root 0, `f(0)=3` is a nonsquare, and the codomain is `Y²=X³+22`. The old sampler returns []; the new API enumerates the rational isogeny. The F101 E(0,2) sample has one irrational and one rational generator kernel in its two x-roots.

## Follow-up gates

Run `cargo test --release --lib stable_three` from the `suite/` crate (check workspace layout) and `cargo clippy --release --all-targets -- -D warnings`; run repository-required validation before merge. Check PCC standing/signature, PR CI and branch protection. Add odd-prime general kernel-polynomial computation and integrate graph/volcano with an explicit completeness flag; do not silently change their return types or count a sampled absence as no isogeny. No new cloud execution or resource spend.

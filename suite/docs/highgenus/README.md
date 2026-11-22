# `highgenus`: Jacobians of genus 5..131, hyperelliptic and non-hyperelliptic

Module `suite/src/highgenus/` (owner request, 2026-11-21): genus-generic
Jacobian arithmetic over `F_p` (`p < 2^32`), Pollard rho and large-genus
index calculus, for hyperelliptic curves (Mumford/Cantor) and for the
one-point superelliptic curves `y^m = ∏ f_i(x)^{e_i}` (ideal arithmetic in
the maximal order), which for `m ≥ 3` are non-hyperelliptic at every genus
`g ≥ 5` (trigonal family `y³ = f₁ f₂²`). Exact Jacobian orders for the
Jacobi-sum families supply planted instances with a known prime subgroup at
any genus. Results: [`RESULTS.md`](RESULTS.md). Everything is
`[pcc:unverified]`: functional verification and counted costs, no speed
claim.

## Layout

| file | content |
|:--|:--|
| `fp.rs` | `F_p`, Barrett multiplication, sqrt, n-th roots, primitive roots, deterministic primality |
| `poly.rs` | dense `F_p[x]`: Karatsuba, divrem, gcd/xgcd, powmod, squarefree decomposition, DDF/EDF (odd `p` and `p = 2`), roots, irreducible enumeration, smoothness test |
| `ext.rs` | `F_q = F_p[x]/(π)`, polynomials over it, root finding (places of degree `> 1`) |
| `cantor.rs` | `HyperellipticCurve`, `Divisor`: Cantor composition and reduction, places, random elements |
| `kummer.rs` | `SuperellipticCurve`, `Ideal`: integral basis, multiplication table, modular Hermite forms, weighted-Popov minimal element, trace-dual inversion, canonical double reduction, places and valuations |
| `jacobi.rs` | `#Jac(F_p)` for `y^m = x^n + a` and `y^m = x^a (1−x)^b` by Jacobi sums in `Z[ζ_L]`, Galois-orbit norms, prime-subgroup search |
| `rho.rs` | distinguished-point `r`-adding rho with the negation map on any `JacobianGroup` |
| `ic.rs` | `IndexCalculusCurve` trait (places, decomposition), factor base, relation walk, lattice index (exact CRT determinants), dense solve mod `N`, verified logarithm |
| `instances.rs` | planted `D₂ = k D₁` on both engines |
| `mod.rs` | `JacobianGroup` trait, `HgError` |

Example: `suite/examples/highgenus_panel.rs`

```sh
cargo run --release --example highgenus_panel -- rho --genera 5,7,11,23,47,97,131 --nbits 20,28 --family hyper
cargo run --release --example highgenus_panel -- rho --genera 7,97 --family power --nbits 12,20
cargo run --release --example highgenus_panel -- ic-known --genera 5 --bound 2 --nbits 12,40 --family hyper
cargo run --release --example highgenus_panel -- ic-order --genera 23 --p 3 --bound 5 --family hyper
cargo run --release --example highgenus_panel -- probe --genera 131 --p 2 --bound 12 --family trigonal --max-trials 20000
```

Each run prints JSON lines (`highgenus.panel/v1`) on stdout and a markdown
table on stderr.

## Mathematics in one page

**Hyperelliptic.** `y² = f(x)`, `f` monic squarefree of degree `2g+1`.
Reduced Mumford pairs `(u, v)`; Cantor composition with the coprime fast
path (CRT of `v₁, v₂`) and the general `gcd` path; reduction
`u ← (f − v²)/u`, `v ← −v mod u` while `deg u > g`. Negation is `v ↦ −v`,
so the negation map is free and the class representative is the sign of
the leading coefficient of `v`.

**Superelliptic one-point model.** `y^m = F = ∏ f_i^{e_i}` with `p ∤ m`,
`gcd(e_i, m) = 1`, `gcd(m, deg F) = 1`. Integral basis
`b_j = y^j / ∏ f_i^{⌊j e_i / m⌋}`, pole orders `w_j = j·deg F − m·deg D_j`
(distinct mod `m`), products `b_j b_k = μ_{jk} b_{(j+k) mod m}`. Genus
`(m−1)(s−1)/2`, `s = Σ deg f_i`. Ideals are `F_p[x]`-lattices of rank `m`
in row Hermite form computed modulo a lattice modulus (`N(I)N(J)` for a
product, `N(I)·rad F·N(φ)` for a quotient) to avoid degree swell. The
minimal pole-order element comes from a weighted Popov reduction; the
inverse from the trace dual `I⁻¹ = I^∨ 𝔇` with the anti-diagonal trace form
`Tr(b_j b_{m−j}) = m·rad F` and the diagonal different
`𝔇_jj = ∏_{j e_i ≢ −1 (m)} f_i`. `R(I) = φ_min I⁻¹` is the minimal-degree
representative of `−[I]`; it is unique because a complete linear system of
positive dimension always has a member through `∞`; so `R(R(I))` is
canonical and class equality is structural equality (tested against Cantor
at `m = 2` and by class invariance under principal ideals).

**Places and smoothness.** A place of degree `d` lies over a monic
irreducible `π` of degree `d`: hyperelliptic `(π, ±v)` with `v² ≡ f`;
superelliptic `(π, y − r)` with `r^m ≡ F (mod π)` (residue degree one) or
the ramified prime `diag(π, 1, …, 1)` when `π | F`. Decomposition factors
the norm, then reads valuations: hyperelliptic from `v mod π`; superelliptic
by Newton-lifting `r` to a root modulo `π^a` and testing
`Σ a_j D_j⁻¹ r^j ≡ 0 (mod π^a)` on the Hermite rows. A norm whose `π`-part
is not accounted for by residue-degree-one places is not smooth.

**Index calculus.** Factor base = all places of degree `≤ B`; relations
from an `r`-adding walk whose steps are sums of 2–3 random places (so no
step is the negative of another) with cycle detection on recent hashes and
periodic restarts; in DLP mode the steps also carry `α D₁ + β D₂`. With
`N` unknown, the index of the relation lattice (gcd of three exact minor
determinants, CRT over 61-bit primes against the Hadamard bound) is the
order of the subgroup generated by the places that occur; it is checked
against `h·R = 0` and the Hasse–Weil interval, factored, and the DLP is
solved in the largest prime-order subgroup. With `N` known (prime,
`< 2^63`), dense elimination mod `N` gives `log D₂`, verified by a scalar
multiplication; relations in the whole group project to its cyclic
`N`-part, so the factor base need not lie in `⟨D₁⟩`.

**Known orders.** For `y^m = x^n + a` over `p ≡ 1 (mod mn)` the Frobenius
eigenvalues are `−χ(a)ψ(−a)J(ψ, χ)` over the `(m−1)(n−1)` pairs of
nontrivial characters of order dividing `m`, `n`; for `y^m = x^a (1−x)^b`
over `p ≡ 1 (mod m)` they are `−J(χ^a, χ^b)`. `#Jac = ∏ (1 − α)`, computed
exactly in `Z[ζ_L]` and reduced modulo `Φ_L`; genus 131 takes under a
second. Checked against brute force at genus 1 and the `L`-polynomial from
point counts over `F_p`, `F_{p²}` at genus 2.

## Limits (this version)

- `p < 2^32`; `N < 2^63` for the mod-`N` solve; dense linear algebra, so
  factor bases above a few thousand places are slow.
- The rank-`m` ideal engine costs about `O(m³)` polynomial operations per
  Hermite form: fine at `m = 3` up to genus 131 (group axioms at genus 131
  in milliseconds), ~0.2 s per group operation at `m = 23`, ~7 s at
  `m = 47`; the three-point family at genus 47 and 131 (`m = 95, 263`) is
  not practical here.
- No exact order for random trigonal curves beyond what index calculus can
  compute over tiny fields (genus ≤ ~47 over `F_2`); a Kedlaya-type point
  counter would lift that.
- Even characteristic only through the ideal engine (`m = 3` over `F_2`
  works); the Cantor path needs odd `p` (the `binary_ecc` module has the
  `h(x)` model and is not yet wired to these traits).

# The a/b (small-rational-height) factor base: generation, and why it cannot buy relations

Date: 2026-11-23. Closes or opens LEAD 8 of `mythos52-b7/ev-leads-pr-records.md`
("small-rational-height base … never measured against intervals at equal size").

---

## 0. What was asked, restated

Two questions were bundled in the request, and they have different answers:

1. **Can a/b generation be made fast?**  Yes, and the reason is a structural
   identity, not an engineering trick: the set is the *Farey sequence* under
   two involutions, so it can be produced by a mediant recurrence (no gcd
   test, no hash set, O(1) memory) and **addressed by index in O(polylog B)
   without storing anything**.
2. **Can a choice of a/b's yield more relations?**  No — and by the end of this
   note, not in any sense: the mean is fixed by a theorem
   (`Check/Farey.lean`, `sum_repCount`); the per-relation cost is shape-blind;
   and the distribution is uniform in the target off the base (§6), so shape
   cannot even move mass between targets except onto the base itself, where
   the relations are already known.
3. **Can a choice of *targets* yield more relations?**  Also no (§6): every
   cheap statistic is null, and the height statistic only appeared to work
   because it aliases onto the base.

The rest of this note is the arithmetic and the measurement behind those three
sentences, plus the one place where the a/b shape does have a real (but
quantitatively useless) edge: the Jochemsz–May box product, worth 0.28 bits.

---

## 1. The set, exactly

    X(B) = { a·b⁻¹ mod p : gcd(a,b) = 1, 1 ≤ |a|,|b| ≤ B, b ≠ 0 } ∪ {0}

The `b = 0` row must be dropped (`a/0` is not a field element), and `x = -x'`
via `(a,b) ~ (-a,-b)`.  What survives is the Farey sequence of order `B` in
`(0,1]`, together with its reciprocals and signs.

**Counts** (exact; `Check/Farey.lean` `farey_card` proves the first line, the
rest is the `2`-to-`1` quotient by `±1` plus the extra `x = 0`):

    #{(a,b) : 1 ≤ a ≤ b ≤ B, gcd(a,b)=1} = Φ(B) = Σ_{b≤B} φ(b)
    |{(a,b) : 1 ≤ |a|,|b| ≤ B, gcd(a,b)=1, b≠0}| = 8Φ(B) − 2
    |X(B)| = 4Φ(B) − 1

`raw/counts.json` checks both lines by brute force for `B ≤ 96` and the
asymptotic `|X(B)|/B² → 12/π² = 1.2158542` to seven digits:

| B | `|X(B)|` | `|X|/B²` |
|---|---|---|
| 2^16 | 5 222 059 703 | 1.2158555 |
| 2^18 | 83 553 058 575 | 1.2158570 |
| 2^20 | 1 336 846 396 983 | 1.2158547 |

(For `B = 2^20` the base has 1.3·10¹² elements — nine orders of magnitude more
than can be materialised, which is where rank/unrank starts to matter.)

---

## 2. Generation: two algorithms and a sharding primitive

`abgen.py`, three modes, all verified to produce the *same* set:

* **naive** — scan the quarter square, `gcd` each pair, batch-invert, insert
  into a set.  The obvious implementation; costs `B²` gcds and needs a
  `|X|`-element set.
* **farey** — mediant recurrence over `(a,b)`, emit `±a/b, ±b/a`
  (`a = b` emits only `±1`), batched inversion per block.  Costs `Φ(B) ≈
  0.304·B²` steps — **3.3× fewer by construction** — no gcd, no set, O(1)
  memory.
* **unrank** — `FareyRank(B).unrank(i)` returns the `i`-th pair in
  `(b ascending, a ascending)` order by binary-searching the totient prefix
  and then finding the `k`-th integer coprime to `b` by inclusion–exclusion
  over its distinct primes.  Storage is the totient prefix only.

Measured (Python 3.12, one core, `raw/bench.json`):

| B | pairs | naive | farey | speedup |
|---|---|---|---|---|
| 2^8 | 19 924 | 0.14 s | 0.03 s | 5.5× |
| 2^10 | 199 264 | 2.31 s | 0.54 s | 4.2× |
| 2^11 | 510 002 | 10.19 s | 2.27 s | 4.5× |
| 2^12 | 1 275 854 | 41.25 s | 9.35 s | 4.4× |

`raw/selfcheck.json`: rank/unrank are mutual inverses at `B ∈ {1,2,7,64,1000,
4096}`, and the image covers exactly the Farey set (full enumeration checked
for `B ≤ 64`).  Random access at `B = 2^20` (a 1.3·10¹²-element base) costs
**58 µs per unrank** in pure Python — the point being that it *exists*: the
base is an addressable array, so it shards across machines with no
communication and no storage.

That is the whole of the generation result: a 4–5× constant, O(1) memory, and
a sharding primitive that the interval base gets for free but that the a/b
base previously lacked.

---

## 3. Yield: the counting identity, and the exact measurement

Let `F ⊂ E(F_p)` be a factor base of `N` points, `r(R)` the number of
`m`-multisets of `F` summing to `R`.  Then

    Σ_{R ∈ E} r(R) = C(N+m−1, m)

for **every** `F` — this is `sum_repCount` in Lean (ordered version:
`Σ_R r(R) = N^m`), and the corollary `mean_shape_blind` is that two
equal-sized factor bases have identical total, hence identical mean yield
`C(N+m−1,m)/|E|`.  A uniform random target set of size `T` therefore yields
`T · C(N+m−1,m)/|E|` relations in expectation, whatever the shape.  Targets
in IC are `kG` for many `k`, i.e. uniform random, so the identity applies.

The measurement is **exact, not sampled**: `ecell.c` builds the discrete-log
table of `E` (so point addition is integer addition mod `n`), then enumerates
*every* `m`-multiset and accumulates `r(R)` over the whole group.  Curve
`y² = x³ + 7`, `p = 1046047` (`#E = 1046779`, prime) and
`p = 16776547` (`#E = 16769119`, prime); all three shapes normalised to the
same `N` points on the same curve.

Exact identities (`raw/cells.json`, `analyse.py` §1) — all hold:

* `tuples = C(N+m−1,m)` for every cell;
* `Σ_R r(R) = tuples` for every cell;
* at `m = 2` the trivial spike is `r(O) = N/2` exactly (`P + (−P)`, the
  negation any symmetric base gives away for free).

Shape comparison at equal `|F|` (`P(r≥1)` is the fraction of non-identity
targets that decompose at all; the relation *count* is fixed by the identity
and does not need a table):

| p | m | N | interval | farey | random |
|---|---|---|---|---|---|
| 2^20 | 2 | 1448 | .63417 | .63327 | .63362 |
| 2^20 | 3 | 184 | .62872 | .62682 | .62720 |
| 2^24 | 2 | 5792 | .63241 | .63245 | .63239 |
| 2^24 | 3 | 464 | .62866 | .62975 | .62979 |

and the means, which are the identical-quantity check:

| p | m | N | mean `r` (all three shapes) |
|---|---|---|---|
| 2^20 | 2 | 1448 | 1.001504 |
| 2^20 | 3 | 184 | 1.008084 |
| 2^24 | 2 | 5792 | 1.000269 |
| 2^24 | 3 | 464 | 0.999299 |

The mean is the same rational number `(C(N+m−1,m) − r(O))/(|E|−1)` in every
shape.  The only shape-dependence left is in `r(O)` — the trivial spike — and
it shows up in the sixth decimal at `m = 3` (`1.008084 / 1.008080 / 1.008082`),
because the number of 3-term zero-sum relations is shape-dependent while the
*total* over all `R` is not.  At `m = 2` the spike is the exact `N/2` counted
in §3 and the means agree to all printed digits.

**Reading the `P(r≥1)` column honestly.** These are deterministic properties
of one specific base each, so a binomial error bar is not a valid uncertainty
on the *comparison*.  What matters is that the differences are ≤ 0.002 in
absolute value (≤ 0.3%) and their **sign flips between rungs**:

    farey − interval (m=2):  −0.0009 at 2^20,  +0.00004 at 2^24
    farey − interval (m=3):  −0.0019 at 2^20,  +0.0011 at 2^24

There is no reproducible direction, and the quantity that a matrix consumes —
the number of relations — is fixed by the identity.  Verdict: **refuted**.

*(Sub-percent effects do exist and are worth naming, but they do not form a
pattern, and they do not favour the a/b base: the a/b base is last in two of
the four rungs and first in one, the interval base last in one, the random base
last in one.  "Structure mildly
regularises the representation function" is at best a 0.05–0.2% effect with no
stable sign.  All random-shape cells use splitmix64 seed 11, as recorded in
`PROTOCOL.json`; the random column is the only seed-dependent one.)*

---

## 4. The one real structural asset, and why it is worthless

At equal `|F|` the a/b base needs only

    B ≈ sqrt(π²/12 · |F|) = 0.907·sqrt(|F|)

of *height*, whereas an interval base needs width `|F|`.  At the corpus's best
cell (`α = 0.2`, `p = 2^256`, `|F| = 2^51.2`) that is `B = 2^25.5`: 26-bit
numerators and denominators describe a 2^51-element base.  That is a genuine
compactness win — and it is exactly cancelled by the doubled variable count,
because `x = a/b` has *two* unknowns where `x` has one, each of individual
degree `d = 2^{m−1}` after clearing denominators:

    interval box product:  X^{m·d}     with X = |F|
    a/b box product:       B^{2m·d}    with B² = (π²/12)|F|
    ⇒ ratio = (π²/12)^{m·d} → the a/b product is 2^{0.28·m·d} smaller.

`box_product` in Lean is the algebraic content (`(B·B)^{m·d} = B^{2·m·d}`).
In bits: at `m = 4`, `d = 8`, the products are `2^1638.4` (interval) and
`2^1629.4` (a/b) against a Jochemsz–May bound of `2^102.4` — a 9-bit cut off a
**1536-bit** gap.  In the exponent: `Δα = log₂(π²/12)/log₂p = 0.0011` at 256
bits, i.e. the a/b base reaches `|F| = 2^51.48` where the interval base reaches
`2^51.2`.  It also doubles the number of Macaulay variables.  Net: a
0.001-in-the-exponent gain for a 2× variable increase.

---

## 5. The last place a/b differs: the inner-loop predicate (added post hoc)

Section 3 settled the *yield*; section 4 settled the *lattice* route. What
neither settles is the third route: the **materialised sieve**, which is the
only prime-field IC backend that actually runs (`rung-slope-20261119`; tables
8 MB → 8.6 GB across k = 32…56). It materialises the base and hashes partial
sums, so it hits the wall the ledger already names: a 2^51.2-element base at
32 B/entry is 2^56 bytes. The natural rescue is to stop materialising and test
membership from the defining data. That test costs:

| base | predicate | cost per probe |
|---|---|---|
| interval `[1,X]` | `x <= X` | 1 comparison ≈ 0.3 ns |
| a/b `X(B)` | rational reconstruction on `(p,x)` | **135 EEA steps** ≈ 16.2 kcycles ≈ 5.4 µs |

(p = secp256k1, `B = 2^26` = `p^0.1`; median 135 steps, p95 150, max 169 over
20 000 random probes; counted model at 3 GHz — Python measured 48.7 µs, which
is the same number with interpreter overhead.)

So the compact description is **1.6·10⁴× too slow** — 14 bits per probe. One
sweep of the base at 5.4 µs/probe is 2^51 · 5.4 µs ≈ 1.2·10¹⁰ s ≈ 380 years,
before any MITM factor. Compactness does not substitute for the table.

Correctness, since a 14-bit penalty is only meaningful if the predicate is
right: exhaustive over **all** `x ∈ F_p` for 44 `(p,B)` pairs (p ∈
{1019, 4093, 10007, 40009, 100003}), zero mismatches against the enumerated
set, and 108/108 recall on planted elements at production height. The early
exit is sound because `|t_i|` is non-decreasing in the EEA, so the first
remainder below the box bound is the only possible witness.

`PROTOCOL-amendment-1.json` records that this hypothesis was declared after
the run; it is reported here as post hoc, with its kill line (10×).

### Shadow price: the relation phase is shape-blind in cost, not just yield

Under the MITM model the cost of one attempted target is `|F|^{⌈m/2⌉}`
half-sum insertions/probes and the expected number of relations per attempt is
`C(|F|+m−1,m)/|E|`, so

    cost per relation  =  |F|^{⌈m/2⌉} · |E| / C(|F|+m−1,m)

which contains no shape at all. Combine with section 3 and section 4:

| lever | a/b vs interval |
|---|---|
| expected yield at fixed `|F|` | identical (theorem, measured) |
| relations per unit MITM work | identical (above) |
| Jochemsz–May box product | 2^{0.28·m·d} smaller, worth `Δα = 0.0011` |
| variables | 2× more |
| enumeration per element | one batched inversion per pair vs none |
| membership probe (unmaterialised) | 1.6·10⁴× slower |
| shardable without storage | **yes — the one genuine win** |

---

## 6. Target side (H8, post hoc): `r(R)` is uniform off the base — and a retraction

The identity fixes the mean of `r` over targets; it says nothing about
*conditioning*. Conditioning is worth checking because it is nearly free: a
selector costs ~10³ ns, one trial costs `|F|^{⌈m/2⌉}` lookups, so a 1% lift
would be a 1% speedup. Measured on the exact `r(R)` for every `R` (both rungs,
three shapes, `m ∈ {2,3}`), null from exchangeability (`sd_b =
sqrt(σ²(1−n_b/N)/n_b)`, so no resampling).

**Cheap x-arithmetic statistics: nothing.** `x < p/2`, `v2(x)`, `x mod 3`,
`x mod 5`, `Legendre(x)`, `floor(log2 x)`: `|lift − 1| ≤ 0.02`, signs
inconsistent (`raw/selector.json`).

**The rational height appeared to split `r`. It does not.** An earlier revision
of this section reported a monotone "height law" — a 9.7× → 1.2× tail over four
octaves for the interval base — and called it "the first structural property
the interval base has and the a/b base lacks". **That is retracted.** The dump
now carries an exact in-base bit per target (`ecell` marks the dlog of every
base point), and with base elements removed the effect disappears completely:

| subset | buckets | max lift | max \|z\| | where the max is |
|---|---|---|---|---|
| all `R ≠ O` | 116 | 109.3 | 1586 | m=3, h/B ≤ ¼, frac 1.3e-5 |
| **`R ∉ F`** | **88** | **1.113** | **3.31** | m=3, h/B ≈ ½, frac 5.5e-5 |

Eighty-eight buckets, max |z| = 3.3 — the expected maximum of 88 standard
normals is 3.0, and Šidák over 88 gives p ≈ 0.08 for that one. On buckets with
≥ 10⁴ targets, every lift is `1.00 ± 0.01`, at every height scale, for every
shape, at both rungs.

What generated the phantom law: for `R ∈ F` and `m = 3`, `{R, P, −P}` is a
relation for every `P`, so `r(R) ≥ N/2` — a spike on a set of measure `N/|E|`.
The height statistic *aliases onto that set*, differently per base, because

* for the a/b base, `h(R) ≤ B` **is** (a prefix of) the base — a
  height-contiguous set, giving the clean 109×/83× spike at `h/B ≤ 1`;
* for the **interval** base, the in-base predicate is `x ≤ X`, which contains
  the integers `1…X` — and those *are* the targets of height `h(x) = x ≤ X`.
  So the in-base mask is again height-contiguous, but truncated, and the
  truncated part masquerades as a decaying tail.

The mechanistic check confirms it: at `m = 2` the same buckets show **no**
spike (1.03, 1.00), exactly as predicted — for pairs, `R ∈ F` gives no
automatic relation, only `R = O` does, and `O` is excluded.  And the `≥`
direction of the spike is a theorem, not a fit: `repCount_three_ge_of_mem`
(§7) proves `|F| ≤ repCount F 3 R` for every `R ∈ F` in a negation-closed `F`.

So the corrected statement is stronger than the one it replaces:

> Off the base, `r(R)` is uniform in `R` to ±1% on every well-populated bucket
> — independent of `R`'s height, of the base's shape, of the rung, and of `m`.
> The only non-uniformity in `r` is the trivially known one, `R ∈ F` at
> `m ≥ 3`.

That removes the last target-side lever, and it removes the last reason to
prefer one *base shape* over another for anything except the base itself.

**Construction caution (this survives the retraction).** A base built as "first
`N` points in Farey order" is a *prefix* of `X(B)`, not the height ball: at
`N = 464, B = 32` it covers ≈ 36% of the points of `X(32)`. So "`R` is in the
base" and "`h(R) ≤ B`" are different predicates, and the difference is visible
in the 83 vs 232 above. A designed base should be the whole ball, or record
that it is a prefix.

---

## 7. Lean

`lean-check/`, `leanprover/lean4:v4.28.0`, mathlib `fadcf92`. Builds clean,
no `sorry`; `raw/axioms.txt`:

    sum_repCount      ⊂ {propext, Classical.choice, Quot.sound}
    mean_shape_blind  ⊂ {propext, Classical.choice, Quot.sound}
    card_coprime_Icc  ⊂ {propext, Classical.choice, Quot.sound}
    farey_card        ⊂ {propext, Classical.choice, Quot.sound}
    box_product            ⊂ {propext}
    repCount_three_ge_of_mem ⊂ {propext, Classical.choice, Quot.sound}

* `sum_repCount : Σ g, repCount F m g = |F|^m` — the load-bearing statement.
* `mean_shape_blind : |F₁| = |F₂| → Σ_g repCount F₁ m g = Σ_g repCount F₂ m g`.
* `card_coprime_Icc : #{a ∈ [1,b] : (a,b)=1} = φ(b)` (via `a ↦ b−a`, which
  preserves coprimality: `Nat.coprime_self_sub_left`).
* `farey_card : #fareyPairs B = Σ_{b≤B} φ(b)`.
* `box_product : (B·B)^{m·d} = B^{2·m·d}`.
* `repCount_three_ge_of_mem : R ∈ F → |F| ≤ repCount F 3 R` for any
  negation-closed `F` in an abelian group — the in-base spike of §6, and the
  only non-uniformity of `r` anywhere in this report.  Proof: `P ↦ (R, P, −P)`
  injects `F` into the fibre.

Not formalised, and why: the *unordered* count `C(|F|+m−1,m)` needs
`#(s.sym n) = C(|F|+n−1,n)`, which Mathlib does not have for `n > 2`; the
ordered statement gives the same conclusion (both totals are shape-blind), so
this is a library gap, not a gap in the argument.  The *exact* value at the
spike (`= N` ordered, `= N/2` unordered) also needs the same count.  The
quotient count `|X(B)| = 4Φ(B) − 1` is checked by brute force rather than
proved.

---

## 8. Verdicts against the pre-registered protocol

| id | claim | outcome |
|---|---|---|
| H1 | `|X(B)| = 4Φ(B) − 1` | **confirmed exactly** (B ≤ 96 brute force; generator asserts it to B = 2^12) |
| H2 | Farey generation ≥3× faster, O(1) memory, shardable | **confirmed**: 4.2–5.5×, set-free, 58 µs random access at `B = 2^20` |
| H3 | `Σ_R r(R) = C(N+m−1,m)` for every shape | **confirmed exactly** in all 18 cells, and **proved** (`sum_repCount`) |
| H4 | some a/b choice yields more relations | **REFUTED** — means identical to 6 dp; `P(r≥1)` differences ≤0.3% with sign flipping between rungs |
| H5 | height advantage survives the doubled variables | **refuted**: exactly cancelled; net `Δα = 0.0011` at 256 bits, 2× variables |
| H6 | sign-redundant pair lists inflate hits by `2^m` | **confirmed exactly** (4.0000 at m=2, 8.0000 at m=3; distinct relations unchanged) |
| H7 | compact a/b description can replace the materialised table | **refuted** (post hoc, `PROTOCOL-amendment-1.json`): 135 EEA steps/probe = 1.6·10⁴× a comparison |
| H8 | a cheap statistic of the target selects high-`r` targets profitably | **refuted outright** (post hoc, amendment 2): x-arithmetic is null, and the apparent height law is the in-base spike — off the base, 88 buckets give max \|z\| = 3.3 and `lift = 1.00 ± 0.01`. The earlier "interval height tail" is retracted (§6) |

### What would have to be true for a/b to win
Not a higher yield (impossible at fixed `|F|`), not cheaper MITM work
(shape-blind, see the shadow price), and not a smaller box product
(cancelled).  The only surviving possibility is a *sub-MITM solver* that
exploits `(P¹)^m`-bihomogeneity directly.

**Withdrawing the test proposed in the previous revision.** That revision
filed "compare the solving degree of the bihomogeneous `S_{m+1}` with the
interval encoding at equal `|F|`" as lead 1.  It is ill-posed at `n = 1`: with
`m` unknowns and one Semaev equation the system is positive-dimensional, so
there is no solving degree to compare — the determined system exists only
after Weil descent (`n ≥ 2`), which is why FFD/d_reg is the right object in the
*binary* literature and the wrong one here.  In the prime case the right object
is the small-root bound, and that is the box product priced in §4.  Anyone
reviving this should first exhibit a determined polynomial system in `2m`
small unknowns with `m ≥ 3`, which is the whole difficulty.

### Where the a/b base still earns its keep
1. As a **shardable, storage-free description** of a large base (rank/unrank).
2. As a **26-bit description of a 2^51-element base** where the interval base
   needs 51 bits — relevant only if a base must be *specified* rather than
   enumerated.  Section 5 closes the natural follow-up: you cannot swap the
   description for the table (1.6·10⁴× per probe).
3. As the **null-model twin** of the interval base: a future claim about a
   factor base must beat both, and there is nothing left to claim — the mean is
   fixed by the identity (§3), the per-relation cost is shape-blind (§5), and
   the distribution is uniform off the base (§6).

---

## RECORDS

```yaml
title: "The a/b factor base has no yield advantage: the mean representation count is shape-blind"
class: disproof
claim: "For any factor base F in a finite abelian group, sum over targets of r(R) = C(|F|+m-1,m) (unordered) / |F|^m (ordered). Any two equal-sized bases therefore have identical expected relation yield. Measured exactly over the whole group for interval, Farey and random bases at 2^20 and 2^24: identical means to 6 dp, P(r>=1) differences <= 0.3% with sign flipping between rungs."
mechanism: "counting identity, not a heuristic: the sum map from m-multisets to the group has a fixed total; shape only moves mass between targets."
novelty_status: "corpus LEAD 8 closed; the identity was folklore-adjacent but never stated as the reason"
citations:
  - {ref: "mythos52-b7/ev-leads-pr-records.md LEAD 8", provenance: internal, claim: "small-rational-height base never measured against intervals at equal size", verified_by: "this note"}
  - {ref: "Check/Farey.lean::sum_repCount", provenance: internal, claim: "sum_g repCount F m g = |F|^m", verified_by: "lean 4.28, #print axioms clean"}
assumptions:
  - "IC targets kG are equidistributed, so a uniform target set is the right model"
  - "the adversary cannot choose F after seeing R without solving the decomposition (circular)"
predictions:
  - {metric: "mean r at equal |F|", direction: "identical across shapes", minimum_effect: "any deviation would falsify the identity"}
```

```yaml
title: "Farey enumeration and rank/unrank: the a/b base is an addressable array"
class: measurement
claim: "X(B) = {a/b : 1<=|a|,|b|<=B, gcd=1, b!=0} u {0} has |X| = 4*Phi(B) - 1 ~ 1.2158542 B^2, is generated by the Farey mediant recurrence in 3.3x fewer steps than the square scan (4.2-5.5x wall in Python), in O(1) memory, and is addressable by index in O(polylog B) with no storage."
mechanism: "the base is the Farey sequence of order B up to x -> -x and x -> 1/x; rank = Phi(b-1) + #{a' <= a : gcd(a',b)=1}, unrank by bisecting the totient prefix and an inclusion-exclusion k-th-coprime search."
novelty_status: "generation constant is folklore; the rank/unrank for sharding is new here"
citations:
  - {ref: "Check/Farey.lean::farey_card", provenance: internal, claim: "#fareyPairs B = sum_{b<=B} phi(b)", verified_by: "lean 4.28"}
  - {ref: "raw/bench.json, raw/selfcheck.json", provenance: internal, claim: "4.2-5.5x, 58us unrank at B=2^20", verified_by: "measured"}
assumptions:
  - "unrank cost is measured in Python; a C port should be ~50x faster"
```

```yaml
title: "The a/b base cannot replace the materialised table: 135 EEA steps per membership probe"
class: disproof
claim: "At alpha = 0.2 (p = secp256k1, B = 2^26) the rational-reconstruction membership test costs 135 EEA divisions (median, p95 150) = 16.2 kcycles ~ 5.4us at 3 GHz, against 1 comparison ~ 0.3 ns for the interval base: 1.6e4x, i.e. 14 bits per probe. One sweep of the 2^51.2-element base is ~380 years. The predicate is exact (exhaustive over all x for 44 (p,B) pairs; 108/108 recall on planted elements)."
mechanism: "membership for x = a/b with |a|,|b| <= B is rational reconstruction on (p,x), exact when 2B^2 < p (here 2B^2 = p^0.2); the EEA must descend from p to sqrt|F| before the box test can fire, which is unavoidable."
novelty_status: "the compactness-for-memory trade had never been priced"
citations:
  - {ref: "rung-slope-20261119/report.md", provenance: internal, claim: "the live backend materialises base + partial sums, 8 MB -> 8.6 GB over k=32..56", verified_by: "frozen run"}
  - {ref: "PROTOCOL-amendment-1.json", provenance: internal, claim: "H7 declared post hoc with a 10x kill line", verified_by: "this note"}
assumptions:
  - "one 256/256-bit division ~ 120 cycles at 3 GHz (limb arithmetic, 4 limbs)"
  - "interval membership is a single comparison because the base is a range"
predictions:
  - {metric: "EEA steps per probe at B = p^0.1", direction: "~log2(p)/log2(B) x constant", minimum_effect: "sub-100 steps would reopen the compactness route"}
```

```yaml
title: "r(R) is uniform off the base: the 'target height law' was in-base aliasing (retraction)"
class: disproof
claim: "Exact r(R) for every target, both rungs, three shapes, m in {2,3}, with an exact in-base bit per target: restricted to R not in F, 88 height buckets give max |lift-1| = 0.113 (at frac 5.5e-5) and max |z| = 3.31, the expected maximum of 88 standard normals. On buckets with >= 1e4 targets every lift is 1.00 +- 0.01 at every height scale. The only non-uniformity in r is R in F at m >= 3, where {R, P, -P} forces r(R) >= N/2."
mechanism: "the height statistic aliases onto the in-base set: for the a/b base h(R) <= B is (a prefix of) the base; for the interval base the in-base predicate x <= X contains the integers 1..X, which are exactly the height-x targets. Mechanistic check passed: m = 2 shows no spike at the same buckets, because pairs have no automatic relation for R in F."
novelty_status: "retracts this study's own earlier 'interval height tail' finding; the corrected statement is stronger"
citations:
  - {ref: "raw/heightlaw.json", provenance: internal, claim: "subset=outside_base rows, 88 buckets, max |z| 3.31", verified_by: "exact enumeration, both rungs, exact in-base mask"}
  - {ref: "raw/selector.json", provenance: internal, claim: "x-arithmetic statistics null (|lift-1| <= 0.02)", verified_by: "exact enumeration"}
  - {ref: "PROTOCOL-amendment-2.json", provenance: internal, claim: "H8 declared post hoc", verified_by: "this note"}
  - {ref: "Check/Farey.lean::repCount_three_ge_of_mem", provenance: internal, claim: "R in F implies |F| <= repCount F 3 R for negation-closed F", verified_by: "lean 4.28, axioms clean"}
assumptions:
  - "h(x) is the smallest B' with x in X(B'), read off the EEA on (p,x) (heights.c)"
  - "the in-base bit is exact: ecell marks the dlog of every base point, both signs"
predictions:
  - {metric: "lift outside the base", direction: "1.00 at every height", minimum_effect: "|lift-1| > 0.05 with |z| > 4 would reopen"}
  - {metric: "in-base spike at m=3", direction: ">= N/2", minimum_effect: "absent at m=2 by construction"}
```

## LEADS

1. **Bihomogeneous solving degree.** The only surviving a/b question: does the
   `(P¹)^m`-bihomogeneous `S_{m+1}` system have a lower first-fall degree than
   the interval encoding at equal `|F|`? Measured via a Macaulay rank profile
   at a 32-bit rung, m = 3,4.  Kill line: D_bihom ≥ D_interval at equal `|F|`.
2. **Sign-redundancy audit of existing yield numbers.** Any corpus yield
   figure computed by counting hits over `(a,b)` pairs is inflated by `2^m`
   (exactly: 4 and 8 measured).  Worth a grep over the campaign's yield tables.
3. **Rank/unrank as a shard primitive** for any large structured base
   (interval bases get it free; subgroup and mixed bases may not).
4. **Uniform rank-profile schema** — already LEAD 11 of b7; nothing here
   changes it.
5. **Withdrawn:** the interval-base "height tail" of the previous revision.
   It was the in-base spike aliasing onto a height-contiguous set (§6).  Do not
   reopen it without an exact in-base mask.
6. **Closed by this note:** the "compact description replaces the table" hope
   for the materialised-sieve backend (135 EEA steps/probe, 1.6·10^4x a
   comparison).  Do not re-propose it without a sub-100-step reconstruction.

## Filing

`raw/claim_draft_relation_yield.json` is a schema-complete `relation_yield`
draft for the **prime** regime of `docs/ic/boundary_targets.json` (schema v2),
18 cells, with all six required stage fields plus the six global provenance
fields.  It is a draft: filing is a write to the `crypto` ledger, which is out
of scope here.  Note for the filer: the hit rate is *exact* per base, so the
`ci95` field carries the binomial interval a T-target estimate would have —
it is there for comparability, not because the value is sampled.  The
`base_id_or_hash` hashes the recipe, not a materialised dlog list (stated in
`base_id_basis`).

## Reproduction

```
cd ecdlp-ideas/prime-ic-52-20261118/ab-farey-20261123
python3 abgen.py counts && python3 abgen.py selfcheck && python3 abgen.py bench
cc -O3 -o ecell ecell.c -lm && cc -O2 -o findprime findprime.c
./findprime 16777216 2 > raw/prime24.txt     # ~6 min, first line used
python3 run_cells.py && python3 analyse.py
python3 membership.py          # section 5 (post hoc, PROTOCOL-amendment-1.json)
cc -O3 -o heights heights.c && python3 selector.py && python3 heightlaw.py
                               # section 6 (post hoc, PROTOCOL-amendment-2.json)
cd lean-check && lake exe cache get && lake build && lake env lean Check/Axioms.lean
```

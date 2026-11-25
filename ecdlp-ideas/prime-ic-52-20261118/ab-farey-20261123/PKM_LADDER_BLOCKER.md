# PKM yield ladder: runnability audit and blocker

Date: 2026-11-25. Goal step 2 of the a/b study: run the PKM yield ladder at
p ≈ 2^48/2^64/2^80 (m=4, t=4, σ=6, mirrored primes) to decide whether the
18–20 bit prime-IC margin survives.

**Verdict: blocked. No backend in the repo instantiates that configuration.**
This note names what is missing, with the evidence for each claim, so the next
person does not repeat the search.

## What the ladder is specified to be

From `ecdlp-ideas/prime-ic-52-20261118/mythos51-b5/pf51-pr-records.md`
(record "PKM yield ladder at p ~ 2^48/2^64/2^80 with mirrored prime shape"):

> At p ~ 2^48, 2^64, 2^80 with p = 3 mod 4, p = 1 mod 3, v₂(p+1) = 4, m=4,
> sigma=6, t=4, measure yield Y and observed D per cell. Kill if
> log Y(48) − log Y(80) ≥ 9 (slope 9/32 = 0.28 per bit) or D rises.

and from `mythos51-b3/pf51-pkm-tower-v2.md`: the entire 18–20 bit margin is
carried by "per-attempt cost at m = 4, and its independence from N and p", for
which the corpus has "exactly one cell (m = 4, D = 7, P-192, N = 2^12) and no
yield measurement at all". m = 3 is explicitly not a substitute: at m = 3 the
model has no rows because it is already dead on the per-attempt budget.

## What exists (all of it m ≤ 3)

| producer | arity | tower family | prime shape | what it measures |
|---|---|---|---|---|
| `examples/pkm_coverage.rs` | **m ∈ {2,3}** — `for m in [2usize, 3]`, `choose_primes(fam, m, …)` | Kummer, Dickson split, Dickson torus | `p = k·2^(t0+1) ± 1` ⇒ 2^t \| p−1 | exact coverage π and mean decompositions (i.e. **yield**) |
| `examples/pkm_odd_tower_f4.rs` | m ∈ {2,3} (`u` at m=3) | any degree mix, `S = ∏ q_j` | whichever the system is built on | F4 solving degree, planted/refute, `null` control |
| `examples/pkm_ss_tower.rs` | m = 2 (`full`), m ≥ 3 (`chain`) — no m=4 flag surface | supersingular j1728/j1728-twist/j0/j0-twist, torus, ordinary | `2^t \| p+1` (the only arm matching v₂(p+1)=4) | F4 solving degree only, at small primes |
| `examples/ic_next10_03_pkm_degree.rs` | exact δ at m=2; "any m" only for the Macaulay matrix | Kummer tower | small primes | XL/Macaulay solving degree |

Checks run: `grep -c 'for m in \[2'` and `grep -c 'm = 4'` across every
`examples/pkm*.rs` — **zero** occurrences of m=4 in any PKM producer;
`grep -rln sigma examples/pkm*.rs` — **zero** hits.

## The four missing pieces

1. **An m = 4 PKM/tower decomposition producer.** All four engines cap at m=3;
   `pkm_coverage`'s arity loop is literally `for m in [2usize, 3]`. This is the
   cell the margin rests on, so nothing else can stand in.
2. **The σ = 6 fold in the PKM path.** `pkm_coverage` multiplies the smoothness
   estimate by a constant `mf = 6.0` for m ≥ 3 — that is a *modelling* factor,
   not a symmetry reduction on the base. No PKM producer folds the
   endomorphism/orbit action.
3. **Yield on the supersingular arm.** The b5 prime shape (v₂(p+1)=4) admits
   only the supersingular tower at t=4, but the supersingular arm
   (`pkm_ss_tower`) computes solving degree at small primes and never yield;
   the yield engine's three families all need 2^t | p−1 and so cannot express
   that shape.
4. **The 48/64/80-bit rung set with mirrored primes.** No script generates
   p ≡ 3 mod 4, p ≡ 1 mod 3, v₂(p+1) = 4 at 2^48/2^64/2^80 with the tower and
   base schedule frozen across rungs.

## Minimum path to unblock

In increasing order of work:

1. Add arity 4 to a coverage-style exact enumerator (|V| = 2^t = 16 keeps the
   enumeration at 2^t·something small, so the yield half is cheap at any p).
2. Add the supersingular tower arm to that enumerator so v₂(p+1)=4 is
   expressible (the set is `x(R' + ⟨Q⟩)` for a cyclic ⟨Q⟩ of order 2^t).
3. Add the σ=6 fold to the base (quotient the base by the order-6
   automorphism action), and report the *effective* base size, not the naive
   one — the a/b work in this repo shows how easily a fold is double counted
   (`sigma` acting as 3 on a negation-closed base).
4. Freeze the rung set and the base schedule, then run ≥ 20 attempts per rung
   and fit per-attempt cost and yield as separate slopes.

Steps 1–2 are small; step 3 is where the corpus has been wrong before.

## What was NOT done, and why

No substitute run. The goal's constraint is explicit: do not swap in a
different experiment if the PKM backend is unrunnable. Running m=3 (which the
engines do support) would answer a question the corpus has already closed, and
running the torus family at v₂(p−1) = t would change the prime shape the test
is defined on. Both would be substitutions, so neither was run.

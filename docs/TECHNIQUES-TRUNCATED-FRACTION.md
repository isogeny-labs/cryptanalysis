# Truncated-product fractions and error budgets

Status: technique note. Adopted 2026-11-04 from an external secp256k1-ecdlp
cost-model submission (LEAF21/22/23 lineage). This note changes no code; it
records the method, its error budget, the verification protocol that backs it,
and where it does and does not transfer to this repository.

Related: [REVIEW-CHECKLIST-COST-CLAIMS.md](REVIEW-CHECKLIST-COST-CLAIMS.md),
[ALGORITHMS.md](ALGORITHMS.md).

## 1. The shape of the problem

A 256-bit prime field is held as four 64-bit words. A consumer needs a
*truncated window* of a product, not the product:

```
T(x) = floor(Z / 2^128) mod 2^128,   Z the integer representative of x mod p
```

with a stated tolerance, typically because `T(x)` is hashed, bucketed or used
as a table index where a small error is absorbed by a fixup path.

The classic route is: full 4x4 word product, fold modulo `p` with a carry
chain, then extract the window in a later stage. That pays for 16 word
products and the reduction, and it pays them **before** the consumer runs.

## 2. The technique: compute the window directly

Let the label coefficient `c` be given by rows `R_k = c * 2^(64k) mod p` and
the multiplicand `w` by words `M_k`. Then

```
Z = sum_k M_k * R_k  ==  c * w   (mod p)
```

and the window of `c*w` at bits 128..255 depends on each row product
`M_k * R_k` only through the words that land at or above bit 64 of that
product. So per row we evaluate **four single-word products** and accumulate
them into 128-bit lanes, skipping the fold and the carry chain entirely. The
rows `R_k` are already reduced; nothing is re-reduced afterwards.

The result is not exact. It sits in `[0, 64]` units of `2^-128` **below** the
true value, from three terms:

| term | worst case | source |
|---|---|---|
| floor | 1 unit | discarding the low 128 bits |
| dropped carries | 7 units | carries out of the accumulated window, one per row boundary |
| shift losses | 56 units | right-shifting partial sums into lane alignment |
| **total** | **64 units** | at most `2^-122` relative to `Z / 2^128` |

The bound is **one-sided and monotone**: every operation drops bits, nothing
rounds up. Containment arguments depend on that, so never introduce a rounding
step into the chain.

## 3. Window shifting: the `beta` amortization

If the consumer needs two adjacent windows — bits 128..255 and bits 192..319 —
do not compute a second product. With `beta = 2^64 mod p`, the window at 128
of `c * (beta * w)` is the window at 192 of `c * w`. So:

1. form `beta * w` once per multiplicand, as a paired product on the tabled
   rows of `beta`;
2. share it across every component that consumes the second window.

In the originating submission one `beta * w` serves three components times two
signs, i.e. six uses, so a single extra multiplication replaces three. The
general rule: for windows separated by `d` words use `beta = 2^(64d) mod p` and
table its four rows once.

## 4. Where the win comes from

The submission's ledger, in instructions per incidence or per leaf:

| stage | before | after |
|---|---|---|
| forward walk | 98 | 98 |
| backward walk | 1206.5 | **1297.5** |
| key/emit stage | 334.5 | **146.5** |
| fixup sites | 37 | 33 |
| **per leaf** | **307.7797** | **291.6131** |

The backward walk gets *more* expensive (it now evaluates the windows inline);
the key stage gets much cheaper (it loads six already-computed fractions and
does only the sums, index and block emit). The trade is worth it because the
key stage has higher fan-out per unit of streamed work:

```
break-even:  d(bwd) * n_bwd  <  d(keys) * n_keys
```

This is the transferable principle, independent of the arithmetic: **move work
from the terminal, high-fan-out stage into the streaming, low-fan-out stage**
when the terminal stage runs more often, and then prove the moved work is
cheap per record.

## 5. Why a bounded error is acceptable at all

An approximate label is only sound under an explicit contract:

* `W` — the set of inputs on which the label is exact.
* `D'` — the set of inputs on which the label is bounded by the error budget.
* Every input outside `W ∪ D'` must take a verified path (fixup), and the
  proportion of inputs inside `D'` must be priced into the success argument.

Widening the error set has three costs, all of which must be recomputed
together: more error residues (here 1,305, rate below `2^-16.65` per leaf), a
larger lattice/box factor (here `1 + 2^-17`), and a lower success probability
at fixed `q1` (here still at least 0.3900000036 at `q1 = 145,292,068`).
Removing the full folds also removes their failure modes, so the fixup rate
improves and `q1` drops slightly — an approximate fast path can be *more*
reliable than the exact path it replaces, but only if the bookkeeping is redone
rather than inherited.

## 6. Branch-free metering

Rare events (carry out of the window, rare index collision, degenerate walk)
are not branched on. The hot path runs an unconditional chain and increments a
counter:

* the instruction count per step becomes constant, which is what an
  instruction-denominated cost model requires;
* the success argument charges `P(event)` analytically instead of paying a
  branch per occurrence;
* the meter must be an exact counter, not a sample, or the analytic charge is
  unsound.

This is how a cost model can claim a number to twelve decimals while a
data-dependent branch would make the count input-dependent.

## 7. Verification protocol

The arithmetic is the small part; this protocol is the durable part.

1. **Exact certificate.** Recompute every claimed constant with exact
   rationals or integers — success probability, ledger, claim rounding — and
   *derive* the error table from the per-term bounds rather than restating it.
2. **Bit-exact reference model.** Compare the optimized kernel against a
   straightforward model record by record, on production batches, not on toys.
3. **Adversarial inputs.** Near ties (fraction within a few units of a bucket
   boundary), edge-of-`W` and edge-of-`D'` classes, weak multipliers, every
   representation the caller can choose.
4. **Fixup coverage.** Each fixup site type alone against its bit-level model,
   including the shortened last-row shift; plus a never-branching copy that
   runs every site as an inline chain.
5. **Mutant testing.** Single-change mutants of kernel, models, bound and
   certificate must all fail. A mutant that survives is an untested claim.
6. **Static count.** Assemble the kernels and count instructions; the count is
   part of the ledger, not an estimate.
7. **Sandboxed reproduction.** No network, no home directory, read-only
   inputs, fixed seeds, several seeds, and a layout that matches the grader's.

## 8. Applicability in this repository

* **Do not port the arithmetic here.** This library works modulo `p < 2^64`
  with single-word Montgomery arithmetic; there is no multiword window to skip
  and the trick degenerates to "multiply". See the scope note in
  [ALGORITHMS.md](ALGORITHMS.md).
* **Do port the methodology.** The certificate/model/mutant triad should back
  every constant published in [BENCHMARKS.md](BENCHMARKS.md); branch-free
  metering is the right way to keep `ca_bench` timings from becoming
  input-dependent; the `W`/`D'` contract is the right shape for any approximate
  index or fingerprint.
* **Where the arithmetic does apply.** Multiword paths: secp256k1-sized
  experiments, `ecc2k130` bignum work, index-calculus matrix stages that use
  truncated fingerprints, and any GLV-style split where a second window is
  needed and a `2^(64d)` shift can be tabled.

## 9. Failure modes

* Assuming the three error terms cannot co-occur; re-derive the worst-case sum
  from the actual loop structure.
* Introducing rounding so the bound stops being one-sided.
* Widening `D'` without recomputing `q1` and the success probability.
* Amortizing an odd leftover pair as if it were full.
* Counting the extra stage work once per component instead of per incidence.
* Truncating *after* reduction instead of before — that changes which words
  contribute and invalidates the term table.
* Replacing the exact meter with a sampled one and keeping the analytic charge.

## References

* Origin: secp256k1-ecdlp submission note, package
  `six-class-stored-leaf-birthday-124921470249497`; lineage LEAF21 (stored
  negatives), LEAF22 (`k`-record transport), LEAF23 (Fourier-component leaves).
* D. E. Knuth, *The Art of Computer Programming*, vol. 2, sec. 4.3.1
  (multiple-precision arithmetic and carry propagation).
* R. P. Gallant, R. J. Lambert, S. A. Vanstone, *Faster point multiplication on
  elliptic curves with efficient endomorphisms*, CRYPTO 2001 (the other reason
  a `beta`-style tabled constant shows up in this stack).

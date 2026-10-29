# Native hashed ECDL: implementation audit and Lemma 1 sampling

2026-10-29. Development correctness work, with no speed or security claim.
Reviewed crypto main `037bfc872342ff66a0cc4c6a5e1d46b1efac3029` and
cryptanalysis main `0366546e2a26c4acc8d3a32890b2427fb9d6a844`.
The requested work was to examine the six supplied approaches, pursue their
implementation, then follow the implementation through validation.

## Six-component examination

Paths below are relative to `crates/hashed-ecdl-tensor/src/` in crypto;
the byte-identical mirror is `bindings/rust/hashed-ecdl-tensor/src/`.

| Component | Existing implementation examined | Assessment and work in this change |
| --- | --- | --- |
| Four-step reduction | `reduction.rs`: `FactorBase::enumerate`, `decompose`, `solve`, `row_dependency`, `verify_with_rng` | Present. Slot-specific columns, N+1 rows, nonzero V, and independent scalar replay are implemented. The deterministic decomposition oracle receives neither relation scalars nor known factor-base logarithms. |
| Counting and finding | `network.rs`, `contraction.rs`: `count`, `witness` | Deterministic search present; random sampling absent. Added `Counter::sample` with exact prefix-count probabilities. Uniform language sampling requires parsimony; otherwise the documented distribution weights auxiliary completions. |
| Fourier multiplication | `encoding.rs`: `MultiplicationParameters`, `transform`, `integer_multiply` | Present. Integer-only J/k/L selection, canonical Fermat-ring words, two transform stages and carry constraints. Existing independent product and size checks cover widths through 513 bits. |
| Point addition | `encoding.rs`: `valid_point`, `point_add` | Present. Identity, second identity, inverse, ordinary and doubling selectors; unconditional intermediates; inactive slope zero. Existing full small-curve pair checks reject altered outputs. |
| Hashed factor bases | `reduction.rs`: `FactorBase`; `encoding.rs`: `hash_member`; `decomposition_network` | Present. Inverse-hash enumeration, canonical coordinate hash predicates, subgroup checks and cofactor projection. Coverage is a probability over random seeds, not a guarantee for each fixed base. |
| Cost and m choice | `reduction.rs`: `Config::for_curve`; `contraction/recursive.rs`: `Setup` | Present as parameter choices and admission guards. These do not certify this implementation's asymptotic cost. The normalized illustrative crossover below is not a measurement. |

The earlier Python binary-curve bucket/cutset prototype is a distinct execution
path, with a quadratic multiplier and stand-in contractor. It is not the native
prime-field Fourier/Appendix D implementation examined here. No Python research
execution path was extended or run.

## Exact sampling implementation

With current count C and zero-prefix count C0, set C1=C-C0 and select the next
bit with integer probabilities C0/C and C1/C. Only a genuinely ambiguous branch
requests randomness, through the existing rejection sampler. Already pinned
interface bits are copied. Zero count returns `None`; resource, counter and
entropy errors propagate. At most one initial contraction and one contraction
per unpinned interface bit are needed. The existing deterministic relation
finder is unchanged.

The three-word OR example has root count 3, a zero subtree of size 1 and a one
subtree of size 2. Tests enumerate all six equiprobable root/child draws and
require exactly two preimages per accepted word, without a statistical tolerance.
When only the first bit is exposed, its interface words instead have weights
1:2. A separate control checks that distinction; projected cofactor witnesses
must not silently be called uniform words.

## Recursive audit control

Existing forced recursive tests used u=1, retaining odd Hermite nodes only.
The added control uses u=2, a=2, L=4, radix 2, two parallel edges and a
degree-4 extension ring at precision 3. It retains both valuation levels 0
and 1, exercising different label coordinates, taper multiplicities and child
precisions. Three label layouts times three predicate pairs give nine exact
comparisons with independent direct contraction, including zero contractions,
crossing ports and local ports. These pass. Forced parameters bypass source
size/shrink admission; this is a bounded correctness control, not a run of the
general admitted recursion or a proof of its complexity.

## Illustrative cost trade-off

Let L=log2(b). For the illustrative exponent E=b/m+mb/sqrt(L), the continuous
minimum is at m=L^(1/4), with E=2b/L^(1/4). Against Pollard's exponent b/2,
their exponent ratio is 4/L^(1/4); equality is at L=256, hence b=2^256 bits.
At b=256, the illustrative integer choice m=2 gives E=128+512/sqrt(8),
about 309.02, against rho's 128. These are derived exponents, not measured
operation counts or evidence about the concrete solver.

The prefactor 2 survives balancing two unit-weight terms. Setting the hidden
constant of the already-collapsed expression b/L^(1/4) to one instead yields
equality at L=16. Thus “all constants one” must specify the pre-balancing model;
neither convention supplies a concrete cryptanalytic crossover. Actual Gaussian
elimination costs, encoding constants, memory, predicate work and the fallback
must be included in any later measured comparison.

## Sources and validation

Read before choosing the implementation change:

- Akshima et al., Bochum v0.2, pinned revision
  [`1ee44e562b1b9a50ea339f3b8f81112b5a24b96f`](https://github.com/bochum-crypto/subexponential-ecdl/tree/1ee44e562b1b9a50ea339f3b8f81112b5a24b96f),
  §§2–3, particularly Lemma 1 and Theorems 3–4.
- OpenAI October 25 manuscript, pinned revision
  [`7ef5c0cc5ca4b0e072b7a050fca09ab24bc6fa3a`](https://github.com/openai/math/tree/7ef5c0cc5ca4b0e072b7a050fca09ab24bc6fa3a/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026),
  Appendix D.4.1–D.4.6: immutable creation precision, packing, both taper levels,
  mode coefficients and child tensors. The external theorem remains conditional.
- Repository `docs/hashed-ecdl.md`, current/historical validation receipts,
  `docs/hashed-ecdl-completion.md`, latest daily log and canonical problem record;
  native source and existing controls were read directly.

The unmodified native release panel passed 27 tests. New focused sampling
controls (2 tests) and the two-level taper control (1 test, nine graph cases)
pass. Final commands and outcomes are recorded in [validation.txt](validation.txt).
This round uses Rust 1.99.1 on a Linux x86-64 cloud development container,
without performance isolation. Test-run durations are not performance evidence.

[Diagram](sampling.svg) · [rendered report](report.pdf) · [editable source](report.typ).
The diagram is explanatory rather than a quantitative performance graph, because
no matched timing comparison was performed. Canonical IC/rho scoreboard,
progress-timeline and leaderboard values are unchanged: no measured cost,
curve, route, rank or admitted result changed.

## Remaining obligations

All six native components exist; this change completes the optional Lemma 1
sampling API and broadens bounded recursion checks. General correctness and
complexity audit remain partial. The public backend still follows literal
admission guards, with finite-size fallback on practical graphs. No speedup,
asymptotic replication proof, deployed-curve run or new mathematical theorem
is established. No Lean theorem is claimed for these software controls.

The next discriminating audit is to cross-check multi-coordinate packet/mode
identities and retained creation precision against direct contraction on richer
small ring-valued tensors, while separately checking the source's construction
and space accounting. Preserve any first mismatch as a regression fixture.
The existing [general audit problem](https://github.com/isogeny-labs/crypto/blob/main/problems/hashed-ecdl-tensor-backend.md)
remains open; a small passing panel does not resolve it.

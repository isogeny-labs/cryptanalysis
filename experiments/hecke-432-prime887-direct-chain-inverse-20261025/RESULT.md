# Direct inversion recovers all 872 p887 level-432 source chains

The [direct inverse](recover_sage.py) reconstructs **every
noncuspidal rational level-432 chain at p=887** from its rational
\((C,E,B)\) triple, without looking up a chain in the saved source
census. For each C point it computes the four modular j values,
constructs the canonical source-curve variants, enumerates cyclic
16- and 27-isogeny paths, filters the 27-path by its j sequence, and
evaluates the normalized B map on each remaining pair. It then
quotients the special source automorphisms and returns every matching
chain key.

The complete input contains 872 rational resolvent pairs from the
preceding exact-gcd screen. Eight have no rational B candidate.
The other **864 valid (C,E,B) triples** yield **872 distinct source
chains**: 856 triples have one chain and eight have two. All 880 raw
forward evaluations map to a valid input triple; the j=1728
automorphism quotient identifies eight redundant raw paths.

| Measurement | Complete p887 result |
| --- | ---: |
| Rational resolvent pairs / valid triples | 872 / 864 |
| Distinct C points / constructed source models | 218 / 110 |
| Raw forward chain evaluations / matched outputs | 880 / 880 |
| Canonical recovered source chains | 872 |
| Triple candidate multiplicities | 856 single, 8 double |
| Unmatched outputs, missing triples, incorrect candidate sets | 0, 0, 0 |

The [protocol](protocol.json) freezes exact hashes for the gcd input
shards, coordinate maps, cyclic-path enumerator, forward modular
evaluator, and the audit-only corrected census. The producer verifies
all hashes but **does not parse or consult the census or corrected rows**. Its
[result](result.json) hashes four [candidate shards](candidates-00.json)
with every input triple and its complete chain-key set. The
[checked-Sage runtime receipt](sage-runtime-info.txt) identifies the
accepted local build.

For generic source j, the construction uses the canonical
`EllipticCurve_from_j` model. At j=0 it uses the base model representing
the common base/twist coarse orbit. At j=1728 it constructs both base
and twist models and recomputes the order-two automorphism orbits from
their degree-16 and degree-27 kernel polynomials. This removes eight
duplicate raw paths while retaining four distinct twist orbits.

The separate [integer-field audit](audit.py) recovers each corrected
source row's original C point from four modular j functions, computes
its E point from the recorded B point, and builds the expected
\((C,E,B)\)-to-chain-key set. It compares **all 864 generated candidate
sets** exactly, including the [eight double fibers](audit.json), and
checks the eight gcd inputs with no rational B. The audit finds no
missing or extra triple and no wrong or dropped chain. The correction
rows enter only this post-generation comparison.

## Proof map

| Result | Proof or replay |
| --- | --- |
| Direct source-model and cyclic-path generation | Checked-Sage 16/27 path enumeration from each C-derived source j, exact modular j filtering, 880 kernel-polynomial forward evaluations, and special automorphism orbit computation. |
| Exact 864 triple candidate sets and 872 chain keys | Producer candidate shards and independent full corrected-source coordinate/pair audit; all keys compare equal. |
| Equality from containment and the two 872-key counts | Pinned Lean theorem `P887DirectChainInverse.generated_keys_perm_corrected`, with explicit duplicate-free, containment, and cardinality hypotheses. |
| 856 single plus eight double fibers; 880 raw minus eight orbit duplicates | Checked Lean arithmetic declarations `candidate_fiber_total` and `raw_orbit_total`; concrete partitions and orbits are verified by the finite-field replays. |

The [Lean build](formal/build-output.txt) passes with only standard
`propext`, `Classical.choice`, and `Quot.sound` foundations for the
list theorem and no axioms for the count identities. The
[dependency record](formal/DEPENDENCIES.json) pins the toolchain.
The concrete modular maps, Sage isogeny objects, and complete
finite-field enumeration remain outside Lean; the exact bridge is
the independent executable audit rather than an assumed Lean
premise. `lean4checker --fresh` is unavailable on this host.

Replay from the repository root:

~~~sh
./sage --runtime-info
./sage -python experiments/hecke-432-prime887-direct-chain-inverse-20261025/recover_sage.py
python3 experiments/hecke-432-prime887-direct-chain-inverse-20261025/audit.py
cd experiments/hecke-432-prime887-direct-chain-inverse-20261025/formal && lean ChainCoverage.lean
cd .. && shasum -a 256 -c SEAL.sha256
~~~

The construction now has a complete rational inverse on the declared
p887 image. The next experiment is the same direct inversion at p883
and p997, followed by an operation-count and online-time study of the
candidate generation path against the frozen source-independent
inputs.

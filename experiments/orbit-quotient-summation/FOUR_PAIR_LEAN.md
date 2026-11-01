# Four-summand pair lookup: proof and implementation check

Date: 2026-10-23. This is a retrospective validation of the frozen
2026-09-26 orbit-quotient toy experiment, not a new density or timing run.

## Question and scope

Does the two-pair index in `m4_stats` preserve four-summand *existence*, and
does its count summary match direct enumeration on an independent small case?
The source is [`orbit_core.py`](orbit_core.py), SHA-256
`ae38c564eb495b87e2293f8e3cc822278082ec79670ef0b87738ddb706af3dd8`.
The frozen [`results/reference.json`](results/reference.json), SHA-256
`2be2d0a18eaadd4d7babe588866b25a8a13bea0021ee630182dcc07d3d925be5`,
was read but not regenerated or changed. Source revision before this addition:
`42761f85b06242cb54f2a5fa405c723451897503`.

| Requirement | Evidence | Status |
|---|---|---|
| Four-summand support equivalence | `quadruple_matches_iff_two_pair_lookup` in [`lean/OrbitPairIndex.lean`](lean/OrbitPairIndex.lean) | Proved for finite natural-number lists and every natural modulus, including zero |
| Faithful source link | `pair_index` forms `(x+y)%r` buckets; `m4_stats` joins complementary buckets | Source reviewed; formal model starts after representative enumeration |
| Four-summand count summary | Direct enumeration in [`test_orbit_quotient.py`](test_orbit_quotient.py) | Verified for the pinned small case; no universal multiplicity proof |
| Frozen n=13/n=19 summary and degree-131 calculation | [Raw full replay](validation/replay-20261023.json) and [source-bound comparator](validation/check_reference_replay.py) | Reproduced under the current source; no independent algorithmic reimplementation or degree-131 measurement |

## Proof map and readable argument

For finite lists \(A,B,C,D\), define \(P_r(A,B)\) as the list of residues
\((a+b)\bmod r\) for every \(a\in A,b\in B\). The theorem states, for every
natural \(r,t\), that

\[
\exists a,b,c,d:\;a\in A, b\in B, c\in C, d\in D,
\quad(a+b+c+d)\bmod r=t\bmod r
\]
is equivalent to
\[
\exists s\in P_r(A,B),u\in P_r(C,D):\quad(s+u)\bmod r=t\bmod r.
\]

The forward direction chooses \(s=(a+b)\bmod r\) and
\(u=(c+d)\bmod r\). `mem_pairTotals_iff` proves each selected residue occurs
in its pair list. Modular addition and associativity make their sum equal
the original four-summand residue. The reverse direction expands each pair
membership into witnesses and applies the same modular identity backward.
Lean's quantifiers range over all finite natural-number lists, including
duplicates and empty lists. They do not encode elliptic-curve points or
certify that `slot_sets` produced the intended representatives. Lean's
natural-number modulus also includes zero, where its `%` operator is defined;
the Python implementation requires a positive subgroup order because Python
raises on `% 0`. All experiment instances and the direct test have `r > 0`.

The existing `mem_pairTotals_iff` and `triple_matches_iff_pair_lookup` remain
the dependencies and three-summand proof. The pinned toolchain is Lean
4.34.1; `lean/check.sh` runs `lake build`, then prints the axioms of all three
theorems and checks the exact output. Each theorem depends only on the
standard foundations `propext` and `Quot.sound`; there is no `sorry`,
`admit`, custom axiom, or unverified native evaluation in this module.

## Independent implementation check

The new test uses modulus 11, keys 1 and 2, scalar labels 1 and 3,
Frobenius label 2, signed orbit factors 1 and 10, four slots, both fixed and
orbit modes, and every target 0 through 10. For each of 16 ordered key
quadruples and each target, it enumerates four representative choices
directly without calling `pair_index` or reading its buckets. It compares
domain size, positive tuple count, density, witness minimum/maximum/mean/
median, and single-witness count against `m4_stats`.

Run from this directory with Python 3.11 or newer:

```sh
cd experiments/orbit-quotient-summation/lean && ./check.sh
cd .. && python -m unittest -v test_orbit_quotient.py
```

Observed on 2026-10-23: Lean built three jobs and printed the expected
axioms for all three declarations; five Python tests passed in 1.868 s with
Python 3.11.17. The initial Python 3.9 invocation could not execute the
pre-existing `int.bit_count` call; the same test suite passed under 3.11.
The raw successful outputs are retained in
[`validation/lean-check.log`](validation/lean-check.log) and
[`validation/python-tests.log`](validation/python-tests.log).
The test checks only this finite case. It does not prove the generic count
multiplicity of each pair bucket or the correctness of curve arithmetic.

## Full frozen-case replay

The original `run.py` was executed with its unchanged seed 20260926 and both
frozen cases, `(n,s,beta)=(13,4,5475)` and `(19,6,112679)`, under Python
3.11.17. Its SHA-256 is
`a65cd729bbddacbbf7522cf05256b2b5c90b56efa3e55446352dfc9114519e12`.
The [complete raw JSON](validation/replay-20261023.json) has SHA-256
`d5355ce904640e77fbc61863a026d53f949321a2ae65808a9e69915234f88295`.
The [receipt](validation/replay-20261023.receipt.json) records the command,
source hashes, output, and checker results.

```sh
python run.py --out validation/replay-20261023.json
python validation/check_reference_replay.py validation/replay-20261023.json
```

The comparator maps the full output to the archived compact summary. It
passed all 22 named n=13/n=19 case fields, the seed, schema, and every
degree-131 projection field. Integer fields compare exactly; equal integer
and float encodings such as `16` and `16.0` compare equal; other floats use
relative and absolute tolerance `1e-13` for cross-runtime comparison. An
initial strict-type check found only five `16` versus `16.0` encodings; no
non-equal float value needed the tolerance. The archive used Python 3.13.5,
while this replay used Python 3.11.17. Changing the first n=19
phase-free m4 positive count from 279208 to 279209 made the checker exit 1
and identify that field. This is a same-code reproduction, so it verifies
determinism and archived summary transcription, not independent correctness
of the curve implementation or the unobserved degree-131 projection input.

## Result and visual

The new result is a structural proof of four-summand support, a finite
implementation cross-check, and a full same-code replay of the archived
summary. No measured performance result, relation density,
curve identity, or ECDLP claim changed. The [editable diagram](four-pair-proof.dot)
and [SVG](four-pair-proof.svg) show the two pair buckets, modular join, and
direct-enumeration check; the [PDF](four-pair-proof.pdf) contains this summary
and the figure. There are no graphable new measurements. The experiment's
frozen `results/reference.json` and this report's existing n=13/n=19 tables
were checked for unchanged source data; unrelated `volcano-ic` route graphs
do not represent this result and are unchanged.

Remaining validation work for the original broad experiment: formalize
representative generation/curve arithmetic and generic bucket
multiplicities; independently reproduce the n=13/n=19 answers with a
separate implementation or independently checked point arithmetic; and
trace the 68/256 degree-131 sample to its original source and controls.
This addition does not close those obligations.

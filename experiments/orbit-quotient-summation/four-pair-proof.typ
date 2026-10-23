#set page(paper: "a4", margin: 1.7cm)
#set text(font: "DejaVu Sans", size: 10pt)
#set heading(numbering: "1.")

= Four-summand pair lookup: proof and check

_2026-10-23 · retrospective validation of the frozen orbit-quotient toy experiment_

The two-pair index used by `m4_stats` has a Lean proof for its four-summand *support*: for arbitrary finite lists of natural-number representatives and every modulus and target, a direct four-summand match exists exactly when two pair-index residues join to the target. The theorem is `OrbitQuotient.quadruple_matches_iff_two_pair_lookup` in `lean/OrbitPairIndex.lean`.

#figure(image("four-pair-proof.svg", width: 100%), caption: [Pair residues, the modular join, and the independent finite check. Solid paths are the theorem's mathematical structure; dashed paths are the Python implementation check.])

== Evidence and limits

- Pinned Lean 4.34.1: `lean/check.sh` built three jobs. Axiom audit: `propext`, `Quot.sound` for each of the three declarations.
- Python 3.11.17: five tests passed in 1.868 s. The new test directly enumerates four representative choices for every one of 16 ordered key quadruples, 11 targets, and both fixed and orbit modes; it checks all eight `m4_stats` summary fields.
- Source `orbit_core.py` SHA-256: `ae38c564eb495b87e2293f8e3cc822278082ec79670ef0b87738ddb706af3dd8`.
- Frozen `results/reference.json` SHA-256: `2be2d0a18eaadd4d7babe588866b25a8a13bea0021ee630182dcc07d3d925be5`.

This proof begins with already enumerated scalar representatives. Lean covers modulus zero under its defined `%` operation; Python requires the positive subgroup order used by every experiment instance. The proof does not establish curve arithmetic, representative generation, generic bucket multiplicities, historical density measurements, the degree-131 projection, or a performance gain. No canonical result table or performance graph changed. The full proof map, method, commands, and open checks are in `FOUR_PAIR_LEAN.md` beside this PDF.

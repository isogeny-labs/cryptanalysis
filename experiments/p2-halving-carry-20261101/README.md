# H111 independent replay: first-layer p² halving carry

The independent implementation replayed every one of 9,096 canonical carries,
32 matched controls, and both coordinate-isomorphic panels. It reproduced
scientific digest
`383eb1faf53a4fe17088780cb71528df3f20913abdc022c4348f411c26ce4fd5`.

All structural and torsion-section checks passed. None of the 24 frozen
predicates was exact on any of 28 rows, so the repeated-halving decoder did not
run. Canonical best-fit accuracy (0.526427–0.657658) overlapped the controls.

The self-contained `h111_reference_verify.py` was run against the canonical
content-addressed result from crypto #3118. It does not import the canonical
H111 runner: it recomputes elliptic-curve arithmetic, Hensel lifts, kernel
formal coordinates, random sections, matched labels, predicate scores, and the
stable digest. `REFERENCE_REPLAY.json` pins the raw and deterministic-gzip
hashes used for the replay.

This is a scoped null for the frozen family, not a generic ECDLP or
external-novelty claim. Store-class gzip/PNG bytes live only in the canonical
crypto artifact store; this replay repo retains the editable SVG and PDF.

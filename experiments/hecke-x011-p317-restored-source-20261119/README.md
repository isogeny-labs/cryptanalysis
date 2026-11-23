# One degree-2 Hecke row completes the corrected p317 fiber rank

The restored X0(11) point `P39=(16,60)` has three rational degree-2
Hecke neighbors in the corrected 40-point `p=317, |t|=2` fiber. Their
exact group equation is

`P15 + P17 + P36 + 2 P39 = 0`.

Adding **this one verified Hecke row** to the archived 103-row matrix
raises its rank from **38 to 39 over F61** and from **39 to 40 over Q**.
The relation therefore supplies the missing direction on the complete
fiber without using a direct-triple row. The 40-column identities and
archived row order are pinned by the preceding
[complete-fiber experiment](../hecke-x011-p317-complete-fiber-rank-20261119/README.md).

| Hecke degree | Neighbor-x factor degrees | Rational-neighbor status | Outside trace | Accepted new class row |
| ---: | --- | --- | --- | ---: |
| 2 | 1, 1, 1 | three class points | none | 1 |
| 5 | 1, 1, 4 | two class points, one four-point orbit | `(109,9)` | 0 |
| 13 | 1, 1, 12 | two class points, one twelve-point orbit | `(235,75)` | 0 |

The degree-5 and degree-13 outside trace points do not match any of the
34 archived degree-13 source traces under the frozen exact-multiset
cancellation rule. They remain recorded in [result.json](result.json),
including their class parts and verified Hecke group sums. All 3, 6 and
14 finite neighbors also passed their respective modular-polynomial checks.

## Protocol and verification

The [protocol](protocol.json) fixes the point, degrees 2/5/13, corrected
class identity, source and cache digests, extension cap, cancellation
rule, rank fields and resource cap. A checked Sage job evaluates the
regularized degree-2/5 q-expansion functions and a content-addressed
degree-13 function artifact at the source. [pre-run.json](pre-run.json)
pins the resulting [moments](moments.json) and archived outside equations
before neighbor reconstruction.

The [producer](run_sage.py) builds the neighbor-x polynomials from Newton
identities, factors them, reconstructs all points from mixed moments in
`F317`, `F317^4` or `F317^12`, checks curve equations and Hecke sums,
verifies modular-polynomial roots, and records Frobenius orbit traces.
It inserts a class row only after exact group verification. The
[independent audit](audit_sage.py) freshly rebuilds all degree-2/5/13
functions from the pinned regularized source, recomputes moments,
factors and orbits, and compares the complete row. Its [receipt](audit.json)
reports `PASS`; the checked [Sage runtime](runtime-info.json) precedes
both jobs.

The [Lean rank certificate](formal/RestoredHeckeRankP317.lean) checks all
104 row-dot products against a nonzero F61 projection vector, a 39×39
inverse modulo 61, and a 40×40 inverse modulo 3. Its build and axiom
output are retained; the [proof map](formal/PROOF_MAP.md) states the rank
implications and remaining curve-to-formal-list bridge.

Reproduce from this worktree with the archived source and function artifact
available at `/Volumes/SSD990/cryptanalysis`:

```sh
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-x011-p317-restored-source-20261119/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p317-restored-source-20261119/extract_moments_sage.py
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p317-restored-source-20261119/run_sage.py
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p317-restored-source-20261119/audit_sage.py
python3 experiments/hecke-x011-p317-restored-source-20261119/formal/generate.py
cd experiments/hecke-x011-p317-restored-source-20261119/formal
lake build RestoredHeckeRankP317
```

The producer's 0.377-second interval starts after Sage import and after
function moments are ready. It is a stage diagnostic on this host. The
experiment measures exact relation rank on one finite fiber; it does not
estimate single-target online IC or matched rho time. A next test should
compare degree-2 closed-row generation cost and rank gain across fresh,
preselected complete fibers under the same source and resource contract.

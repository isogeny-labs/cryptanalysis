# Half-fixed twelve-leaf ECC2K-130 formula

Fixing the six even-position adjacent-image branches to the original
source yields an exact official-point XCNF with **379,964 variables,
346,253 clauses, and 279,260 native XOR rows**. The
[formula](official_q_d13_halfbranch_m12_v1.xcnf) is 15,820,842 bytes,
about 2.09 MB smaller than the full-union m12 formula. The
[formula receipt](formula_receipt.json) and [frozen protocol](protocol.json)
bind the source, branch pattern, field/curve inputs, official point,
and exact source hashes.

The [class screen](class_result.json) convolves the independently
enumerated four-torsion classes across six original-source and six
union-source positions. It gives about **2.399 billion** ordered raw
representations per cofactor endpoint under an assumed uniform
distribution within the subgroup coset. The class counts are exact;
the mean is a model of target occupancy, not measured relation yield.

A [complete planted XCNF assignment](planted_result.json) satisfies
348,513 clauses after pins and all 279,260 native XOR rows. An
[independent checked-Sage replay](sage_result.json) verifies all
twelve selected curve points, ten partial sums, and four target-fiber
endpoints. The [read-only verifier](verify.py) checks the formula,
class-count and control custody.

The full-union m12 encoding had 414,775 variables, 378,221 clauses,
and 302,885 XOR rows. This restriction reduces those counts by roughly
8%, 8%, and 8%, respectively, while retaining a much larger modeled
ordinary-target multiplicity than the earlier m10 union. The next gate
is an unpinned, one-worker, 4-GiB, 615-second ordinary query against
the same frozen public point. Any SAT assignment must pass independent
curve-group and projected-subgroup replay before relation use.

Run `python3 verify.py` here to repeat the custody check.

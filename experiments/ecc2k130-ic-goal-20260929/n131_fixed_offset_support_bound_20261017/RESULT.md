# Exact N131 source-capacity gate for the fixed-offset root index

**The 33,191-code fixed-offset W18 source is too narrow for a four-slot
ordinary-relation search.** This is the source behind the
[prior indexed two-block join](../n41_indexed_two_block_20261017/RESULT.md).
An independent scan of its canonical binary
table found 33,191 valid codes and the receipt records exactly two raw
pair-output x roots per code. Allowing both curve-point signs gives at
most **132,764 point states per slot**. Four slots therefore supply at
most 310,685,735,921,621,852,416 labeled group-sum assignments.
Against the recorded N131 subgroup order
680,564,733,841,876,926,932,320,129,493,409,985,129, the fraction
of uniformly sampled subgroup targets covered is at most
**4.56511659321 × 10⁻¹⁹**. Column restrictions and duplicate sums
can only reduce this ceiling.

| Fixed-offset slots | Labeled-assignment ceiling divided by subgroup order |
| ---: | ---: |
| 4 | 4.56511659321 × 10⁻¹⁹ |
| 5 | 6.06083139381 × 10⁻¹⁴ |
| 6 | 8.04660219168 × 10⁻⁹ |
| 7 | 0.00106829909338 |
| 8 | 141.831660833 |

Eight is the first arity whose *ceiling* exceeds one; this does not
establish actual yield or an eight-slot solver. The ceiling is a
probability bound for a uniform target under a fixed source policy,
not a proof about the particular frozen public point. The full
all-seed W18 source has 34,482,792,912 signed pair states per rotation,
about 259,730 times the restricted per-slot upper count. Its earlier
four-slot labeled mean ceiling is 2,077.496. Consequently the
memory-efficient streaming version of the **restricted** four-slot
index would still have insufficient target coverage under this input
law. The next search should retain the exact target quadratic but
represent the full all-seed pair family implicitly, or change arity
with a complete source and solver cost model.

The [protocol](protocol.json) pins the binary table, table receipt,
curve record, all-seed report, and count script. The [result](result.json)
keeps exact integer fractions and the independent 131,072-code scan.
The checked [Lean theorem](SupportBound.lean) counts all labeled
tuples of an arbitrary finite list and proves the seven-slot and
eight-slot arithmetic thresholds. Its [`#print axioms` output](lean.stdout)
uses only `propext` for the tuple theorem and no axioms for the
arithmetic thresholds. The bridge from pair-output x roots to at most
two signed curve points per root is the usual nonexceptional
Weierstrass-coordinate fact; it is not formalized in this module.
The [verifier](verify.py) checks hashes, counts, thresholds, and proof
transcript. This is a source-capacity gate with `candidate_id: null`.

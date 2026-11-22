# Half-fixed m12 ordinary query on ECC2K-130

The branch-restricted adjacent-union source reduced the official-point
XCNF to **379,964 variables, 346,253 clauses, and 279,260 native XOR
rows**, while retaining about **2.399 billion** ordered raw
representations per cofactor endpoint under the declared uniform
subgroup-occupancy model. Its one-worker CCNR
[ordinary query](query_result.json) ended `BOUNDED_UNKNOWN` at the
**615.065-second parent wall cap**, with **91 local-search rounds** and
**781,189,120 bytes** sampled peak combined RSS under the 4-GiB cap.
The [custody verifier](verify.py) passed. Other solver work was live on
this ordinary host; the wall time is a bounded query diagnostic.

The [frozen protocol](query_protocol.json) binds the exact challenge
point, branch pattern `(0,2,4,6,8,10)` fixed to the original source,
formula and control hashes, checked Sage runtime, solver binary, flags,
and limits. The [formula and controls](../n131_d13_union_m12_halfbranch_20261115/RESULT.md)
include a complete planted assignment and independent Sage replay of
twelve leaves, ten partial sums, and four cofactor endpoints.

The exact four-class tuple counts have a checked
[Lean theorem and proof map](PROOF_MAP.md). `#print axioms` reports no
axioms for either declaration. An independent
[four-character audit](class_closed_form_result.json) obtains the same
counts without repeating the convolution recurrence. The theorem uses
the audited one-position class vectors as inputs; uniform occupancy
within each subgroup coset remains a labeled model.

The [SAT replay script](replay_sat.py) is prepared to verify a future
model against every XCNF row, the twelve Sage points and partial sums,
the selected cofactor lift, and the projected subgroup relation to the
public point. This bounded run produced no model for that replay.
The method remains a design proposal with `candidate_id: null` while
ordinary decomposition, useful rank, factor logs, scalar recovery, and
the matched one-target rho comparison remain open.

The next method screen should make target-dependent information reject
or recover multiple source-code families in one operation on a frozen
smaller-field ordinary relation, with exact source validity and a
credible N131 time/memory projection. The 8% circuit reduction alone
has not cleared the N131 ordinary-relation gate.

Run `python3 verify.py` here for the read-only query custody check.

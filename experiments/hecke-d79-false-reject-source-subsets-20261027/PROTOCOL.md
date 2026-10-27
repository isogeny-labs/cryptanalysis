# Retained-source rank certificates for the p103357 false reject

Freeze the gate, challenge, and audit files by SHA-256 in `inputs.json`. Use only the selected p103357 class and its 40 retained source entries. Recompute all signed outside-trace cancellations with distinct support of size at most four by an independent pair index; verify every resulting class row on the recorded curve. Form the baseline from the retained degree-2/5 and direct rows and calculate ranks over F_197.

For each ascending source prefix of size 0 through 40, retain only rows whose source support lies inside that prefix. Report the first prefix reaching rank 39 and the full rank sequence. Starting with all 40 sources, remove sources in descending index order whenever rank 39 remains; repeat passes until one pass removes none. Report the resulting inclusion-minimal certificate, its rank, relation count, and source-lift time sum from the original trace. This deletion result is order-dependent and is not a minimum-cardinality proof. Rebuild all rows from the frozen trace before checking the final certificate.

This is a retrospective scheduling diagnostic on a class already identified as a false reject. The source-lift sum is an observed component cost; it is not a prospective policy time. Keep `candidate_id` and `target_online_ms` null.

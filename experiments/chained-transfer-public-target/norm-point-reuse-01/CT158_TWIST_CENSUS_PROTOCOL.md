# CT158 — nu=12 twist census follow-up protocol

2026-11-16. [pcc:unverified].

**Retrospective discovery disclosure:** the first developer-local exploratory
C++ census was executed *before* this protocol was written. Its point-count
result must not be described as prospective, blinded or benchmark evidence.

Follow-up acceptance: compile exact source with C++17 -O3 -Wall -Wextra
-Werror; enumerate all 223³ elements as y squares and x arguments on both
the CT152 translated original E0short and its explicit v=12 quadratic twist;
require exact 11,092,292 / 11,086,844 orders, complementary nonzero-square
counts, and #E + #E_twist = 2*(223³+1). Change only the twist B[0] constant
and require an independently recalculated violation. Independently derive
coefficients, nonsquare witness, trace gaps and 128 shift/twist identities in
Python under normal and optimized (-O), including three model mutations.
Record raw integer JSON and byte hashes, not estimated costs.

**Source binding:** TwistedPair::construct() twists old.source(), not E0
literally. Establish a K-defined isogeny E0 -> old.source() separately before
transferring this count to fixed nu12. Do not infer a completed Jacobian map,
source prime-field ECDLP, signed PCC, full 695/701 parity or measured advantage.

Keep source fixtures, PCC ledger, native pricing approvals and protected
root branches untouched; re-use existing CT125/CT142 owner lanes.

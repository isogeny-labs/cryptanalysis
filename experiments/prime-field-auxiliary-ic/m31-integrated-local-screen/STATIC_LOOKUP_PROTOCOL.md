# Static x lookup development screen

Question: can a static, exact open-addressed x table reduce the integrated
M31 signed-pair solve cost relative to the existing integer-key HashMap?
This is a representation change; the arithmetic and search are unchanged.

Use the frozen public target Q=(988441464,1643383878), interval B384 and B768,
m2, 64 lanes, seeds 0,1,2, 4M-query and 5s online limits. Build control and
candidate binaries before timing. Run each arm in a fresh process, rotate arm
order, and charge wall and parent-plus-child CPU through process exit and JSON
parsing. Require identical basis points, certificate, scalar, work counts and
pair counts within each seed/size; verify [scalar]G=Q independently. Preserve
failures and incomplete arms. Report index construction, online and full cold
time; the development target is not a fresh-target confirmation.

The candidate passes this screen only if it is correct on all six matched
cells and improves median paired charged CPU at both B values. A subsequent
fresh-target protocol must be committed before drawing new public targets.

Source checked: the repository's signed pair index and the rootfinding
decomposition paper (`papers/rootfinding-decomposition/rootfinding_decomposition.tex`,
KB source `source:17a1b67993e4b781bbf1198fd2598c2f`). The paper establishes
exact pair lookup and witness replay, not this table's runtime. KB revision
`0ebe094eb6054cb8ae9da01c6a8f25c4` was refreshed 2026-11-25; newer
local work was checked directly in the checkout.

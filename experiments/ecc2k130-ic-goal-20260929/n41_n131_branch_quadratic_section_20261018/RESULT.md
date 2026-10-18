# Branch-invariant quadratic-section certificates

**Contribution.** A checked output parity is invariant under both roots
of every sampled source quadratic, yet has Boolean algebraic degree at
least three on a frozen source-code subset. This excludes **every**
code-dependent branch assignment from a degree-at-most-two Boolean
source-root map on the audited N41 and N131 domains. The N131 certificate
uses a 12-bit-weight parity mask, annihilates all 512 sampled root
differences, and has a 192-code feature dependency with odd root parity.

The input domains are the 71 valid aligned W9 source codes over
`GF(2^41)` on `EC1N41Ckb1h7d5e80d3c4d0` and 512 valid sampled aligned
W29 source codes over `GF(2^131)` on `EC1N131Ckb1heb5f1998f20b`.
The N131 constructed-control codes are excluded. Code bits are 8 and
28 respectively. The source root records and their original Sage
runtime are hash-pinned in [protocol.json](protocol.json). The first
arithmetic [audit](result.json) eliminated the quadratic feature
dependencies against arbitrary branch bits as a binary linear system.
Both domains yielded a contradiction, after 8 and 32 scalar bit
equations respectively.

The separate [certificate protocol](certificate_protocol.json) freezes
the extractor and root records. Its [output](certificate_result.json)
provides an explicit index subset and field-output mask. The independent
[verifier](verify.py) recomputes the feature XOR, all branch-difference
parities, and the root XOR directly from the pinned roots, without
rerunning either elimination.

| Domain | Codes | Quadratic features | Dependency size | Output mask | Mask weight | Checked root parity |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| N41 W9 | 71 | 37 | 14 | `0x7c04000000` | 6 | 1 |
| N131 W29 sample | 512 | 407 | 192 | `0x6925a3800000000000000000000000000` | 12 | 1 |

The mask annihilates the difference between the two source roots for
every code in each declared domain. The feature XOR of the listed
dependency codes is zero, while the masked root parity XOR is one.
The written implication and kernel-checked structural theorem are in
the [proof map](PROOF_MAP.md). The concrete bit-vector certificates are
verified by exact integer arithmetic; the source-specific Lean bridge
is recorded as open there.

This result rules out quadratic Boolean interpolation as the next
source-root circuit for these domains. A higher-degree branch-adaptive
map remains a concrete experiment, but it must beat the already frozen
two-quadratic N41 solver gate before promotion to the 600-second N131
public-point relation search. `candidate_id` remains `null` because this
is a source-root diagnostic, not a complete IC pipeline.

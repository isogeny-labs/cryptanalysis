# Proof map

The algebraic operation is the same source norm as in the
[N41 proof map](../n41_w11_global_code_norm_20261018/PROOF_MAP.md).
The checked declaration `JointNorm.product_zero_iff` in the existing
`n41_joint_fourpair_resultant_20261012/JointNorm.lean` proves the
finite-product zero criterion under the field's no-zero-divisor law.
The written polynomial argument identifies the root set of the GCD of
the target norm and the source vanisher with valid two-code resultant
zeros. Formalization of Sage's concrete polynomial-GCD call and the
actual W20 product map remains open.

The exact N131 source, target coefficients, and field representation
are frozen in [protocol_256.json](protocol_256.json),
[protocol_1024.json](protocol_1024.json), and [protocol.json](protocol.json).
An independent C++ field implementation exhaustively evaluates the
resultant on every pair of the 256- and 1,024-code subsets and agrees
with their norm/GCD root sets. At 4,096 codes, the known positive pair
has the independent curve replay in
`n131_w33_resultant_core_20261018/replay_result.json`; the remaining
4,096-code pairs were not independently exhaustively replayed here.

# Proof map

The native NTL kernel computes the same exact global valid-code norm
specified in the [N41 proof map](../n41_w11_global_code_norm_20261018/PROOF_MAP.md).
The checked prior declaration `JointNorm.product_zero_iff` proves the
finite-product zero criterion under field multiplication assumptions.
The polynomial-GCD/root-set argument is written in that proof map.

The concrete GF(2^131) representation, NTL conversion, product construction,
and target coefficients are computational bridges. The 256- and 4,096-code
native results match the independent Sage norm; the 4,096-code positive and
public rows also match an exhaustive native evaluator using a separate field
kernel. The full-source dense run is capped before a target row, so there is
no full-source norm root set to formalize or audit.

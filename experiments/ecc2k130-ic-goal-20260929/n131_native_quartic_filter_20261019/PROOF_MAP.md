# Proof map: native quartic/subspace gate

| Result | Lean declaration or replay | Exact hypotheses and status |
| --- | --- | --- |
| `a ↦ a²+sa` is additive | `SourceProductLinear.source_product_additive` in [SourceProductLinear.lean](SourceProductLinear.lean) | Any commutative ring with `1+1=0`, any seed and inputs; kernel-checked under Lean 4.34.1. |
| Repeated squaring preserves addition | `SourceProductLinear.frobIter_additive` | Same characteristic-two ring, any nonnegative iteration count; kernel-checked. This supplies the structural basis for the rotated product code and prefix-XOR update. |
| Prefix/suffix inverse factorization supplies a one-factor inverse | `SourceProductLinear.batch_inverse_sound` | Any commutative ring; assumes `(pref*a)*suff=1` and concludes `a*(pref*suff)=1`. Kernel-checked. The native code also checks `a*inverse=1` for each specialization. |
| Right-subspace membership is equivalent to a zero determinant | Written proof below; 258 checked-Sage GCD decisions matched by each native build; 100 planted roots preserved | The exact `GF(2^131)` modulus, 28 independent rotated basis products, specialized quartic, and faithful field operations. The concrete matrix and curve bridge is computationally checked, not yet a Lean theorem. |

## Readable proof

In characteristic two, `(a+b)²=a²+b²`, so `(a+b)²+s(a+b)=(a²+sa)+(b²+sb)`. Repeated squaring is additive by induction. Thus the source-product map and its Frobenius rotation take a Boolean code to the XOR of its basis images; toggling consecutive binary-code bits updates the product by the corresponding basis-prefix XOR.

Let `H` be a nonzero specialized quartic, normalized to monic form, and let `R=L_V mod H`. Multiplication by `R` on the quotient algebra `K[Z]/(H)` is a linear endomorphism. Its determinant vanishes exactly when this multiplication has a nonzero kernel, equivalently when `R` is not a unit in the quotient, equivalently when `gcd(H,R)` has positive degree. Since `L_V` is the product of distinct linear factors over the 28-dimensional right-product subspace, this is equivalent to `H(q)=0` for some permitted right product `q`. If `H` is a nonzero constant, the gate rejects; if `H=0`, it retains. A retained algebraic root still requires exact source-point and group checks.

For a block of nonzero leading coefficients `a_i`, let `P_i=∏_{j<i} a_j` and `T=∏_j a_j`. At reverse position `i`, the accumulator is `U_i=T⁻¹∏_{j>i}a_j`. Since `T=P_i a_i∏_{j>i}a_j`, the product `P_i U_i` is the inverse of `a_i`; the code verifies `a_i(P_i U_i)=1`. Zero leading coefficients are omitted from the batch and handled by the lower-degree path. The checked Lean `batch_inverse_sound` theorem proves the underlying commutative-ring implication for one factor; the finite batch indexing and exact field implementation are audited by the native controls.

## Verification boundary

`lean SourceProductLinear.lean` passes with pinned `leanprover/lean4:v4.34.1`; [lean_check.json](lean_check.json) records source/output hashes and `#print axioms` for all three theorems. Only `propext`, `Classical.choice`, and `Quot.sound` are reported. `lean4checker --fresh` is unavailable on this host. A full Lean development would define the exact field, quotient algebra, 4-by-4 multiplication matrix, determinant, and the 13-term curve eliminant, then prove the concrete matrix/GCD/curve bridge. The checked-Sage [reference](reference_result.json), pinned field kernel, native [unit controls](unit_frozen.stdout), and [terminal verifier](verify.py) currently establish the finite-instance implementation boundary.

# Norm-point reuse: proof and program boundary

The compiled-source checkpoint36f906 and exact local theorem bindings bb43e2,
ff6c64 and a97a91 are unsigned. Both original proof gates check the three
roots under Lean4.34.1 and4.35.0, using only propext, Classical.choice and
Quot.sound; zero trusted native evaluation. [pcc:unverified]

| Result | Declaration | Explicit hypotheses |
| --- | --- | --- |
| A corrected half still doubles to the source norm | NormPointReuse.corrected_lift_doubles | 2p=q and 2t=0 in an IntModule |
| Final-point doubling equals the old transported norm | NormPointReuse.corrected_norm_reuse | Target norm/Phi dual identity; elliptic map preserves doubling; actual half and two-torsion correction |
| Two factored elliptic maps give the same reused norm | NormPointReuse.factored_norm_reuse | The same target dual identity; both maps preserve doubling; actual half and correction |

The written argument is short. If2p=q and2t=0, then2(p+t)=q. For the
homomorphism gamma,2gamma(p+t)=gamma(q). The target HLP identity gives
N(Phi(gamma(p+t)))=2gamma(p+t), so the retained final elliptic point supplies
the same norm as evaluating gamma on q. Apply the same argument to a
composition of two maps. Neither desired transported-norm equality nor
norm equality for an arbitrary encoded packet is assumed. [pcc:unverified]

The proof remains conditional on the earlier actual variety/field/HLP norm,
Frobenius, correction-kernel and encoded-program bridges. Native acceptance
must separately check descent of doubled coordinates to the original cubic
field, equality with the actual prime-field Jacobian norm, all independent
old elliptic checks, full cofactor inverses and the entire frozen population.
Compilation and the conditional theorem do not establish that native result.
[pcc:unverified]

The existing graph sources were checked against the proposed change: this
optimization changes how the in-memory norm is obtained, not the vertices,
edge directions, norm scalars or geometric degrees. The complete-chain report
and its transfer diagram remain current for those geometric data. A result
report must record the actual whole-population outcome and selected vectors
before interpreting this candidate. Complete primitive setup/reuse cost,
known initial elliptic lifts, calibrated reference comparisons and original
full cold120 acceptance remain separate open obligations. [pcc:unverified]

# Conditional proof map for original-prime reprojection

Proof data6d8c42 records both original Lean4.34.1/4.35.0 gates passing seven
roots with zero trusted native evaluation, and all seven exact local statement
bindings. The only recorded standard foundations are propext, Classical.choice
and Quot.sound. All standing is unsigned. [pcc:unverified]

| Claim | Declaration | Scope |
| --- | --- | --- |
| c5ec84 | PrimeReprojection.inverse_two | Bezout witness and actual ell annihilation normalize doubling |
| fc42be | PrimeReprojection.normalized_norm_pair | Both HLP identities and Phi linearity derive normalized norm/Phi inverses |
| dfa181 | PrimeReprojection.reprojection_dual_norm | Both desired transfer norms derive from individual HLP/elliptic dual norms; no matching-kernel or desired-transfer-norm hypothesis |
| 5da496 | PrimeReprojection.reprojection_chain | The middle HLP identity cancels one normalization in an adjacent chain |
| cbd44d | PrimeReprojection.known_initial_point | Public elliptic P avoids norm/inverse-two and has the exact same output |
| 1c4eb7 | PrimeReprojection.transfer_integer_linear | Integer linearity gives the DLP relation |
| 287578 | PrimeReprojection.actual_original_witnesses | Exact old inverse-two, coprimality and selected positive-square witnesses |

The written argument is to normalize Ni by inverse-two on the actual prime
subgroup. Ni Phi_i=2 and Phi_i Ni=2 then make Phi_i and normalized Ni inverse.
Conjugating the original elliptic gamma and signed dual by these inverses gives
both norm-n identities. The existing FullGroupNorm.inverse_on_full_annihilator
lemma applies with annihilator ell and an actual inverse-n witness to recover
X. Integer linearity preserves Q=[k]P, and recovery gives injectivity. The
middle inverse pair cancels in a chain; for an initially known elliptic point,
normalization cancels before gamma. [pcc:unverified]

The formal types must be the stated ell-torsion carriers. These conditional
abstract lemmas do not define the actual HLP varieties/polarizations, fields,
Frobenius, Jacobian order, norms, finite-field descent or encoded Picard program.
Those exact bridges remain explicit. Finite tests must independently check the
selected supported sources, norms, prime admission, all original controls and
all whole native records. No cofactor inversion, full-group geometric norm,
endpoint isomorphism or cost conclusion follows from the formal algebra.
[pcc:unverified]

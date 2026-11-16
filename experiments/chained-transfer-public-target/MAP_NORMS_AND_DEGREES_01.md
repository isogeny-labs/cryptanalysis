# Elliptic degrees, Jacobian norms and geometric degrees

The implemented edge labels13 and169 are the degrees of the elliptic maps
and the scalars in the corresponding Jacobian dual norms. They are not the
geometric degrees of the genus3 Jacobian maps. [pcc:unverified]

Under the explicit HLP quotient and descent bridges, let phi_i and phi_j
be the polarized quotient isogenies of degree8. A degree-n elliptic map
gamma over the cubic field induces a degree-n³ map of Weil restrictions.
The descended map beta satisfies beta ◦ phi_i = phi_j ◦ Res(gamma).
Multiplicativity of finite isogeny degrees gives

    deg(beta) · 8 = 8 · n³,

hence deg(beta)=n³. Equivalently, the polarization identity
beta_hat ◦ beta=[n] on a principally polarized abelian threefold has the
expected degree n³. These are classical conditional geometric degree
arguments, not encoded-variety or program proofs. The primary HLP
degree8/polarization construction and field qualification remain the cited
bridges. [pcc:unverified]

For the two adjacent edges n=13; for the direct elliptic composite n=169.
The native runtime's `degree(from,to)` returns this norm scalar/elliptic
degree. No degree28561 multiplication-polynomial expansion or Jacobian
geometric degree169 is asserted. Native ed33ef checks the full13/169 norm
and inverse identities on the frozen finite population; its broader
geometric and program bridges remain explicit. [pcc:unverified]

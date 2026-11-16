#set page(paper:"a4",margin:15mm)
#set text(font:"DejaVu Sans",size:9.2pt)
#set par(leading:.4em)
#let vec = json("render-inputs.json").representative
#text(size:15.5pt,weight:"bold")[Original-prime Jacobian reprojection: full finite result]
#v(4pt)
#text(fill:rgb("#295477"),weight:"bold")[ACTUAL NATIVE02 · claim 976f50 · source 2a1a8e5 · unsigned]

The original prime subgroup now passes the frozen three-model reprojection experiment. One unfiltered native test completes all 1,077 ordered records; the whole-record auditor accepts the entire output and rejects four deliberate whole-class omissions. This continues the original ell = 2,773,073 instance without transporting its logarithm to a twist.

== The actual models and maps
#table(columns:(1fr,.22fr,1fr,.22fr,1fr),inset:7pt,stroke:.5pt+rgb("#aebdcb"),fill:rgb("#eef4f7"),
 [*Original E2 / J2*\ case (0,0), D100],[↔],[*Original E3 / J3*\ case (0,1), D39],[↔],[*Original E4 / J4*\ case (1,0), D38],
 [root10; P0(1:0:38)],[13],[root40; P0(1:0:90)],[13],[root22; P0(1:2:95)],
)

The Jacobian models are over F223; the original elliptic curves use F223[z]/(z³−3), full order 11,092,292. The lexicographically first eligible cases were fixed in protocol38b827, published at bd603d0 before implementation. All18 original model rows remain present and exact. The old fixed-kernel D12/D24/D67 failures remain unchanged.

#block(fill:rgb("#eef4f7"),inset:9pt)[*Opaque prime Jacobian input X*\
X → actual norm N_i(X) → multiply by a = 1,386,537 → gamma_ij → Phi_j\
b_ij(X) = Phi_j(gamma_ij(a N_i(X))), with 2a = 1 modulo ell.]

Under the explicit HLP identities N_i Phi_i = [2] and Phi_i N_i = [2], linearity and ell-annihilation, the signed reverse map has composite [13], or [169] for the two-edge endpoint map. The intermediate norm/Phi factors and inverse-two scalars cancel on the prime group. A retained normalized elliptic lift reduces a chain to one initial norm/inverse-two and one final Phi. Actual target norm and subgroup checks remain in the program.

== Complete frozen acceptance
#table(columns:(1.65fr,1fr),inset:6pt,stroke:.5pt+rgb("#bbc4cf"),
 [*Requirement*],[*Actual outcome*],
 [Models / complete old rows / line origins],[3 /18 /224 per model],
 [Exceptional descriptors, explicitly projected by [4]],[672, both outgoing maps: 1,344 evaluations],
 [Public points / outgoing evaluations],[384 /768, independent elliptic checks],
 [Cofactor attempts / sectors],[228 per domain /all4; nonzero sectors rejected],
 [Addition pairs / original public transfers],[64 per undirected pair /15],
 [Matched scalar vectors / routes],[12 /5, whole outputs equal],
 [Whole records / actual omission controls],[1,077 /4 reject101, no accepted output],
 [Unfiltered test / worker / supervisor],[0 /0 /0; all13 phases expected],
)

All 1,131 frozen input hashes and actual compiler/runtime test and auditor bytes remain exact. The native attempt used the published compiled03 source, exact original checkpoint15 and immediate original gate0, with the unchanged 900-second /2-GiB test limits. Its correctness footer is not used as a benchmark.

#pagebreak()
#text(size:15.5pt,weight:"bold")[A stronger presentation and the next full-group question]
#v(4pt)
#text(fill:rgb("#966932"),weight:"bold")[SELECTED SOURCE CALLS · conditional algebra · complete primitive prices open]

For a known initial elliptic point P, b_ij(Phi_i(P)) = Phi_j(gamma_ij(P)). The runtime does not need to recover that presentation by norm and inverse-two. This route is included in the actual comparison, alongside opaque-input direct expansion, a literal two-Jacobian chain and the retained normalized lift.

#block(fill:rgb("#eef4f7"),inset:9pt)[*Known initial elliptic point*\
P → direct169 or factored13+13 → final Phi\
All five whole canonical endpoint outputs agree for each of the12 frozen vectors.]

The following entries are read directly from the actual domain0→2, scalar1 vector. They count selected source calls, not primitive field operations or equal-priced work.

#table(columns:(1.65fr,.6fr,.6fr,.6fr,.6fr,.6fr,.6fr),inset:5pt,stroke:.5pt+rgb("#bbc4cf"),
 [*Route*],[*Initial norm*],[*Inv2*],[*Target Phi*],[*13*],[*169*],[*Norm doubles*],
 [Opaque direct],[#str(vec.direct.external_norm_and_geometry)],[#str(vec.direct.elliptic_inverse_two)],[#str(vec.direct.target_prime_phi)],[#str(vec.direct.degree13_evaluation)],[#str(vec.direct.degree169_evaluation)],[#str(vec.direct.norm_point_doubling)],
 [Literal Jacobian chain],[#str(vec.literal_jacobian_chain.external_norm_and_geometry)],[#str(vec.literal_jacobian_chain.elliptic_inverse_two)],[#str(vec.literal_jacobian_chain.target_prime_phi)],[#str(vec.literal_jacobian_chain.degree13_evaluation)],[#str(vec.literal_jacobian_chain.degree169_evaluation)],[#str(vec.literal_jacobian_chain.norm_point_doubling)],
 [Retained prime lift],[#str(vec.retained_normalized_prime_lift.external_norm_and_geometry)],[#str(vec.retained_normalized_prime_lift.elliptic_inverse_two)],[#str(vec.retained_normalized_prime_lift.target_prime_phi)],[#str(vec.retained_normalized_prime_lift.degree13_evaluation)],[#str(vec.retained_normalized_prime_lift.degree169_evaluation)],[#str(vec.retained_normalized_prime_lift.norm_point_doubling)],
 [Known point, direct],[#str(vec.known_point_direct.external_norm_and_geometry)],[#str(vec.known_point_direct.elliptic_inverse_two)],[#str(vec.known_point_direct.target_prime_phi)],[#str(vec.known_point_direct.degree13_evaluation)],[#str(vec.known_point_direct.degree169_evaluation)],[#str(vec.known_point_direct.norm_point_doubling)],
 [Known point, factored],[#str(vec.known_point_factored.external_norm_and_geometry)],[#str(vec.known_point_factored.elliptic_inverse_two)],[#str(vec.known_point_factored.target_prime_phi)],[#str(vec.known_point_factored.degree13_evaluation)],[#str(vec.known_point_factored.degree169_evaluation)],[#str(vec.known_point_factored.norm_point_doubling)],
)

External admission, final actual norm and prime checks are preserved in the full literal vectors. The correctness constructor also retains older preflight checks; its setup is not claimed minimal. Complete setup/online primitive accounting and calibrated matched references remain necessary for a cost comparison.

== Proof boundary and preserved failure
Both original Lean4.34.1/4.35.0 gates pass all seven PrimeReprojection roots with zero trusted assumptions; all seven local statement bindings pass in6d8c42. The proofs derive inverse-two normalization, reverse norms, chain collapse, the known-point identity and scalar transfer from explicit hypotheses. Actual field, HLP, variety, Picard, Frobenius and encoded-program bridges remain conditional.

Native01 e62fb2 failed101 after eight records because a cubic diagnostic formatter received actual degree6 line-origin coordinates. Compiled03 a3c6eb changes only that formatter, preserving all six coefficients and checking higher slots vanish. No runtime arithmetic, model, kernel, sample, acceptance criterion or bound changed. Both failed and successful whole runs, sources, actual executables and full prepared libraries remain retained.

== Next discriminating experiment
A separate full-group census will ask whether any of the six original models at each endpoint have compatible transported two-torsion kernels. Its prospective scope is18 vertices,36 pairs on each adjacent edge and216 triples, with every reason retained. The current prime-only choices and fixed-kernel negatives stay frozen. No outcome is calculated or inferred here; the census receives its own protocol before implementation.

#text(size:8pt)[Sources: native976f50; prospective38b827; compiled03a3c6eb; conditional proof6d8c42; original checkpoint43684688854/job132722574569/artifact14149624251, all28 matching members; HLP math/9809210v1 section4.1, Lemma13/Propositions14–15 and field qualification. KB is unavailable and the autoresearcher vault remains locked. Result scope: unsigned finite prime-group reprojection, with explicit [4] projection and cofactor rejection; no full-group geometric-degree or calibrated performance conclusion.]

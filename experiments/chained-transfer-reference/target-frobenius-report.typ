#set page(paper:"a4",margin:17mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= Nonisomorphic Jacobians,forced Richelot backtracks
2026-11-11 · Chained ECDLP Transfers · CT16

*Unsigned/unverified standing.* Both accepted17/101 targets have a six-cycle
branch Frobenius,16 versus4 source/target2-torsion over the cubic extension,
and only the previous-dual rational next Richelot kernel. No other-degree
or universal transfer impossibility is asserted. PCC954795/4823b5 bind
the producer-run discovery/regression. [pcc:unverified]

#image("target-frobenius.svg",width:100%)

== Actual branch fields and all geometric two-torsion
The fixed accepted maps have determinants11/63 and raw scales3/22 over
F17/shiftedF101. All three target-bracket discriminants are nonsquare in
Fp³. The existing quadratic adjunction splits them inFp⁶,and all six
distinct roots satisfy the target. Actual Frobenius orbit labeling gives
[1,2,3,4,5,0] in each case. [pcc:unverified]

Each unordered branch pair gives u=(X−ri)(X−rj),v=0,plus=0 in the balanced
model. All15 nonzero classes on each side are valid,distinct and killed by
doubling; with identity they exhaust geometric2-torsion. Source Frobenius³
fixes16,target fixes4. All are Frobenius⁶-fixed. Completed branch fibers
have kernel4/image4,and every256 addition/Frobenius-equivariance check
passes. Both group layers use Cantor; this is unsigned correctness evidence.
[pcc:unverified]

== Stronger isomorphism obstruction
In odd characteristic a genus2 Jacobian has16 geometric2-torsion points,
and each nonzero class uniquely corresponds to one of15 unordered branch
pairs. That standard geometric bridge remains a written primary input.
Source branch action(012)(345) has cube identity. Target action(012345)
has cube(03)(14)(25),fixing just the three opposite pairs. [pcc:unverified]

An Fp-isomorphism of abelian varieties would induce a Frobenius-equivariant
bijection of their2-torsion,then of Frobenius³-fixed subsets. Cardinalities
16≠4 contradict this. Thus these isogenous Jacobians are Fp-nonisomorphic
even without a polarization requirement. This strengthens a curve-model
test; it makes no extension-field nonisomorphism claim. [pcc:unverified]

#pagebreak()
= The rational next hop is forced to be the dual

A rational Richelot kernel corresponds to a Frobenius-stable perfect
matching on six branches. All15 matchings are enumerated. A six-cycle has
only the opposite matching(03),(14),(25). The actual target H factors give
precisely that matching,so it is the previous dual. Reversing the accepted
hop composes to[2],without supplying another destination. [pcc:unverified]

Combinatorially,any nonopposite edge has six distinct translates under the
cycle,too many for a matching of three edges. An opposite edge has exactly
three translates,which form the unique stable matching. Consequently neither
accepted target admits a rational nonbacktracking next Richelot hop. Other
degrees,products,extension kernels and starting covers remain open.
[pcc:unverified]

== Formal scope
Seven core Lean lemmas in crypto TargetFrobenius.lean pass gate7,PCC8c5ee5:
source cube identity,15 versus3 nonzero fixed branch pairs,unique stable
target matching,moved target pair,generic cube intertwining and conditional
commuting-map/right-inverse obstruction. No new axioms. The finite-field,
Jacobian and branch-pair geometry is not formalized. [pcc:unverified]

Written primary inputs: Galbraith corrected ch.10 and Kunzweiler
DCC92(2024),§§3.1–3.2 for branch pairs,maximal isotropic kernels and duals.
Source review remains upstream; KB/ecdb unavailable,no novelty claim.

== Exact evidence and reproduction
Source767c945a0 passes exact-head focused43022364261:native25/reference46,
one old benchmark ignored,formatting,strict Clippy and source guards,
PCC46a880. That immutable run precedes the new CT16 source. Current CT16
targeted discovery/regression and Clippy pass; full47-test CI is pending.
[pcc:unverified]

Receipts: target-frobenius-proposal-01,target-frobenius-01/02,
target-frobenius-clippy-01 and shifted109-focused-ci-01. Discovery and
frozen regression are retained separately. Reproduce with Rust1.99.1:
`cargo test --release --manifest-path experiments/chained-transfer-reference/Cargo.toml accepted_targets_frobenius_two_torsion_and_next_kernels -- --nocapture`.
Or run consumer check.sh and crypto proof-gate.sh on TargetFrobenius.lean.
[pcc:unverified]

Full account: TARGET_FROBENIUS.md,src/nonsplit_map.rs. Independent flat
field replays from the previous checkpoint validate bounded field arithmetic,
not independently whole Jacobian maps. Scientific standing stays unsigned.
[pcc:unverified]

== Continuing research
Keep the positive nonisomorphic DLP-preserving transfers and the negative
continuation together. Choose another mathematical route instead of repeating
these closed neighbors. No benchmark,solver advantage,cross-prime descent
or canonical cost edge is established. Construction,transport,solver,recovery
and verification all belong in a future cost comparison. S3/live-budget,
KB/vault and crypto ledger/archive gates remain. [pcc:unverified]

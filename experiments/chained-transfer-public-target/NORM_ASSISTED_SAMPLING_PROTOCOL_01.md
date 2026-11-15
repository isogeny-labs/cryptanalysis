# Exact-class norm-assisted sampling in the three transferred Jacobians

Prospective,2026-11-14,before norm-assisted-ic code. Source39b932dd and
all754 portable common-origin replay inputs remain immutable. This is
bounded native correctness development;performance admission is separate.
No novelty or speed claim is proposed. [pcc:unverified]

## Question and algebra

Can the actual new-target IC solver generate exactly its usual R=[r]G
by doing the scalar multiplication on the existing elliptic source and
then one completed transfer,while leaving relation collection,linear
algebra,descent additions and final independent group check unchanged?
Use q223,K=F223[z]/(z^3-3),ell2773073 and EACH actual HLP(1,0),(1,1),(2,1)
with allfive unchanged public Q. Keep every actual curve,P0 and tag.
[pcc:unverified]

For the implemented Phi=Adapter.transfer_point and N=NormNew.norm,put
u=[1386537]N(G),computed from the public tagged G alone. The genuine
written bridges are Phi N=[2] and scalar equivariance;2*1386537=ell+1.
Thus Phi(u)=G on the ell subgroup and Phi([r]u)=[r]G. Preparation MUST
check canonical field/model tags,nonzero ell-order G,the source curve
and ell membership of u,and the actual equality Phi(u)=G. No Q logarithm,
scalar witness,source DLP solver or lookup table enters preparation or
runtime. This is a change to public group multiplication,not to solving
the DLP or its relation oracle. General geometric bridges stay explicit.
[pcc:unverified]

## Additive implementation and exact controls

Create norm-assisted-ic as an additive crate. Keep a byte-exact snapshot
of new-target-ic/derived/class_solver.rs at39b and a complete literal diff.
Change ONLY the context type and the single R=[r]G expression to call the
prepared sampler. Keep R+G,R+Q,all random draws,relation/large-prime/SGE/
Lanczos/holdout/log-recovery/inner-descent bodies and FINAL ORIGINAL
Picard[k]G=Q verification literal. Never replace final verification with
the sampler under test. [pcc:unverified]

The sampler is bound to one exact canonical G key and actual target
model/P0. Reject zero/nonodd/foreign/noncanonical generators and targets,
changing the prepared generator,foreign model/P0 tags and scalar>=ell.
Do not silently fall back to Picard scalar multiplication or source DLP
if preparation or a complete transfer fails;retain the actual failure.
For a wrong-half control,omit1386537 and check that Phi N(G)=[2]G differs
from G for each nonzero generator. [pcc:unverified]

Use the eleven scalars[0,1,2,3,12,13,26,52,ell/2,ell-2,ell-1] plus64
draws from the original public RNG seed0x71A55157 per actual model.
Retain the full75-scalar list,source points and exact canonical classes;
duplicates stay. For each scalar require samplerR=originalPicard[r]G,
and for allfive public Q require exact R,R+G,R+Q equality. This is225
scalar-pair observations and1125 three-class comparisons,not a full
enumeration or a completeness proof. [pcc:unverified]

Run ALL3targets x5publicQ x4settings[30,36,48,64],seeds[102,103,104,105],
zero-based attempt indices0..3. Compare the original39b new-target IC
and candidate on the SAME parameters and exact G,Q. Retain all60 pairs/
120 reports,including all relation/descent/denominator failures. Require
equal success/failure,fail text,k_found,all non-timing stats except the
existing wall_total,and identical phase order. Require all native
non-wall phase counters equal EXCEPT the descent phase where the R
implementation changes. Raw counters and wall times are all retained.
Every reported success MUST satisfy actual original target Picard
verification and independent original elliptic source verification.
Require at least one common correct setting for each of the15 public
target cases;do not stop at the first success or remove failing arms.
[pcc:unverified]

## Costs and falsification

Record preparation and sampling high-level call vectors separately,
including the norm,source scalar/ell check,completed Phi checks/maps and
input/final verification. Preserve existing native/Picard counters as
diagnostics only. They omit FpR internals and other work;do not call a
smaller existing counter a stage win or price it as S. A failure of
exact class/path/outcome equality rejects the candidate at this scope;
retain all output and diagnose the first actual mismatch. [pcc:unverified]

Before any performance comparison,implement isolated-fork arithmetic
taps across nativeFp/Kf,coverFp/Kf,PicardFp,FpR including coefficient
arithmetic,constructorZp and scalar-field operations. Avoid summing
Picard primitive taps again through the old pc aggregate. Cover complete
cold setup/transport/admission/solver/verification and online reuse,
record remaining unpriced machine/hash/allocation work,then obtain fresh
original S3 checkpoint/livebudget/capacity/isolation and strongest matched
IC/rho/precomputation references under the repository rules.
[pcc:unverified]

## Bounds,evidence and source review

ONE serial unfiltered comprehensive native unit test;900s build,900s
native,2GiB native address-space limit,labeled existing warm outside
cache. All225 scalar pairs/all1125 triples/all60 IC pairs are inside
that whole bound. No paid benchmark or growing-size performance run.
Preserve full inputs/source hashes/literal diff/toolchains/commands/raw
JSON/logs/exits/negative results and checkpoint after every result.
Supply written derivation and feasible faithful conditional Lean proof,
source-linked editable report/PDF and strict independent replay.
[pcc:unverified]

Sources checked: existing NEW_TARGET_IC_DERIVATION_01.md and
ODD_PRODUCT_REFINEMENT_DERIVATION_03.md;actual Adapter/NormNew and original
Picard/scalar implementations. HLP,Large torsion subgroups of split
Jacobians,section4.1,printedpp23-24,explains the degree2 cover product and
both[2] compositions:https://math.mit.edu/~poonen/papers/large.pdf .
Tian,Cover attacks for elliptic curves with prime order,section1 and
section4,distinguishes cover transfer and explicitly costly isogeny
evaluation:https://arxiv.org/pdf/2012.07173 . The EFD short-Weierstrass
formulas and Jacobian-coordinate tables show why actual coordinate and
inversion costs must be matched:https://www.hyperelliptic.org/EFD/g1p/auto-shortw.html
and https://www.hyperelliptic.org/EFD/g1p/auto-shortw-jacobian.html .
The Doche-Icart-Kohel2006 metadata identifies adjacent scalar-isogeny
decomposition work;its full paper was not read and is not used as proof
or a novelty claim. [pcc:unverified]

Sources checked(KB):MCP not loaded;original wrapper status and four
distinct mechanism/negative/application/adjacent queries each exited127
(no executable). Retain exact receipts. Local source/literature fallback
supports this protocol;it establishes no literature absence or novelty.
The crypto-autoresearcher vault remains locked and untouched.
[pcc:unverified]

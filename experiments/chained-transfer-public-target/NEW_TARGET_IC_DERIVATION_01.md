# Class-input IC on the three actual prime-field Jacobians

2026-11-13. Prospective98c6f0 was normally published at2aee9ef5 BEFORE
new solver code. Nativee869bd is an unsigned finite correctness
observation,not a measured computational advantage or a general
completeness proof for index calculus. [pcc:unverified]

## Exact problem and implementation change

Keep the original q223/seed1 source,ell2773073 and all five literal
public targets. The actual degree13 isogeny and fresh HLP models give
three implemented Jacobians J'(1,0),J'(1,1),J'(2,1) over F223. Their full
equations,P0s and model tags are unchanged from source45ee45d2.
FastSourceChain of fb9ee1d6 maps G,Q to H(G),H(Q) with the SAME class
outputs as the prior four-map Chain. Its inverse on the source ell
subgroup is[159985]delta NormPrime. [pcc:unverified]

The original public IC solver is bound to Inst:its particular quartic,
source elliptic arithmetic and transfer_cubics. The additive new solver
takes a checked actual NormNew,typed tagged Jacobian G,Q,ell and ordinary
IC parameters. It admits canonical class packets in the correct field/
model,requires ell-torsion and a nonzero generator,and uses no scalar
witness,DLP lookup table,source-point recovery or elliptic DLP solver.
The byte-exact original solver and complete literal derivative diff
are retained in new-target-ic/original and derived. [pcc:unverified]

Relation collection,large-prime graph construction,matrix assembly,
Lanczos/SGE,holdouts,log recovery and the inner split3/random-add descent
body remain the original implementations. Input plumbing changes the
quartic/context,fixes the actual P0 at fb[0],constructs R=rG,R+G,R+Q as
actual target classes,and verifies the returned k in that Jacobian.
The unused source-specific rho function is omitted from the derivative.
No original engine or original source constructor is modified.
[pcc:unverified]

## Origin anchor and conditional log calculation

The original relation matrix omits the fb[0] column and fixes its log
to zero. It is therefore essential that fb[0] represents the actual
Picard origin P0. The new solver reuses the actual NormNew Picard model
and deterministically swaps P0 into position0 if already sampled,or
replaces the first sampled point otherwise. All remaining factor-base
points remain distinct. It does not reinterpret target class keys in
the original solver's independently selected origin. [pcc:unverified]

Let L:J'(F223)→Fell be a genuine additive homomorphism whose restriction
to the cyclic ell subgroup is nonzero. Suppose the relation-vector
values used by descent extend this L. For the true unknown Q=[k]G,
linearity gives L(Q)=k L(G). Three descents at R,R+G,R+Q may share a
constant offset c:the original descent body subtracts eta. Hence

    y0=L(R)-c, y1=L(R+G)-c, y2=L(R+Q)-c,
    y1-y0=L(G), y2-y0=k L(G).

If d is the inverse of y1-y0,then (y2-y0)d=k. This argument explicitly
cancels the same affine offset. A zero denominator is a retained failure,
never an inverse. The primality of ell and the actual nonzero source
generator are checked by the original constructor. [pcc:unverified]

The extension of a computed relation-kernel vector to a genuine global
L is not proved merely by sampled relations or holdouts. This remains
an algorithmic completeness/certificate bridge. Runtime final group
verification makes a false positive reject even when that bridge is
not supplied:the solver checks[k]H(G)=H(Q). [pcc:unverified]

## Soundness of checked answers

The actual H is scalar-equivariant and has the genuine left inverse
Recover=[159985]delta NormPrime on the original ell subgroup. Therefore

    [k]H(G)=H(Q)
    implies H([k]G)=H(Q)
    implies Recover(H([k]G))=Recover(H(Q))
    implies [k]G=Q.

This soundness implication needs neither a guessed scalar nor a
completeness claim about relation generation. The native harness also
checks the returned scalar through the original independent source
curve engine and compares with the known-answer fixture OUTSIDE the
runtime solver. [pcc:unverified]

## Actual native panel and preserved gaps

Nativee869bd passes one unfiltered comprehensive test,all2543 selected
hashes unchanged. Every one of the3 Jacobians receives all5 unchanged
public targets at all4 fixed factor-base sizes30,36,48,64:ALL60 attempts
are retained,including relation failures. Each of the15 public cases
has at least one correct IC solve. Every reported success passes both
the actual target group check and independent original source check.
There are82 whole native JSON records. [pcc:unverified]

Zero generator,nonodd generator/target,foreign field,foreign target and
source-model tags,noncanonical coordinates and malformed class-tag
controls reject. Actual foreign-target packets are also tested across
successive model instances. The original source-bound solver's random
P0 and affine legacy-transfer triples do not yet have a supplied exact
same-origin/same-input native compatibility bridge to this new generic
class-input pipeline. That protocol control remains explicitly open;
it is not replaced with source ECDLP solving. [pcc:unverified]

Original IC and wrapped canonical Picard counters and raw wall values
are retained only as diagnostics. FpR has no exposed operation counters;
source/model construction,map setup/evaluation,input admission and
independent source verification are outside those counters. Their cost
is unknown,not zero. Reusing a prepared NormNew also does not constitute
a cold pipeline run. No S,ratio,stage improvement or advantage over
matched IC/rho/precomputation references is established. [pcc:unverified]

Feasible Lean implications cover checked-target reflection and common
offset cancellation. Actual curve/Picard/scalar/recovery interpretation,
valid global relation-log extension and solver completeness remain open.
Next:exact partial bindings,source-linked report,strict independent
replay/CI,normal source publication,genuine whole-data preservation and
the remaining compatibility/counter/admission obligations.
[pcc:unverified]

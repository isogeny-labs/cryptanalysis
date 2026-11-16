# Paired norm-assisted sampling on the fixed original models

Prospective, 2026-11-15, before new sampler Rust. Continue from native7df2ae,
inspected reportab5c32 and published consumerba1fae2/root4de29a1. Reuse the
existing sampler9bc5e6 and its complete literal IC derivative. This task
changes the original-geometry context, not the relation/linear-algebra/
descent algorithm or the fixed model/input/seed population. [pcc:unverified]

## Freeze the same inputs and sampler mechanism

Keep original E2/E3/E4 cases(2,0)/(0,1)/(2,0), D116/39/36, roots89/40/6,
all masks/quartics/P0s/tags, K=F223[z]/(z^3-3), ell2773073,
full order11092292 and the unchanged five original public targets. Construct
G,Q through the accepted opaque full Jacobian maps and compare them with
independent source-point transports and prime-field Phi, as in the accepted
baseline. Expected scalar answers stay outside runtime/solver inputs.
No outcome-dependent model, kernel, origin or parameter reselection.
[pcc:unverified]

The new sampler constructor takes only the fixed geometry side and a public
tagged generator. Reuse the old source body: admit G, compute public
u=[1386537]Norm(G), check nonzero ell-torsion/source admission and actual
Phi(u)=G, bind the exact generator key, then sample(r)=Phi([r]u) for
canonical0<=r<ell. Keep all explicit Calls accounting and its nested-work
limitations. Source scalar/transfer work is part of the algorithm, not an
elliptic DLP solver, witness lookup or fallback. [pcc:unverified]

Copy norm-assisted-ic/derived/class_solver.rs byte-for-byte. Its only existing
differences from the original baseline remain the TargetContext-to-
SamplerContext type name and the random R expression replaced by sample(r).
Preserve the exact two literal substitutions, snapshots and all other bytes,
including the original final Picard verification. Adapt only imports and the
surrounding constructor/type boundary to original-full-geometry NormNew and
the accepted fixed TargetContext. [pcc:unverified]

## Complete sample and paired IC populations

For every one of the3 fixed models, use the existing75 scalar list: the11
boundary/structured scalars0,1,2,3,12,13,26,52,ell/2,ell-2,ell-1, followed by64
values from the unchanged RNG seed0x71A55157. Retain all225 scalar pairs and
the1125 triples across five Q: R, R+G and R+Q. Each prepared sample must
equal the original Picard scalar and all three resulting classes exactly.
Preserve the scalar values, source points, both classes, every triple and
explicit call deltas. [pcc:unverified]

Run all60 paired attempts (3 models x5 public Q xFB30/36/48/64), retaining
both full reports for all120 solver executions. Keep seeds102/103/104/105,
rows_mult1.2, max_desc100000, sge=false, maxw12, lp2=true and relation
verification. Do not stop after an early success. Require at least one
jointly correct setting for each of all15 cases, and require every claimed
success to verify in the actual target and independent original source.
Keep all shared or differing failures, including every rejected candidate.
[pcc:unverified]

Reuse the old comparison projection exactly: exclude raw wall values and
wall_total only from the comparison, and exclude the seven original partial
counter fields in the changed descent phase. All other report fields must
agree. Both full unmodified reports, all omitted comparison fields and raw
walls remain in the retained records; this is a paired correctness comparison
and permits no scientific evidence trimming or price claim. [pcc:unverified]

## Strong known-point reference and controls

After deriving u only from public G, independently compare it with the
already available original-source generator transported to the selected
elliptic model. Record the exact equality or failure. This reference is
outside the sampler input boundary. It prevents treating public norm
preparation as a new advantage when an initial source point is already
known; the source-scalar-plus-Phi sampling path and its full preparation
cost must be compared with that stronger retained-point reference.
[pcc:unverified]

Retain noncanonical scalar/zero generator/malformed key/noncanonical class/
foreign field/model/source tag/non-ell generator and target/changed prepared
generator controls. Construct an actual same-quartic different-P0 model using
the existing original-geometry Adapter::with_base_point and a real alternate
rational point; reject its packet against the frozen context. Include actual
cross-target packets on all three sides, invalid side and bounded parameters.
Retain the actual omitted-inverse2 control Phi(Norm(G))=[2]G!=G. No origin or
map is changed to make a failed control pass. [pcc:unverified]

## Execution, proofs, custody and remaining costs

Use one serial unfiltered900s/2GiB native test, bounded builds/auditors and
the exact existing prepared field engine after full closure and RLIB/RMETA
comparison. Obtain the exact original checkpoint transport for the clean
source. Keep complete compiler/runtime binary custody and source guards
before/after; whole record checks and actual entire-class omissions must
reject without accepted output. Whole omission inputs may be preserved as
complete lossless XZ, with checked production/integrity and full independent
decompressed byte custody as in native7df2ae. [pcc:unverified]

Recheck the unchanged three-root NormAssistedSampling source and its exact
bindings under both original Lean versions. Its actual scalar-law/geometry/
Picard/program bridges remain explicit; the ordinary inverse2 witness and
Phi(u)=G check do not prove every program identity in Lean. The previous
NewTargetIC/InducedFullTransfer scopes stay intact. Preserve any proof,
compiler, wrong-answer, timeout or incomplete prefix with its real exit.
[pcc:unverified]

Retain all whole source, data, full reports, executables, prepared libraries,
failures and editable inspected result for genuineNEW26 before canonical
fixtures/additive native CI. API Calls and old IC/Picard counters do not
flatten FpR/extension, model/map setup, nested decode, admission, final source
verification, known-point-reference or hardware costs. All complete costs
and live budget/capacity/isolation/image admission remain unknown. No timing
ratio, calibrated ECDLP advantage, novelty, new asymptotic result or signed
standing follows from this discriminator. [pcc:unverified]

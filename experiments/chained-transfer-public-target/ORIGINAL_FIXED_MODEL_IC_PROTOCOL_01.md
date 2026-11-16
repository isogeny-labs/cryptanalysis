# IC on the fixed original-prime Jacobian chain

Prospective protocol, 2026-11-15, before new Rust source. Continue from full
native e245d0, induced-transfer proof eddc37, complete exact CI03 a93f80 and
fresh proof run43707728617 at41e35d8. Reuse the existing new-target IC solver
e869bd and later the norm-assisted sampler9bc5e6. All original source,
workflows, 1440 reference paths and negative results remain immutable.
This is a correctness and cost-coverage investigation. [pcc:unverified]

## Fixed mathematical inputs

Keep K=F223[z]/(z^3-3), ell2773073 and full source order11092292. Use exactly
the accepted original E2/E3/E4 models in original-full-geometry-01:

| Side | Original source | Case | D | Chosen root | Kernel mask | Actual P0 |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | E2 | (2,0) | 116 | 89 | 1155177839943778305 | (1:0:28) |
| 1 | E3 | (0,1) | 39 | 40 | 5188291906266857505 | (1:0:90) |
| 2 | E4 | (2,0) | 36 | 6 | 1155177839943778305 | (1:1:165) |

No model, kernel, origin, field basis, prime, public input or order is
reselected after observing a solver outcome. Quartics and model/field tags
are the complete actual constructor outputs, checked against the accepted
fixed geometry. The five original public targets and their independent
source verification remain fixed. Expected scalar answers stay outside all
solver/context/runtime inputs. [pcc:unverified]

## Public input construction and the actual chain

Construct the unchanged full Runtime and its fixed geometry. Independently
transport the original generator and each public target to E2 using the
existing ThirdHop map. Produce the side0 Jacobian packets with the actual
prime-field Phi. Obtain sides1/2 using the existing opaque full Runtime maps,
including its actual degree169 composite. Assert equality with independent
source-point transports and prime-field Phi on each destination. Record all
generator/target packets, actual quartics/P0s/tags and construction calls.
The direct and retained-lift comparisons already established remain intact.
[pcc:unverified]

The solver receives only an admitted actual target context, public G,Q,
ell, ordinary IC parameters and an RNG seed. Its context binds the exact
selected geometry side, uses canonical decoding, rejects a zero generator
and rejects inputs outside ell-torsion. It does not receive an elliptic
point lift, a scalar witness, an ECDLP solver, a recovery fallback or a DLP
lookup table. All transfer construction precedes the IC solver boundary.
Final verification checks every reported answer in the actual Jacobian and
in the independent original source group. [pcc:unverified]

## Literal solver reuse and complete population

Create a separate original-fixed-model-ic-01 crate. Preserve the complete
existing new-target-ic/derived/class_solver.rs byte-for-byte and reuse it
without changing relation collection, large-prime handling, RNG, holdouts,
linear algebra, descent or final canonical Picard verification. The new
TargetContext supplies the already compatible original-geometry NormNew
type and the exact selected side; preserve the actual P0 at factor-base
index0. Any necessary edit beyond the context/type boundary is a separately
identified source difference and must be reviewed before native execution.
[pcc:unverified]

Run all3 fixed targets x all5 public Q x all4 factor-base sizes30/36/48/64:
exactly60 attempts. Freeze seeds102/103/104/105 respectively, matching the
existing accepted implementation. Keep rows_mult1.2, max_desc100000,
sge=false, maxw12, lp2=true and relation verification enabled. Do not stop
after an early success. Retain every complete success/failure report,
relation/descent/denominator failure, counter and raw phase wall value.
Acceptance requires at least one verified IC solve for each of all15
public cases. Any reported success with a wrong Jacobian or original-source
answer rejects the run immediately; preserve its actual completed prefix.
A timeout or incomplete panel remains an incomplete result. [pcc:unverified]

Retain actual malformed/noncanonical/foreign-field/foreign-model/source-tag,
zero-generator, non-ell generator/target and cross-target packet controls.
Reject invalid side selections and invalid bounded IC parameters. Whole
record checks must account for every model input, attempt, public-case
summary, target summary and final population. Actual entire-class omission
controls must reject without accepted output. The whole original raw stream
and complete decoded reports are retained; acceptance is correctness, not a
fixed success count or deterministic wall-time claim. [pcc:unverified]

## Bounds, evidence and cost obligations

Use one serial unfiltered test with a900-second whole native bound and2GiB
address-space limit. Build within a900-second supervisor, with120-second
individual fetch/compile/auditor bounds, reusing only the exact existing
field-engine preparation after full dependency/features/targets closure and
whole prepared RLIB/RMETA equality checks. Record actual compiler/runtime
binary equality, both repository proof obligations, exact original checkpoint
transport, source guards before/after, commands, toolchains and actual exits.
If the engine recompiles or its preparation differs, retain the failure and
resolve that discrepancy before treating native execution as accepted.
Warm preparation supplies no cold120 or performance acceptance.
[pcc:unverified]

Inventory source validation, both geometry origins, model/map setup, known
initial point construction, opaque and retained-lift transfers, field FpR
and extension arithmetic, admission, factor-base setup, relation collection/
verification, linear algebra, hashing/lookups, descent, and final independent
verification. Preserve original IC/Picard counters as diagnostics; missing
primitive counters and setup costs remain unknown. No calibrated ratio,
pipeline improvement or advantage over existing IC/rho follows from success
on these three toy models. Existing strongest-reference and live hardware/
budget/capacity/isolation/image admission requirements remain open.
[pcc:unverified]

After this complete discriminator, adapt the existing norm-assisted sampler
to the same fixed original models as a separate next task, retaining the
full paired original-vs-assisted reports and every shared failure. Preserve
all source snapshots, full data, executables, prepared libraries, proofs,
reports and failed attempts for genuine NEW26. Supply source-linked written
soundness and faithful conditional Lean coverage, readable editable result
report and additive replay/CI. Never reinterpret old prime-only selections
or old nu12 facts as results on these original models. [pcc:unverified]

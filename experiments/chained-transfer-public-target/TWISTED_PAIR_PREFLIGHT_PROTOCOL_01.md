# Fixed quadratic-twist pair: new-instance prime-field preflight

Prospective study, 2026-11-14. Publish this protocol before new proof or
native implementation. This is a separate ECDLP instance. It preserves the
existing supplied-source D12/D24 negatives and does not transport the
original prime-order ECDLP to its quadratic twist. [pcc:unverified]

## Question and fixed inputs

The actual second and third matched HLP rows have D12 and D24, respectively
(27fb3a/6d2c97), and retain smooth F223 quartics. Their required original
supplied-source identifications are unsupported. Fix ONE new twist factor
nu=12 in F223 and BOTH already-fixed elliptic endpoints E2 and E3. No
alternate twist, HLP kernel, root/sign case or fourth edge is selected in
this study. The original E2->E3 isogeny and full transported G2/G3 masks are
fixed inputs; model admissibility must be examined after transport.
[pcc:unverified]

Investigate the standard HLP twisting construction for these new sources:
E_i^nu: y^2=x^3+nu^2*a_i*x+nu^3*b_i. The proposed homogeneity is
A'=nu*A, B'=nu^2*B, Delta'=nu^2*Delta, h'=nu*h, H'=nu*H,
adj(H')=nu^2*adj(H), T'=nu^3*T and D'=nu^3*D. This predicts unchanged
normalized descended quartics after a common coefficient scale, with a
different supplied elliptic source. These are hypotheses to check, not a
new native result. A square twisting factor alone is not a complete
Jacobian evaluator. [pcc:unverified]

## Sources checked and limits

Primary: Howe, Leprevost and Poonen, *Large torsion subgroups of split
Jacobians of curves of genus two or three*, arXiv:math/9809210v1, section4.1,
Proposition15 and its following remark. The proposition identifies the
polarized quotient with a plane-quartic Jacobian over k(sqrt(T)); the remark
explains the additional quadratic character for a nonhyperelliptic
Jacobian. Read the complete local paper/text, including the actual
twisting-factor formula and the field-extension qualification. Source
hashes and the exact relevant text are retained with the prospective report.
[pcc:unverified]

Implementation sources checked: original odd-product-models lib/source/even,
actual fixed-kernel second/third model appendices, and the original degree13
kernel construction. Original kernel_data hardcodes eigenvalues2/4 and
SourceE::check hardcodes cofactor4. Neither is silently reusable for a new
twisted source. The primary result is standard prior work, not a novelty
claim. Research-KB/ecdb tools remain unavailable in this runtime; the
previous wrapper127 and locked autoresearcher8edec422 supply no absence
inference. No secret/key access or vault edit is needed. [pcc:unverified]

## Mathematical obligations

1. Check the scalar homogeneity independently by full original finite-field
   operations and faithful Lean ring/field identities, using both original
   proof gates and exact statement bindings. Explicitly retain the
   nonzero-denominator hypotheses and the HLP geometric bridge. A finite
   modular square witness does not by itself formalize the field encoding.
2. Certify each new elliptic order/subgroup. The original order and the
   standard quadratic-twist trace relation give a candidate order only.
   Factor that fixed candidate using native Rust; select its largest prime
   factor before model construction, use the original deterministic
   primality check, find a nonzero point of that order and require a unique
   Hasse multiple equal to the full candidate order. Use at most256
   lexicographic x candidates and a fixed root seed. Retain all attempts.
   Failure keeps the certificate open; it does not authorize a different
   twist or endpoint. If the cofactor differs from4, use an explicit new
   parameterized certificate retaining every original smoothness/primality/
   point/Hasse check; do not weaken or edit the old SourceE checker.
3. Twist the already-fixed complete E2->E3 degree13 rational map and its
   signed dual. Check all coefficients, the whole curve identities,
   separability/coprimality, both[13] compositions and actual target
   equations. Do not rerun the old eigenvalue2/4 constructor on the twist.
   Retain any changed Frobenius eigenvalues explicitly. Check36 points on
   each side,1024 addition pairs each way, every rational2-torsion point,
   and five fixed public multiples of the new generator, including an
   independent original source arithmetic check. Actual wrong-order/zero-generator
   certificate controls must reject.
4. Transport all64 actual product2-torsion points under x->nu*x with all
   coordinate/index permutations explicit. Check Frobenius, all4096
   addition/original alternating-pairing rows and the original135 masks.
   Freeze the rescaled G2/G3 masks BEFORE constructing any new model. Do
   not assume sorted root/sign indices remain(2,1)/(0,0).
5. Run allsix original HLP cases at both new endpoints. Require unique
   equality to each fixed full mask, retain every candidate and all
   matrices/adjugates/factors/quotient identities/square roots/coefficients.
   Compare the matched normalized quartic arrays to the two frozen old
   matched arrays exactly. A mismatch or unsupported identification is a
   negative result. No relabeling, square-case reselection or retwist.

The written quotient-factorization argument must distinguish a supported
HLP source identification and a geometric induced odd map from a complete
rational Jacobian evaluator. The latter requires a subsequent separately
frozen implementation/direct-composite protocol. No complete map, chain,
global rational evaluation, field descent of the original logarithm or
Jacobian isomorphism classification is inferred from this preflight.
[pcc:unverified]

## Execution, controls and acceptance

Keep all original source guards, workflows, model negatives and genuinely
published fixtures unchanged. Use an additive literal-source derivative;
record every source edit, actual Cargo profile/library/executable and all
complete compiled/runtime bytes. One explicit unchanged-engine package
preparation in a NEW declared graph/cache has a900s bound, followed by120s
wrapper builds. This does not discharge the old whole cold120 requirement.
Publish code and obtain an exact original clean-source checkpoint/local
gate before native execution. [pcc:unverified]

Run ONE unfiltered fixed-pair preflight within900s and2GiB. Reject on any
certificate, rational identity, point, torsion, whole old-array or matched
source failure. Keep all unsuccessful outcomes. Freeze and compare every
whole ordered native record with no masks or deduplication; removing an
actual complete required record must reject101/no accepted output. Run
both original Lean gates with zero trusted declarations and exact original
PCC statement bindings. Preserve finite-field/geometric/program bridges
and unsigned standing. [pcc:unverified]

This is a bounded correctness preflight, not a timing experiment. No paid
compute, calibrated source-operation price, benchmark, ECDLP advantage or
novelty inference is authorized. Any performance study still needs live
budget/capacity/isolation/tested-image admission and strongest matched
rho/index-calculus references. After either outcome, preserve the new
instance and old negative results, report/prove/commit the exact finding,
and advance the next unblocked task. [pcc:unverified]

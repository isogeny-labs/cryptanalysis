# Exact cubic gluing checks, 2026-10-25

Freeze this contract, `CUBIC_GLUING.md`, and `examples/cubic_gluing.rs`
before collecting the new outputs. This is a finite mathematical/software
verification and complete small-field census, with no performance claim.
The original novelty and explicit-transfer requirements remain open.

1. For each q in F5*, enumerate every rank-three RREF subspace of F5^6,
   retaining exactly the subspaces isotropic for J + qJ + q^2 J.
   Each form must give (5+1)(25+1)(125+1) = 19,656 Lagrangians.
2. For all 480 matrices M in GL2(F5), use the unique q with det(M)=q^3.
   Count all stable Lagrangians and all stable transverse Lagrangians.
   Existence of the latter must agree with the written split-semisimple
   criterion. Expected positive matrix count: 4 + C(4,2)*5*6 = 184.
   No quotient existence, indecomposability or curve statement follows
   from this finite enumeration alone.
3. Check the constructive formula on every positive compatible GL2(F11)
   input. Expected positive count: 10 + C(10,2)*11*12 = 5,950.
   This is not an exhaustive negative-case check at ell=11.
4. Fixed controls: split-distinct diag(3,4), q=3; scalar I, q=1;
   Jordan [[1,1],[0,1]], q=1; irreducible [[0,3],[1,0]], q=3.
   Reject wrong determinant, zero q, out-of-range entries, unsupported ell.
   Explicitly use det(M)=q^3, which generally differs from q modulo 5.
5. Enumerate all 1,008 models (a,b), a in {0,1}, b of absolute degree 9,
   in F512 with the existing deterministic power basis. Verify exact source
   orders with both log-table and raw carryless multiplication. The counting
   formula/control flow is shared; this is not external independent review.
   Tabulate by exact trace. Compare the established d=3 3-kernel criterion
   t=0 mod 3 with the sufficient 5-kernel criterion that t^2-4*512 is a
   nonzero square modulo 5. Repeated eigenvalues remain unresolved by trace.
   No yield is extrapolated beyond these exact models. b=1 is excluded by
   the full-degree hypothesis, regardless of its torsion predicates.

Save outputs, exact commands, source hashes, host/tool versions and exit
statuses in a new `cubic-gluing-checks/` directory. Retain failed attempts.
Run formatting, Clippy and the release all-target tests. Preserve previous
frozen manifests and reports. The core sweeper and checkpoint database must
not change. The historical missing-checker dependency was removed by
integration of cryptanalysis main c5aa7b39; this note supersedes that
procedural blocker for new work only.

Attempt a pinned Lean proof for the fixed constructive example. Keep the
general theorem's written proof and record the missing formalization bridges;
a fixed finite certificate does not formalize the general classification.
Record standard foundations with `#print axioms`; no native-decision bypass.

The next experiment after a successful kernel census is quotient construction,
not automatic promotion into the weak-curve catalogue. Full prior-art priority,
geometric indecomposability for ell=5, a target equation, source-twist selection,
and explicit subgroup/log transport remain separate obligations.

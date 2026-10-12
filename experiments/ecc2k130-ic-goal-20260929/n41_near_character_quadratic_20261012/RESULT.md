# Full quadratic feature rank for N41 source-addition errors

The degree-at-most-two Boolean feature vectors of the first **825** archived N41 source-addition errors span all **821** coordinate features for both `x` and reciprocal `1/x`. An independent low-pivot elimination and all 1,642 explicit XOR basis witnesses agree with the producer's high-pivot computation. Checked Sage independently reconstructed all 825 source additions from the frozen signed diagonal-pair table. Therefore any degree-at-most-two Boolean polynomial in the 40 nonconstant error bits that vanishes on **every** source-addition error is the zero polynomial in that feature basis. Terms containing the known constant-zero bit are algebraically redundant. This closes exact quadratic parity gates on this coordinate error for the declared N41 source law.

The complete concrete rank certificate is verified computationally and by independent curve replay. Lean 4.34.1 checked the general structural implication and one concrete basis equality. A monolithic Lean check of all 1,642 concrete equalities reached the 4-GiB guard; the remaining kernel formalization is recorded precisely below.

## Frozen input and feature law

The source is the preceding [approximate-additivity panel](../n41_near_character_20261012/RESULT.md) on `EC1N41Ckb1h7d5e80d3c4d0`, over `GF(2)[t]/(t^41+t^3+1)` with `y²+xy=x³+1`. Its deterministic train law chooses a signed state from each of the first two diagonal-pair slots and retains four distinct folded columns. For `u(P)=x(P)` or `u(P)=1/x(P)`, the archived error is `e_u=u(P)+u(Q)+u(P+Q)`. Bit zero of both errors was zero on the frozen source and uniform baseline panels, so the 40 remaining polynomial-basis bits are the variables here.

The feature vector has **821** entries in this exact order: a constant, 40 individual bits, then the 780 products of distinct bit pairs in lexicographic order. The [protocol](protocol.json) hashes the source, archived vectors, prior group audit, toolchain, and feature order before certificate generation. It fixes the first 1,024 training errors as the selection prefix. [build.py](build.py) selects independent source rows and records an XOR subset for each of the 821 standard feature-basis vectors. Raw `x` reaches rank 821 at source index **824**, reciprocal `1/x` at index **823**; each certificate uses 821 source rows from that prefix.

For a feature coefficient vector `c`, the Boolean polynomial's value at an error point is the binary dot product of `c` with its feature vector. If it vanishes on all source errors, it vanishes on the selected rows. Their full rank forces every coefficient of `c` to be zero. This argument uses exact finite-source vectors and does not infer a rate from the constructed rows.

## Verification and formalization

| Gate | Result |
| --- | --- |
| Producer [rank certificate](certificate.json) | 821 independent rows and 821 XOR witnesses for each coordinate |
| Independent [feature and certificate verifier](verification.json) | `PASS_INDEPENDENT_N41_QUADRATIC_RANK_CERTIFICATE`; low-pivot rank 821 for both, all 1,642 XOR equalities replay |
| Checked-Sage [group audit](audit.json) | `PASS_INDEPENDENT_N41_QUADRATIC_RANK_SOURCE_REPLAY`; first 825 source errors reconstructed from archived curve points |
| Group-audit [run receipt](audit_run_status.json) | `EXIT_0`, 21.765 s parent wall, 305,250,304 B sampled peak RSS, one worker, 60 s/4 GiB cap |
| Lean [structural theorem](QuadraticStructural.lean) | `sampled_basis_forces_linear_zero` checked; exact hypotheses and axioms in [proof map](PROOF_MAP.md) |
| Lean [first concrete basis equality](QuadraticFirst.lean) | `EXIT_0`, 28.368 s, 3,497,197,568 B peak; [output](first_basis_stdout.log) reports only `propext` |
| Complete Lean concrete certificate | **Partial formalization**: full source hit the 4-GiB cap at 106.433 s; size-32 chunk hit a 2-GiB cap at 29.857 s |

The first Lean launch failed before running its workload because the Python chosen inside the proof directory lacked `psutil`; [that receipt](lean_launch_failure_v1.json) is retained. The initial [full source](QuadraticRank_v1.failed.txt) and [log](lean_check_v1.log) record a default recursion-depth failure. Adding evaluator limits led to the [full OOM receipt](lean_run_status.json), with 4,296,376,320 B sampled peak. The [chunk plan](chunk_plan.json) and [generator](build_chunks.py) reproduce 52 bounded modules, but a 32-equality chunk also exceeded its 2-GiB guard; its source and [receipt](first_chunk_v2_status.json) are preserved. The unrun generated chunk files were removed after that gate. The [repair receipt](lean_repair.json) binds the generated and amended proof sources. `lean4checker --fresh` was unavailable; no fresh-checker result is reported.

The [proof map](PROOF_MAP.md) separates the checked general theorem, the one checked concrete equality, the Python-verified remaining 1,641 equalities, and the Sage curve-law bridge. The complete 821-dimensional Lean certificate remains open. The exact rank observation and the independent curve replay are retained as the current mathematical evidence.

## Consequence for the ECDLP direction

The prior panel already found no stable low-weight **approximate** additive parity on holdout. This exact rank result now rules out **every exact quadratic** Boolean equation in the 40 nonconstant error bits as a source-only additive filter for this N41 law. It does not rule out higher-degree, approximate, or public-target-conditioned constraints. The next experiment should specify one of those constraints before searching, then test whole-family pruning and preservation of an unpinned N41 public relation with a source-bound N131 work and memory projection. The active N131 ordinary-relation gate remains one worker, 600 seconds, and 4 GiB.

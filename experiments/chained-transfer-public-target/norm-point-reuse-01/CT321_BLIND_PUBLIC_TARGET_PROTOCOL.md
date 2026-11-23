# CT321 — Prospective hidden-scalar public-target challenge protocol (2026-11-22)

**Standing:** preregistered **before** implementation. [pcc:unverified]. A source-only commit/reveal and toy arithmetic gate, not a native Jacobian execution, complete ECDLP solve, authenticated independent challenge custody, or measured speedup.

## Evidence and scope

Reuses CT315 complete cold seven-arm panel, CT317 independent short-Weierstrass source-group replay, CT319 raw receipt binding and CT320 requirement of >=4 algebraically distinct Q on the *same* source group. CT320's distinct Q can still be selected by a benchmark producer that knows k and adapts the solver to the targets. Read [CT320 protocol](CT320_DISTINCT_PUBLIC_TARGET_PROTOCOL.md), [CT317 implementation](ct317_group_replay.py) and [CT319 implementation](ct319_receipt_cost_binding.py). Shared research-KB MCP/CLI and lead atlas are unavailable in this connector-only runtime; GitHub code search of cryptanalysis and crypto for “hidden scalar”, “challenge generator”, “commit reveal” was consulted; no novelty or exhaustive negative claim is made. Related existing cryptanalysis benchmark protocols use frozen `target_seed` and source Q, but source publication alone cannot establish blindness.

## Prospective protocol / fixed acceptance gate

1. Input is an exact, canonical-parameter short-Weierstrass source curve over prime `5 <= p <= 2^31-1`, with prime `3 <= n <= 2^32-1`, prime-order generator `P`, `[n]P=O`, nonzero P, and `count >= 4` and `count <= min(128,n-1)`. Use CT317's existing arithmetic and deterministic trial-division checks. Do not silently accept points at infinity.
2. Draw each k independently with `secrets.randbelow(n-1)+1`, rejecting repeated k/Q; this is uniform sampling without replacement *after* rejection, assuming OS CSPRNG. For each target draw a separate 32-byte secret salt using `secrets.token_hex(32)`. Public Q is `[k]P`.
3. Publish a canonical, exact-schema public challenge: source group witness with Q and unique target IDs, plus per-target commitments `H(domain || canonical({curve_id,target_id,Q,k,salt_hex}))`. Publish a **separate private** reveal manifest with k and salts, bound by exact SHA-256 of the public challenge. Neither k nor salt is printed to stdout or placed in the public witness. Persist private output only by exclusive-create with `0600` mode and fail on existing paths/symlinks. Never commit a production private manifest, attach it to a PR/CI artifact, give it to a solver process, or pass it in argv/environment.
4. When the challenge is issued, record the public file hash and immutable, *independent* pre-execution custody/timestamp outside producer control. Run seven cold arms for each public Q in the registered ABBA order. The producer/process must receive only the public challenge and solver binaries; capture argv, stdout/stderr, all phase costs, RSS and source/binary hashes. After **all** process receipts exist, reveal private file to an independent evaluator and verify commitments, Q=[k]P, target uniqueness, public SHA and panel target IDs/scalars through CT315/317/319/320.
5. Audit emits only counts/digests and boolean checks, never full private scalars or salts. Reject altered public bytes, wrong curve, duplicate or noncanonical Q, invalid subgroup, wrong salt, wrong k, wrong ID, missing commitment, malformed JSON, and pre-existing output files. A self-test uses deterministic injected draws solely for synthetic toy controls and must never be treated as random or an authenticated blind trial.
6. Keep separate the claim of *mathematical validity of challenge and later reveal* from the unproved claims that the solver lacked private access, no cross-run caching occurred, the setup was truly cold, and external receipts are authenticated. A 5-element toy subgroup offers no cryptographic secrecy even with a 256-bit salt; practical targets also must not be mistaken for secure DLP parameters.

## Required outputs and execution

- Stdlib-only `ct321_blind_challenge.py` supporting `--issue --curve ... --public ... --private ... --count 4`, `--audit --public ... --private ...`, and `--self-test`.
- Exact canonical JSON bytes, domain-separated 256-bit commit salt, strict key sets, consistent SHA-256 binding.
- Positive toy algebraic audit, intentional public/private corruption rejections and permission/exclusive-create checks; normal Python and `python3 -O` source CI, same results.
- No AWS, S3, STS, native 695/701 replay, unapproved EKS/Spot, paid compute, fixture replacement, revision of CT320, PCC or protected merge.

**Beyond CT321:** owner-approved coherent artifact/config provenance, six original S3 objects under authorized STS, actual CT244 C169/C13a/C13b/D/N2_actual native timing, complete same-host cold source ECDLP against retained/rho/BSGS/frontier IC with validated hidden challenge custody, memory/uncertainty, independently signed PCC. A commit/reveal gate alone is not the requested complete-solve advantage.

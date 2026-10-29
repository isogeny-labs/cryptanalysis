# Full tensor implementation workstream

The user's scope is the complete Bochum algorithm in both crypto and
cryptanalysis, including the compact encoder and contraction backend, without
ending at a toy generic reduction. The earlier reference is preserved.

Primary sources read before implementation:

- Bochum v0.2, `1ee44e562b1b9a50ea339f3b8f81112b5a24b96f`, all of §2
  (including the two-stage Fourier multiplication encoding), §3 and Figure 2.
- OpenAI, *The Exponential Time Hypothesis is False*, October 25 version,
  `7ef5c0cc5ca4b0e072b7a050fca09ab24bc6fa3a`, Appendix D.1 and D.4:
  unramified coefficient ring, conditional-expectation packet packing,
  Cauchy deformation, tapered Hermite recovery, weighted modes, recursive
  packet tensors and creation-precision lifting.
- Agrawal–Kayal–Saxena, *PRIMES is in P*, Algorithm in §4 and its correctness
  and parameter bounds, primary author copy `primality_v6.pdf`.
- Existing boundary ledger, native field/decomposition code and ECDLP atlas
  reviewed in the first reference; no exact BTN implementation was found.

Implementation ownership: native standalone `crates/hashed-ecdl-tensor` in
crypto, mirrored as a Rust workspace dependency in cryptanalysis. This keeps
the complete code testable without rebuilding unrelated root-library code.

| Obligation | Acceptance condition | State |
| --- | --- | --- |
| Exact BTN graph, pins, counts and witness extraction | Independent truth-table checks including parallel edges and isolated vertices | implemented; bounded controls pass |
| Compact arithmetic encodings | Independent products, canonical residues, carry/parity boundaries; explicit edge/degree checks | implemented; independent products through 513 bits pass |
| Point and factor-base predicates | Identity/inverse/doubling checks, canonical coordinates, exact affine hashes | implemented; complete small-curve pair controls pass |
| Recursive contraction | Exact ring/kernel/Hermite/mode tests and forced small recursion compared with direct contraction | implemented; coupled ports, quadratic modes and two recursion levels agree with direct counts; independent general audit open |
| General reduction | Arbitrary-precision coordinates, certified hash-prime selection, known-answer and corrupted-certificate replay | implemented; full tiny pipeline and file replay pass |
| Both integrations | Byte-identical native sources, public Rust API, checked builds/lint and paired PRs | API/parity, core lint, MSRV, supply chain and binding checks pass; publication pending |
| Prior validation gaps | Repair own post-merge lint failure and complete the required broad root regression | maintained strict lint passes; uncapped root regression running |

The paper's recursive constants imply brute-force fallback at all practical
network sizes. The implementation must report the backend actually used and
preserve resource failures. Small forced-recursion correctness controls do not
establish an asymptotic or practical speedup. No benchmark or deployed-curve
claim is part of this implementation task.

Current commands and observed outcomes are recorded in
[the tensor validation receipt](hashed-ecdl-tensor-validation.md). The first
25-test release panel passed, as did the final 27-test native panel after
adding coupled/nested recursion controls. The selected binding package also
passed 20 unit tests, 19 FFI parity tests and 14 documentation tests. A
Rustdoc-only correction quotes the cofactor formula; strict docs passed.

The initial reference PRs are merged and their scheduled tracker is disabled.
The native follow-up remains a separate paired deliverable until its PRs land.
Concurrent main additions (the binary-curve bucket/cutset prototype and an
unrelated protocol) were merged without changing their source or evidence;
the native Rust/Cargo inputs are otherwise unchanged by that refresh.

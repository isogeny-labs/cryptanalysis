# PQC-Assay: native C modular-arithmetic proofs

This adopts the implementation/model/mathematics split and mutation controls
from [PQC-Assay](https://github.com/amarshat/pqc-assay/tree/6b0096f4a2bda9cf07c7347094affc85d9eb24ff).
It verifies this repository's actual `ca_addmod` and `ca_submod` inline
functions in `include/cryptanalysis/ca_modarith.h`. No PQC reference C is
substituted for the local implementation.

## Checked scope

For all 64-bit unsigned a, b, m with `m != 0`, `a < m`, and `b < m`:

| Function | Implementation-to-model check | Model-to-mathematics check |
| --- | --- | --- |
| `ca_addmod` | its result equals `add_mod a b m` | zero-extended result equals `(a + b) mod m`, computed at 65 bits |
| `ca_submod` | its result equals `sub_mod a b m` | zero-extended result equals `(a + m - b) mod m`, computed at 65 bits |

The widened additions cannot overflow: each operand is at most 64 bits.
The subtraction expression is nonnegative because b < m. The models are
written independently using widened arithmetic. Both mathematical properties
are SAW/z3 proofs. A separate Lean 4 arithmetic layer checks the same modular
results for explicit unsigned-wrap transcriptions of the C branches; it does
not replace the SAW implementation proof or establish a C-to-Lean refinement.
Every implementation obligation and
mathematical property has a wrong-output control that must produce a solver
counterexample. `mutations.sh` also compiles copies of the actual header with
wrong add and subtract expressions; the unchanged proofs must reject both.

The nonempty domain includes m = 1, zero operands, unequal operands and
64-bit moduli above 2^63. There is no small-modulus or no-carry restriction.
The proof says nothing about unreduced operands, modulus zero, multiplication,
Montgomery reduction, group operations, solvers, timing or side channels.

### Lean proof map

[`lean/Modarith.lean`](lean/Modarith.lean) uses Lean 4.34.1 with only `Init`.
`U = 2^64`, and every theorem assumes `0 < m < U`, `a < m`, and `b < m`.
The corresponding SAW domain is `m != 0`, `a < m`, `b < m` for 64-bit words.

| C operation | Lean model and theorem | Exact statement |
| --- | --- | --- |
| `ca_addmod` | `PqcAssay.cAdd64`, `PqcAssay.cAdd64_correct` | `(a+b) % m` after 64-bit input and conditional-result wrapping |
| `ca_submod` | `PqcAssay.cSub64`, `PqcAssay.cSub64_correct` | `(a+m-b) % m` after 64-bit else-branch wrapping |

The Lean definitions transcribe the header's unsigned addition, comparison,
subtraction and wrap points. A human review still connects those definitions
to C; SAW independently checks the compiled header against the widened
Cryptol models. The repository Lean gate compiles both theorems and rejects
transitive axioms beyond Lean's standard foundations. No `sorry`, custom
axiom or `native_decide` is used.

## Reproduce

Linux x86_64, clang 19.1.7, git, curl, tar and sha256sum:

```sh
verification/pqc-assay/setup.sh
verification/pqc-assay/verify.sh
verification/pqc-assay/mutations.sh
tools/lean/proof-gate.sh verification/pqc-assay/lean/Modarith.lean
```

CI uses Debian 13's `clang-19=1:19.1.7-3+b1`. `CLANG` can select that
compiler at another path. `ASSAY_SAW_HOME` selects an existing SAW 1.5.1;
`ASSAY_CACHE` selects the cache. The bootstrap checks the published archive's
SHA-256. `verify.sh` checks the pinned compiler version and production hashes,
then compiles a thin wrapper that includes the actual public header at `-O0`.
Unsigned C wrapping remains in force. There are no assumed callee specs.

`sources.sha256` pins both included project headers. Source changes fail the
gate until the hashes are deliberately updated and the proofs and controls
rerun. The runner checks native and mathematical counterexample counts so
an unrelated error from SAW's `fails` cannot pass the mutation gate.
Logs, tool versions and input/bitcode hashes go to `build/verify.txt`; CI
uploads them on success and failure.

Trusted: clang's C-to-LLVM translation, the two ABI wrappers, SAW's LLVM
semantics, Cryptol and the bundled z3 solver. Unlike upstream's HQC and
ML-DSA developments, this small port has no Isabelle leg. The full native
Rust-to-upstream-model adaptation lives in
[crypto/verification/pqc-assay](https://github.com/aburan28/crypto/tree/main/verification/pqc-assay).

See [VALIDATION.md](VALIDATION.md) for the exact local results and gaps.

## Attribution

Upstream project: [amarshat/pqc-assay](https://github.com/amarshat/pqc-assay),
commit `6b0096f4a2bda9cf07c7347094affc85d9eb24ff`. Its original project
license is preserved in `UPSTREAM-LICENSE`. This port introduces its own
Cryptol models for the local C functions and does not copy upstream's
algorithm-specific proof claims.

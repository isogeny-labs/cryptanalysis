# Initial port validation

Base revision: `c5aa7b39bfa30e8cdbd46a158c7cbadaa8be3503`.
Date: 2026-10-25. Host: Linux x86_64, Debian 13.6.
This is correctness validation. No performance measurement or comparison was made.

| Requirement | Status | Evidence |
| --- | --- | --- |
| Compile actual production functions | Verified | `harness.c` includes the pinned public headers; `sources.sha256` |
| C equals widened arithmetic model | Verified | SAW 1.5.1 exited 0 for both `llvm_verify` obligations |
| Models equal modular arithmetic | Verified | both `prove_print z3` obligations exited 0 at 65 bits |
| Wrong specifications are rejected for the intended reason | Verified | two LLVM counterexamples and two mathematical `Invalid` models |
| Wrong production functions are rejected | Verified | add and subtract source mutants both rejected with solver counterexamples |
| Existing arithmetic tests | Verified | existing `test_modarith.c`: `ok: 404488 checks` |
| Shell and workflow syntax | Verified | ShellCheck 0.10.0 and actionlint 1.7.12 exited 0 |
| Other functions, Isabelle proofs and side channels | Not attempted | outside this port's two-function scope |

## Commands

The proof run used these environment selectors; the values are tool paths, not credentials:

```sh
export ASSAY_SAW_HOME=/workspace/toolchains/saw-1.5.1
export CLANG=/workspace/toolchains/clang19/usr/bin/clang-19
export LD_LIBRARY_PATH=/workspace/toolchains/clang19/usr/lib/x86_64-linux-gnu
verification/pqc-assay/verify.sh
verification/pqc-assay/mutations.sh
gcc -std=c11 -O2 -Iinclude -Isrc -Itests src/modarith.c src/util.c \
  tests/test_modarith.c -pthread -lm -o verification/pqc-assay/build/test_modarith
verification/pqc-assay/build/test_modarith
```

SAW: `1.5.1 (1f227d9 (release tag v1.5.1))`.
Compiler: `Debian clang version 19.1.7 (3+b1)`.
Regression compiler: `gcc (Debian 14.2.0-19) 14.2.0`.
Compact raw proof and mutation outputs are retained under `evidence/`.
CI uploads fresh logs per run; a new run does not replace this initial receipt.

## Failed development attempts

The initial version checks incorrectly assumed SAW wrote its version to
stdout; it writes stderr. A subsequent SAW script used an unsupported string
concatenation operator, and the first Cryptol predicate lacked parentheses
around comparisons. Those attempts exited nonzero before a proof result.
The runner initially required a print message suppressed by verbosity 3;
it now relies on the prover exit status and explicit counterexample counts.
The mathematical negative controls use SAW's `Invalid:` format, separately
from LLVM's `Counterexample` format. These corrections did not change the
production code or weaken a contract. The compact attempt logs are retained.

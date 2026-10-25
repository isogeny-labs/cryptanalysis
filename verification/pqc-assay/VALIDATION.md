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
| Lean reduced-input arithmetic transcription | Verified locally | `lean/Modarith.lean`, Lean 4.34.1; 2 theorems, 0 failing, 0 trusted, transitive axioms `propext` and `Quot.sound` |
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

## CI follow-up, 2026-10-25

The native proof workflow and ordinary C CI passed on `5314ec7d8d20560402a67fd4ee43c7614936f898`.
The changed-lines formatting check rejected the ABI wrappers' multiline layout.
The harness now uses the one-line layout requested by that check; local
clang-format 19.1.7 accepts it. SAW, all four specification controls and both
source mutants were rerun successfully after formatting. Their new receipts
are `evidence/format-fix-*.txt`; the original receipts remain unchanged.

Other initial-head failures do not inspect changed production code:

- [artifact hydration](https://github.com/aburan28/cryptanalysis/actions/runs/40150318534):
  the existing sparse job tries to copy `docs/ecdlp-surfaces/report.pdf` into
  an absent directory;
- [analysis](https://github.com/aburan28/cryptanalysis/actions/runs/40150318557):
  ShellCheck flags the literal `$HOME` test in unchanged `scripts/cli_smoke.sh`,
  gcc reports an uninitialized-state warning in unchanged `src/ca_internal.h`,
  and clang-tidy/cppcheck report findings in unchanged library/test files.

Those checks remain merge gates. The port does not suppress their findings
or change their policies. Merge is authorized, but remains pending successful
applicable checks.

## Lean arithmetic follow-up, 2026-10-25

The standalone [`lean/Modarith.lean`](lean/Modarith.lean) adds two reduced-input
theorems without changing the pinned production C or Cryptol source. The Nat
models represent unsigned 64-bit wrap at each C operation that can wrap.
`PqcAssay.cAdd64_correct` states addition equals `(a+b)%m`;
`PqcAssay.cSub64_correct` states subtraction equals `(a+m-b)%m`. Both assume
`0<m<2^64`, `a<m`, and `b<m`. The model-to-header correspondence was checked
by reading the C branch expressions; the Lean proof alone does not certify
that correspondence. SAW remains the machine check of compiled C against the
independent widened Cryptol models.

For addition, `a+b<2m`, so at most one subtraction of `m` is needed. If the
64-bit sum does not wrap, the comparison with `m` performs exactly that
subtraction when needed. If it wraps, the wrapped sum is less than `a` because
`b<2^64`; the carry branch adds back `2^64` before subtracting `m`, yielding
`a+b-m` in `[0,m)`. For subtraction, `a>=b` returns `a-b`; otherwise
`a+(m-b)=a+m-b` lies in `[0,m)`, so the unsigned addition cannot wrap.

Local `TMPDIR=/var/tmp tools/lean/proof-gate.sh --out ...
verification/pqc-assay/lean/Modarith.lean` exited 0. The audit reported
`PASS`, two theorems, zero failing and zero trusted. Each theorem has exactly
the reported transitive axioms `propext` and `Quot.sound`; there is no
`sorry`, user axiom or `native_decide`. The Lean source SHA-256 is
`83c8a9ec8cd48f0c49d686ad551977d170130b06b726cf0bd002227a89036170`;
the pinned toolchain file SHA-256 is
`d5edba4e4b8faad9c1baeadb265716d20d03be4d1a2647dc5e35b0c0325bea7b`.
The hosted proof gate on this new PR head is still required before merge.

## Hosted static-analysis gate, 2026-10-25

The exact-head hosted rerun at `1d3023db770cd51de10f31c32bf990a564c59c48`
passed the assay, Lean corpus/source, and general CI checks, but its
repository-wide `analysis` workflow failed `clang-tidy` and `cppcheck`. The
unchanged base-main analysis run used Ubuntu 24.04 with clang-tidy 18 and
cppcheck 2.13; this rerun used Ubuntu 26.04 with clang-tidy 21 and cppcheck
2.19. The newer versions reported 36 candidate warnings in untouched C files.
See the linked [runner drift problem](../../problems/static-analysis-ubuntu26-tool-drift.md)
for exact run IDs, scope, and the required triage. This does not change the
local Lean or SAW receipts; the PR's full code-validation gate remains red and
no merge is claimed.

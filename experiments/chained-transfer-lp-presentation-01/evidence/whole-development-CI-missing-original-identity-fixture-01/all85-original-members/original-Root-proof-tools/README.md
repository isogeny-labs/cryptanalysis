# Lean proof gate

`proof-gate.sh` checks every Lean target in the repository. CI runs it through
[`lean-proof-gate.yml`](../../.github/workflows/lean-proof-gate.yml): on any
change to a `.lean` file, lakefile, toolchain or manifest, on pushes to `main`,
and weekly.

| target | how it is checked |
|:--|:--|
| Lake project (directory with `lakefile.toml` / `lakefile.lean`) | `lake exe cache get` if it uses Mathlib, then `lake build` plus each tracked proof source as an explicit Lake source target, then an audit of every module the project built |
| Lake project (directory with `lakefile.toml` / `lakefile.lean`) | `lake exe cache get` if it uses Mathlib, then `lake build`, then explicitly build every tracked project `.lean` source as a `+Module` target, and audit every built module |
| standalone `.lean` file outside any Lake project | `lean -o` against the core library under its directory's `lean-toolchain`, then an audit of that module |

The retained first attempt at
`research/isogeny_world_frontier_20261016/replay-optimization-v1/implementation-01/Newton.failed.lean`
is one explicit negative control. It stays in `--list` and its source SHA-256
is pinned in `proof-gate.sh`. The gate compiles it with the repository's pinned
Lean toolchain and accepts only exit status 1 with its single recorded
`lean.unknownIdentifier` error for `Int.mul_two`. A changed file, successful
compile, timeout, or different diagnostic fails the target. The corrected
`proof/Newton.lean` remains a separate positive target subject to the normal
build and axiom audit. `PASS_expected_failure` certifies only that the frozen
historical failure reproduced; it is not a theorem proof.

The audit, [`AuditAxioms.lean`](AuditAxioms.lean), imports the modules and
collects each theorem's **transitive** axioms. Only `propext`,
`Classical.choice` and `Quot.sound` are accepted. A grep cannot do this
check, because a `sorry` or axiom can be several imports away.

The gate supplies the trust-manifest path to the audit program through
`LEAN_AUDIT_TRUSTED_FILE`. This keeps its command-line arguments as module
names, including under Lean 4.19, whose CLI rejects a `--trusted` argument
after `--run`. CI installs each target's pinned toolchain before the proof
step and retries only transient installation failures; an axiom or build
failure remains a failure.

| outcome | meaning |
|:--|:--|
| `ok` | kernel-checked on the standard foundations |
| `TRUST` | closed by `native_decide` (the compiler is trusted, not only the kernel), and listed in [`trusted-native.txt`](trusted-native.txt) with the reason and where the study records that decision |
| `FAIL` | `sorryAx`, an unlisted `native_decide`, or any other axiom |

A target also fails when it doesn't build, when its build log reports
`declaration uses 'sorry'`, or when it contains no theorems. A gate that
audits nothing must not pass. A failure to fetch the Mathlib cache exits 3. It
is an infrastructure failure and never evidence about a proof.
Tracked project sources that Lake cannot build as module targets fail the gate
as `FAIL_source_build`; they cannot silently disappear behind `defaultTargets`.
Project `lakefile.lean` configuration and dedicated `AxiomAudit.lean` scripts
are excluded from this source enumeration. The separate self-test project is
excluded from normal repository discovery because its deliberately false
theorem must be rejected by the self-test.

```sh
tools/lean/proof-gate.sh --list                  # what would be checked
tools/lean/proof-gate.sh                         # check everything
tools/lean/proof-gate.sh research/<study>/lean   # one target
tools/lean/proof-gate.sh --out receipts          # keep build and audit logs
```

## Self-test

[`selftest/run.sh`](selftest/run.sh) runs the gate on known fixtures:
`selftest/pass/` must pass (`Good.lean` is plain kernel proofs,
`Trusted.lean` is a listed `native_decide`), and `selftest/fail/` must fail
(a transitive `sorry`, a user axiom, an unlisted `native_decide`, a file with
no theorems, a build error). The `project-omitted/` fixture registers a module
outside its Lake default targets and requires the gate to catch its `sorryAx`.
The same control runs with canonical, leading `./`, and trailing `/` project
paths. Targets are normalized against the repository root with Python 3 before
module names or archived-control exclusions are derived; paths outside the
checkout are refused. Python 3 is therefore required alongside Git and Lean.
CI runs it on every trigger, so the gate stays
exercised even in a repository with no Lean proofs yet. The CI matrix covers
the repository's pinned toolchain and Lean 4.19, used by the SEA project.
`LEAN_GATE_TRUSTED`
points the gate at another trust manifest. The self-test uses its own one.

The audit invocation separates compiler options from program arguments with
`--`; the auditor accepts both toolchain conventions for forwarding that
separator. Cache-download failures retain `cache.log` and an `INFRA_cache`
status under `--out`, while still exiting with infrastructure status 3.

## What passing does not mean

The gate shows that each theorem is proved from the standard foundations. It
does **not** show that the Lean statement is the report's theorem. That
fidelity check (quantifiers, hypotheses, the bridge to the real objects) is
still the proof map and review AGENTS.md requires.

## Adding to `trusted-native.txt`

Only add an entry when the study itself records the decision to trust the
compiler, for example a registered replay. Never add one for a theorem a
report or paper states as proved. Prefer `decide` or `decide +kernel` when
they finish in reasonable time.

The gate checks tracked project sources omitted by default targets. Unregistered
source targets compile directly with the project environment into private
olean output and receive the same axiom audit; frozen Lakefiles need no edits. `sources.log` records the inventory. Nested projects are
checked separately; Lake configuration and gate code/fixtures under
`tools/lean` or `tools/selftest` are explicit exclusions. Untracked files
are outside repository discovery. The self-test exercises unconfigured true/false and configured
positive/negative project modules. A green default build alone
is insufficient.

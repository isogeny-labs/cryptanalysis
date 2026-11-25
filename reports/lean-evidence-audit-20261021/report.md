# Lean evidence inventory — 2026-10-21

**Scope.** Audited the cryptanalysis main tree at
`d1a10f6d537dc4e9b5aff02c1e4dcef3e2267c1b`, then added a root Lean
toolchain pin and a read-only source/receipt audit. A subsequent local replay
compiled all 93 tracked Lean files in this repository. It is not a semantic
review of every theorem or experiment in the three requested repositories.
No new scientific trial or performance measurement was run.
[The diagram](diagram.svg) separates these validation layers.

**Delivery:** Git smart HTTP returned HTTP 403 (“Your repository is disabled”)
on October 21. On October 22, `git ls-remote` succeeded at current main
`7bcc0bf05f51132e74637657275420f1e71f72ff`, and the audit branch was
pushed successfully. The [access problem record](../../problems/cryptanalysis-git-remote-rejects-push.md)
preserves the failed and successful observations. The branch integrated that
main in merge commit `94a38d8b26931e4f9cbcd223ef6a6a2fba864bb9`; none
of its 93 Lean source files or dedicated receipts changed across the merge.
The [merged-tree metadata audit](evidence/corpus/merged-main-audit-20261022.json)
still reports 93 files, zero unpinned, 13/13 matching receipt hashes, and zero
forbidden tokens. Hosted CI and review are separate from this local evidence.

## Observed inventory and correction

The main tree has **93 tracked Lean files**. Before this change, 33 inherited
no `lean-toolchain` from their source directories or the repository root.
The new root pin is `leanprover/lean4:v4.34.1`; it leaves local pins in force.
After the change, 92 files resolve to Lean 4.34.1 and one binary-genus-2
module retains its local Lean 4.24.0 pin. A version pin makes a proof
reproducible; it does not make an unbuilt proof valid.

The new [`audit_lean_evidence.py`](../../tools/audit_lean_evidence.py) reads
tracked files, including files omitted by a sparse checkout. It checks each
effective pin, scans source code outside Lean comments and strings for
`sorry`, `admit`, `sorryAx`, `native_decide`, or custom `axiom` tokens, and
checks each dedicated `*lean-receipt.json` source SHA-256 and toolchain claim.
It found **0 missing pins, 0 files with those tokens, and 13/13 matching
source receipts**. The [CI workflow](../../.github/workflows/lean-evidence-audit.yml)
runs this check on relevant proof-source and receipt changes. This is a static
check; the actual Lean compiler and axiom audit remain authoritative for a
theorem verdict.

Two files have no `#print axioms` in that file:
[`OrbitPairIndex.lean`](../../experiments/orbit-quotient-summation/lean/OrbitPairIndex.lean)
is audited by its sibling `AxiomAudit.lean`, and
`SplitPrime12211NearestSelector.lean` is imported through
`ProofAudit.lean`. The local scan flags them for that separate review instead
of silently treating file presence as proof. The new audit has five parser
controls for comments, strings, split tokens, and a real `sorry`; all passed.

## Live proof and code checks

| Check | Observed result | Limit |
|:--|:--|:--|
| Complete tracked Lean source corpus | **93/93 files compiled locally** on their effective pins; [source-by-source index](evidence/corpus/cryptanalysis-corpus-index-20261021.json) | Compilation checks the declarations in those files. Printed axiom sets were restricted to `propext`, `Classical.choice`, and `Quot.sound`; source-to-claim fidelity is separate. |
| Pinned experiment receipt scripts | **13/13 passed**, covering 28 distinct Lean files; [run summary](evidence/corpus/experiment-checks.json) | Two scripts have no Lean source row; the other scripts build their named sources and compare pinned axiom receipts. Original hardware was not reproduced. |
| Standalone dependency chains | **17/17 mixed-radix**, **24/24 independent core**, and **19/19 dependent split-prime** sources compiled with matching, allowed [axiom printouts](evidence/corpus/) | `SplitPrime12211NearestSelector.lean` has no local print; the dependent `ProofAudit.lean` printed its selected-bound axiom set. |
| Direct and Lake projects | `GaugeTree` and `OrbitCompression` rebuilt; orbit project and Lean 4.24 binary-genus-2 project built; [orbit audit](evidence/corpus/cryptanalysis-orbit-audit-20261021.log) and [binary build](evidence/corpus/cryptanalysis-binary-genus2-build-20261021.log) retained | The orbit audit covers `OrbitPairIndex`; the binary theorem has a nonzero-denominator hypothesis and does not model a complete genus-two/Jacobian construction. |
| Archived point/model receipts | **Six 512-row calibration/holdout checks matched** their frozen receipts; [orbit](evidence/corpus/cryptanalysis-hex-orbit-replay-20261021.json) and [DAG/work-depth](evidence/corpus/cryptanalysis-hex-dag-workdepth-replay-20261021.json) results retained | They check archived points and model counts, not fresh timing, independent scalar replay of all research, or attack performance. |
| Dedicated receipt source hashes | 13/13 match committed Lean bytes | A matching hash does not prove a theorem; the live compiler replays above supply the local proof check. |

The source-bound [corpus index](evidence/corpus/cryptanalysis-corpus-index-20261021.json)
and [raw replay scripts and logs](evidence/corpus/) document this local
93-file check. The two files without a local axiom print were covered by
`AxiomAudit.lean` and `ProofAudit.lean`. These gates validate compilation and
the recorded axiom checks, not the meaning of every research theorem.
The [initial](evidence/corpus/cryptanalysis-check-replay-20261021.json) and
[retry](evidence/corpus/cryptanalysis-check-retry-20261021.json) traces also
retain sparse-checkout failures and three data checkers invoked with the wrong
`--check` interface. After the tracked helpers and native source were included,
all 13 pinned experiment receipt checks passed; the three data checkers were
then run with their protocol-specified fixture and row arguments.

The archived point/model replays found no corrected scientific measurement.
The existing
[`OrbitCompression` result](../../experiments/prime-j0-hex-orbit-materialized-20261013/RESULT.md)
explicitly leaves complete-operation wall time for an isolated host. Its
archived numbers and the orbit quotient reference JSON were not rewritten.
There is therefore no changed performance datum to put into a canonical
performance graph. The new visual shows proof-evidence coverage only.

## Requested scope and status

| Requirement | Status |
|:--|:--|
| Faithful Lean theorems for all historical experiments in crypto, cryptanalysis, and crypto-autoresearcher | **Partial.** All 93 existing cryptanalysis Lean files compiled locally and their available axiom checks passed. Missing theorems for historical claims and semantic proof maps remain open; the companion autoresearcher workspace separately verified 62 present targets. |
| Legitimate implementation and archived results | **Partial.** Six frozen 512-row point/model checks replayed, but complete Rust/Python implementation refinement and historical raw performance replay were not established. |
| Updated graphs and performance dashboards | **Partial.** The previous autoresearcher change refreshed the nine-row N13 dashboard; this change adds an evidence diagram. Other graph sources have no verified numerical correction from this audit. |
| Everything good to go | **Not established.** Code-to-model bridges, empirical performance replay, cross-repository semantic reviews, the crypto PR's full Lean CI matrix, and cryptanalysis remote CI remain open. |

## Reproduction

```sh
python3 tools/audit_lean_evidence.py --json /tmp/cryptanalysis-lean-audit.json
python3.12 experiments/prime-j0-axis152-20261012/check.py --check
cd experiments/orbit-quotient-summation/lean
lake build && lake env lean AxiomAudit.lean
cd ../../../research/binary_genus2_cover_20261014/lean
lake build
cd ../../../
cd experiments/prime-j0-hex-orbit-materialized-20261013
elan run leanprover/lean4:v4.34.1 lean OrbitCompression.lean
cd ../prime-j0-gauge-tree-20261012
elan run leanprover/lean4:v4.34.1 lean GaugeTree.lean
```

The audit output on this change was:

```text
93 Lean files; 0 unpinned; 13/13 receipt hashes match; 0 files with forbidden tokens
Separate axiom audit required for: OrbitPairIndex.lean, SplitPrime12211NearestSelector.lean
```

The [PDF](report.pdf) carries the report and proof-boundary diagram.

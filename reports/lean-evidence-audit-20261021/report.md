# Lean evidence inventory — 2026-10-21

**Scope.** Audited the cryptanalysis main tree at
`d1a10f6d537dc4e9b5aff02c1e4dcef3e2267c1b`, then added a root Lean
toolchain pin and a read-only source/receipt audit. This is not a kernel build
of every theorem or a semantic review of every experiment in the three
requested repositories. No scientific trial or performance measurement was
run. [The diagram](diagram.svg) separates these validation layers.

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
| Lean 4.34.1 `lean OrbitCompression.lean` | PASS; four reported declarations, with only `propext`/`Quot.sound` on the cost formula | Abstract orbit reconstruction and tree cost model; no Rust-to-Lean refinement proof. |
| Lean 4.34.1 `lean GaugeTree.lean` | PASS; five reported declarations, with only `propext` | Gauge-aware tree equations under the explicit group and order-three automorphism premises. |
| Orbit pair-index project | Already built and axiom-audited in merged [PR #1008](https://github.com/aburan28/cryptanalysis/pull/1008), with four independent Python tests | Three-slot modular lookup equivalence; no full elliptic-curve or four-summand certification. |
| Dedicated receipt source hashes | 13/13 match committed Lean bytes | Receipts were checked for source identity, not independently replayed on their original hardware or toolchains. |
| Lean 4.24 binary-genus-2 module and remaining Lean files | **Not built in this change** | Pin and lexical checks alone are not kernel validation. |

The examined orbit quotient and prime-j0 work in this report did not create
a corrected scientific measurement. The existing
[`OrbitCompression` result](../../experiments/prime-j0-hex-orbit-materialized-20261013/RESULT.md)
explicitly leaves complete-operation wall time for an isolated host. Its
archived numbers and the orbit quotient reference JSON were not rewritten.
There is therefore no changed performance datum to put into a canonical
performance graph. The new visual shows proof-evidence coverage only.

## Requested scope and status

| Requirement | Status |
|:--|:--|
| Faithful Lean theorems for all historical experiments in crypto, cryptanalysis, and crypto-autoresearcher | **Partial.** Existing modules were inventoried, pins and receipts checked, and three representative modules were built across the prior and current slices. Exhaustive theorem builds and semantic proof maps remain open. |
| Legitimate implementation and archived results | **Partial.** Two proof models were replayed; the complete Rust/Python implementations and historical raw results were not independently replayed by this metadata audit. |
| Updated graphs and performance dashboards | **Partial.** The previous autoresearcher change refreshed the nine-row N13 dashboard; this change adds an evidence diagram. Other graph sources have no verified numerical correction from this audit. |
| Everything good to go | **Not established.** Full kernel, code-to-model, empirical replay, and cross-repository claim reviews are still required. |

## Reproduction

```sh
python3 tools/audit_lean_evidence.py --json /tmp/cryptanalysis-lean-audit.json
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

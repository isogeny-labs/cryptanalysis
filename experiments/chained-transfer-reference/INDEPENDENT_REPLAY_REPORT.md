# Independent source replay and complete input closure

The isolated replay at crypto commit `0796b36df6ee9712bfa335d81191abc26ed937ce`
passes all 32 standalone tests, all 23 algebra tests, both byte-identical
certificate comparisons, and all 32 Lean modules. The proof gate reports
186 compiled theorems, 160 written declarations and zero trusted native
evaluation. All 695 protected source files and eight consumer driver subjects
retain their pre-run hashes. Consumer claim `PCC-20261112-db5e8a` and root
mirror `PCC-20261112-868a06` record the result; standing is unsigned.
[pcc:unverified]

This change adds a second exact upstream pin and a separate 20-minute CI job.
The original source pin `75a737b8366ec6c78ed8672886423fcbe69853a2`, all 13
reference Rust sources, `check.sh`, and the original 75-minute reference job
remain unchanged. Its fixed parent is ready PR1508 at `c7128485`; parent CI
43202427032 passed 25 native and 98 reference tests plus five integrations,
with one historical ignored benchmark. Claim700efe records the corrected
249,037-byte UTF8 log count; earlier1976fd and its explicit correction remain.
The new child must pass its own complete reference and independent jobs.
[pcc:unverified]

| Requirement | Result and evidence |
| --- | --- |
| Exact source and clean inputs before execution | Wrong HEAD and dirty JSON fixture both reject with exit2 before output creation; positive03 checks exact0796 and protected Git state. |
| Complete independent native corpus | 32 passed, no failed/ignored/filtered tests; formatting, strict Clippy, old source guards pass. |
| Existing native identity checker | 23 passed, no failed/ignored/filtered tests; `--locked` retained; exact duplication/halving certificates replay. |
| Reproducible formal checks | 32 passing modules, 186 compiled theorems, 160 written declarations, zero trusted native evaluation. Actual geometric realization remains partial upstream. |
| Source and raw custody | All695 upstream and8 driver hashes unchanged; one125-file tar.xz54,612bytes, per-file SHA256 and exact roundtrip. |
| Failed attempts | Whole first/second run trees retained as separate standard tar.xz with hashes/statuses; neither accepted as a complete replay. |
| Own child CI | Required after publication; no completion asserted here. |
| Scientific standing | Unsigned; no producer receipt, local proof check or green CI supplies independent signing. |

All rows have claimdb5e8a or the explicitly linked failure/parent claims as
their evidence. The complete raw tree is
[independent-positive-03](evidence/independent-positive-03/custody.json).
The [diagram and PDF](reports/independent-replay/report.pdf) show execution
coverage rather than a performance comparison. [pcc:unverified]

## Preserved failures and exact fixes

Attempt01 at16c passes32 standalone tests and exits101 at `cargo fetch
--locked`: the already tested Cargo.lock was globally ignored and absent from
Git. Algebra tests and proof stages did not run. Claim56d812 retains the
whole14-file tar.xz40,092bytes and its custody. Commitdd03 tracks the exact
tested2,888-byte lockfile with a package ignore exception. No dependency
version, native mathematical code, or test criterion changed.
[pcc:unverified]

Attempt02 atdd03 passes32 standalone tests, then exits101 during algebra
all-target compilation because the imported identity checker includes
`docs/identity-certificates/schoenhage-10mult.json`, absent from the sparse
worktree. The fixture already existed in Git at blob
`8a17c8270bbb6c2ffee6c3cddf6ccd5c2093586e`. Algebra tests and proofs did not
run. Claimd11dfb retains the whole14-file tar.xz41,040bytes. Commit0796 adds
that unchanged fixture to both sparse manifests and the checksum/protected
input guards. A literal-input audit covers the two Rust imports, two Lean
sources and this JSON fixture; other file operations write explicit outputs.
[pcc:unverified]

Attempt03 at0796 runs the entire original acceptance again and exits0.
Protocols V1/V2 and all failed evidence remain immutable; V3 specifies the
final input closure. The run started13:40:42 and finished13:44:19UTC on
2026-11-12. These timestamps describe custody, not a benchmark: compilation
caches were reused and there was no timing protocol or isolation claim.
[pcc:unverified]

The original reference source guard, old98 acceptance and upstream mathematical
graphs remain current: this PR changes orchestration and source closure.
Upstream reports/two-primary and reports/quartic-gluing were checked for scope;
their mathematical graph topology and values need no change. New diagrams
describe only replay01/02/03 and preserve NOT RUN states.

## Reproduction and scope

Install Rust1.99.1 (rustfmt and Clippy) and Lean4.35.0. Check out this consumer
child and crypto0796 in a separate clean worktree with the workflow's explicit
sparse inputs, then run `bash experiments/chained-transfer-reference/check-independent.sh
/path/to/crypto-independent /path/to/new-output-directory`. The output directory
must not exist. The driver records all protected Git inputs before execution
and checks every hash and Git state after the native/proof stages. It runs
the unchanged existing Rust engines and Lean gate; it introduces no new
cryptographic implementation or external Python/JS/Go arithmetic oracle.

Sources checked (KB): no MCP KB tools are loaded; the repository wrapper
reports no executable. Fallback sources are the accepted exact-source root
protocols, proofs492496/933d35, native956a3e/algebrae13811, existing CI manifests,
and the imported checker's literal source inputs. Root PR3877 comments and
external PR1502cc5d5541 were reviewed for adjacent CT43/44 work; this integration
does not assert or duplicate their abstract graph results. There is no novelty
claim. [pcc:unverified]

Ready child base is the immediate1508 feature branch. Integrate bottom-up,
retarget and rerun after parents land. Frozen ledger forks, parent1484 source
conflict/C findings, scientific signing, live budget/S3 admission, and the
locked atlas remain open. Local build/proof correctness is the scope of this
checkpoint. Next research is bounded actual elliptic continuation and gluing
closure, after primary-source review. [pcc:unverified]

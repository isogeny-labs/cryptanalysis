#set page(paper: "a4", margin: 17mm)
#set text(font: "DejaVu Sans", size: 9pt)
#set par(justify: false)
#set heading(numbering: none)
#align(center)[#text(size: 19pt, weight: "bold")[M31 recovery, end to end]\
#text(size: 10pt)[2026-11-27 · Isogeny Labs · local producer observations · pcc:unverified]]

The selected direct two-point pipeline recovered *5/5 fresh targets* at a median *71.356 ms cold*, range 54.148–110.804 ms. Setup, relation collection, signed elimination and full certificate replay are charged. On those same targets its geometric-mean cost was 0.316790 of m3 and 0.324465 of m4. This is an exploratory shared-host result, with no admitted isolation tier or signed independent verdict. [pcc:unverified]

*Exact instance:* Fp, p=2147483647=2^31−1; y²=x³+2x+14; N=2147505293; G=(1,814455902). The native worker receives Q by coordinates alone; evaluator scalars stay separate. There is no rho fallback or planted decomposition. [pcc:unverified]

#image("pipeline.svg", width: 100%)

== Usable fast path
#raw("cargo +1.88.0 build --locked --release \\\n  --manifest-path crates/prime-field-auxiliary-ic/Cargo.toml \\\n  --example m31_e2e\nscripts/m31-fast 2144058214 807222724 --seed 1", block: true)

Defaults: B256 interval base, m2 signed lookup, 64 lanes/chunk, four million queries and five-second soft online cap. JSON includes explicit status, scalar when recovered, complete certificate, base points and costs. Other targets/seeds can reach the bound. The standard CLI supports auxiliary --pair-index --summands 2. Fixed lab curve only. [pcc:unverified]

#image("m2-cold.svg", width: 100%)

#text(size: 8pt)[Follow-up run 20261127T1801Z-m31-e2e-m2; five independent fresh targets, paired arms, A/A repeats. All four IC arms recover all five. Lines connect target indices, not a scaling model. Native cold milliseconds. [pcc:unverified]]

#pagebreak()
== What integration changed
*Targets and signs:* retain every signed pair witness by canonical x, reuse ± target successes, and replay fresh witnesses. *Staging:* one target-independent table supports m2, residual m3 and balanced m4; actual development selected direct m2 lookup. *Explicit addition:* complete native numerical addition handles inverses, doubling and identity intermediates with batched inversions. *Partial relations:* the full signed sparse matrix cancels columns modulo N; all ambient columns remain priced. *Bases:* interval won the first interval/random/torus comparison; a separate m2 size comparison selected B256. Binary trace and Koblitz orbit shortcuts do not apply to this prime-field curve. [pcc:unverified]

The solver reuses the original sampler, arithmetic, elimination and strict certificate verifier. Existing suite batched MITM m2/m3 is prior native code; this is integration and reusable witness engineering, not a new MITM algorithm. Polynomial/F4 variants remain measured diagnostic competitors rather than extra hidden query stages. [pcc:unverified]

== Separate frozen panels
First run: 46 planned, attempted and reported; zero excluded. Twenty development/base cells selected B512 m4 on two old targets, then five fresh targets were generated after committing selection and analysis. Primary/A/A/m3 recovered 5/5 each; same-base direct search recovered 0/5 within its soft cap. First-panel median was 215.426 ms. Selected/m3 geometric mean 1.039258, conditional95% interval [0.902952,1.169314]: no demonstrated gain over optimized m3. A/A range 0.751249–1.189347. Development overlapped a CLI build; held-out timing did not. [pcc:unverified]

Follow-up: 32 planned, attempted and reported; zero excluded. A new protocol/seeds froze six development cells before timing. B128 missed one old target at4M queries; B256/B512 completed both. B256 selection and analysis were committed before creating five fresh target coordinates. The exact original release worker binary was reused. Twenty held-out IC cells, five rho references and one separate profile complete this panel. Do not pool the two panels. [pcc:unverified]

#table(columns: (1fr, 1fr, 1fr, 1fr, 1fr), inset: 5pt,
 [Target], [m2 ms], [A/A ms], [m3 ms], [m4 ms],
 [0],[110.804],[92.380],[293.205],[218.689],
 [1],[54.148],[58.414],[220.240],[266.458],
 [2],[71.356],[66.510],[190.329],[197.441],
 [3],[63.935],[64.999],[202.224],[249.395],
 [4],[79.944],[77.212],[275.948],[212.068])

Family-adjusted conditional bootstrap ranges for m2/reference: m3 [0.267169,0.364080], m4 [0.238859,0.446374];10000 resamples, seed1729, per-comparison1.25/98.75 percentiles. Derived reciprocal ratios are3.157x and3.082x on this panel. A/A ratios0.833721–1.078774. Follow-up rho recovered5/5, median reference-call1.934125ms; m2 cold/rho call geometric mean44.703210. Boundaries differ and rho remains faster. [pcc:unverified]

#image("costs.svg", width: 100%)
#text(size: 8pt)[Left: first panel only. Right: follow-up primary cold clocks with full setup, search, replay and teardown. No cross-panel speed ratio. Source: both manifests and summaries. [pcc:unverified]]

#pagebreak()
== Correctness, accounting and preserved failures
Cold starts at main entry and includes parsing, base/group/table construction, search, elimination, internal certificate verification, an additional full replay, proof serialization preparation and math teardown. Runtime startup/final stdout are excluded; watchdog wall time includes them. No pair table is reused across target processes. B256 constructs65536 signed pair witnesses and checks reservation before allocation. [pcc:unverified]

Native tests include every108 nonzero finite-control target for each m2/m3/m4, exceptional point additions, identity pair intermediates, wrong-base/foreign-scratch rejection, resource guards and signed cache recovery. Existing pipeline/multi tests remain. Standard CLI tests cover cold setup accounting, legacy m2 JSONL replay, conflict/reservation rejection and solved exit status. [pcc:unverified]

Second-arithmetic replay via ic_boundary::PrimeCurve checked all ten primary certificates:2372 first-panel rows and637 follow-up rows, full row equations, scalar equations and signed column cancellation. Wrong-scalar and wrong-weight mutations were rejected. This is producer supplemental replay; no independent signed verification is asserted. [pcc:unverified]

The first evaluation launcher exited1 after misparsing pretty JSON from a rho shell. The complete native output and raw log were retained; a parser fix resumed remaining frozen cells without repeating any completed process. Earlier CLI compile/fixture failures are retained; test placement was corrected and exact tracked sparse fixture blobs restored. No test or verifier threshold was weakened. [pcc:unverified]

Rho shells retain incomplete one-query IC status and exit1, despite solved rho subreports; watchdog label “crashed” means that status here, not an OS crash. Direct soft deadlines are checked between batches: incomplete cold costs about5.95–7.82s for a5s online cap. No cell hit the independent20s/2GiB watchdog. One m2 development target reached its query cap. All outcomes are retained. [pcc:unverified]

Phase profiles are separate diagnostics. The m2 profile performs5.45million clock reads and takes243.030ms versus85.382ms uninstrumented on that old development target. Clock overhead prevents interpreting its phase percentages as uninstrumented costs. perf/valgrind were unavailable; no PMU claim is made. [pcc:unverified]

== Provenance and scope
Worker execution source bfa695d0c5963a2bbdb6a59766683188a40df8f4; SHA256:
#raw("ee67b81916a6a762af01e781a4ae72af6faee98c7e5715663444c60138f1d067", block: true)
First selection/analysis a52ce2f; follow-up protocol c94c0b7, runner0f5ec2d, selection/analysis67f5e90. RESULTS.json binds manifests, full summaries and replay receipts. Local original commits survive in the delivery source bundle. All78 native reports and failure logs remain in the local archive. [pcc:unverified]

AMD EPYC9V74, x86-64 Linux container, five allowed CPUs, one exposed CPU pinned, portable scalar CPU path, no GPU. Physical RAM type/speed, physical-host exclusivity and provider allocation receipt are unknown. hardware.json records observable topology/cgroups after evaluation; process CPU-time and NUMA placement were not captured. User authorized local execution/storage; no S3 upload is asserted. Artifact admission remains open. [pcc:unverified]

Full source-linked narrative, exact commands, limitations and requirement/evidence table: REPORT.md. Raw evidence: manifest.json, summary.json, replay.json and m2/ counterparts. Local delivery: /workspace/isogeny-m31-e2e.zip. Source PR cryptanalysis#2005, stacked on#2002; workspace#192. No new PCC claims, general scaling result or rho victory is asserted. Canonical scoreboard/curve-route graphs remain unchanged because the exploratory records lack admission; study graphs and unqualified progress metrics carry this result. [pcc:unverified]


Initial delivery checkpoint (18:12 UTC): the inherited PCC ledger fails at entry3583 (seq3535);
HEAD has exactly the parent ledger bytes and pcc/ is unchanged. Missing
artifact uploads also fail the global publication gate. No push/merge or
ready transition was attempted at that checkpoint. Original source commits
and outputs were delivered locally; the PRs were tracking drafts.
[pcc:unverified]


#pagebreak()
= Completion update: usable command and saved-proof checking
The final source reconciles the separately published pair-root acceleration
checkpoint with the prospectively measured B256/m2 indexed path. Both studies,
protocols, source histories and original outputs remain separate. The original
71.356ms median is a frozen worker measurement; the new wrapper's builds,
process startup, file emission and extra checker are not relabeled as that
clock. No new performance claim is made by these correctness controls.
[pcc:unverified]

One command now rebuilds current source, recovers from coordinates, saves a
new complete certificate and checks it through the original strict verifier
and a second native arithmetic implementation:
#raw("scripts/m31-complete 2144058214 807222724 \
  --out recovery.json --seed 1", block: true)

The saved certificate can be checked separately and bound to the intended
public target:
#raw("scripts/m31-verify recovery.json \
  --qx 2144058214 --qy 807222724", block: true)

Existing destination files are refused atomically. A valid checked recovery
returns0; a bounded incomplete report is saved and returns1; invalid worker
arguments/points return2 without a panic. The checker rejects an incomplete
or malformed report, incorrect scalar, signed column, weight, missing or
duplicate row, wrong curve and substitution of another target.
[pcc:unverified]

The merged native library passes45 release tests and its documentation test.
Clippy all-targets with warnings denied passes after installing the declared
component; no lint was disabled. Two verifier tests check a complete nontrivial
three-row dependency and corruption controls. Twenty-four executable controls
pass against a clean native build in a separate target directory. The combined
command recovers and checks the public example, and the overwrite control
preserves its existing file SHA256. Normal auxiliary CLI and exit checks
are retained. These are local correctness checks, not signed independent
verification. [pcc:unverified]

The new delivery archive includes both Linux x86-64 executables, a run-complete
entry point, the saved example, both original frozen panels, the other remote
checkpoint's study, original and merged source bundles, build/test/failure logs,
and SHA256SUMS. It can be used without Cargo or network access; source builds
remain available in the owning repository. The earlier archive is retained
unchanged. [pcc:unverified]

Repository-wide PCC/data admission remains separate: the inherited ledger
sequence error and unavailable S3-backed inputs are not repaired by changing
claims or disabling checks. Source parity and local correctness can pass while
these base-branch dependencies prevent merge. The tracking PR records the exact
CI state; no merge or independent standing is asserted. [pcc:unverified]

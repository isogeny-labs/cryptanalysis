#set page(paper:"a4",margin:18mm)
#set text(font:"DejaVu Sans",size:10.5pt)
#set par(leading:0.7em)
= Failed isolated replay01
2026-11-12 · crypto16c9927b · unsigned correctness integration

All32 standalone tests passed. The complete replay exited101 at cargo fetch --locked.
Algebra unit tests and the proof gate were NOT RUN. This is a source input
closure failure, not a failed mathematical assertion. Claim56d812.
[pcc:unverified]

#image("replay.svg",width:100%)
The diagram records executed stages; there are no comparable performance
arms, isolation claim or solver measurements. [pcc:unverified]

== Exact failure and correction
The already tested lockfile was globally ignored and absent from Git. Commitdd03 tracks the exact tested2,888-byte Cargo.lock with a package ignore exception. No dependency version, native code or test criterion changes. [pcc:unverified]

The next attempt executes the complete unchanged acceptance again. The first
and second failures remain immutable; accepted replay03/db5e8a at0796 is a
separate checkpoint and does not replace this evidence. [pcc:unverified]

== Raw custody and source integrity
The whole14-file raw tree is preserved as one40,092-byte standard tar.xz,
with every raw file's SHA256, transcript, source snapshots, before/after
guards, status and exact roundtrip. Raw evidence: ../../evidence/
independent-failed-01/custody.json and raw-tree.tar.xz. The run's frozen
protocol and source pin remain archived. No filtered criterion or test was
removed; --locked stays required. [pcc:unverified]

Sources checked: the repository's frozen protocol, exact native/checker source
and literal imported inputs. KB MCP is absent and the wrapper unavailable;
fallback review is limited to those sources. Read ../../INDEPENDENT\_REPLAY\_REPORT.md
for the three attempts, original reference98 preservation and reproduction.
The upstream mathematical graphs remain current; this report updates only
source closure and execution flow. [pcc:unverified]

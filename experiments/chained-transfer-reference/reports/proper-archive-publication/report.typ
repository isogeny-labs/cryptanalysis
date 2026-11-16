#set page(paper:"a4",margin:17mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(leading:0.6em)
#set heading(numbering:none)
= Proper replay archives: publication addendum
2026-11-12 · actual trusted-base migration · unsigned

Both complete original raw archives were uploaded and replayed by the
existing artifact-autofix workflow. Exact bot5bec81e36ac9b6f7b91ddc5437766248bf7aacfe
adds real manifests/ignore and removes only these two tracked archives.
The local branch fast-forwards to that exact bot commit. [pcc:unverified]

#image("publication.svg",width:94%)

Run43319185494/job131535060041 succeeds. The whole log explicitly records
two remote objects replayed before the normal push. Its entire425602-byte
UTF8 output is preserved as standardXZ with raw/archiveSHA256 and exact
roundtrip. Actual artifact and workflow-wiring checks both return0.
The manifest's complete hashes match both intact local originals.
[pcc:unverified]

This addendum supersedes only raw-publication-pending status. Failed01
remains NOT accepted;complete full02/400f38 remains LOCAL acceptance.
Original reports,claims,custody,receipts and source snapshots remain
immutable. No tree was split/pruned,no policy/bypass label changed,and
the previous no-op job is not used as upload proof. [pcc:unverified]

Sources:REPORT.md links the full job/API/custody,canonical manifest at
immutable crypto5bec81e,exact full hashes/content-addressed S3 keys,
original handoff and documented docs/artifacts.md mechanism. Consumer
PR1517 links these canonical objects;its old three jobs remain unchanged.
These archives are report evidence,not runtime replay inputs.
[pcc:unverified]

The diagram shows custody flow,not a cost comparison. Prior scientific
graphs/IC timeline/scoreboard stay unchanged. No new mathematical claim,
benchmark,leaderboard row or scientific signature follows. [pcc:unverified]

# Whole report storage with the original PCC hydration path

Prospective,2026-11-13,before moving the final report file. The final
69377-byte PDF/d1027f stays byte-identical;no report content,claim pin,
policy,workflow,gate,verifier or trust changes. [pcc:unverified]

The unchanged PCC workflow hydrates managed data under docs before
verifying every claim. It does not hydrate arbitrary new experiment
report paths. Therefore use a canonical genuine managed whole PDF at
docs/research-artifacts/chained-transfer/new-target-IC-01/report.pdf,
and preserve the original research report path as a small relative Git
symlink to that canonical file. The original PCC subject resolves to
the SAME whole PDF bytes;both paths and the symlink target are guarded.
The canonical directory is outside existing PDF keep exceptions.
[pcc:unverified]

Publish the whole PDF through the unchanged genuine root data publisher
as an explicitly named raw binary carrier,new-target-IC-final-report.pdf.bin.
The root repository keeps .pdf files in Git,but the consumer requires
this whole PDF in S3. A .bin carrier applies the original stricter data
threshold to exactly the same PDF bytes;no format conversion,compression,
splitting,pruning,policy edit or size-threshold change is permitted.
The manifest projection uses the canonical documentation PDF path only
AFTER actual original remote byte replay;no synthetic S3 manifest.
[pcc:unverified]

Record full source/carrier/canonical-PDF hashes,all closed capture/index
roundtrips and NEWcurrentguard07 before normal publisher FF. Preserve
both repositories' owned dirty bytes and link types. Require original
artifact verification and the unchanged original PCC report-pin result
to remain unsigned not_covered2 with no failure,plus an independent
clean CI hydration. An absent/substituted PDF must still fail. Keep the
actual large file and complete raw originals;do not reduce the report
to evade policy. [pcc:unverified]

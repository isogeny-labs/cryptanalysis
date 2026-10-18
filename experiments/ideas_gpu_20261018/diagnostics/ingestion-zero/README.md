# Additive zero-length ingestion qualification

Run-1's 1,719 paired reports contain six native-valid zero-length trails at record indices 0, 1, 2, 862, 1082 and 1504. All six are on the public curve, inside DP46, in run53180's seed namespace, paired consistently between DP32/DP64 and independently reproduced as exact golden-model start points. See `actual.stdout` and the separate native scan `zero-scan.jsonl`.

The original v1 ingestion predicate `iters > 0` rejects these valid native reports. This is an overstrict ingestion assumption, not a GPU arithmetic or report-validity failure. `v1-rejects-valid-zero.{stdout,stderr,exit}` preserves the original rejection on an actual extracted zero report. Prior frozen evidence/source remains unchanged.

New `../../ingest_control_v2.cpp` accepts zero only after every existing seed/format/public-curve/canonical-coordinate/weight/DP32-pair check, and then independently rewalks **every zero**, unconditionally. Zero replays do not consume the first-eight eligible positive-trail budget. Positive upper length bound 2^32 and replay selection remain unchanged. The retained corpus passes all1,719 checks, all6zero replays and8positive replays <=512;1,705 positive trails remain unreplayed. This does not claim independent replay of every positive trail.

The extracted valid-zero fixture passes even at max_replays=0/max_steps=0, demonstrating the zero check cannot be disabled by those positive limits. The paired negative changes the seed low bit in both DP32/DP64 while preserving the endpoint and zero length; it passes earlier structure/curve/weight/pair checks then fails specifically with `zero-length golden-model start-point mismatch`. The positive fixture passes; its coordinate-tamper negative fails. All original/negative stdout, stderr, exits, inputs and command lines are retained. `protocol.json` was frozen before validation; `frozen.sha256` verifies original v1/source/raw inputs unchanged.

Native semantics: `source/tree/ecc2k130/src/hostcheck.h` referenceReport checks i=0 before a step; rewalk performs zero steps and compares exact x/y. `cpuwalk.h` revive records now-start, which can be zero when an initialized/restarted seed is already distinguished. Source/code review plus the independent native diagnostic scan confirm the retained cases.

Compilation from repository root:

```
cc -O2 -c experiments/ideas_gpu_20261018/source/tree/fpga/model/ecc2k130.c -o experiments/ideas_gpu_20261018/diagnostics/ingestion-zero/model.o
g++ -O2 -std=c++17 -DECC_WALK_TABLE=0 -Iexperiments/ideas_gpu_20261018/source/tree/ecc2k130/src experiments/ideas_gpu_20261018/ingest_control_v2.cpp experiments/ideas_gpu_20261018/diagnostics/ingestion-zero/model.o -o experiments/ideas_gpu_20261018/diagnostics/ingestion-zero/ingest-control-v2
bash experiments/ideas_gpu_20261018/diagnostics/ingestion-zero/validate.sh
```

Parent/root owns prospective cloud protocol admission, whole-pipeline rerun, graph/PDF integration and publication. No cloud or Git action was performed here. These are local native correctness qualifications, without a timing/speed claim.

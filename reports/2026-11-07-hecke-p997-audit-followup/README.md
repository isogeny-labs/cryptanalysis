# p=997 finite-record guard follow-up

Task `T-1796`, source base `65d1b502e9f378ccbca9ee0c1d4c0c70760cde87`.
This source-only follow-up to [the p=997 review](../2026-11-07-hecke-p997-review/report.md)
adds `tools/hecke-432-prime997/verify.py` without editing any sealed
experiment file. It addresses two concrete holes in the archived consistency
audit: a wrong kernel root and incorrect source-j metadata both previously
passed. The new checker rejects those mutations after reconstructing the
finite chain formulas and source key map.

The checked unmodified archive has 17/17 seal entries, 62 generic classes,
1,800 paired chains, 2,306 checked edge occurrences, 72 saved E outputs,
and the 12/24/48 projected histogram (6, 60, 6). Direct B/E point
enumeration gives 1,008 points in each curve and three B preimages for each
saved E output. The exact machine-readable output is [`receipt.json`](receipt.json),
which binds the verifier and input SHA-256 digests. Four control tests passed
in [`controls.txt`](controls.txt).

The third mutation, exchanging two complete source projections, still passes
this guard. That behavior is an explicit negative control: the checker does
not independently recompute the quarter-shift map from each source. The
degree-24 modular-map, reduction and cusp-image bridges also remain outside
this finite verifier. The complete B-image bound retains its conditional
status in the prior review. No new experiment, performance measurement,
Lean theorem or official evidence decision is introduced.

Replay from the repository root:

```sh
python3 -I tools/hecke-432-prime997/verify.py --output /tmp/p997-finite-guard.json
python3 tools/hecke-432-prime997/test_controls.py -v
```

This run used one local CPU for seconds, with no cloud job or new research
cost. The archive remains sealed. The technical review's PDF and graph are
unchanged because this update strengthens only the finite-record instrument.

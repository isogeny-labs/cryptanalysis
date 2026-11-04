# Cryptanalysis current Lean gate reconciliation

The [successful corpus job 41077865188](https://github.com/isogeny-labs/cryptanalysis/actions/runs/41077865188) checked the 97-source historical receipt **and 77 further admitted theorem modules** at `5939def096fd181973e1abb7279644a8aa531557`. Its terminal log line reports `native added theorem modules checked: 77`. All 184 tracked `.lean` paths and Git blob IDs, plus 287 gate, pin, dependency and historical-input paths selected by the [replay verifier](verify.py), match cryptanalysis main `d3673ee089dd2a3a4ba15da087b95ebf2fb8e123`. No new Lean build was run for this packet.

| Exact path group | Files | Gate relationship |
| --- | ---: | --- |
| Historical corpus, unchanged archive | 90 | Bound through the 97-source receipt and archived native evidence |
| Historical corpus, fresh native sources | 7 | Bound through the same receipt and its direct checks |
| Further admitted current theorem modules | 77 | Discovered as additions and natively checked by `current-corpus-gate.py` in the hosted run |
| `tools/lean/` sources outside that corpus selector | 10 | Seven positive/negative selftest examples, two audit modules, one transfer-audit source; their other gates are separate |
| **Tracked Lean source paths** | **184** | **174 in this corpus gate; 10 tool-tree paths outside it** |

The 77 further modules consist of 37 source-pinned quartic certificates, one known-label algebra module, one pair-index module, one Hasse-square module, one XEDNI compatibility module, and 36 other admitted Hecke/XEDNI modules. The [machine result](result.json) lists every path. The [diagram](scope.svg) and visually inspected [one-page PDF](report.pdf) show this exact source-path partition. These are **source paths**, not a percentage of scientific claims or semantic review verdicts.

## Evidence and replay

The packet retains the fetched [GitHub run metadata](run.json) and [compressed complete job log](cryptanalysis-lean-gate-41077865188.log.gz), with their SHA-256 digests in `result.json`. The log was fetched with `gh run view 41077865188 --repo isogeny-labs/cryptanalysis --log`; its compressed archive is below the repository's 64 KiB artifact threshold. The verifier recomputes the 184-file path/blob map at both exact commits, checks the 97-source receipt against the 93-file archived index plus seven fresh paths, classifies the remaining 87 paths, compares the gate-relevant Git blobs, and checks the stored run status and terminal log marker. An altered terminal count is rejected by the retained negative control. Re-run against a repository with both commits available:

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -O \
  docs/reports/2026-10-31-lean-gate-reconciliation/verify.py \
  --repo /path/to/cryptanalysis
python3 docs/reports/2026-10-31-lean-gate-reconciliation/render.py
```

`run.json` and the log are retained observations of GitHub's hosted run, not self-authenticating execution certificates. The current corpus gate checks builds and transitive axioms at admitted source pins; it does not independently review theorem meaning, connect each theorem to its experiment claim, or validate historical experiment execution. The old 97-source receipt correctly described its selected historical bridge. This packet clarifies that the other 77 current theorem modules were separately admitted by the same native gate. The archived receipt and prior reports remain unchanged.

## Prior sources checked

- The committed `tools/lean/current-corpus-gate.py`, `.github/workflows/lean-proof-gate.yml`, `tools/ci/quartic_certificates.json`, historical corpus index, and 97-source receipt at the pinned cryptanalysis commits define the actual discovery and build routes.
- The [Lean proof-validation reference](https://lean-lang.org/doc/reference/latest/ValidatingProofs/) distinguishes a built statement and transitive axiom list from its intended informal meaning.
- [GitHub's workflow-log documentation](https://docs.github.com/en/actions/how-tos/monitor-workflows/use-workflow-run-logs) describes job status and log access; the hosted run is the external execution record cited here.

The existing experiment performance graphs and dashboards have no changed measurement in this reconciliation. The affected visualization is this Lean source-path scope diagram; no performance curve is inferred from proof-gate coverage.

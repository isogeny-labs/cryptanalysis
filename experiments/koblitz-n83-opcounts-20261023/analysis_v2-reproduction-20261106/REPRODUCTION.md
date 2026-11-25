# Reproduction of the v2 analysis outputs (2026-11-06)

Why this exists: sheriff case SHF-20261106-a114e7, finding CAX-3
(crypto-autoresearcher `research/sheriff/SHF-20261106-a114e7/`). The
experiment README and `run_github_39882571652/ARTIFACT.json` say the v2
outputs were "reproduced byte for byte by a second run", but no output,
hash or log of that second run was committed. That 2026-10-23 second run
stays uncited: nothing about it is recoverable here. This directory
records two new runs of the same analysis, made on 2026-11-06, with their
output hashes, so that the reproduction claim now cites something.
`ARTIFACT.json` is an archived receipt and is not edited.

## What was run

Analyzer `experiments/koblitz-n83-opcounts-20261023/analyze_v2.py`, sha256
`426351930389235b0178ba00a2a762ab1533c3c2f1a9eeb40f021fed8a2c8493`
(`sha256sum -c ANALYSIS_V2.sha256`: OK), which imports the frozen `band.py`
(sha256 `4de78e40...6cb3619`, as pinned in `PINS.sha256`). Default 10,000
bootstrap draws.

Inputs, each in a fresh scratch copy of `run_github_39882571652/panel/`
(`run1/`, `run2/`):

- `panel/runs/`, `counts.json`, `band.md`, `opcounts_result.json`,
  `runner_start.json` as committed on `main`.
- `panel/runs.jsonl`, which lives in the artifact store
  (`panel/.artifacts.json`: sha256 `13829d0d...6723d`, 291,368 bytes). The
  AWS CLI was not available in this session, so it was taken from the
  commit that first added it,
  `git show 5a6c233ea161dbaf80c8232945092a98ecf4a744:experiments/koblitz-n83-opcounts-20261023/run_github_39882571652/panel/runs.jsonl`;
  its sha256 equals the manifest's.
- The archived twin's `runs.jsonl`
  (`experiments/koblitz-n83-stacked-20261016/run_github_38862448935/panel/`,
  manifest sha256 `f68af5e3...48d82`), which `analyze_v2.py` reads at its
  repository path, taken the same way from `5a6c233ea`; sha256 equal to its
  manifest. It was placed at that path for the runs and removed afterwards.

```sh
python3 experiments/koblitz-n83-opcounts-20261023/analyze_v2.py --receipt-dir <scratch>/run1 > run1/analyze_v2-stdout.txt
python3 experiments/koblitz-n83-opcounts-20261023/analyze_v2.py --receipt-dir <scratch>/run2 > run2/analyze_v2-stdout.txt
```

Environment: Python 3.13.18, Linux 6.18.44 x86_64 (cloud agent container),
not the original host. Both runs exited 0.

## Result

`SHA256SUMS` here lists the four outputs of each run. All eight hashes
equal the corresponding entries of `run_github_39882571652/SHA256SUMS`
(`analysis_v2/band-v2.md` `b81a6e25...`, `counts-v2.json` `981c664c...`,
`opcounts_result-v2.json` `688e56b2...`, `analyze_v2-stdout.txt`
`098744cc...`). So the archived v2 outputs are reproduced byte for byte by
two runs on 2026-11-06 `[pcc:unverified]`. The output files themselves are
not committed again: they are byte-identical to the archived
`analysis_v2/` files.

Limits: this checks that the analysis is deterministic on the archived
receipts. It does not re-run the producer, re-measure anything or check
that the counters count what they name. It was run by the session that
wrote this file; hashes are integrity evidence, not an execution proof.

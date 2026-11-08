# Archived GLV confirmation input audit (2026-11-08)

This is a new audit of the frozen 2026-10-23 held-out confirmation. It does
not alter that run, its protocol, result, or graph. The source revision
inspected was `7a0eeee735bbd80e857d36d7069e388786231014`.
The scoped audit statement is `PCC-20261108-3401d0`; its standing is
`unverified` because a statement record carries no independent proof.

## Observation and replay

The historical `SHA256SUMS` passed for all 13 entries after retrieving the two
raw archives and PDF from their content-addressed store locations. The raw
archive hashes are `46237cc3602ff7582aacf43b3fa7c8de3d38e0330ae85c9b97ef985196178b30`
(`rows_main.jsonl.gz`) and
`4bb57c61f156a3871cd757460cce17223fd91950534f4c41d693f4b50531805a`
(`rows_c12.jsonl.gz`). The checked archive is local at
`/var/tmp/cryptanalysis-glv-raw-replay-20261108`; the canonical remote paths
follow `.artifacts.json` and `docs/artifacts.md`.

In a separate scratch directory, Python 3.9.25 ran the frozen `analyze.py`
against those raw archives. Its `results.json` and `results.md` were byte
identical to the committed versions. The current `chart.py` regenerated
`confirm.svg` byte identically (SHA-256
`7eb54ee2bd801bee14dc508e2558d37a219ec4a268939f1831b595bc0acc4195`).
The historical PDF passed its archived hash; it was not regenerated.

An independent streaming pass checked that both arms have the same 80,000
row keys, paired curve and target metadata, and zero differing operation
counts among the 45,700 rows where the table rules choose the same size.
Recomputing the four-cell geometric means from the raw operation counts gave
`0.9565397206383895` for `j1728` and `0.9670782595099048` for `j0`, equal
to the archived results. These are archive-consistency observations, not new
measurements. [pcc:unverified]

`check_inputs.py` additionally checked all 160,000 archived rows' target
scalars against the runner's seed formula, and all 3,200 distinct curves for
prime field/subgroup moduli, family equation, nonsingularity, cofactor and
Hasse bounds. Its own elliptic-curve arithmetic reconstructed a nonidentity
subgroup point and seed-derived target on the first and last curve of each
family/size cell (32 curves). The deterministic sample and coordinates are in
`receipt.json`. These are local audit checks. [pcc:unverified]
In a negative control, changing the first archived `k` to zero caused the
checker to exit nonzero before writing a new receipt. [pcc:unverified]

## Reproduce

From the repository root, retrieve the archives using the checked manifest:

```sh
python3 tools/artifacts/artifacts.py pull experiments/glv-table-rule-confirm-20261022
python3 experiments/glv-table-rule-confirm-20261022/audits/input-20261108/check_inputs.py
```

For the frozen analysis, copy `analyze.py`, `chart.py`, and both raw archives
to a scratch directory, run `python3 analyze.py` and `python3 chart.py` there,
then compare `results.json`, `results.md`, and `confirm.svg` to the committed
files. The scratch copy avoids modifying the historical study.

## Boundary and next check

The raw rows store `correct` and `rho_correct` flags but not the solver's
returned scalar, base point, or target point. The point reconstruction checks
that the archived curve metadata supports the intended input construction;
it cannot independently verify each historical solver return. Checks that
sampled points are annihilated by the recorded order also do not establish
the full curve order. A measurement claim needs an independent replay
certificate over sufficient raw outputs and a trusted signature under the
repository's PCC keyring. No such certificate is supplied by this audit, so
the historical measurement's PCC standing is not promoted.

The graph remains the frozen archive graph because the replay reproduced its
source data and SVG exactly. A future correction or new result
should add a new evidence record and render a new graph, rather than overwrite
the historical one.

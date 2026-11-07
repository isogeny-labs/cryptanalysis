# Replaying the p=997 review checks

Run from the Cryptanalysis repository root with Python 3. The reviewer script
is preserved byte for byte. It expects the reviewed inputs in a sibling
`scratch-base/` tree, so extract them to an isolated temporary directory.
Do not run it with Python `-O`, which disables its assertions. It reads
`census.json` and `image.json`, enumerates finite-field objects, and writes
its result only into the temporary directory.

```sh
review_tmp=$(mktemp -d)
mkdir -p "$review_tmp/scratch-base"
git archive 927d1eada55ff51e87b89930cad48672147e0929 \
  experiments/hecke-432-prime997-20261025 |
  tar -x -C "$review_tmp/scratch-base"
cp reports/2026-11-07-hecke-p997-review/source/finite_source_recheck.py \
  "$review_tmp/finite_source_recheck.py"
python3 -I "$review_tmp/finite_source_recheck.py"
cmp "$review_tmp/finite-source-recheck.json" \
  reports/2026-11-07-hecke-p997-review/source/finite-source-recheck.json
```

The blind arithmetic verifier is self-contained:

```sh
python3 -I -S reports/2026-11-07-hecke-p997-review/blind/check_arithmetic.py
```

The archived audit replay receipt identifies the original scratch extraction,
resource limits and exact output hashes. Its scratch result was byte-identical
to the sealed `audit.json`. Repeating the archived audit may rewrite an
`audit.json` in its working directory, so replay it in an isolated extract,
never in the sealed experiment tree.

The hosted Lean proof gate is recorded in `machine-receipt.json`; the raw
`hosted-lean-42339546067.log` is bound by `.artifacts.json` and held in the
content-addressed store. Hydrate it with
`python3 tools/artifacts/artifacts.py pull reports/2026-11-07-hecke-p997-review`
and compare its SHA-256 with the machine receipt. The proof gate at that head is run through
`.github/workflows/lean-proof-gate.yml`; the report binds its exact gate and
workflow hashes. This replay does not independently authenticate the older
Sage execution or supply the modular-map bridge.

# p=997 finite-record guard

`verify.py` rechecks the sealed p=997 Hecke archive with standard-library
Python. It verifies all 17 seal entries, independently enumerates finite
2/3-isogeny chain roots across every j-value and the ten special twists,
checks each archived edge and source-j field, re-enumerates the B and E
rational points, and compares every saved three-point B preimage coset with
the full inverse dual-isogeny image. It writes only a requested receipt.

```sh
python3 tools/hecke-432-prime997/verify.py \
  --output /tmp/p997-finite-guard.json
python3 tools/hecke-432-prime997/test_controls.py
```

The negative controls mutate copies in memory. The invalid kernel root and
wrong source-j metadata must fail; a complete projection swap must still
pass. That last control records the instrument's boundary: this checker
does not recompute the source-specific quarter-shift map. It also does not
prove that chain pairs are distinct modular points, the normalized map has
degree 24, or all rational cusps map to B identity. Those bridges are
separate obligations in the [review packet](../../reports/2026-11-07-hecke-p997-review/report.md).

The source archive remains sealed and unchanged. Run without Python `-O` for
ordinary `unittest` assertions; the verifier itself uses explicit checks
that remain active under `-O`.

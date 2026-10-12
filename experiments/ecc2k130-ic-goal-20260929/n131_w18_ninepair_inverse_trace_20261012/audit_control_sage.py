#!/usr/bin/env sage -python
"""Independently check inverse-trace gates on every constructed pair endpoint."""

import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing

here = Path(__file__).resolve().parent
root = here.parent
fixture_path = root / "n131_fixed_seed_ninepair_cubic_20261011/control_fixture.json"
support_path = root / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((here / "protocol.json").read_text())
    control = json.loads((here / "control_result.json").read_text())
    runtime = json.loads((here / "sage_runtime_info.json").read_text())
    fixture = json.loads(fixture_path.read_text())
    assert runtime["status"] == "verified"
    assert protocol["source_sha256"]["fixture"] == sha(fixture_path)
    assert protocol["source_sha256"]["support"] == sha(support_path)
    assert control["source_pair_checks"] == len(fixture["selected"]) == 9
    support = {int(mask): int(column) for mask, column in
               (line.split() for line in support_path.read_text().splitlines())}
    polynomial = PolynomialRing(GF(2), "t")
    t = polynomial.gen()
    field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
    used_columns = set()
    rows = []
    for item in fixture["selected"]:
        masks = item["masks"]
        assert len(masks) == 2 and masks[0] ^ masks[1] == 212
        for mask in masks:
            w = sum((field(t**(bit+1)) for bit in range(18) if mask >> bit & 1),
                    field.zero())
            assert w != 0
            reciprocal = 1 / w
            assert w * reciprocal == 1
            assert reciprocal.trace() == 0
            column = support[mask]
            assert column not in used_columns
            used_columns.add(column)
            rows.append({"slot": item["slot"], "mask": mask,
                         "folded_column": column, "inverse_trace": 0})
    assert len(rows) == len(used_columns) == 18
    result = {"status": "PASS_SAGE_N131_NINEPAIR_INVERSE_TRACE_CONTROL",
              "curve_id": protocol["curve_id"], "source_pair_checks": 9,
              "inverse_witness_checks": len(rows),
              "distinct_folded_columns": len(used_columns),
              "rows": rows,
              "source_sha256": {"script": sha(Path(__file__)),
                                "protocol": sha(here / "protocol.json"),
                                "control": sha(here / "control_result.json"),
                                "fixture": sha(fixture_path),
                                "support": sha(support_path),
                                "sage_runtime": sha(here / "sage_runtime_info.json")}}
    with (here / "control_gate_sage.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(result["status"], len(rows), flush=True)


if __name__ == "__main__":
    main()

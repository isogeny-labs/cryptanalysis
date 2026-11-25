"""Check retained equal-decomposition outputs against raw logs and group law."""

import gzip
import json
import re

from balanced_panel import OUTPUT, ROOTS
from generate_msolve_pilot import HERE
from panel import ROUND, TARGETS, sha256
from validate_panel import count_decompositions


def main():
    records = json.loads((OUTPUT / "summary.json").read_text())
    baseline = json.loads((HERE / "panel" / "summary.json").read_text())
    reference = {record["case"]: record for record in baseline if record["arm"] == "cayley"}
    assert len(records) == 8
    checked = []
    for record, (case, xy) in zip(records, TARGETS):
        assert record["case"] == case and record["target_xy"] == list(xy)
        raw_log = gzip.decompress((OUTPUT / f"{case}.log.gz").read_bytes())
        input_bytes = (OUTPUT / f"{case}.ms").read_bytes()
        output_bytes = (OUTPUT / f"{case}.out").read_bytes()
        assert sha256(raw_log) == record["log_sha256"]
        assert sha256(input_bytes) == record["input_sha256"]
        assert sha256(output_bytes) == record["output_sha256"]
        rows = [tuple(map(int, match.groups())) for match in ROUND.finditer(raw_log.decode(errors="replace"))]
        geometry = sha256(json.dumps(rows).encode())
        assert geometry == record["round_geometry_sha256"]
        count = count_decompositions(ROOTS, xy[0])
        assert count == (6 if case.startswith("shared_") else 0)
        assert record["exit_code"] == 0
        assert record["has_solution"] == (count > 0)
        assert record["ideal_degree"] == (count or None)
        assert record["reference_geometry_equal"] == (geometry == reference[case]["round_geometry_sha256"])
        checked.append({"case": case, "group_law_count": count, "geometry_equal": record["reference_geometry_equal"]})
    print(json.dumps(checked, sort_keys=True))


if __name__ == "__main__":
    main()

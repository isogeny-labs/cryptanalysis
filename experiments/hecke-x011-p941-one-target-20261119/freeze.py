"""Freeze a public point with its known scalar in a separate audit fixture."""

import json
from pathlib import Path
from common import G, N, digest_scalar, mul

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
source = json.loads((HERE / protocol["fiber_source"]).read_text())
fiber = {tuple(r["point"]) for r in source["source_records"]["2"]}
assert len(fiber) == 112
for counter in range(10000):
    scalar = digest_scalar(protocol["target_seed"], counter)
    point = mul(scalar, G)
    if scalar and point not in fiber:
        break
else:
    raise RuntimeError("target selection cap reached")
(HERE / "public.json").write_text(json.dumps({"schema": "x011-p941-public-target-v1", "point": point}, indent=2) + "\n")
(HERE / "fixture.json").write_text(json.dumps({"counter": counter, "scalar": scalar, "point": point}, indent=2) + "\n")
print("published point", point, "counter", counter)

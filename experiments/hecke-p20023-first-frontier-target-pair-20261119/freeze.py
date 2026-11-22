"""Freeze an unseen public point outside the prepared first-frontier table."""

import json
from hashlib import sha256
from pathlib import Path
from common import G, N, digest_scalar, mul

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
for key in ("fresh_source", "solved_table"):
    assert sha256((HERE / protocol[key]).read_bytes()).hexdigest() == protocol[key + "_sha256"]
solved = json.loads((HERE / protocol["solved_table"]).read_text())
prepared_logs = set(solved["logs_by_column"])
assert len(prepared_logs) == 1760
for counter in range(10000):
    scalar = digest_scalar(protocol["target_seed"], counter)
    if scalar and scalar not in prepared_logs:
        break
else:
    raise RuntimeError("target selection cap reached")
point = mul(scalar, G)
(HERE / "public.json").write_text(json.dumps({"schema": "hecke-p20023-public-target-v1", "point": point}, indent=2) + "\n")
(HERE / "fixture.json").write_text(json.dumps({"counter": counter, "scalar": scalar, "point": point}, indent=2) + "\n")
(HERE / "pre-run.json").write_text(json.dumps({
    "schema": "hecke-p20023-pre-run-v1",
    "protocol_sha256": sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
    "public_sha256": sha256((HERE / "public.json").read_bytes()).hexdigest(),
    "fresh_source_sha256": protocol["fresh_source_sha256"],
    "solved_table_sha256": protocol["solved_table_sha256"],
}, indent=2) + "\n")
print("published point", point, "counter", counter)

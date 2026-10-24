"""Independent group-law audit that each pair-output x root has both signs."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "source_sign_audit_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N41_SOURCE_SIGN_AUDIT"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
geometry = json.loads(Path(cfg["sources"]["geometry"]["path"]).read_text())
spec = importlib.util.spec_from_file_location("independent_n41_replay",
                                             cfg["sources"]["replay"]["path"])
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)
F = replay.Field()


def frob(value, power):
    for _ in range(power):
        value = F.square(value)
    return value


started = time.monotonic()
records = []
state_count = sign_pair_count = 0
first_roots = None
for block in geometry["blocks"][:6]:
    rotation = block["rotation"]
    local_roots = []
    for mask in geometry["permitted_canonical_a"]:
        states = [row for row in block["states"] if row["a"] == mask]
        assert len(states) == 4
        by_root = {}
        for row in states:
            point = tuple(row["raw_sum"])
            assert replay.on_curve(F, point) and point[0] not in (0, 1)
            assert F.inv(point[0] ^ 1) == row["z"]
            root = F.inv(frob(point[0], (41 - rotation) % 41))
            by_root.setdefault(root, []).append(point)
        assert len(by_root) == 2
        for root, points in sorted(by_root.items()):
            assert len(points) == 2 and points[0] != points[1]
            assert replay.add(F, points[0], points[1]) is None
            records.append((rotation, mask, root, points[0], points[1]))
            sign_pair_count += 1
        local_roots.append(tuple(sorted(by_root)))
        state_count += len(states)
    if first_roots is None:
        first_roots = local_roots
    else:
        assert local_roots == first_roots
assert state_count == cfg["expected_states"]
assert sign_pair_count == cfg["expected_root_sign_pairs"]
payload = json.dumps(records, separators=(",", ":"))
out = {"status": "PASS_N41_SOURCE_ROOT_SIGN_AUDIT",
       "curve_id": cfg["curve_id"],
       "state_count": state_count, "root_sign_pairs": sign_pair_count,
       "edge_count": len(geometry["permitted_canonical_a"]),
       "rotation_count": 6,
       "ordered_record_sha256": hashlib.sha256(payload.encode()).hexdigest(),
       "wall_seconds": time.monotonic() - started,
       "protocol_sha256": sha(HERE / "source_sign_audit_protocol.json")}
(HERE / "source_sign_audit_result.json").write_text(
    json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps(out, sort_keys=True))

"""Freeze witness and lexicographic negative complete four-axis boxes."""
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = {
    "geometry": ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json",
    "root_polynomial": ROOT / "n41_w8_three_pair_resultant_20261013/result.json",
    "coordinate_audit": ROOT / "n41_w8_two_code_affine_span_20261013/cases.jsonl",
    "target_table": HERE / "target_table.json",
    "witness_protocol": ROOT / "n41_w8_fixedseed_ordinary_join_20261013/protocol.json",
    "field_arithmetic": Path("/Volumes/SSD990/crypto/research/sat_factor_base_review_20260908/autolab_orbit_extract_20260924/independent_replay.py"),
    "sage_curve_audit": ROOT / "n41_w8_fixed_sum_table_20261009/audit.py",
    "sage_runtime": HERE / "sage_runtime_info.json",
    "target_table_producer": HERE / "make_target_table_sage.py",
    "producer": HERE / "run.py",
    "auditor": HERE / "audit_sage.py",
    "freeze": HERE / "freeze.py",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


geo = json.loads(SOURCES["geometry"].read_text())
blocks = geo["blocks"]
permitted = geo["permitted_canonical_a"]
suffix = [14, 109, 51]
suffix_columns = set().union(*(set(blocks[axis]["states"][state]["columns"])
                               for axis, state in enumerate(suffix, 4)))
columns = [[set(blocks[axis]["states"][4*code]["columns"])
            for code in range(40)] for axis in range(4)]
counts = Counter()
for i, j, k in itertools.product(range(40), repeat=3):
    first = (columns[0][i], columns[1][j], columns[2][k])
    if any(col & suffix_columns for col in first):
        continue
    if any(first[a] & first[b] for a in range(3) for b in range(a+1, 3)):
        continue
    used = set().union(*first)
    for l in range(40):
        if not columns[3][l] & (suffix_columns | used):
            counts[tuple(permitted[code] >> 2 for code in (i, j, k, l))] += 1
assert sum(counts.values()) == 1386816
code_map = defaultdict(list)
for code, mask in enumerate(permitted):
    code_map[mask >> 2].append(code)
full = sorted(prefix for prefix, count in counts.items()
              if count == 16 and all(len(code_map[index]) == 2 for index in prefix))
print(json.dumps({"eligible_quads": sum(counts.values()), "complete_two_code_boxes": len(full),
                  "first_complete_prefix": full[0]}))
witness_prefix = (38, 53, 16, 0)
assert witness_prefix in full
selected = [("control", full[0]), ("witness", witness_prefix)]
boxes = []
for label, prefix in selected:
    quads = list(itertools.product(*(code_map[index] for index in prefix)))
    assert len(quads) == 16
    for quad in quads:
        cs = [columns[axis][code] for axis, code in enumerate(quad)]
        assert all(not col & suffix_columns for col in cs)
        assert all(not cs[a] & cs[b] for a in range(4) for b in range(a+1, 4))
    boxes.append({"label": label, "prefix": prefix, "code_quads": quads})
assert (24, 37, 10, 0) in boxes[1]["code_quads"]
record = {
    "status": "FROZEN_N41_FOUR_CODE_SUFFIX_QUOTIENT",
    "candidate_id": None, "curve_id": geo["curve_id"],
    "field_degree": 41, "field_modulus": [41, 3, 0],
    "suffix_state_ids": suffix, "checkpoints": [8, 12, 16, 24],
    "eligible_quads": sum(counts.values()), "complete_boxes": len(full),
    "boxes": boxes,
    "selection": "First lexicographic complete 2x2x2x2 box plus complete box containing the archived public witness, frozen before symbolic execution.",
    "worker_count": 1, "wall_cap_seconds": 300, "rss_cap_bytes": 4 * 1024**3,
    "sources": {name: {"path": str(path), "sha256": sha(path)}
                for name, path in SOURCES.items()},
}
assert not (HERE / "protocol.json").exists()
(HERE / "protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")

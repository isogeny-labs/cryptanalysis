"""Freeze complete three-axis product-code boxes before symbolic execution."""
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = {
    "geometry": ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json",
    "root_polynomial": ROOT / "n41_w8_three_pair_resultant_20261013/result.json",
    "coordinate_audit": ROOT / "n41_w8_two_code_affine_span_20261013/cases.jsonl",
    "prior_result": ROOT / "n41_w8_three_pair_resultant_20261013/result.json",
    "witness_protocol": ROOT / "n41_w8_fixedseed_ordinary_join_20261013/protocol.json",
    "field_arithmetic": Path("/Volumes/SSD990/crypto/research/sat_factor_base_review_20260908/autolab_orbit_extract_20260924/independent_replay.py"),
    "sage_curve_audit": ROOT / "n41_w8_fixed_sum_table_20261009/audit.py",
    "sage_runtime": HERE / "sage_runtime_info.json",
    "producer": HERE / "run.py",
    "auditor": HERE / "audit_sage.py",
    "freeze": HERE / "freeze.py",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


geo = json.loads(SOURCES["geometry"].read_text())
blocks = geo["blocks"]
permitted = geo["permitted_canonical_a"]
suffix = [0, 14, 109, 51]
suffix_columns = set().union(*(set(blocks[axis]["states"][state]["columns"])
                               for axis, state in enumerate(suffix, 3)))
assert len(suffix_columns) == 8
groups = defaultdict(list)
for triple in itertools.product(range(40), repeat=3):
    cols = [set(blocks[axis]["states"][4 * code]["columns"])
            for axis, code in enumerate(triple)]
    if any(cols[axis] & suffix_columns for axis in range(3)):
        continue
    if any(cols[i] & cols[j] for i in range(3) for j in range(i + 1, 3)):
        continue
    groups[tuple(permitted[code] >> 2 for code in triple)].append(triple)
full = [(prefix, sorted(triples)) for prefix, triples in sorted(groups.items())
        if len(triples) == 8 and all(len({t[i] for t in triples}) == 2 for i in range(3))]
assert sum(map(len, groups.values())) == 38874
assert len(full) == 720
witness = next((prefix, triples) for prefix, triples in full if (24, 37, 10) in triples)
assert witness[0] == (38, 53, 16)
selected = full[:7] + [witness]
assert len({p for p, _ in selected}) == 8
record = {
    "status": "FROZEN_N41_THREE_CODE_QUOTIENT_FINGERPRINT",
    "candidate_id": None,
    "curve_id": geo["curve_id"],
    "field_degree": 41,
    "field_modulus": [41, 3, 0],
    "suffix_state_ids": suffix,
    "checkpoints": [8, 12, 16, 24],
    "eligible_triples": 38874,
    "complete_boxes": 720,
    "boxes": [{"label": "witness" if prefix == witness[0] else "control",
               "prefix": prefix, "code_triples": triples}
              for prefix, triples in selected],
    "selection": "First seven lexicographic complete boxes plus box containing archived witness triple, frozen before symbolic execution.",
    "worker_count": 1,
    "wall_cap_seconds": 300,
    "rss_cap_bytes": 4 * 1024**3,
    "sources": {name: {"path": str(path), "sha256": sha(path)}
                for name, path in SOURCES.items()},
}
assert not (HERE / "protocol.json").exists()
(HERE / "protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")

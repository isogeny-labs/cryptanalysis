"""Independently rebuild every fixed-seed N41 pair state with checked Sage."""
import hashlib
import importlib.util
import json
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT / "n41_w8_fixed_sum_table_20261009/audit.py"
BASE = ROOT / "n41_lowpower_w8_s6/basis8.json"
R = 549756390943


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "sage_protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    for path, digest in protocol["sources"].items():
        assert sha(Path(path)) == digest, path
    spec = importlib.util.spec_from_file_location("old_n41_sage_audit", OLD)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    geometry = json.loads((ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json").read_text())
    curve, elem, integer = old.sage_curve()
    rows = old.first_rows()
    basis = json.loads(BASE.read_text())["basis_halftrace_by_unique_rotation"][0]

    @lru_cache(None)
    def raw(mask, sign):
        point = old.raw_source(curve, elem, rows, basis, mask, sign)
        assert R * (4 * point) == curve(0)
        return point

    @lru_cache(None)
    def rotated(mask, sign, rotation):
        point = raw(mask, sign)
        for _ in range(rotation):
            point = curve(point[0] ** 2, point[1] ** 2)
        return point

    slot_rows = []
    all_outputs = []
    for slot, block in enumerate(geometry["blocks"]):
        rotation = geometry["rotations"][slot]
        outputs = []
        for state in block["states"]:
            left = rotated(state["a"], state["sign_a"], rotation)
            right = rotated(state["b"], state["sign_b"], rotation)
            total = left + right
            assert total != curve(0)
            actual = [integer(total[0]), integer(total[1])]
            projected = [integer((4 * total)[0]), integer((4 * total)[1])]
            assert actual == state["raw_sum"]
            assert projected == state["projected_sum"]
            assert integer(1 / (total[0] + 1)) == state["z"]
            outputs.append(actual)
        all_outputs.extend(outputs)
        slot_rows.append({"slot": slot, "rotation": rotation,
                          "source_states_checked": len(outputs),
                          "raw_output_sha256": hashlib.sha256(json.dumps(outputs, separators=(",", ":")).encode()).hexdigest()})
    assert len(all_outputs) == 1120
    assert raw.cache_info().currsize == 160
    result = {"status": "PASS_INDEPENDENT_SAGE_N41_SEVENPAIR_ALL_STATES",
              "states_checked": len(all_outputs),
              "distinct_unrotated_raw_leaves": raw.cache_info().currsize,
              "slots": slot_rows,
              "all_raw_outputs_sha256": hashlib.sha256(json.dumps(all_outputs, separators=(",", ":")).encode()).hexdigest()}
    with (HERE / "sage_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], result["states_checked"], flush=True)


if __name__ == "__main__":
    main()

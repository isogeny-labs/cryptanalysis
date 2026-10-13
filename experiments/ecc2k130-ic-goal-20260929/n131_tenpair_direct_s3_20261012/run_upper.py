"""Positive SAT control for direct S3 with true upper-tree coordinates."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("direct_runner", HERE / "run.py")
direct = importlib.util.module_from_spec(spec)
spec.loader.exec_module(direct)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "upper_protocol.json").read_text())
    for name, path in (("runner", HERE / "run_upper.py"),
                       ("direct_runner", HERE / "run.py"),
                       ("direct_formula", HERE / "direct_control.xcnf")):
        assert sha(path) == protocol["sha256"][name], name
    direct.ten.build = direct.direct_build()
    chain, rows, root, nodes, intermediates, points = direct.input_data()
    circuit, wires = direct.ten.build([row["standard_reciprocal"] for row in rows], root, nodes)
    checked, groups = direct.constructed_check(circuit, wires, chain, intermediates, points)
    assert checked == protocol["assignment_check"]
    intermediate_units = [wire if value >> bit & 1 else -wire
                          for wireset, value in zip(wires["intermediates"], intermediates)
                          for bit, wire in enumerate(wireset)]
    units = groups["target"] + groups["selectors"] + groups["outputs"] + intermediate_units
    assert len(units) == 10 + 170 + 1310 + 1048
    construction = json.loads((HERE / "construction.json").read_text())["formula"]
    direct.run_arm("full_upper_control", HERE / "direct_control.xcnf", units,
                   construction["variables"], construction["clauses"],
                   construction["native_xor_rows"])


if __name__ == "__main__":
    main()

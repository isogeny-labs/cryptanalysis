"""Frozen constructed-control ladder for exact direct-S3 upper-tree hints."""
import gzip
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DIRECT = ROOT / "n131_tenpair_direct_s3_20261012"
CHECKER = ROOT / "n41_n131_fouratom_product_anf_sat_20261012" / "run.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


direct = load("direct_runner_ladder", DIRECT / "run.py")
checker = load("explicit_xcnf_checker_ladder", CHECKER)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def units_for(bits, values, indexes):
    return [wire if values[index] >> bit & 1 else -wire
            for index in indexes for bit, wire in enumerate(bits[index])]


def archive(name, receipt):
    raw = HERE / (name + ".xcnf")
    packed = HERE / (name + ".xcnf.gz")
    with packed.open("xb") as output:
        with gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=0,
                           compresslevel=1) as stream:
            with raw.open("rb") as source:
                for block in iter(lambda: source.read(1 << 20), b""):
                    stream.write(block)
    assert sha(raw) == receipt["formula"]["sha256"]
    result = {"raw_sha256": sha(raw), "raw_bytes": raw.stat().st_size,
              "gzip_sha256": sha(packed), "gzip_bytes": packed.stat().st_size}
    raw.unlink()
    return result


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    for name, path in (("runner", HERE / "run.py"),
                       ("direct_runner", DIRECT / "run.py"),
                       ("checker", CHECKER),
                       ("direct_formula", DIRECT / "direct_control.xcnf"),
                       ("solver", direct.SOLVER)):
        assert sha(path) == protocol["sha256"][name], name
    direct.ten.build = direct.direct_build()
    chain, rows, root, nodes, intermediates, points = direct.input_data()
    started = time.monotonic_ns()
    circuit, wires = direct.ten.build([row["standard_reciprocal"] for row in rows], root, nodes)
    built = time.monotonic_ns()
    checked, groups = direct.constructed_check(circuit, wires, chain, intermediates, points)
    checked_at = time.monotonic_ns()
    assert checked == protocol["assignment_check"]
    replay = HERE / "rebuilt.xcnf"
    circuit.write(replay)
    assert sha(replay) == protocol["sha256"]["direct_formula"]
    replay.unlink()
    profile = json.loads((DIRECT / "construction.json").read_text())["formula"]
    (HERE / "build.json").write_text(json.dumps({
        "status": "PASS_EXACT_DIRECT_S3_REBUILD_AND_ASSIGNMENT",
        "source_build_ns_exploratory": built - started,
        "constructed_assignment_check_ns_exploratory": checked_at - built,
        "assignment_check": checked}, indent=2, sort_keys=True) + "\n")
    direct.HERE = HERE
    sys.modules["run"] = checker
    baseline = groups["target"] + groups["selectors"] + groups["outputs"]
    assert len(baseline) == 1490
    aggregate = []
    for arm in protocol["arms"]:
        name, indexes = arm["name"], arm["upper_indexes"]
        pins = baseline + units_for(wires["intermediates"], intermediates, indexes)
        assert len(pins) == 1490 + 131 * len(indexes)
        status = direct.run_arm(name, DIRECT / "direct_control.xcnf", pins,
                                profile["variables"], profile["clauses"],
                                profile["native_xor_rows"])
        receipt = json.loads((HERE / (name + ".json")).read_text())
        aggregate.append({"name": name, "upper_indexes": indexes,
                          "status": status, "archive": archive(name, receipt)})
    (HERE / "aggregate.json").write_text(json.dumps({
        "status": "COMPLETE_FROZEN_DIRECT_S3_HINT_LADDER",
        "candidate_id": None, "arms": aggregate,
        "protocol_sha256": sha(HERE / "protocol.json")}, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

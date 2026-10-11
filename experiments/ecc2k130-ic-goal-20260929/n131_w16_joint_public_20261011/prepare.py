#!/usr/bin/env sage -python
"""Bind the archived 32 signed W16 prefixes to the published target."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
JOINT = ROOT / "n131_w16_joint_prefix_20261010"
OFFICIAL = ROOT / "n131_w2_m15_official_single_target_4g_20261003"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


joint = load("frozen_joint_run", JOINT / "run.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert not (HERE / "inputs.json").exists()
    prior = json.loads((JOINT / "prefixes.json").read_text())
    assert prior["status"] == "FROZEN_32_SIGNED_FIRST_PAIR_CHOICES"
    assert len(prior["prefixes"]) == 32
    params = json.loads((OFFICIAL / "official_fixed_parameters.json").read_text())
    bridge = json.loads((OFFICIAL / "bridge_audit.json").read_text())
    assert bridge["status"] == "PASS"
    assert sha(OFFICIAL / "official_fixed_parameters.json") == bridge["input_sha256"]["official_fixed_parameters"]
    target = params["targets"][0]
    assert target["id"] == "ecc2k-130"
    q = (int(target["x"], 16), int(target["y"], 16))
    columns, field, curve, _, _ = joint.old.experiment.run.source()
    subgroup_order = 680564733841876926932320129493409985129
    assert curve.on_curve(q) and curve.mul(subgroup_order, q) is None
    rows = []
    for archived in prior["prefixes"]:
        masks = archived["masks"]
        assert [columns[mask] for mask in masks] == archived["columns"]
        prefix = tuple(archived["projected_sum"])
        assert curve.on_curve(prefix)
        residual = curve.add(q, curve.neg(prefix))
        assert residual is not None and curve.add(prefix, residual) == q
        preimages = joint.old.experiment.run.prior.prior.old.target_preimages(curve, residual)
        assert len(preimages) == 4
        rows.append({"masks": masks, "signs": archived["signs"],
                     "columns": archived["columns"],
                     "projected_sum": list(prefix), "residual_q": list(residual),
                     "preimages": [list(point) for point in preimages],
                     "target_reciprocals": [field.inv(point[0]) for point in preimages]})
    record = {"status": "FROZEN_W16_32_PREFIX_PUBLISHED_INPUT",
              "candidate_id": None, "curve_id": prior["curve_id"],
              "target_id": "ecc2k-130", "target_q": list(q),
              "input_law": "32 signed pairs from archived prefix list fixed before this published point; all 128 target fibers searched jointly",
              "prefixes": rows, "prefix_count": len(rows),
              "source_sha256": {"prepare": sha(__file__),
                                "archived_prefixes": sha(JOINT / "prefixes.json"),
                                "official_parameters": sha(OFFICIAL / "official_fixed_parameters.json"),
                                "official_bridge": sha(OFFICIAL / "bridge_audit.json")}}
    (HERE / "inputs.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": record["status"], "prefixes": len(rows),
                      "target": list(q)}))


if __name__ == "__main__":
    main()

"""Freeze the 4,134 exact valid d13 selectors for independent Sage replay."""

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "ecc2k130" / "codegen"))
from indexcalc_e2e import AuditCurve, AuditField, Ledger  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(values):
    return hashlib.sha256(b"".join(int(v).to_bytes(17, "little")
                                for v in values)).hexdigest()


def main():
    p = json.loads((HERE / "valid_codes_protocol.json").read_text())
    assert p["status"] == "FROZEN_BEFORE_ENUMERATION"
    assert p["source_sha256"] == sha(__file__)
    for name, value in p["input_sha256"].items():
        assert sha(p["inputs"][name]) == value
    geometry = json.loads(Path(p["inputs"]["geometry"]).read_text())
    prior = json.loads(Path(p["inputs"]["audit_result"]).read_text())
    onb = AuditField(131, Ledger())
    curve = AuditCurve(onb, Ledger())
    basis = [int(x, 16) for x in geometry["domain"]["basis_coordinate_masks_hex"]]
    started = time.monotonic()
    rows = []
    for code in range(1, 1 << len(basis)):
        mask = 0
        for j, value in enumerate(basis):
            if code >> j & 1:
                mask ^= value
        phi = onb.fromCoords(mask)
        x = onb.inv(phi) ^ onb.one()
        if curve.pointFromX(x) is not None:
            rows.append([code, mask])
        if (code & 63) == 0:
            assert time.monotonic()-started < p["wall_cap_seconds"]
            assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < p["rss_cap_bytes"]
    assert len(rows) == prior["valid_selectors"] == 4134
    assert digest([mask for _, mask in rows]) == prior["source_phi_digest"]
    output = HERE / "valid_codes.json"
    assert not output.exists()
    output.write_text(json.dumps(rows, separators=(",", ":")) + "\n")
    print(json.dumps({"kind": "n131_d13_exact_valid_selector_list",
                      "status": "PASS_EXACT_ENUMERATION",
                      "protocol_sha256": sha(HERE / "valid_codes_protocol.json"),
                      "count": len(rows),
                      "codes_sha256": sha(output),
                      "source_phi_digest": prior["source_phi_digest"],
                      "elapsed_seconds": time.monotonic()-started,
                      "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
                     sort_keys=True))


if __name__ == "__main__":
    main()

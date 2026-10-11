#!/usr/bin/env sage -python
"""Freeze a fresh public point and verified reusable state logs for N41."""

import hashlib
import json
import sys
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "n41_w7_entropy_cubic_20261011/w8"
JOIN = HERE.parent / "n41_w8_sixpair_mitm_20261011"
LOGS = HERE.parent / "n41_w8_sixpair_logprep_20261011"
R = 549756390943
ROTATIONS = (0, 7, 14, 21, 28, 35)
TARGET_SEED = "N41-W8-heldout-one-target-20261011-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def sources():
    return {"script": Path(__file__), "runtime": HERE / "sage_runtime_info.json",
            "geometry": BASE / "geometry.json", "fixture": BASE / "fixture.json",
            "state_table": JOIN / "join_input.tsv",
            "source_relation": JOIN / "audit_result.json",
            "factor_logs": LOGS / "audit_result.json",
            "known_scalar_panel": LOGS / "panel.tsv"}


def freeze():
    audit = json.loads((LOGS / "audit_result.json").read_text())
    assert audit["status"] == "PASS_N41_FULL_FACTOR_LOG_AND_TARGET_RECOVERY"
    assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"
    record = {"status": "FROZEN_N41_W8_HELDOUT_TARGET_PREPARATION",
              "curve_id": "EC1N41Ckb1h7d5e80d3c4d0", "subgroup_order": R,
              "target_scalar_law": "SHA256(UTF8 target_seed) modulo r; reject zero, panel scalars, and previous public scalar",
              "target_seed_sha256": hashlib.sha256(TARGET_SEED.encode()).hexdigest(),
              "factor_base_folded_columns": 70, "source_pair_seed": 184,
              "rotations": ROTATIONS, "target_count": 1,
              "source_sha256": {name: sha(path) for name, path in sources().items()}}
    save(HERE / "preparation_protocol.json", record)
    print(record["status"])


def produce():
    protocol = json.loads((HERE / "preparation_protocol.json").read_text())
    assert protocol["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    audit = json.loads((LOGS / "audit_result.json").read_text())
    geometry = json.loads((BASE / "geometry.json").read_text())
    fixture = json.loads((BASE / "fixture.json").read_text())
    rows = {int(item["mask"]): item for item in geometry["rows"]}
    edges = [(a, a ^ 184) for a in sorted(rows)
             if a < (a ^ 184) and a ^ 184 in rows
             and rows[a]["column"] != rows[a ^ 184]["column"]]
    assert len(edges) == 35
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def dec(value):
        return field(ring([(int(value) >> i) & 1 for i in range(41)]))

    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    def xy(point):
        return [enc(point[0]), enc(point[1])]

    raw = {mask: curve(*map(dec, item["raw_point"])) for mask, item in rows.items()}
    projected = {mask: 4 * point for mask, point in raw.items()}
    representative = {}
    for mask, item in sorted(rows.items()):
        representative.setdefault(int(item["column"]), mask)
    generator = curve(*map(dec, audit["generator_projected"]))
    assert R * generator == curve(0)
    eigenvalue = int(audit["frobenius_eigenvalue_mod_r"])
    logs = {int(column): int(value) for column, value in audit["factor_logs"].items()}
    assert len(logs) == 70
    for column, value in logs.items():
        assert value * generator == projected[representative[column]]
    source_log = {}
    for mask in {mask for edge in edges for mask in edge}:
        column = int(rows[mask]["column"])
        rep = projected[representative[column]]
        matches = []
        for exponent in range(41):
            rotated = curve(rep[0]**(1 << exponent), rep[1]**(1 << exponent))
            if rotated == projected[mask]:
                matches.append((exponent, 1))
            if -rotated == projected[mask]:
                matches.append((exponent, -1))
        assert len(matches) == 1
        exponent, sign = matches[0]
        source_log[mask] = sign * pow(eigenvalue, exponent, R) * logs[column] % R
        assert source_log[mask] * generator == projected[mask]
    state_rows = {}
    for line in (JOIN / "join_input.tsv").read_text().splitlines()[1:]:
        cells = line.split()
        if cells[0] != "S":
            continue
        _, slot, sid, edge, a, b, sa, sb, x, y = cells
        slot, sid, edge, a, b, sa, sb = map(int, (slot, sid, edge, a, b, sa, sb))
        assert edges[edge] == (a, b) and sid // 4 == edge
        value = (((-1 if sa else 1) * source_log[a] +
                  (-1 if sb else 1) * source_log[b]) *
                 pow(eigenvalue, ROTATIONS[slot], R)) % R
        point = curve(dec(x), dec(y))
        assert value * generator == 4 * point
        state_rows[(slot, sid)] = value
    assert len(state_rows) == 840
    path = HERE / "state_logs.tsv"
    with path.open("x") as stream:
        stream.write("STATE_LOGS 6 140\n")
        for (slot, sid), value in sorted(state_rows.items()):
            stream.write(f"L {slot} {sid} {value}\n")

    old_raw = [curve(*map(dec, value)) for value in fixture["raw_target_preimages"]]
    torsion = [point - old_raw[0] for point in old_raw]
    assert len(set(torsion)) == 4 and all(4 * point == curve(0) for point in torsion)
    with (HERE / "torsion.tsv").open("x") as stream:
        stream.write("TORSION 4\n")
        for index, point in enumerate(torsion):
            if point == curve(0):
                stream.write(f"T {index} -1 -1\n")
            else:
                stream.write(f"T {index} {enc(point[0])} {enc(point[1])}\n")

    scalar = int.from_bytes(hashlib.sha256(TARGET_SEED.encode()).digest(), "big") % R
    assert scalar
    panel_scalars = {int(line.split()[3]) for line in
                     (LOGS / "panel.tsv").read_text().splitlines()[1:]}
    assert scalar not in panel_scalars
    assert scalar != int(audit["recovered_public_target"]["target_log_mod_r"])
    target = scalar * generator
    with (HERE / "public_target.tsv").open("x") as stream:
        stream.write(f"Q {enc(target[0])} {enc(target[1])}\n")
    save(HERE / "secret_audit.json", {"status": "HELDOUT_SCALAR_FOR_INDEPENDENT_REPLAY",
                                      "scalar_mod_r": str(scalar), "public_target": xy(target),
                                      "generator_projected": xy(generator),
                                      "target_seed_sha256": protocol["target_seed_sha256"]})
    result = {"status": "PASS_N41_W8_HELDOUT_INPUT_PREPARATION",
              "state_log_checks": len(state_rows), "torsion_points": 4,
              "panel_overlap_count": 0, "public_target": xy(target),
              "generator_projected": xy(generator),
              "source_sha256": {name: sha(path) for name, path in sources().items()},
              "state_logs_sha256": sha(path),
              "torsion_sha256": sha(HERE / "torsion.tsv"),
              "public_target_sha256": sha(HERE / "public_target.tsv"),
              "secret_audit_sha256": sha(HERE / "secret_audit.json"),
              "protocol_sha256": sha(HERE / "preparation_protocol.json")}
    save(HERE / "preparation_result.json", result)
    print(result["status"], result["public_target"])


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("freeze", "produce"):
        raise SystemExit("usage: prepare_sage.py freeze|produce")
    {"freeze": freeze, "produce": produce}[sys.argv[1]]()

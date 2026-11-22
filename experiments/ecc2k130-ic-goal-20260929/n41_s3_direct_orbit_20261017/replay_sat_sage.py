"""Independently replay a CryptoMiniSat orbit model as an elliptic relation."""
import hashlib
import itertools
import json
from pathlib import Path
from sage.all import GF, PolynomialRing, EllipticCurve

import circuit

D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def parse_model(path):
    lines = path.read_text().splitlines()
    assert "s SATISFIABLE" in lines
    values = {}
    for line in lines:
        if not line.startswith("v "):
            continue
        for token in line.split()[1:]:
            literal = int(token)
            if literal == 0:
                continue
            index = abs(literal)
            value = literal > 0
            assert index not in values or values[index] == value
            values[index] = value
    assert values
    return values


def main():
    q = read(D / "query_protocol_v2.json")
    result = read(D / "query_v2_result.json")
    build = read(D / "build_result.json")
    assert result["status"] == "SAT_PENDING_REPLAY"
    assert sha(D / "solver_v2.stdout") == result["stdout_sha256"]
    for name, digest in q["sources"].items():
        assert sha(D / name) == digest, name
    model = parse_model(D / "solver_v2.stdout")
    machine, wires = circuit.build(build["target_reciprocal"])
    assert machine.and_count == build["and_gates"]
    assert len(machine.clauses) == build["ordinary_clauses"]
    selected = [j for j, wire in enumerate(wires["target_selector"]) if model[wire]]
    assert len(selected) == 1
    orbit_index = selected[0]
    geometry = read(ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json")
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, "t", modulus=t**41 + t**3 + 1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def dec(word):
        return field(ring([(int(word) >> i) & 1 for i in range(41)]))

    def point(pair):
        return curve(dec(pair[0]), dec(pair[1]))

    qraw = point(read(D / "protocol.json")["public_raw_point"])
    target = curve(qraw[0] ** (1 << orbit_index), qraw[1] ** (1 << orbit_index))
    candidates = []
    code_masks = []
    for slot in range(6):
        packed = sum((1 << j) for j, wire in enumerate(wires["codes"][slot]) if model[wire])
        mask = sum(((packed >> j) & 1) << bit
                   for j, bit in enumerate(wires["source_bits"]))
        code_masks.append(mask)
        c_word = sum((1 << bit) for bit, wire in enumerate(wires["outputs"][slot]) if model[wire])
        c = dec(c_word)
        assert c != 0
        rotated = c ** (1 << geometry["rotations"][slot])
        x = rotated ** (-1)
        possibilities = []
        for sid, state in enumerate(geometry["blocks"][slot]["states"]):
            if state["a"] == mask and dec(state["raw_sum"][0]) == x:
                possibilities.append((sid, point(state["raw_sum"]), frozenset(state["columns"])))
        assert len(possibilities) == 2
        candidates.append(possibilities)
    matches = []
    for choice in itertools.product(*candidates):
        columns = [column for _, _, cols in choice for column in cols]
        if len(set(columns)) != 12:
            continue
        total = sum((point for _, point, _ in choice), curve(0))
        if total != target:
            continue
        pulled = [curve(point[0] ** (1 << ((41 - orbit_index) % 41)),
                        point[1] ** (1 << ((41 - orbit_index) % 41)))
                  for _, point, _ in choice]
        assert sum(pulled, curve(0)) == qraw
        matches.append([sid for sid, _, _ in choice])
    audit = {"status": "PASS_NEW_ORBIT_RELATION_GROUP_REPLAY" if matches else "MODEL_NO_GROUP_WITNESS",
             "query_result_sha256": sha(D / "query_v2_result.json"),
             "solver_stdout_sha256": sha(D / "solver_v2.stdout"),
             "audit_source_sha256": sha(D / "replay_sat_sage.py"),
             "orbit_index": orbit_index,
             "code_masks": code_masks,
             "state_candidates": [[sid for sid, _, _ in group] for group in candidates],
             "verified_state_ids": matches,
             "assigned_model_variables": len(model),
             "curve_order": int(curve.cardinality())}
    (D / "sat_group_replay.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()

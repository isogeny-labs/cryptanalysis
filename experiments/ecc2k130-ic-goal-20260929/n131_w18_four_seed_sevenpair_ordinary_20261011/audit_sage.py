"""Independent Sage replay of public residuals and any seven-pair model."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
POOL = ROOT / "n131_w18_terminal_fiber_20261011" / "pool.json"
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010" / "support_w18.tsv"
R = 680564733841876926932320129493409985129
ROTATIONS = (0, 16, 32, 48, 64, 80, 96)
SOURCE_BITS = tuple(bit for bit in range(18) if bit != 7)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    query = json.loads((HERE / "query_result.json").read_text())
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    pool = json.loads(POOL.read_text())
    assert runtime["status"] == "verified"
    assert query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert query["public_target"] == protocol["public_target"]
    assert len(pool["states"]) == 32
    poly = PolynomialRing(GF(2), "t")
    t = poly.gen()
    field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def decode(integer):
        return sum((field(t**bit) for bit in range(131) if integer >> bit & 1),
                   field.zero())

    def encode(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    def point(row):
        return curve([decode(row[0]), decode(row[1])])

    def coordinate(mask):
        return decode(sum(1 << (bit + 1) for bit in range(18)
                          if mask >> bit & 1))

    def halftrace(value):
        out, term = field.zero(), value
        for _ in range(66):
            out += term
            term = term**4
        assert out**2 + out == value
        return out

    def options(mask):
        u = halftrace(coordinate(mask))
        assert u != 0
        x = field.one() + 1/u
        rows = curve.lift_x(x, all=True)
        assert len(rows) == 2
        return rows

    torsion = [curve(0) if row is None else point(row)
               for row in (None, [0, 1], [1, 0], [1, 1])]
    assert len(set(torsion)) == 4
    assert all(4*offset == curve(0) for offset in torsion)
    public = point(protocol["public_target"])
    assert R*public == curve(0)
    canonical = pow(4, -1, R)*public
    preimages = [canonical + offset for offset in torsion]
    assert all(4*row == public for row in preimages)
    terminals = [point(row["rotated_raw_point"]) for row in pool["states"]]
    assert len(set(terminals)) == 32
    assert len(query["raw_preimages"]) == 4
    assert len(query["residuals"]) == 128
    for raw_index, raw in enumerate(preimages):
        assert [encode(raw[0]), encode(raw[1])] == query["raw_preimages"][raw_index]
        for terminal_index, terminal in enumerate(terminals):
            residual = raw-terminal
            row = query["residuals"][32*raw_index + terminal_index]
            assert row["preimage_index"] == raw_index
            assert row["terminal_state_index"] == terminal_index
            assert residual != curve(0) and residual[0] not in (0, 1)
            assert [encode(residual[0]), encode(residual[1])] == row["point"]
            assert encode(1/residual[0]) == row["standard_reciprocal"]

    receipt = {"candidate_id": None, "curve_id": protocol["curve_id"],
               "public_target": protocol["public_target"],
               "public_preimages": 4, "terminal_states": 32,
               "independently_checked_residuals": 128,
               "query_status": query["status"],
               "sha256": {"audit": sha(Path(__file__)),
                          "protocol": sha(HERE / "protocol.json"),
                          "query": sha(HERE / "query_result.json"),
                          "runtime": sha(HERE / "sage_runtime_info.json"),
                          "support": sha(SUPPORT), "pool": sha(POOL)}}
    if query["status"] == "SAT_PENDING_GROUP_REPLAY":
        model = json.loads((HERE / "decoded_model.json").read_text())
        assert model["formula_sha256"] == query["formula"]["xcnf_sha256"]
        choice = model["selected_choice_index"]
        assert choice == 32*model["selected_preimage_index"] + model["selected_terminal_state_index"]
        target = preimages[choice // 32] - terminals[choice % 32]
        assert encode(1/target[0]) == query["residuals"][choice]["standard_reciprocal"]
        columns = {int(a): int(b) for a, b in
                   (line.split() for line in SUPPORT.read_text().splitlines())}
        folded = []
        pair_choices = []
        masks = []
        for slot, (code, delta, reciprocal, rotation) in enumerate(zip(
                model["selected_codes"], model["seed_deltas"],
                model["pair_reciprocals"], ROTATIONS)):
            a = sum(((code >> i) & 1) << bit for i, bit in enumerate(SOURCE_BITS))
            seed = 212 ^ delta
            b = a ^ seed
            assert seed in (212, 213, 214, 215)
            assert a in columns and b in columns and columns[a] != columns[b]
            masks.append([a, b])
            folded.extend((columns[a], columns[b]))
            assert coordinate(a)*decode(model["inverse_witnesses"][slot][0]) == 1
            assert coordinate(b)*decode(model["inverse_witnesses"][slot][1]) == 1
            assert decode(model["inverse_witnesses"][slot][0]).trace() == 0
            assert decode(model["inverse_witnesses"][slot][1]).trace() == 0
            candidates = []
            for left_index, left in enumerate(options(a)):
                for right_index, right in enumerate(options(b)):
                    combined = left + right
                    if combined == curve(0) or combined[0] == 0:
                        continue
                    if encode(1/combined[0]) == reciprocal:
                        rotated = curve([combined[0]**(2**rotation),
                                         combined[1]**(2**rotation)])
                        candidates.append((rotated, (left_index, right_index)))
            assert candidates, (slot, code, delta)
            pair_choices.append(candidates)
        terminal_columns = pool["states"][choice % 32]["folded_columns"]
        assert len(set(folded + terminal_columns)) == 16
        states = [(curve(0), [])]
        for slot, candidates in enumerate(pair_choices):
            next_states = []
            for previous, history in states:
                for pair_point, signs in candidates:
                    total = previous + pair_point
                    if total == curve(0) or total[0] == 0:
                        continue
                    expected = (model["middle_reciprocals"][slot-1]
                                if 1 <= slot <= 5 else
                                query["residuals"][choice]["standard_reciprocal"]
                                if slot == 6 else None)
                    if expected is None or encode(1/total[0]) == expected:
                        next_states.append((total, [*history, signs]))
            states = next_states
            assert states, slot
        witnesses = [history for total, history in states if total == target]
        assert witnesses
        assert target + terminals[choice % 32] == preimages[choice // 32]
        assert 4*(target + terminals[choice % 32]) == public
        receipt.update({"status": "PASS_INDEPENDENT_SAGE_ORDINARY_SEVENPAIR_RELATION",
                        "selected_choice_index": choice,
                        "source_masks": masks,
                        "folded_columns": folded,
                        "source_sign_choices": witnesses[0],
                        "exact_group_witnesses": len(witnesses),
                        "raw_target_preimage": query["raw_preimages"][choice // 32]})
    else:
        assert query["status"] in ("BOUNDED_UNKNOWN", "UNSAT", "MODEL_DECODE_FAILURE")
        receipt["status"] = "PASS_INDEPENDENT_SAGE_ALL_128_PUBLIC_RESIDUALS"
    with (HERE / "sage_audit_result.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(receipt["status"])


if __name__ == "__main__":
    main()

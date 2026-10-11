#!/usr/bin/env sage -python
"""Independent one-target IC/rho replay and exclusive phase audit."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "n41_w7_entropy_cubic_20261011/w8"
JOIN = HERE.parent / "n41_w8_sixpair_mitm_20261011"
LOGS = HERE.parent / "n41_w8_sixpair_logprep_20261011"
R = 549756390943
ROTATIONS = (0, 7, 14, 21, 28, 35)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    prepared = json.loads((HERE / "preparation_result.json").read_text())
    ic = json.loads((HERE / "ic_result.json").read_text())
    rho = json.loads((HERE / "rho_result.json").read_text())
    secret = json.loads((HERE / "secret_audit.json").read_text())
    logs = json.loads((LOGS / "audit_result.json").read_text())
    geometry = json.loads((BASE / "geometry.json").read_text())
    assert protocol["source_sha256"]["online_source"] == sha(HERE / "online.cpp")
    assert protocol["source_sha256"]["public_target"] == sha(HERE / "public_target.tsv")
    assert protocol["source_sha256"]["state_logs"] == sha(HERE / "state_logs.tsv")
    assert prepared["secret_audit_sha256"] == sha(HERE / "secret_audit.json")
    assert ic["protocol_sha256"] == rho["protocol_sha256"] == sha(HERE / "protocol.json")
    assert all(item["status"] == "SCALAR_FOUND_PENDING_INDEPENDENT_SAGE_REPLAY"
               for item in (ic, rho))
    assert all(item["stop_reason"] is None and item["exit_code"] == 0
               for item in (ic, rho))
    for mode, record in (("ic", ic), ("rho", rho)):
        assert record["stdout_sha256"] == sha(HERE / f"{mode}.stdout.txt")
        assert record["stderr_sha256"] == sha(HERE / f"{mode}.stderr.txt")
        assert not (HERE / f"{mode}.stderr.txt").read_bytes()
        assert record["public_target"] == protocol["public_target"]
        assert record["generator_projected"] == protocol["generator_projected"]
        assert record["worker_count"] == 1
        assert record["combined_peak_rss_bytes_sampled"] < 4*1024**3
    assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"
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

    def frobenius(point, exponent):
        return curve(point[0]**(1 << exponent), point[1]**(1 << exponent))

    generator = curve(*map(dec, protocol["generator_projected"]))
    target = curve(*map(dec, protocol["public_target"]))
    assert R * generator == R * target == curve(0)
    assert xy(generator) == secret["generator_projected"]
    assert xy(target) == secret["public_target"]
    secret_scalar = int(secret["scalar_mod_r"])
    assert secret_scalar * generator == target
    panel_scalars = {int(line.split()[3]) for line in
                     (LOGS / "panel.tsv").read_text().splitlines()[1:]}
    assert secret_scalar not in panel_scalars
    assert secret_scalar != int(logs["recovered_public_target"]["target_log_mod_r"])

    ic_cells = ic["result_line"].split()
    rho_cells = rho["result_line"].split()
    assert len(ic_cells) == 17 and ic_cells[0] == "IC_RESULT"
    assert len(rho_cells) == 10 and rho_cells[0] == "RHO_RESULT"
    ic_scalar = int(ic_cells[1])
    rho_scalar = int(rho_cells[1])
    assert ic_scalar == rho_scalar == secret_scalar
    assert ic_scalar * generator == target
    assert rho_scalar * generator == target
    raw_index = int(ic_cells[2])
    state_ids = list(map(int, ic_cells[3:9]))
    probes = int(ic_cells[9])
    ic_phases = list(map(int, ic_cells[10:15]))
    ic_online, ic_measured = map(int, ic_cells[15:17])
    assert sum(ic_phases) == ic_online == ic_measured
    rho_steps, rho_dp, rho_collisions = map(int, rho_cells[2:5])
    rho_phases = list(map(int, rho_cells[5:8]))
    rho_online, rho_measured = map(int, rho_cells[8:10])
    assert sum(rho_phases) == rho_online == rho_measured
    assert rho_steps > 0 and rho_dp > 0 and rho_collisions > 0
    assert 0 <= raw_index < 4 and len(state_ids) == 6
    assert probes >= 0

    rows = {int(item["mask"]): item for item in geometry["rows"]}
    edges = [(a, a ^ 184) for a in sorted(rows)
             if a < (a ^ 184) and a ^ 184 in rows
             and rows[a]["column"] != rows[a ^ 184]["column"]]
    assert len(edges) == 35
    raw = {mask: curve(*map(dec, item["raw_point"])) for mask, item in rows.items()}
    torsion = []
    for line in (HERE / "torsion.tsv").read_text().splitlines()[1:]:
        tag, index, x, y = line.split()
        assert tag == "T" and int(index) == len(torsion)
        torsion.append(curve(0) if int(x) < 0 else curve(dec(x), dec(y)))
    assert len(torsion) == 4 and all(4*point == curve(0) for point in torsion)
    expected_raw0 = pow(4, -1, R) * target
    expected_raw = expected_raw0 + torsion[raw_index]
    assert 4 * expected_raw == target
    running = curve(0)
    occupied_edges, occupied_columns = set(), set()
    relation_scalar = 0
    state_log_table = {}
    for line in (HERE / "state_logs.tsv").read_text().splitlines()[1:]:
        tag, slot, sid, value = line.split()
        assert tag == "L"
        state_log_table[(int(slot), int(sid))] = int(value)
    assert len(state_log_table) == 840
    source_pairs = []
    for slot, sid in enumerate(state_ids):
        edge, choice = divmod(sid, 4)
        a, b = edges[edge]
        assert edge not in occupied_edges
        occupied_edges.add(edge)
        sa, sb = divmod(choice, 2)
        first = -raw[a] if sa else raw[a]
        second = -raw[b] if sb else raw[b]
        rotated = frobenius(first + second, ROTATIONS[slot])
        running += rotated
        assert 4 * rotated == state_log_table[(slot, sid)] * generator
        relation_scalar = (relation_scalar + state_log_table[(slot, sid)]) % R
        occupied_columns.update((int(rows[a]["column"]), int(rows[b]["column"])))
        source_pairs.append({"slot": slot, "state_id": sid, "edge": edge,
                             "masks": [a, b], "source_sign_bits": [sa, sb],
                             "rotation": ROTATIONS[slot], "rotated_pair": xy(rotated)})
    assert len(occupied_edges) == 6 and len(occupied_columns) == 12
    assert running == expected_raw
    assert 4 * running == target
    assert relation_scalar == ic_scalar

    speedup = rho_online / ic_online
    result = {"status": "PASS_INDEPENDENT_N41_HELDOUT_IC_RHO_REPLAY",
              "candidate_id": None, "curve_id": protocol["curve_id"],
              "workload_id": protocol["workload_id"], "target_count": 1,
              "public_target": xy(target), "generator_projected": xy(generator),
              "recovered_scalar_mod_r": str(ic_scalar),
              "secret_scalar_matches": True,
              "raw_preimage_index": raw_index, "raw_preimage_replayed": xy(running),
              "source_edges_distinct": len(occupied_edges),
              "folded_columns_distinct": len(occupied_columns),
              "source_pairs": source_pairs,
              "ic_online_phases_ns": dict(zip(
                  ("target_query", "target_PDP", "target_relation_check",
                   "target_descent", "target_recovery_check"), ic_phases)),
              "ic_online_ns": ic_online,
              "rho_online_phases_ns": dict(zip(
                  ("target_partition_setup", "walk_and_collision", "scalar_check"),
                  rho_phases)),
              "rho_online_ns": rho_online, "rho_steps": rho_steps,
              "rho_distinguished_points": rho_dp,
              "rho_collisions": rho_collisions,
              "rho_over_ic_online_ratio_exploratory": speedup,
              "timing_status": "EXPLORATORY_UNISOLATED_HOST_AND_EXTERNAL_SAGE_REPLAY",
              "correctness_replay_outside_native_online_interval": True,
              "source_sha256": {"script": sha(Path(__file__)),
                                "protocol": sha(HERE / "protocol.json"),
                                "ic_result": sha(HERE / "ic_result.json"),
                                "rho_result": sha(HERE / "rho_result.json"),
                                "sealed_scalar": sha(HERE / "secret_audit.json"),
                                "factor_logs": sha(LOGS / "audit_result.json"),
                                "sage_runtime": sha(HERE / "sage_runtime_info.json")}}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], format(speedup, ".6g"), ic_scalar)


if __name__ == "__main__":
    main()

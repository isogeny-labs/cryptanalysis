"""Checked-Sage conductor-2 degree-3 graph and projected Hecke rank."""
from hashlib import sha256
import json
from pathlib import Path
import sys

from sage.all import EllipticCurve_from_j, QQ, PolynomialRing, classical_modular_polynomial, hilbert_class_polynomial, matrix

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "hecke-two-sheet-small-order-20261023"
sys.path.insert(0, str(PARENT / "tools"))
import hecke11 as H


def main():
    protocol_raw = (HERE / "protocol.json").read_bytes()
    protocol = json.loads(protocol_raw)
    assert protocol["status"] == "FROZEN_BEFORE_FIBER_GATE"
    p, d = protocol["p"], protocol["d"]
    assert protocol["conductor2_class_number"] == 38
    funcs, jfun = H.build([3])
    rd = H.Reduced(p, funcs, jfun, [3])
    js = hilbert_class_polynomial(-4*d).change_ring(rd.Fp).roots(multiplicities=False)
    assert len(js) == 38
    points = []
    for j in js:
        model = EllipticCurve_from_j(j)
        assert abs(int(model.trace_of_frobenius())) == 20
        assert int(model.endomorphism_order().conductor()) == 2
        lifts = rd.points_with_j(j)
        assert len(lifts) == 1
        points.extend(lifts)
    points.sort(key=lambda q: (int(q[0]), int(q[1])))
    idx = {q: i for i, q in enumerate(points)}
    assert len(idx) == 38
    phi3 = classical_modular_polynomial(3)
    jring = PolynomialRing(rd.Fp, 'J')
    J = jring.gen()
    edges = set()
    rows = []
    neighbour_counts = {}
    for i, q in enumerate(points):
        all_neighbours = rd.neighbours_all(3, q)
        assert all_neighbours is not None and len(all_neighbours) == 4
        assert sum(int(m) for _,m in rd.neighbour_x(3,q).roots()) == 4
        assert sum(int(m) for _,m in jring(phi3(rd.j(q),J)).roots()) == 4
        assert all(phi3(rd.j(q),rd.j(z)) == 0 for z in all_neighbours)
        assert sum(all_neighbours, rd.E(0)) == rd.a_l[3] * q
        same = [idx[z] for z in all_neighbours if z in idx]
        neighbour_counts[str(len(same))] = neighbour_counts.get(str(len(same)), 0) + 1
        assert len(same) == 2 and len(set(same)) == 2
        for j in same:
            assert i != j
            edges.add(tuple(sorted((i, j))))
        row = [0] * len(points)
        for j in same: row[j] += 1
        row[i] -= rd.a_l[3]
        rows.append(row)
    assert len(edges) == 38
    adjacency = {i: set() for i in range(len(points))}
    for i, j in edges:
        adjacency[i].add(j); adjacency[j].add(i)
    assert all(len(v) == 2 for v in adjacency.values())
    unseen = set(adjacency)
    components = []
    while unseen:
        start = min(unseen)
        stack = [start]
        comp = set()
        while stack:
            u = stack.pop()
            if u in comp: continue
            comp.add(u); stack.extend(adjacency[u] - comp)
        unseen -= comp
        components.append(sorted(comp))
    lengths = sorted(map(len, components))
    assert lengths == protocol["primary_prediction"]["conductor2_degree3_cycles"]
    projected = matrix(QQ, rows)
    projected_rank = int(projected.rank())
    projected_determinant = int(projected.det())
    out = {
        "status": "PASS_ONE_SHEET_TWO_19_CYCLES",
        "protocol_sha256": sha256(protocol_raw).hexdigest(),
        "script_sha256": sha256((HERE / "walk.py").read_bytes()).hexdigest(),
        "hecke11_source_sha256": sha256((PARENT / "tools/hecke11.py").read_bytes()).hexdigest(),
        "p": p, "d": d, "a3": rd.a_l[3],
        "x0_11_model": [int(x) for x in H.AINV],
        "x0_11_group_order": int(rd.E.order()),
        "conductor2_points": len(points),
        "j_values": [int(rd.j(q)) for q in points],
        "points": [[int(q[0]), int(q[1])] for q in points],
        "degree3_horizontal_edges": sorted(map(list, edges)),
        "degree3_horizontal_neighbours_per_point": neighbour_counts,
        "cycles": components,
        "cycle_lengths": lengths,
        "projected_degree3_rank_QQ": projected_rank,
        "projected_degree3_determinant_ZZ": projected_determinant,
        "projected_degree3_kernel_dimension_QQ": len(points) - projected_rank,
        "candidate_id": None, "timing_claim": None,
    }
    (HERE / "walk.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("status", "a3", "conductor2_points", "cycle_lengths", "projected_degree3_rank_QQ", "projected_degree3_kernel_dimension_QQ")}, sort_keys=True))


if __name__ == "__main__":
    main()

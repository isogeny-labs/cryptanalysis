"""Independent standard-Python audit of the saved fiber and cycle graph."""
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'hecke-two-sheet-small-order-20261023'


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def rank_mod(rows, prime):
    a = [[v % prime for v in row] for row in rows]
    r = 0
    for c in range(len(a[0])):
        pivot = next((i for i in range(r, len(a)) if a[i][c]), None)
        if pivot is None:
            continue
        a[r], a[pivot] = a[pivot], a[r]
        inv = pow(a[r][c], -1, prime)
        a[r] = [(v * inv) % prime for v in a[r]]
        for i in range(r + 1, len(a)):
            if a[i][c]:
                factor = a[i][c]
                a[i] = [(v - factor * w) % prime for v, w in zip(a[i], a[r])]
        r += 1
    return r


def determinant_bareiss(rows):
    a = [row[:] for row in rows]
    n = len(a); prior = 1; sign = 1
    for k in range(n-1):
        if a[k][k] == 0:
            pivot = next((i for i in range(k+1,n) if a[i][k]), None)
            if pivot is None: return 0
            a[k],a[pivot] = a[pivot],a[k]; sign = -sign
        pivot = a[k][k]
        for i in range(k+1,n):
            for j in range(k+1,n):
                num = a[i][j]*pivot - a[i][k]*a[k][j]
                assert num % prior == 0
                a[i][j] = num//prior
            a[i][k] = 0
        prior = pivot
    return sign*a[-1][-1]


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    fiber = json.loads((HERE / "fiber_gate_raw.json").read_text())
    walk = json.loads((HERE / "walk.json").read_text())
    assert protocol["p"] == fiber["p"] == walk["p"] == 10891
    assert protocol["dk"] == fiber["dk"] == -1199
    assert protocol["u_abs"] == fiber["u"] == 20
    assert 20*20 - 4*10891 == -1199*36
    assert (20*20 - 4*10891) % 11 == 0
    assert {t: [x for x in range(11) if (x*x-t*x+10891)%11 == 0]
            for t in (20,-20)} == {20:[10],-20:[1]}
    assert fiber["status"] == "FAIL_UNIFORM_TWO_SHEET_GATE"
    assert fiber["script_sha256"] == sha(PARENT/'fiber_gate.py')
    for f, h in ((1,38),(2,38),(3,76),(6,76)):
        s = fiber["strata"][str(f)]
        assert s == {"class_number":h, "rational_j_count":h,
                     "rational_point_count":h, "points_per_j":{"1":h}}
    assert len(fiber["exceptions"]) == sum((38,38,76,76))
    assert walk["protocol_sha256"] == sha(HERE / "protocol.json")
    assert walk["script_sha256"] == sha(HERE / "walk.py")
    assert walk["hecke11_source_sha256"] == sha(PARENT/'tools/hecke11.py')
    assert walk["conductor2_points"] == 38
    assert len(set(walk["j_values"])) == 38
    assert len(set(map(tuple, walk["points"]))) == 38
    edges = {tuple(x) for x in walk["degree3_horizontal_edges"]}
    assert len(edges) == 38 and all(0 <= a < b < 38 for a,b in edges)
    adj = [set() for _ in range(38)]
    for a,b in edges: adj[a].add(b); adj[b].add(a)
    assert all(len(s) == 2 for s in adj)
    unseen = set(range(38)); sizes = []
    while unseen:
        todo = [min(unseen)]; seen = set()
        while todo:
            x = todo.pop()
            if x not in seen:
                seen.add(x); todo.extend(adj[x]-seen)
        unseen -= seen; sizes.append(len(seen))
    assert sorted(sizes) == [19,19] == walk["cycle_lengths"]
    assert walk["a3"] == -1
    rows = [[int(i==j) + int(j in adj[i]) for j in range(38)] for i in range(38)]
    ranks = {str(q):rank_mod(rows,q) for q in (101,1000000007,2147483647)}
    assert set(ranks.values()) == {38}
    assert walk["projected_degree3_rank_QQ"] == 38
    determinant = determinant_bareiss(rows)
    assert determinant == walk["projected_degree3_determinant_ZZ"] == 9
    out = {"status":"PASS_INDEPENDENT_RAMIFIED_FIBER_AND_GRAPH_REPLAY",
           "protocol_sha256":sha(HERE/'protocol.json'),
           "fiber_gate_sha256":sha(HERE/'fiber_gate_raw.json'),
           "walk_sha256":sha(HERE/'walk.json'),
           "validator_sha256":sha(HERE/'validate.py'),
           "stratum_point_counts":{"1":38,"2":38,"3":76,"6":76},
           "conductor2_cycle_lengths":sorted(sizes),
           "projected_rank_mod_primes":ranks,
           "projected_determinant_ZZ":determinant,
           "candidate_id":None,"timing_claim":None}
    (HERE/'validation.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__ == '__main__':
    main()

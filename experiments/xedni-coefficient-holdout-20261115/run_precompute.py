"""Public group search with the frozen 14-vector family through first hit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRAIN = HERE.parent / "xedni-coefficient-family-control-20261115"
HOLD = HERE.parent / "xedni-nonisomorphic-holdout-20261115"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def add(P, Q, p):
    if P is None: return Q
    if Q is None: return P
    x1, y1 = P; x2, y2 = Q
    if x1 == x2 and (y1+y2) % p == 0: return None
    slope = ((3*x1*x1-1)*pow(2*y1,-1,p)) % p if x1 == x2 else \
            ((y2-y1)*pow((x2-x1) % p,-1,p)) % p
    x3 = (slope*slope-x1-x2) % p
    return (x3,(slope*(x1-x3)-y1) % p)

def neg(P,p):
    return None if P is None else (P[0],-P[1] % p)

def mul(k,P,p):
    if k < 0: return mul(-k,neg(P,p),p)
    R = None
    while k:
        if k & 1: R = add(R,P,p)
        P = add(P,P,p); k >>= 1
    return R

def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    for key, path in (("training_family_protocol_sha256",TRAIN / "protocol.json"),
                      ("training_family_source_sha256",TRAIN / "run.py"),
                      ("holdout_selection_sha256",HOLD / "selection.json"),
                      ("holdout_relation_result_sha256",HOLD / "relation-result.json")):
        assert sha(path) == protocol[key], key
    vectors = [tuple(c) for c in protocol["coefficient_family"]]
    assert len(vectors) == 14 and (1,2) in vectors and (1,-1) in vectors
    selected = json.loads((HOLD / "selection.json").read_text())["selected"]
    parent = json.loads((HOLD / "relation-result.json").read_text())
    fields = []
    for (p,q), old in zip(selected,parent["fields"]):
        assert (p,q) == (old["field_prime"],old["subgroup_order"])
        G = (2 % p,2 % p)
        Q = mul(17,G,p)  # construct the public fixture before querying
        minus_G = neg(G,p)
        sampled = [Q]
        for _ in range(1,q): sampled.append(add(sampled[-1],minus_G,p))
        rows = []; tests = 0; admitted = 0; hit = None
        for t1,U in enumerate(sampled):
            if hit: break
            for t2,V in enumerate(sampled):
                index = t1*q+t2+1
                if U is None or V is None or U == V:
                    rows.append({"t":[t1,t2],"status":"excluded","tests":[]})
                    continue
                admitted += 1
                checks = []
                for a,b in vectors:
                    relation = add(mul(a,U,p),mul(b,V,p),p) is None
                    tests += 1
                    checks.append([a,b,int(relation)])
                    if relation:
                        C = (a+b) % q
                        assert C != 0
                        recovered = ((a*t1+b*t2)*pow(C,-1,q)) % q
                        assert mul(recovered,G,p) == Q
                        hit = {"t":[t1,t2],"vector":[a,b],
                               "query_index_one_based":index,
                               "vector_tests_to_hit":tests,
                               "admitted_queries_to_hit":admitted,
                               "recovered_scalar":recovered}
                        break
                rows.append({"t":[t1,t2],"status":"hit" if hit else "nonrelation","tests":checks})
                if hit: break
        assert hit is not None
        path = HERE / f"p{p}-prefix.jsonl"
        path.write_text(''.join(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n" for row in rows))
        fields.append({"field_prime":p,"subgroup_order":q,"first_family":hit,
                       "first_fixed_vector":old["first_direct"],
                       "first_rational":old["first_rational"],
                       "prefix_rows":len(rows),"prefix_path":path.name,"prefix_sha256":sha(path)})
    print(json.dumps({"schema":"xedni-coefficient-holdout-result-v1","status":"PASS",
                      "protocol_sha256":sha(HERE / "protocol.json"),
                      "source_sha256":sha(Path(__file__)),
                      "holdout_result_sha256":sha(HOLD / "relation-result.json"),
                      "family_size":len(vectors),"fields":fields},sort_keys=True,indent=2))

if __name__ == "__main__":
    main()

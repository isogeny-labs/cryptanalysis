"""Independent checked-Sage replay and operation-accounting audit."""
import gzip
import hashlib
import json
import math
from pathlib import Path
from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
TRAIN = HERE.parent / "xedni-coefficient-family-control-20261115"
HOLD = HERE.parent / "xedni-nonisomorphic-holdout-20261115"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def mul_add_calls(k):
    k = abs(k)
    return k.bit_length() + k.bit_count()

protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
old_result = json.loads((HERE / "result-precompute.json").read_text())
holdout = json.loads((HOLD / "relation-result.json").read_text())
assert result["protocol_sha256"] == sha(HERE / "protocol.json")
assert result["source_sha256"] == sha(HERE / "run.py")
assert old_result["protocol_sha256"] == sha(HERE / "protocol-initial.json")
assert old_result["source_sha256"] == sha(HERE / "run_precompute.py")
assert result["holdout_result_sha256"] == protocol["holdout_relation_result_sha256"] == sha(HOLD / "relation-result.json")
assert protocol["training_family_protocol_sha256"] == sha(TRAIN / "protocol.json")
assert protocol["training_family_source_sha256"] == sha(TRAIN / "run.py")
vectors = [(a,b) for a in range(1,4) for b in range(-3,4) if b and math.gcd(a,abs(b)) == 1]
assert [list(v) for v in vectors] == protocol["coefficient_family"]
fields = []
for row, old_row, parent in zip(result["fields"],old_result["fields"],holdout["fields"]):
    p,q = row["field_prime"],row["subgroup_order"]
    assert p == old_row["field_prime"] == parent["field_prime"]
    assert q == old_row["subgroup_order"] == parent["subgroup_order"]
    E = EllipticCurve(GF(p),[-1,-2]);G=E(2,2);Q=17*G
    assert int(E.cardinality()) == q and int(G.order()) == q
    raw = HERE / row["prefix_path"]
    assert sha(raw) == row["prefix_sha256"] == old_row["prefix_sha256"]
    saved = [json.loads(line) for line in raw.read_text().splitlines()]
    assert len(saved) == row["prefix_rows"] == 35
    assert row["first_family"]["t"] == [0,34]
    assert row["first_family"]["query_index_one_based"] == 35
    assert row["first_fixed_vector"] == parent["first_direct"]
    assert row["first_rational"] == parent["first_rational"]
    tests=admitted=add_calls=0
    first=None
    for index, saved_row in enumerate(saved):
        t1,t2=saved_row["t"]
        assert [t1,t2] == [0,index]
        U,V=Q-t1*G,Q-t2*G
        if U.is_zero() or V.is_zero() or U==V:
            assert saved_row["status"] == "excluded" and saved_row["tests"] == []
            continue
        admitted += 1
        expected=[]
        for a,b in vectors:
            relation=(a*U+b*V).is_zero()
            tests += 1
            add_calls += mul_add_calls(a)+mul_add_calls(b)+1
            expected.append([a,b,int(relation)])
            if relation:
                assert (a+b) % q != 0
                recovered=((a*t1+b*t2)*pow((a+b)%q,-1,q)) % q
                assert recovered*G == Q
                first={"t":[t1,t2],"vector":[a,b],
                       "query_index_one_based":index+1,
                       "vector_tests_to_hit":tests,
                       "group_add_calls_to_hit":add_calls+index,
                       "admitted_queries_to_hit":admitted,
                       "recovered_scalar":recovered}
                break
        assert saved_row["tests"] == expected
        assert saved_row["status"] == ("hit" if first else "nonrelation")
        if first: break
    assert first == row["first_family"]
    assert tests == 452 and add_calls+34 == 3065
    first_fixed=None
    for t2 in range(q):
        U,V=Q,Q-t2*G
        if U.is_zero() or V.is_zero() or U==V: continue
        if (U+2*V).is_zero():
            first_fixed={"t":[0,t2],"query_index_one_based":t2+1}
            break
    assert first_fixed["query_index_one_based"] == parent["first_direct"]["query_index_one_based"]
    assert first_fixed["t"] == parent["first_direct"]["t"]
    membership=admitted_parent=0
    stop=parent["first_rational"]["query_index_one_based"]
    with gzip.open(HOLD / parent["raw_path"],"rt") as stream:
        for index in range(stop):
            item=json.loads(next(stream))
            assert item["t"] == [index//q,index%q]
            membership += len(item["s"])
            admitted_parent += sum(code in ("N","R") for code in item["s"])
            assert ("R" in item["s"]) == (index==stop-1)
    assert membership == stop*len(parent["models"])
    fields.append({"field_prime":p,"subgroup_order":q,
                   "family_first_query":35,"family_vector_tests":tests,
                   "family_group_add_calls":add_calls+34,
                   "fixed_first_query":first_fixed["query_index_one_based"],
                   "rational_first_query":stop,
                   "rational_membership_checks_to_hit":membership,
                   "rational_admitted_relation_tests_to_hit":admitted_parent})
print(json.dumps({"schema":"xedni-coefficient-holdout-audit-v1","status":"PASS",
                  "fields":fields},sort_keys=True,indent=2))

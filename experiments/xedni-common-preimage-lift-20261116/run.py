"""Screen all frozen relations and construct common-preimage rational lifts."""
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())
paths = {"rows": ROOT / "xedni-vector-shift-lift-search-20261116" / "rows.jsonl",
         "registry": ROOT / "xedni-crt-band-panel-20261115" / "result.json",
         "family": ROOT / "xedni-coefficient-optimization-20261115" / "family-selection.json"}
for kind, path in paths.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == protocol[{
        "rows": "source_rows_sha256", "registry": "source_registry_sha256",
        "family": "selected_family_sha256"}[kind]]
fields = {f["field_prime"]: f for f in json.loads(paths["registry"].read_text())["fields"]}
vectors = {tuple(v) for v in json.loads(paths["family"].read_text())["selected"]}
assert len(fields) == 8 and len(vectors) == 13
deadline = time.monotonic() + protocol["run_cap_seconds"]


def centered(z, p):
    z = int(z) % p
    return z if z <= p//2 else z-p


def xy(point):
    return None if point.is_zero() else [int(point[0]), int(point[1])]


seen = set()
negative_by_field = Counter()
counts = Counter()
screen_path = HERE / "screen.jsonl"
lift_path = HERE / "lifts.jsonl"
with screen_path.open("w") as screens, lift_path.open("w") as lifts:
    for line in paths["rows"].open():
        raw = json.loads(line)
        if raw.get("kind") != "candidate":
            continue
        p, j = raw["field_prime"], raw["target_index"]
        t1,t2 = raw["offsets"]
        a,b = raw["vector"]
        key = (p,j,t1,t2,a,b)
        if key in seen:
            continue
        seen.add(key)
        assert (a,b) in vectors
        field = fields[p]
        q = field["subgroup_order"]
        finite = EllipticCurve(GF(p), [-1,-2])
        G = finite(*field["generator"])
        assert (q*G).is_zero()
        target = raw["fixture_scalar"]*G
        U,V = target-t1*G,target-t2*G
        assert xy(U) == raw["public_points"][0]
        assert xy(V) == raw["public_points"][1]
        relation = bool((a*U+b*V).is_zero())
        assert relation == raw["public_relation_diagnostic"]
        counts["screened"] += 1
        counts["public_relation"] += int(relation)
        screen = {"field_prime":p,"subgroup_order":q,"target_index":j,
                  "offsets":[t1,t2],"vector":[a,b],"fixture_scalar":raw["fixture_scalar"],
                  "U":xy(U),"V":xy(V),"public_relation":relation}
        screens.write(json.dumps(screen,sort_keys=True,separators=(",", ":"))+"\n")
        selected = relation or negative_by_field[p] < 4
        if not relation and selected:
            negative_by_field[p] += 1
        if not selected:
            continue
        counts["selected_lifts"] += 1
        record = dict(screen)
        record["kind"] = "positive" if relation else "negative_control"
        try:
            assert b % q != 0
            S = (pow(b,-1,q))*U
            assert b*S == U
            assert not S.is_zero()
            x,y = centered(S[0],p),centered(S[1],p)
            A,B = -1, y*y-x*x*x+x
            rational = EllipticCurve(QQ,[A,B])
            T = rational(x,y)
            P,R = b*T, -a*T
            assert (a*P+b*R).is_zero()
            assert A % p == p-1 and B % p == p-2
            assert int(rational.discriminant()) % p != 0
            rP = finite(GF(p)(P[0]),GF(p)(P[1]))
            rR = finite(GF(p)(R[0]),GF(p)(R[1]))
            assert rP == U
            assert rR == (-a)*S
            assert (rR == V) == relation
            record.update({"S":xy(S),"T":[x,y],"A":A,"B":B,
                           "P":[str(P[0]),str(P[1])],
                           "R":[str(R[0]),str(R[1])],
                           "P_reduction":xy(rP),"R_reduction":xy(rR),
                           "matches_U_V":bool(rP==U and rR==V),
                           "rational_relation":True,"status":"pass"})
            if relation:
                assert (a+b) % q != 0
                w = ((a*t1+b*t2)*pow(a+b,-1,q)) % q
                assert w*G == target and w == raw["fixture_scalar"]
                record["derived_scalar"] = w
                counts["positive_pass"] += 1
            else:
                counts["negative_control_pass"] += 1
        except Exception as error:
            record["status"] = "failure"
            record["error"] = f"{type(error).__name__}: {error}"
            counts["failure"] += 1
        lifts.write(json.dumps(record,sort_keys=True,separators=(",", ":"))+"\n")
        if time.monotonic() >= deadline:
            break

status = "complete" if counts["screened"] == 6656 and counts["public_relation"] == 127 and counts["selected_lifts"] == 159 and counts["failure"] == 0 else "capped_or_failed"
result = {"schema":"xedni-common-preimage-lift-result-v1","status":status,
          "counts":dict(sorted(counts.items())),"negative_controls_by_field":dict(sorted(negative_by_field.items())),
          "protocol_sha256":hashlib.sha256((HERE/"protocol.json").read_bytes()).hexdigest(),
          "screen_sha256":hashlib.sha256(screen_path.read_bytes()).hexdigest(),
          "lifts_sha256":hashlib.sha256(lift_path.read_bytes()).hexdigest()}
(HERE/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,indent=2,sort_keys=True))

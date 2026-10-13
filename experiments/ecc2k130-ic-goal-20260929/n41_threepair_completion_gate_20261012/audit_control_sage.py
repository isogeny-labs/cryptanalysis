"""Independent source-atom and group replay of the constructed triple hit."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
GEOMETRY = GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
ORDER = 549756390943


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "control_audit_protocol.json").read_text())
    files = {"script": HERE / "audit_control_sage.py", "pairs": SOURCE,
             "geometry": GEOMETRY, "fixture": HERE / "fixture.json",
             "control_result": HERE / "control_result.json",
             "control_stdout": HERE / "control.stdout", "runtime": HERE / "sage_runtime_info.json"}
    assert protocol["status"] == "FROZEN_BEFORE_INDEPENDENT_CONTROL_REPLAY"
    assert protocol["sha256"] == {key: sha(path) for key, path in files.items()}
    fixture = json.loads((HERE / "fixture.json").read_text())
    result = json.loads((HERE / "control_result.json").read_text())
    assert result["status"] == "HIT_PENDING_INDEPENDENT_REPLAY"
    parts = result["hit_line"].split()
    assert parts[0] == "HIT" and len(parts) == 11
    ids = list(map(int, parts[1:6]))
    assert ids == fixture["selected_subset_ids"]
    assert int(parts[6]) == int(parts[7]) == 1
    subset = []
    with SOURCE.open() as stream:
        assert stream.readline().split() == ["ECC2K41_ALLSEED4", "4", "4"]
        for line in stream:
            fields = line.split()
            if (fields[0] == "S" and int(fields[1]) == 0 and
                    int(fields[3]) < 64 and int(fields[4]) < 64):
                subset.append(tuple(map(int, fields[2:])))
    assert len(subset) == 1956
    rows = {int(item["mask"]): item for item in json.loads(GEOMETRY.read_text())["rows"]}
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1,0,0,0,1])
    def dec(n):
        return field(ring([(n >> bit) & 1 for bit in range(41)]))
    def enc(a):
        return sum(int(bit) << i for i, bit in enumerate(a.polynomial().list()))
    def xy(point):
        return [enc(point[0]), enc(point[1])]
    def frob(point, shift):
        return curve(point[0]**(1 << shift), point[1]**(1 << shift))
    raw = {mask: curve(*map(dec, row["raw_point"])) for mask,row in rows.items()}
    diag = {mask: raw[mask] + frob(raw[mask], 1) for mask in raw}
    columns = set()
    total = curve(0)
    selected = []
    for idx in ids:
        original, a, b, ca, cb, sa, sb, x, y = subset[idx]
        assert (ca,cb)==(rows[a]["column"],rows[b]["column"])
        assert sa==((original>>1)&1) and sb==(original&1)
        assert ca not in columns and cb not in columns and ca!=cb
        columns.update((ca,cb))
        pair = (-diag[a] if sa else diag[a]) + (-diag[b] if sb else diag[b])
        assert xy(pair)==[x,y]
        total += 4*pair
        selected.append({"subset_state_id": idx, "original_state_id": original,
                         "masks": [a,b], "columns": [ca,cb], "sign_bits": [sa,sb],
                         "projected_pair_point": xy(4*pair)})
    target = curve(*map(dec,fixture["projected_target"]))
    assert len(columns)==10 and total==target and ORDER*target==curve(0)
    original_target = target+frob(target,7)
    assert original_target!=curve(0) and ORDER*original_target==curve(0)
    audited = {"status": "PASS_INDEPENDENT_CONSTRUCTED_THREEPAIR_CONTROL",
               "selected": selected, "distinct_folded_columns": len(columns),
               "projected_target": xy(total), "original_factored_target": xy(original_target),
               "protocol_sha256": sha(HERE / "control_audit_protocol.json")}
    with (HERE / "control_audit_result.json").open("x") as out:
        json.dump(audited,out,sort_keys=True,indent=2)
        out.write("\n")
    print(audited["status"],len(columns),flush=True)


if __name__ == "__main__":
    main()

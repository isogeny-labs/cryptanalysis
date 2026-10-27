"""Compress exact row certificates by verified finite Fricke transport."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
TRANSPORT = json.loads((HERE / "transport_inputs.json").read_text())
F_VALUES = (60, 70, 90, 150, 210)


def load(path):
    entry = next(item for item in INPUTS["inputs"] if item["path"] == str(path))
    full = ROOT / path
    assert hashlib.sha256(full.read_bytes()).hexdigest() == entry["sha256"]
    return json.loads(full.read_text())


def key(row):
    return tuple(sorted((int(i), int(v)) for i, v in row.items() if v))


def neg(point, p):
    return None if point is None else (point[0], (-point[1] - 1) % p)


def add(a, b, p):
    if a is None:
        return b
    if b is None:
        return a
    x1, y1 = a
    x2, y2 = b
    if x1 == x2 and (y1+y2+1) % p == 0:
        return None
    if x1 == x2:
        slope = (3*x1*x1 - 2*x1 - 10) * pow(2*y1+1, -1, p) % p
    else:
        slope = (y2-y1) * pow(x2-x1, -1, p) % p
    x3 = (slope*slope + 1 - x1 - x2) % p
    y3 = (-slope*(x3-x1) - y1 - 1) % p
    return x3, y3


def checked_certificate(rows, target, denominator, coefficients):
    assert denominator > 0
    total = Counter()
    for item in coefficients:
        for i, value in rows[item["row_index"]].items():
            total[int(i)] += item["numerator"] * int(value)
    for i, value in target.items():
        total[int(i)] -= denominator * int(value)
    return all(value == 0 for value in total.values())


def inspect(f):
    entry = next(item for item in TRANSPORT["certificate_inputs"]
                 if item["conductor"] == f)
    cert_path = ROOT / entry["path"]
    assert hashlib.sha256(cert_path.read_bytes()).hexdigest() == entry["sha256"]
    certificates = json.loads(cert_path.read_text())["targets"]
    assert len(certificates) == 2
    data = load(Path(f"experiments/ecdlp-hecke-floor-rank-20261012/data/exp11_class_walk_D7_f{f}.json"))
    p = int(data["p"])
    rows = data["relation_rows"]
    points = []
    for encoded in data["column_points"]:
        match = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded)
        assert match is not None
        points.append(tuple(map(int, match.groups())))
    point_index = {point: i for i, point in enumerate(points)}
    torsion = (16 % p, -61 % p)
    perm = {i: point_index[add(torsion, neg(point, p), p)]
            for i, point in enumerate(points)}
    assert all(perm[perm[i]] == i for i in perm)

    def reflect(row):
        return tuple(sorted((perm[int(i)], int(v)) for i, v in row.items() if v))

    original_keys = Counter(map(key, rows))
    assert original_keys == Counter(reflect(row) for row in rows)
    index_for_key = {}
    for i, row in enumerate(rows):
        index_for_key.setdefault(key(row), i)
    first, second = certificates
    assert reflect(first["target_row"]) == key(second["target_row"])
    assert reflect(second["target_row"]) == key(first["target_row"])
    chosen, partner = sorted(certificates, key=lambda c: (c["support_size"], c["source"]))
    assert checked_certificate(rows, chosen["target_row"], chosen["denominator"],
                               chosen["coefficients"])
    mapped = Counter()
    for item in chosen["coefficients"]:
        mapped[index_for_key[reflect(rows[item["row_index"]])]] += item["numerator"]
    coefficients = [{"row_index": i, "numerator": v}
                    for i, v in sorted(mapped.items()) if v]
    assert checked_certificate(rows, partner["target_row"],
                               chosen["denominator"], coefficients)
    return {"conductor": f, "status": "TRANSPORTED_INTEGER_IDENTITY_PASS",
            "source": chosen["source"], "partner": partner["source"],
            "original_partner_support": partner["support_size"],
            "chosen_support": chosen["support_size"],
            "transported_support": len(coefficients),
            "denominator": chosen["denominator"],
            "target_row": partner["target_row"], "coefficients": coefficients}


def main():
    assert TRANSPORT["schema"] == "hecke-d7-fricke-certificate-transport-v1"
    results = [inspect(f) for f in F_VALUES]
    output = {"status": "FRICKE_CERTIFICATE_TRANSPORT_PASS", "cases": results,
              "transport_inputs_sha256": hashlib.sha256((HERE / "transport_inputs.json").read_bytes()).hexdigest()}
    (HERE / "transported.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": output["status"], "cases": [
        {k: value for k, value in row.items() if k not in ("target_row", "coefficients")}
        for row in results]}, sort_keys=True))


if __name__ == "__main__":
    main()

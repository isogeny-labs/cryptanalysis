"""Complete fixed-curve bounded-coordinate admission census."""
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
INPUT = PARENT / "xedni-large-order-admission-20261115" / "result.json"
CONTROL = PARENT / "xedni-rank-one-coordinate-control-20261115" / "result.json"
GROUP = PARENT / "xedni-public-coordinate-lift-20261115" / "run.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    for path, key in ((INPUT, "input_selection_result_sha256"),
                      (CONTROL, "rank_one_control_result_sha256"),
                      (GROUP, "finite_group_source_sha256")):
        assert sha(path) == protocol[key]
    spec = importlib.util.spec_from_file_location("xedni_public_group", GROUP)
    group = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(group)
    selected = [r for r in json.loads(INPUT.read_text())["rows"] if r["selected"]]
    controls = {r["field_prime"]: r for r in json.loads(CONTROL.read_text())["rows"]}
    assert len(selected) == len(controls) == 8
    out = []
    for item in selected:
        p, q = item["field_prime"], item["subgroup_order"]
        P = (2 % p, 2 % p)
        order = group.point_order(P, p, item["curve_order"])
        m = order // q
        assert order == controls[p]["rational_generator_reduction_order"]
        G = group.mul(m, P, p)
        Q = group.mul(17, G, p)
        image = {group.mul(k, P, p): k for k in range(-4, 5)}
        assert len(image) == 9
        points = [group.add(Q, group.mul(-t, G, p), p) for t in range(q)]
        admitted = [R in image for R in points]
        count = Counter()
        raw = HERE / "rows" / f"p{p}.jsonl.gz"
        raw.parent.mkdir(parents=True, exist_ok=True)
        with raw.open("wb") as fh:
            with gzip.GzipFile(fileobj=fh, mode="wb", filename="", mtime=0) as gz:
                for t1, R1 in enumerate(points):
                    for t2, R2 in enumerate(points):
                        if R1 is None or R2 is None:
                            status = "identity"
                        elif R1 == R2:
                            status = "duplicate"
                        elif admitted[t1] and admitted[t2]:
                            status = "admitted"
                        else:
                            status = "outside_cap"
                        count[status] += 1
                        row = {"t": [t1, t2], "status": status}
                        gz.write((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode())
        n = sum(admitted)
        nonidentity = sum(admitted[t] and points[t] is not None for t in range(q))
        assert count["admitted"] == nonidentity * (nonidentity - 1)
        assert sum(count.values()) == q * q
        out.append({"field_prime": p, "subgroup_order": q,
                    "generator_reduction_order": order, "subgroup_multiplier_m": m,
                    "public_generator": list(G), "public_target": list(Q),
                    "admitted_offset_count": n,
                    "admitted_offsets": [t for t in range(q) if admitted[t]],
                    "admitted_full_pair_support": n * n,
                    "admitted_distinct_nonidentity_pairs": count["admitted"],
                    "capacity_bound": 81,
                    "counts": dict(count), "raw_path": str(raw.relative_to(HERE)),
                    "raw_sha256": sha(raw)})
    print(json.dumps({"schema": "xedni-fixed-curve-admission-result-v1",
                      "status": "PASS", "protocol_sha256": sha(HERE / "protocol.json"),
                      "source_sha256": sha(Path(__file__)),
                      "input_sha256": sha(INPUT), "control_sha256": sha(CONTROL),
                      "group_source_sha256": sha(GROUP), "fields": out,
                      "totals": {"queries": sum(r["subgroup_order"] ** 2 for r in out),
                                 "admitted_full_pair_support": sum(r["admitted_full_pair_support"] for r in out),
                                 "admitted_distinct_nonidentity_pairs": sum(r["admitted_distinct_nonidentity_pairs"] for r in out)}} , sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

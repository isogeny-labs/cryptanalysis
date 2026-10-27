"""Independent integer replay of local Hecke-commutator certificates."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
F_VALUES = (42, 60, 70, 90, 150, 210)
EXPECTED_TRACES = {2: -2, 3: -1, 5: 1, 7: -2}


def load(path):
    entry = next(item for item in INPUTS["inputs"] if item["path"] == str(path))
    full = ROOT / path
    assert hashlib.sha256(full.read_bytes()).hexdigest() == entry["sha256"]
    return json.loads(full.read_text())


def key(row):
    return tuple(sorted((int(i), int(v)) for i, v in row.items() if v))


def source_targets():
    first = load(Path("experiments/hecke-multiplicity-collector-20261026/replay.json"))
    second = load(Path("experiments/hecke-d7-f60-f90-multiplicity-20261027/replay.json"))
    result = {}
    for case in first["cases"] + second["cases"]:
        result[case["conductor"]] = {entry["source"]: key(entry["row"])
            for entry in case["repeated_fibers"]
            if entry["degree"] == 2 and "row" in entry}
    return result


def expected_terms(cert, traces):
    ell, anchor = cert["partner_degree"], cert["anchor"]
    terms = defaultdict(int)
    for i, count in cert["anchor_neighbors"][str(ell)].items():
        terms[2, int(i)] += int(count)
    terms[2, anchor] -= traces[ell]
    for i, count in cert["anchor_neighbors"]["2"].items():
        terms[ell, int(i)] -= int(count)
    terms[ell, anchor] += traces[2]
    return {item: value for item, value in terms.items() if value}


def inspect(f, targets):
    data = load(Path(f"experiments/ecdlp-hecke-floor-rank-20261012/data/exp11_class_walk_D7_f{f}.json"))
    report_path = HERE / f"result_f{f}.json"
    report = json.loads(report_path.read_text())
    assert report["conductor"] == f and report["status"] == "ALL_ONE_STEP"
    assert report["points"] == len(data["column_points"])
    assert report["archived_rows"] == len(data["relation_rows"])
    assert report["archived_rows_retained"] is True
    traces = {int(i): int(v) for i, v in report["eigenvalues"].items()}
    assert traces == {ell: EXPECTED_TRACES[ell] for ell in data["hecke_primes"]}
    assert sorted(c["source"] for c in report["certificates"]) == INPUTS["degree2_targets"][str(f)]
    assert len(report["certificates"]) == 2
    supports = []
    for cert in report["certificates"]:
        assert cert["status"] == "ONE_STEP_CERTIFICATE"
        assert cert["degree"] == 2 and cert["partner_degree"] in traces
        assert key(cert["target_row"]) == targets[f][cert["source"]]
        assert cert["denominator"] == 1
        expected = expected_terms(cert, traces)
        terms = {(item["degree"], item["source"]): item["coefficient"]
                 for item in cert["commutator_terms"]}
        assert terms == expected
        assert terms[2, cert["source"]] != 0
        total = Counter()
        for item in cert["commutator_terms"]:
            degree, source = item["degree"], item["source"]
            if (degree, source) == (2, cert["source"]):
                assert item["archived_row_index"] is None
                row = cert["target_row"]
            else:
                row_index = item["archived_row_index"]
                assert isinstance(row_index, int) and 0 <= row_index < len(data["relation_rows"])
                row = data["relation_rows"][row_index]
            for i, value in row.items():
                total[int(i)] += item["coefficient"] * int(value)
        assert all(value == 0 for value in total.values())
        coefficients = cert["coefficients"]
        assert len(coefficients) == cert["support_size"]
        assert len({item["row_index"] for item in coefficients}) == len(coefficients)
        identity = Counter()
        for item in coefficients:
            row_index = item["row_index"]
            assert 0 <= row_index < len(data["relation_rows"])
            for i, value in data["relation_rows"][row_index].items():
                identity[int(i)] += item["numerator"] * int(value)
        for i, value in cert["target_row"].items():
            identity[int(i)] -= cert["denominator"] * int(value)
        assert all(value == 0 for value in identity.values())
        supports.append(cert["support_size"])
    return {"conductor": f, "role": "discovery" if f in INPUTS["discovery_conductors"]
            else "heldout", "targets": 2, "support_sizes": supports,
            "result_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest()}


def main():
    assert INPUTS["schema"] == "hecke-d7-local-commutator-v1"
    for entry in INPUTS["inputs"]:
        assert hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    targets = source_targets()
    cases = [inspect(f, targets) for f in F_VALUES]
    assert sum(case["targets"] for case in cases) == 12
    supports = [support for case in cases for support in case["support_sizes"]]
    assert Counter(supports) == {6: 9, 8: 3}
    output = {"status": "INDEPENDENT_LOCAL_COMMUTATOR_PASS",
              "target_count": 12, "support_histogram": {"6": 9, "8": 3},
              "cases": cases,
              "inputs_sha256": hashlib.sha256((HERE / "inputs.json").read_bytes()).hexdigest()}
    (HERE / "validation.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()

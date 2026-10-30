"""Pure-Python verification of all exact recovered-row dependencies."""
import hashlib
import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
F_VALUES = (42, 60, 70, 90, 150, 210)


def load(path, manifest):
    entry = next(item for item in manifest["inputs"] if item["path"] == str(path))
    full = ROOT / path
    assert hashlib.sha256(full.read_bytes()).hexdigest() == entry["sha256"]
    return json.loads(full.read_text())


def key(row):
    return tuple(sorted((int(i), int(v)) for i, v in row.items() if v))


def recovered_targets(manifest):
    first = load(Path("experiments/hecke-multiplicity-collector-20261026/replay.json"), manifest)
    second = load(Path("experiments/hecke-d7-f60-f90-multiplicity-20261027/replay.json"), manifest)
    result = {}
    for case in first["cases"] + second["cases"]:
        rows = {}
        for entry in case["repeated_fibers"]:
            if "row" in entry:
                rows[entry["source"], entry["degree"]] = key(entry["row"])
        result[case["conductor"]] = rows
    return result


def verify_certificate(archived, target_key, certificate):
    denominator = int(certificate["denominator"])
    assert denominator > 0
    coefficients = certificate["coefficients"]
    assert len(coefficients) == certificate["support_size"]
    assert len({item["row_index"] for item in coefficients}) == len(coefficients)
    assert all(item["numerator"] != 0 for item in coefficients)
    accumulated = Counter()
    for item in coefficients:
        row_index = int(item["row_index"])
        assert 0 <= row_index < len(archived)
        for i, value in archived[row_index].items():
            accumulated[int(i)] += int(item["numerator"]) * int(value)
    for i, value in target_key:
        accumulated[i] -= denominator * value
    assert all(value == 0 for value in accumulated.values())
    assert max(abs(item["numerator"]) for item in coefficients) == certificate["max_abs_numerator"]
    return len(coefficients)


def main():
    manifest = json.loads((HERE / "inputs.json").read_text())
    assert manifest["schema"] == "hecke-d7-row-dependency-v1"
    targets = recovered_targets(manifest)
    cases = []
    for f in F_VALUES:
        data = load(Path(f"experiments/ecdlp-hecke-floor-rank-20261012/data/exp11_class_walk_D7_f{f}.json"), manifest)
        archived = data["relation_rows"]
        report_path = HERE / f"certificates_f{f}.json"
        report = json.loads(report_path.read_text())
        assert report["status"] == "EXACT_DEPENDENCIES_VERIFIED"
        assert report["conductor"] == f
        assert report["archived_rows"] == len(archived)
        assert report["archived_rank"] == report["modular_basis_rank"] == data["rank"]
        assert len(report["targets"]) == len(targets[f])
        supports = []
        for certificate in report["targets"]:
            target_key = key(certificate["target_row"])
            assert target_key == targets[f][certificate["source"], certificate["degree"]]
            supports.append(verify_certificate(archived, target_key, certificate))
        cases.append({"conductor": f, "targets": len(supports),
                      "support_sizes": supports,
                      "denominators": [c["denominator"] for c in report["targets"]],
                      "certificate_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest()})
    assert sum(case["targets"] for case in cases) == 13
    transported = json.loads((HERE / "transported.json").read_text())
    transport_inputs = json.loads((HERE / "transport_inputs.json").read_text())
    assert transported["status"] == "FRICKE_CERTIFICATE_TRANSPORT_PASS"
    assert transported["transport_inputs_sha256"] == hashlib.sha256(
        (HERE / "transport_inputs.json").read_bytes()).hexdigest()
    assert len(transported["cases"]) == 5
    transported_checks = []
    for item in transported["cases"]:
        f = item["conductor"]
        assert f in (60, 70, 90, 150, 210)
        data = load(Path(f"experiments/ecdlp-hecke-floor-rank-20261012/data/exp11_class_walk_D7_f{f}.json"), manifest)
        pinned = next(entry for entry in transport_inputs["certificate_inputs"]
                      if entry["conductor"] == f)
        cert_path = ROOT / pinned["path"]
        assert hashlib.sha256(cert_path.read_bytes()).hexdigest() == pinned["sha256"]
        originals = json.loads(cert_path.read_text())["targets"]
        original_partner = next(c for c in originals if c["source"] == item["partner"])
        original_chosen = next(c for c in originals if c["source"] == item["source"])
        assert item["original_partner_support"] == original_partner["support_size"]
        assert item["chosen_support"] == original_chosen["support_size"]
        assert item["transported_support"] <= item["original_partner_support"]
        assert key(item["target_row"]) == targets[f][item["partner"], original_partner["degree"]]
        certificate = {"denominator": item["denominator"],
                       "coefficients": item["coefficients"],
                       "support_size": item["transported_support"],
                       "max_abs_numerator": max(abs(c["numerator"])
                                                for c in item["coefficients"])}
        verify_certificate(data["relation_rows"], key(item["target_row"]), certificate)
        transported_checks.append({"conductor": f, "partner": item["partner"],
                                   "before_support": item["original_partner_support"],
                                   "after_support": item["transported_support"]})
    assert sum(x["before_support"] for x in transported_checks) == 487
    assert sum(x["after_support"] for x in transported_checks) == 97
    output = {"status": "INDEPENDENT_EXACT_DEPENDENCIES_PASS",
              "target_count": 13, "cases": cases,
              "transported_checks": transported_checks,
              "transported_support_before": 487,
              "transported_support_after": 97,
              "inputs_sha256": hashlib.sha256((HERE / "inputs.json").read_bytes()).hexdigest()}
    (HERE / "validation.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()

"""Exhaustive model-family admission masks and candidate-test accounting."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-fixed-curve-admission-20261115"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    source = PARENT / "result.json"
    theorem = PARENT / "formal" / "SelectedAdmission.lean"
    assert sha(source) == protocol["parent_fixed_curve_result_sha256"]
    assert sha(theorem) == protocol["parent_selected_pair_theorem_sha256"]
    parent = json.loads(source.read_text())
    fields = []
    for field in parent["fields"]:
        p, q = field["field_prime"], field["subgroup_order"]
        admitted = set(field["admitted_offsets"])
        models = []
        for j in range(4):
            a = j * p
            coeffs = [0, -3 * a, 0, 3 * a * a - 1, -a * a * a + a - 2]
            assert [x % p for x in coeffs] == [0, 0, 0, (-1) % p, (-2) % p]
            models.append({"j": j, "shift_a": a, "coefficients": coeffs,
                           "generator": [2 + a, 2],
                           "bounded_image_offsets": sorted(admitted)})
        raw = HERE / "rows" / f"p{p}.jsonl.gz"
        raw.parent.mkdir(parents=True, exist_ok=True)
        model_images = [set(model["bounded_image_offsets"]) for model in models]
        pair_count = 0
        with raw.open("wb") as fh:
            with gzip.GzipFile(fileobj=fh, mode="wb", filename="", mtime=0) as gz:
                for t1 in range(q):
                    for t2 in range(q):
                        mask = sum(1 << j for j, image in enumerate(model_images)
                                   if t1 in image and t2 in image)
                        assert mask in (0, 15)
                        pair_count += mask != 0
                        gz.write((json.dumps({"t": [t1, t2], "mask": mask},
                                             sort_keys=True, separators=(",", ":")) + "\n").encode())
        assert pair_count == field["admitted_full_pair_support"]
        fields.append({"field_prime": p, "subgroup_order": q,
                       "model_constructions": 4, "candidate_pair_tests": 4 * q * q,
                       "union_admitted_pairs": pair_count,
                       "single_model_admitted_pairs": field["admitted_full_pair_support"],
                       "new_pairs_from_extra_models": 0,
                       "models": models, "raw_path": str(raw.relative_to(HERE)),
                       "raw_sha256": sha(raw)})
    print(json.dumps({"schema": "xedni-isomorphic-family-admission-result-v1",
                      "status": "PASS", "protocol_sha256": sha(HERE / "protocol.json"),
                      "source_sha256": sha(Path(__file__)),
                      "parent_result_sha256": sha(source),
                      "parent_theorem_sha256": sha(theorem),
                      "fields": fields,
                      "totals": {"queries": sum(f["subgroup_order"] ** 2 for f in fields),
                                 "model_constructions": sum(f["model_constructions"] for f in fields),
                                 "candidate_pair_tests": sum(f["candidate_pair_tests"] for f in fields),
                                 "union_admitted_pairs": sum(f["union_admitted_pairs"] for f in fields),
                                 "new_pairs_from_extra_models": 0}},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

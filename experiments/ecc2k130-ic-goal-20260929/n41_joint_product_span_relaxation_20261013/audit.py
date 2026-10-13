"""Independent archived inverse and direct S3 replay of the native census."""

import hashlib
import importlib.util
import json
import random
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVED = HERE.parent / "n41_n131_universal_product_linearized_20261011" / "n41_control.py"
sys.path.insert(0, str(HERE))
from run import source_pair_map, s3_right_roots, quadratic_roots  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_archived():
    spec = importlib.util.spec_from_file_location("archived_n41_control", ARCHIVED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_u64(path):
    data = path.read_bytes()
    assert len(data) % 8 == 0
    return list(struct.unpack("<" + "Q" * (len(data) // 8), data))


def exact_join(target, source, arithmetic):
    hits = set()
    for c in source:
        for d in s3_right_roots(c, target):
            if d in source:
                hits.add(tuple(sorted((c, d))))
                e3 = arithmetic.multiply(arithmetic.multiply(c, d), target)
                assert (arithmetic.square(e3) ^ e3 ^
                        arithmetic.square(c ^ d ^ target)) == 0
    return hits


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    for name in ("native_join.cpp", "native_join", "exact_outputs.bin", "relaxed_outputs.bin"):
        assert protocol[name.replace(".", "_") + "_sha256"] == digest(HERE / name)
    assert protocol["native_source_sha256"] == digest(HERE / "native.cpp")
    assert protocol["native_binary_sha256"] == digest(HERE / "native")
    assert protocol["run_sha256"] == digest(HERE / "run.py")
    assert protocol["arithmetic_sha256"] == digest(HERE / "n41_arithmetic.py")
    native = json.loads((HERE / "native_stdout.log").read_text())
    joined = json.loads((HERE / "join_stdout.log").read_text())
    native_receipt = json.loads((HERE / "native_receipt.json").read_text())
    join_receipt = json.loads((HERE / "join_receipt.json").read_text())
    assert native_receipt["status"] == join_receipt["status"] == "COMPLETE"
    assert native_receipt["output_sha256"] == digest(HERE / "relaxed_outputs.bin")
    outputs = read_u64(HERE / "relaxed_outputs.bin")
    sources = read_u64(HERE / "exact_outputs.bin")
    assert outputs == sorted(set(outputs)) and sources == sorted(set(sources))
    assert len(outputs) == native["distinct_outputs"] == 130405
    source_map = source_pair_map()
    assert sources == sorted(source_map)
    output_set = set(outputs)
    assert set(sources).issubset(output_set)
    arithmetic = load_archived()
    half_basis = [arithmetic.halftrace(arithmetic.square(1 << (i + 1)))
                  for i in range(arithmetic.D)]
    rng = random.Random(202610132315)
    positives = rng.sample(outputs, 128)
    negatives = set()
    while len(negatives) < 128:
        c = rng.getrandbits(41)
        if c and c not in output_set:
            negatives.add(c)
    for c in positives:
        rank, solutions = arithmetic.solve(c, half_basis)
        assert solutions, (c, rank)
    for c in negatives:
        rank, solutions = arithmetic.solve(c, half_basis)
        assert not solutions, (c, rank)
    constructed = joined["cases"]["constructed"]["target_reciprocal"]
    first, second = sources[:2]
    assert constructed in s3_right_roots(first, second)
    public = arithmetic.inverse(protocol["public_point_x"])
    assert public == joined["cases"]["public_point_inverse_x"]["target_reciprocal"]
    exact_counts = {}
    for name, target in (("constructed", constructed), ("public_point_inverse_x", public)):
        hits = exact_join(target, source_map, arithmetic)
        exact_counts[name] = len(hits)
        assert len(hits) == joined["cases"][name]["exact_unordered_hits"]
    result = {"status": "PASS_INDEPENDENT_ARCHIVED_INVERSE_AND_EXACT_S3",
              "protocol_sha256": digest(HERE / "protocol.json"),
              "archived_inverse_sha256": digest(ARCHIVED),
              "sample_positive": len(positives), "sample_negative": len(negatives),
              "all_exact_outputs_in_relaxation": len(sources),
              "exact_join_counts": exact_counts,
              "native_relaxed_outputs": len(outputs)}
    (HERE / "audit_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

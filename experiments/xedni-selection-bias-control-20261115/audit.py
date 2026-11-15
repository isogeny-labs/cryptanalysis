"""Check source receipts and count the selected event without Sage."""

import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def main():
    spec = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert result["status"] == "PASS"
    assert result["protocol_sha256"] == sha("protocol.json")
    assert result["source_sha256"] == sha("run.py")
    assert result["sage_runtime_sha256"] == sha("sage-runtime-info.json")
    assert (HERE / "run.stderr").stat().st_size == 0
    q = result["reduced_generator_order"]
    m = spec["sample"]["selected_lift_multipliers"]
    relation = spec["sample"]["relation_vector"]
    triples = list(itertools.permutations(m, 3))
    hits = sum(sum(a * x for a, x in zip(relation, triple)) == 0 for triple in triples)
    assert len(triples) == result["selected_total"]
    assert hits == result["selected_relation_count"]
    assert result["uniform_total"] == (q - 1) * (q - 2) * (q - 3)
    assert result["uniform_relation_count"] == (q - 1) * (q - 3)
    selected = Fraction(hits, len(triples))
    uniform = Fraction(result["uniform_relation_count"], result["uniform_total"])
    assert str(selected) == result["selected_fraction"]
    assert str(uniform) == result["uniform_fraction"]
    assert str(selected / uniform) == result["event_enrichment_factor"]
    print("PASS: source receipts, selected enumeration, uniform closed count, exact rate ratio")


if __name__ == "__main__":
    main()

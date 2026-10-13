"""Certify the plus Frobenius-linked subtotal with a 24-bit source table."""

import argparse
import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n131_w18_tenpair_linked_frob_20261012"
sys.path.insert(0, str(PRIOR))
import ten as prior  # noqa: E402

ORIGINAL_BUILD = prior.build
ORIGINAL_SOURCES = prior.sources
WIDTH = 14


def signature(value, masks):
    return sum((bin(value & mask).count("1") & 1) << bit
               for bit, mask in enumerate(masks))


def table_rows():
    with gzip.open(HERE / "rows.tsv.gz", "rt") as stream:
        assert stream.readline().strip().split("\t") == [
            "code", "mask_a", "mask_b", "root_bit", "a0", "a1",
            "plus0", "minus0", "plus1", "minus1"]
        for line in stream:
            yield tuple(map(int, line.split()))


def build(target_reciprocals, bdd_root, bdd_nodes):
    circuit, wires = ORIGINAL_BUILD(target_reciprocals, bdd_root, bdd_nodes)
    source_bits = wires["selectors"][0]
    pair_bits = wires["outputs"][0]
    subtotal_bits = wires["intermediates"][0]
    assert len(source_bits) == 17 and len(pair_bits) == len(subtotal_bits) == 131
    manifest = json.loads((HERE / "hash_manifest.json").read_text())
    assert manifest["status"] == "PASS_EXACT_ALL_SOURCE_LINEAR_SIGNATURE_SEPARATOR"
    assert manifest["signature_width_bits"] == WIDTH
    masks = list(map(int, manifest["masks"]))
    assert len(masks) == WIDTH
    subtotal_signature = [circuit.xor(
        subtotal_bits[index] for index in range(131) if mask >> index & 1)
        for mask in masks]
    negative_source = [circuit.xor((wire, -1)) for wire in source_bits]
    negative_pair = [circuit.xor((wire, -1)) for wire in pair_bits]
    # A prefix trie shares selector equality gates among all table rows.
    prefix = {(0, 0): -1}
    source_count = 0
    root_count = 0
    for code, mask_a, mask_b, bit, a0, a1, plus0, minus0, plus1, minus1 in table_rows():
        assert code < 1 << len(source_bits) and mask_a ^ mask_b == 212
        assert bit < len(pair_bits) and ((a0 ^ a1) & (1 << bit)) != 0
        assert signature(plus0, masks) != signature(minus0, masks)
        assert signature(plus1, masks) != signature(minus1, masks)
        guard = -1
        for index in range(len(source_bits)):
            key = (index + 1, code & ((1 << (index + 1)) - 1))
            if key not in prefix:
                literal = (source_bits[index] if (code >> index & 1)
                           else negative_source[index])
                prefix[key] = circuit.and_(guard, literal)
            guard = prefix[key]
        for a, wanted in ((a0, plus0), (a1, plus1)):
            matching_root = (pair_bits[bit] if a >> bit & 1
                             else negative_pair[bit])
            root_guard = circuit.and_(guard, matching_root)
            wanted_signature = signature(wanted, masks)
            for out_bit, output_wire in enumerate(subtotal_signature):
                required = (output_wire if wanted_signature >> out_bit & 1
                            else -output_wire)
                circuit.clauses.append(f"-{root_guard} {required} 0")
            root_count += 1
        source_count += 1
    assert source_count == 33191 and root_count == 66382
    circuit.signature_gate_stats = {
        "source_codes": source_count,
        "pair_roots": root_count,
        "signature_width": WIDTH,
        "signature_seed": manifest["first_passing_seed"],
        "selector_prefix_nodes": len(prefix),
    }
    return circuit, wires


def sources():
    result = ORIGINAL_SOURCES()
    result["balanced_runner"] = Path(__file__)
    result["linked_signature_table"] = HERE / "rows.tsv.gz"
    result["linked_signature_census"] = HERE / "census_result.json"
    result["linked_signature_sage_audit"] = HERE / "audit_result.json"
    result["linked_signature_gate"] = Path(__file__)
    result["linked_signature_hash"] = HERE / "hash_manifest.json"
    result["linked_signature_hash_source"] = HERE / "select_hash.py"
    return result


prior.HERE = HERE
prior.orbit9.HERE = HERE
prior.build = build
prior.orbit9.build = build
prior.sources = sources
prior.orbit9.sources = sources


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "control", "query"))
    choice = parser.parse_args().mode
    {"freeze": prior.freeze, "control": prior.control,
     "query": prior.query}[choice]()

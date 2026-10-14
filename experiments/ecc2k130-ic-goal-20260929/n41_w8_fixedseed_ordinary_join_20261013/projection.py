"""Exact storage and probe counts for a literal W20 seven-pair 3+4 join."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w20_sevenpair_gate_20261010" / "count_result_v2.json"


def main():
    source = json.loads(SOURCE.read_text())
    assert source["signed_pair_states_per_slot"] == 528180
    S = source["signed_pair_states_per_slot"]
    entries = S**3
    probes = S**4
    result = {"status":"PASS_EXACT_LITERAL_W20_JOIN_PROJECTION",
              "candidate_id":None,"source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "pair_states_per_slot":S,"left_triples_upper":str(entries),
              "right_quadruples_upper":str(probes),
              "left_payload_bytes_at_one_bit_per_entry":str((entries+7)//8),
              "left_payload_bytes_at_16_bytes_per_entry":str(16*entries),
              "minimum_right_probes_per_second_to_exhaust_in_600s":str((probes+599)//600),
              "scope":"literal exhaustive 3+4 state enumeration; distinct-column filtering can reduce counts"}
    path = HERE/"projection_result.json"
    if path.exists():
        assert json.loads(path.read_text()) == result
    else:
        path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(result["status"],result["left_triples_upper"])


if __name__ == "__main__": main()

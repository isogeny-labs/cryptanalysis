"""Literal W20 two-code table size and traversal projection."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/"n131_w20_sevenpair_gate_20261010"/"count_result_v2.json"


def main():
    source = json.loads(SOURCE.read_text())
    P = source["selected_valid_unordered_pairs_per_slot"]
    assert P == 132045
    pairs = P*P
    coordinate_bytes = (131+7)//8
    out = {"status":"PASS_LITERAL_W20_TWO_CODE_TABLE_PROJECTION",
           "candidate_id":None,"source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
           "valid_codes_per_slot":P,"ordered_code_pairs":str(pairs),
           "code_pairs_per_second_for_600s_exhaustion":str((pairs+599)//600),
           "bytes_for_eight_131_bit_coordinates_per_pair":str(pairs*8*coordinate_bytes),
           "bytes_for_one_bit_per_pair":str((pairs+7)//8),
           "scope":"literal uncompressed full code-pair table; N131 affine rank and implicit representations unmeasured"}
    path = HERE/"transfer_result.json"
    if path.exists():assert json.loads(path.read_text()) == out
    else:path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(out["status"],out["ordered_code_pairs"])


if __name__ == "__main__":main()

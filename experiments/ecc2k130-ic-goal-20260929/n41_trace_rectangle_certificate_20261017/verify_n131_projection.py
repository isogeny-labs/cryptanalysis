"""Independently replay prefix counts from the frozen 19-bit validity bitmap."""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
BITMAP = GOAL / 'n131_w20_code_trace_bitset_20261014/valid_bitmap.bin'
PREFIX = GOAL / 'n131_symbolic_rect_projection_20261015/prefix_result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = HERE / 'n131_projection_protocol.json'
    result_path = HERE / 'n131_projection_result.json'
    protocol = json.loads(protocol_path.read_text())
    result = json.loads(result_path.read_text())
    assert result['status'] == 'PASS_EXACT_N131_LOW_BIT_RECTANGLE_PROJECTION'
    assert result['protocol_sha256'] == sha(protocol_path)
    assert result['source_sha256'] == protocol['source_sha256']
    bitmap = BITMAP.read_bytes()
    assert len(bitmap) == 65536
    codes = [i for i in range(1 << 19) if bitmap[i >> 3] >> (i & 7) & 1]
    assert len(codes) == result['valid_codes_per_slot'] == 132045
    prior = json.loads(PREFIX.read_text())
    for row in result['rows']:
        bits = row['low_bits_per_slot']
        occupancy = Counter(code >> bits for code in codes)
        hist = Counter(occupancy.values())
        assert len(occupancy) == row['nonempty_groups_per_slot']
        assert {str(k): v for k, v in sorted(hist.items())} == row['occupancy_histogram']
        assert len(occupancy)**3 == row['three_slot_rectangles_before_exclusions']
        if bits == 2:
            assert prior['nonempty_prefixes_per_slot'] == len(occupancy)
            assert prior['prefix_occupancy_histogram'] == row['occupancy_histogram']
    receipt = {'status': 'PASS_INDEPENDENT_N131_PREFIX_BITMAP_REPLAY',
               'valid_codes': len(codes),
               'groups_per_slot': {str(row['low_bits_per_slot']):
                                   row['nonempty_groups_per_slot'] for row in result['rows']},
               'bitmap_sha256': sha(BITMAP), 'prior_prefix_sha256': sha(PREFIX),
               'result_sha256': sha(result_path), 'verifier_sha256': sha(Path(__file__))}
    (HERE / 'n131_projection_verification.json').write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(receipt['status'], receipt['groups_per_slot'])


if __name__ == '__main__':
    main()

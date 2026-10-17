"""Exact W20 source occupancy under the same low-bit rectangle rule."""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n131_w20_sevenpair_gate_20261010'
SUPPORT = SOURCE / 'support_w20.tsv'
COUNT = SOURCE / 'count_result_v2.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = HERE / 'n131_projection_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['source_sha256'] == {
        'n131_prefix_projection.py': sha(Path(__file__)),
        'support_w20.tsv': sha(SUPPORT),
        'count_result_v2.json': sha(COUNT)}
    count = json.loads(COUNT.read_text())
    seed = count['selected_seed_mask']
    support = {}
    for line in SUPPORT.open():
        mask, column, _shift = map(int, line.split())
        support[mask] = column
    omitted_pivot = seed.bit_length() - 1
    selector_bits = [bit for bit in range(20) if bit != omitted_pivot]
    assert len(selector_bits) == 19
    valid = []
    for mask, column in support.items():
        other = mask ^ seed
        if mask < other and other in support and column != support[other]:
            valid.append(sum(((mask >> bit) & 1) << i
                             for i, bit in enumerate(selector_bits)))
    assert len(valid) == count['selected_valid_unordered_pairs_per_slot'] == 132045
    assert len(set(valid)) == len(valid)
    rows = []
    for bits in protocol['low_bits_per_slot']:
        occupancy = Counter(value >> bits for value in valid)
        histogram = Counter(occupancy.values())
        groups = len(occupancy)
        rows.append({'low_bits_per_slot': bits,
                     'nonempty_groups_per_slot': groups,
                     'occupancy_histogram': {str(k): v for k, v in sorted(histogram.items())},
                     'three_slot_rectangles_before_exclusions': groups**3,
                     'two_slot_rectangles_before_exclusions': groups**2,
                     'minimum_three_slot_rectangle_rate_per_second_600s':
                         (groups**3 + 599) // 600,
                     'minimum_two_slot_rectangle_rate_per_second_600s':
                         (groups**2 + 599) // 600,
                     'total_three_slot_code_triples_before_exclusions': len(valid)**3})
    result = {'status': 'PASS_EXACT_N131_LOW_BIT_RECTANGLE_PROJECTION',
              'candidate_id': None, 'valid_codes_per_slot': len(valid),
              'source_sha256': protocol['source_sha256'],
              'protocol_sha256': sha(protocol_path), 'rows': rows}
    (HERE / 'n131_projection_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'], [(r['low_bits_per_slot'], r['nonempty_groups_per_slot'])
                             for r in rows])


if __name__ == '__main__':
    main()

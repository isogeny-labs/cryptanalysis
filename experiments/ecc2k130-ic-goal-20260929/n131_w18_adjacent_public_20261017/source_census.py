"""Count distinct adjacent first-join coordinates on the frozen W18 source."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n41_n131_adjacent_frob_leaf_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipt = json.loads((SOURCE / 'n131_result.json').read_text())
    path = SOURCE / 'adjacent_roots.bin'
    assert receipt['status'] == 'PASS_N131_ADJACENT_ROOT_MAP'
    assert receipt['output_sha256'] == sha(path)
    data = path.read_bytes()
    assert len(data) == receipt['raw_roots']*34
    values = [int.from_bytes(data[offset:offset+17], 'little')
              for offset in range(0, len(data), 17)]
    plus, minus = set(values[::2]), set(values[1::2])
    result = {'status': 'PASS_ADJACENT_SOURCE_DISTINCT_CENSUS',
              'candidate_id': None, 'raw_roots': receipt['raw_roots'],
              'plus_unique': len(plus), 'minus_unique': len(minus),
              'cross_intersection': len(plus & minus),
              'union_unique': len(plus | minus),
              'source_table_sha256': sha(path),
              'source_receipt_sha256': sha(SOURCE / 'n131_result.json'),
              'script_sha256': sha(Path(__file__))}
    assert result['plus_unique'] == result['minus_unique'] == 66382
    assert result['union_unique'] == 132764 and result['cross_intersection'] == 0
    with (HERE / 'source_census.json').open('x') as file:
        json.dump(result, file, indent=2, sort_keys=True)
        file.write('\n')
    print(result['status'], result['union_unique'])


if __name__ == '__main__':
    main()

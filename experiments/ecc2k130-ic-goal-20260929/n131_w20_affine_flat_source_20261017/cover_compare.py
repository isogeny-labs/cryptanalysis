"""Matched continuation of first-valid versus best-of-eight flat covers."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

import numpy as np

from flat_search import trial

HERE = Path(__file__).resolve().parent
BITMAP = HERE.parent / 'n131_w20_code_trace_bitset_20261014/valid_bitmap.bin'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def branch(valid, initial_covered, policy, protocol):
    covered = initial_covered.copy()
    pointer = 0
    rng = np.random.default_rng(protocol['search_seed'])
    rows = []
    attempts = 0
    intersections = 0
    begin = time.monotonic_ns()
    filename = HERE / ('compare_' + policy + '.jsonl')
    with filename.open('x') as out:
        for block_index in range(protocol['blocks_per_arm']):
            while pointer < len(valid) and (not valid[pointer] or covered[pointer]):
                pointer += 1
            assert pointer < len(valid)
            chosen = None
            used = 0
            for _ in range(protocol['trials_per_anchor']):
                row = trial(valid, np.array([pointer], dtype=np.uint32), rng)
                attempts += 1
                intersections += row['intersections']
                used += 1
                if row['dimension'] < 4:
                    continue
                added = sum(not covered[code] for code in row['codes'])
                if (chosen is None or added > chosen[0] or
                        (added == chosen[0] and row['directions'] < chosen[1]['directions'])):
                    chosen = (added, row)
                if policy == 'first':
                    break
            if chosen is None:
                codes, directions, dimension = [pointer], [], 0
            else:
                _score, row = chosen
                codes, directions, dimension = row['codes'], row['directions'], row['dimension']
            added = sum(not covered[code] for code in codes)
            for code in codes:
                covered[code] = True
            record = {'block_index': block_index, 'anchor': pointer,
                      'trials_used': used, 'dimension': dimension,
                      'directions': directions, 'codes': codes, 'added': added}
            out.write(json.dumps(record, sort_keys=True) + '\n')
            rows.append(added)
            if (block_index + 1) % 128 == 0:
                out.flush()
                print(policy, block_index + 1, sum(rows), flush=True)
    return {'policy': policy, 'blocks': len(rows), 'new_codes': sum(rows),
            'covered_after': int(covered.sum()), 'attempts': attempts,
            'intersections': intersections, 'wall_ns': time.monotonic_ns() - begin,
            'blocks_sha256': sha(filename),
            'added_per_block_histogram': {str(k): rows.count(k) for k in sorted(set(rows))}}


def main():
    signal.alarm(180)
    protocol_path = HERE / 'compare_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    files = {'cover_compare.py': Path(__file__),
             'flat_search.py': HERE / 'flat_search.py',
             'valid_bitmap.bin': BITMAP,
             'cover_result.json': HERE / 'cover_result.json',
             'cover_blocks.jsonl': HERE / 'cover_blocks.jsonl'}
    assert protocol['source_sha256'] == {name: sha(path) for name, path in files.items()}
    valid = np.unpackbits(np.frombuffer(BITMAP.read_bytes(), dtype=np.uint8),
                          bitorder='little').astype(np.bool_)
    initial = np.zeros(len(valid), dtype=np.bool_)
    for line in (HERE / 'cover_blocks.jsonl').open():
        for code in json.loads(line)['codes']:
            initial[code] = True
    start_count = int(initial.sum())
    assert start_count == json.loads((HERE / 'cover_result.json').read_text())['covered_codes']
    arms = [branch(valid, initial, policy, protocol) for policy in ('first', 'best')]
    out = {'status': 'PASS_BOUNDED_MATCHED_W20_FLAT_COVER_CONTINUATION',
           'candidate_id': None, 'source_sha256': protocol['source_sha256'],
           'protocol_sha256': sha(protocol_path), 'start_covered_codes': start_count,
           'arms': arms, 'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / 'compare_result.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(out['status'], [(x['policy'], x['new_codes'], x['wall_ns']/1e9) for x in arms])


if __name__ == '__main__':
    main()

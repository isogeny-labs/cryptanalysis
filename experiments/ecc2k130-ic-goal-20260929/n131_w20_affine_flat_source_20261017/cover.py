"""Deterministic bounded cover pilot using source-valid affine flats."""
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
N = 1 << 19


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    signal.alarm(180)
    protocol_path = HERE / 'cover_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['source_sha256'] == {
        'cover.py': sha(Path(__file__)),
        'flat_search.py': sha(HERE / 'flat_search.py'),
        'valid_bitmap.bin': sha(BITMAP)}
    bitmap = BITMAP.read_bytes()
    valid = np.unpackbits(np.frombuffer(bitmap, dtype=np.uint8),
                          bitorder='little').astype(np.bool_)
    assert int(valid.sum()) == 132045
    covered = np.zeros(N, dtype=np.bool_)
    rng = np.random.default_rng(protocol['search_seed'])
    anchor = 0
    blocks = 0
    attempts = 0
    intersections = 0
    covered_count = 0
    dimensions = {}
    additions = {}
    checkpoints = []
    start = time.monotonic_ns()
    block_path = HERE / 'cover_blocks.jsonl'
    with block_path.open('x') as out:
        while blocks < protocol['block_limit'] and covered_count < 132045:
            while anchor < N and (not valid[anchor] or covered[anchor]):
                anchor += 1
            assert anchor < N
            chosen = None
            retries = 0
            for _ in range(protocol['retries_per_anchor']):
                row = trial(valid, np.array([anchor], dtype=np.uint32), rng)
                attempts += 1
                intersections += row['intersections']
                retries += 1
                if row['dimension'] >= 4:
                    chosen = row
                    break
            if chosen is None:
                chosen = {'dimension': 0, 'base': anchor, 'directions': [],
                          'codes': [anchor], 'intersections': 0}
            codes = chosen['codes']
            assert len(codes) == 1 << chosen['dimension']
            assert anchor in codes
            assert all(valid[code] for code in codes)
            added = sum(not covered[code] for code in codes)
            for code in codes:
                covered[code] = True
            covered_count += added
            blocks += 1
            key = str(chosen['dimension'])
            dimensions[key] = dimensions.get(key, 0) + 1
            additions[str(added)] = additions.get(str(added), 0) + 1
            record = {'block_index': blocks - 1, 'anchor': anchor,
                      'attempts_for_anchor': retries,
                      'dimension': chosen['dimension'], 'directions': chosen['directions'],
                      'codes': codes, 'added': added}
            out.write(json.dumps(record, sort_keys=True) + '\n')
            if blocks % protocol['checkpoint_every'] == 0:
                out.flush()
                checkpoint = {'blocks': blocks, 'covered': covered_count,
                              'wall_ns': time.monotonic_ns() - start}
                checkpoints.append(checkpoint)
                print('checkpoint', checkpoint, flush=True)
    result = {'status': 'PASS_BOUNDED_VALID_AFFINE_FLAT_COVER_PILOT',
              'candidate_id': None, 'protocol_sha256': sha(protocol_path),
              'source_sha256': protocol['source_sha256'],
              'blocks': blocks, 'attempts': attempts, 'intersections': intersections,
              'covered_codes': covered_count, 'total_valid_codes': 132045,
              'dimension_histogram': dimensions,
              'added_per_block_histogram': additions,
              'checkpoints': checkpoints, 'query_independent_wall_ns': time.monotonic_ns() - start,
              'blocks_sha256': sha(block_path),
              'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / 'cover_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'], blocks, covered_count, attempts, flush=True)


if __name__ == '__main__':
    main()

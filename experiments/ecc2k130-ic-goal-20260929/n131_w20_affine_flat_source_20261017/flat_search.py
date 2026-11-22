"""Bounded constructive search for source-valid affine flats in GF(2)^19."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BITMAP = HERE.parent / 'n131_w20_code_trace_bitset_20261014/valid_bitmap.bin'
N = 1 << 19
INDEX = np.arange(N, dtype=np.uint32)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trial(valid, valid_codes, rng):
    base = int(rng.choice(valid_codes))
    candidates = valid[INDEX ^ base]
    span = np.array([0], dtype=np.uint32)
    directions = []
    intersections = 0
    candidate_counts = [int(candidates.sum())]
    for _ in range(3):
        eligible = np.flatnonzero(candidates)
        eligible = eligible[~np.isin(eligible, span)]
        if len(eligible) == 0:
            return {'dimension': len(directions), 'base': base,
                    'directions': directions, 'candidate_counts': candidate_counts,
                    'intersections': intersections}
        direction = int(rng.choice(eligible))
        candidates = candidates & candidates[INDEX ^ direction]
        intersections += 1
        span = np.concatenate((span, span ^ direction))
        directions.append(direction)
        candidate_counts.append(int(candidates.sum()))
    assert len(span) == 8 and np.all(valid[span ^ base])
    eligible = np.flatnonzero(candidates)
    eligible = eligible[~np.isin(eligible, span)]
    best = None
    for direction in eligible:
        direction = int(direction)
        new_candidates = candidates & candidates[INDEX ^ direction]
        intersections += 1
        count = int(new_candidates.sum())
        if best is None or count > best[0] or (count == best[0] and direction < best[1]):
            best = (count, direction, new_candidates)
    if best is None:
        return {'dimension': 3, 'base': base, 'directions': directions,
                'candidate_counts': candidate_counts, 'intersections': intersections}
    count, direction, candidates = best
    span = np.concatenate((span, span ^ direction))
    directions.append(direction)
    candidate_counts.append(count)
    assert len(span) == 16 and np.all(valid[span ^ base])
    outside = np.flatnonzero(candidates)
    outside = outside[~np.isin(outside, span)]
    if len(outside) == 0:
        dimension = 4
    else:
        direction = int(outside[0])
        span = np.concatenate((span, span ^ direction))
        directions.append(direction)
        dimension = 5
        assert len(span) == 32 and np.all(valid[span ^ base])
    return {'dimension': dimension, 'base': base,
            'directions': directions, 'candidate_counts': candidate_counts,
            'intersections': intersections,
            'codes': sorted(int(base ^ offset) for offset in span)}


def panel(valid, attempts, seed):
    rng = np.random.default_rng(seed)
    valid_codes = np.flatnonzero(valid)
    begin = time.monotonic_ns()
    hist = {}
    intersections = 0
    found = []
    first_four = None
    for attempt in range(attempts):
        row = trial(valid, valid_codes, rng)
        dimension = row['dimension']
        hist[str(dimension)] = hist.get(str(dimension), 0) + 1
        intersections += row['intersections']
        if dimension == 4 and first_four is None:
            first_four = {**row, 'attempt_index': attempt}
        if dimension >= 5:
            found.append({**row, 'attempt_index': attempt})
        if attempt % 256 == 255:
            print('attempts', attempt + 1, 'hist', hist, flush=True)
    return {'attempts': attempts, 'dimension_histogram': hist,
            'intersections': intersections, 'first_four': first_four,
            'dimension_five_flats': found, 'wall_ns': time.monotonic_ns() - begin}


def main():
    signal.alarm(120)
    protocol_path = HERE / 'flat_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['source_sha256'] == {'flat_search.py': sha(Path(__file__)),
                                         'valid_bitmap.bin': sha(BITMAP)}
    valid = np.unpackbits(np.frombuffer(BITMAP.read_bytes(), dtype=np.uint8),
                          bitorder='little').astype(np.bool_)
    assert len(valid) == N and int(valid.sum()) == 132045
    actual = panel(valid, protocol['attempts'], protocol['search_seed'])
    controls = []
    for j in range(protocol['random_controls']):
        rng = np.random.default_rng(protocol['control_seed'] + j)
        synthetic = np.zeros(N, dtype=np.bool_)
        synthetic[rng.choice(N, size=132045, replace=False)] = True
        controls.append(panel(synthetic, protocol['attempts'],
                              protocol['control_search_seed'] + j))
    result = {'status': 'PASS_BOUNDED_W20_VALID_AFFINE_FLAT_SEARCH',
              'candidate_id': None, 'source_sha256': protocol['source_sha256'],
              'protocol_sha256': sha(protocol_path), 'source_panel': actual,
              'random_control_panels': controls,
              'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / 'flat_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'], actual['dimension_histogram'],
          [x['dimension_histogram'] for x in controls])


if __name__ == '__main__':
    main()

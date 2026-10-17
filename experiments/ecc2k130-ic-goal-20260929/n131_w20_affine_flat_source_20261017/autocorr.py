"""Exact XOR autocorrelation of the frozen W20 valid-code indicator."""
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fwht(values):
    out = values.astype(np.int64, copy=True)
    step = 1
    while step < len(out):
        view = out.reshape(-1, step * 2)
        left = view[:, :step].copy()
        right = view[:, step:].copy()
        view[:, :step] = left + right
        view[:, step:] = left - right
        step *= 2
    return out


def autocorrelation(valid):
    transform = fwht(valid)
    inverse = fwht(transform * transform)
    assert np.all(inverse % len(valid) == 0)
    return inverse // len(valid)


def summary(corr, count):
    nonzero = corr[1:]
    top = sorted(range(1, N), key=lambda v: (-int(corr[v]), v))[:20]
    return {'valid_codes': count, 'zero_shift': int(corr[0]),
            'minimum_nonzero_shift': int(nonzero.min()),
            'maximum_nonzero_shift': int(nonzero.max()),
            'median_nonzero_shift': int(np.median(nonzero)),
            'mean_nonzero_shift_numerator': int(nonzero.sum()),
            'mean_nonzero_shift_denominator': N - 1,
            'top_shifts': [{'direction': v, 'valid_overlap': int(corr[v])} for v in top],
            'autocorrelation_sha256': hashlib.sha256(corr.tobytes()).hexdigest()}


def main():
    signal.alarm(120)
    protocol_path = HERE / 'autocorr_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['source_sha256'] == {'autocorr.py': sha(Path(__file__)),
                                         'valid_bitmap.bin': sha(BITMAP)}
    bitmap = BITMAP.read_bytes()
    valid = np.unpackbits(np.frombuffer(bitmap, dtype=np.uint8), bitorder='little')
    assert len(valid) == N
    count = int(valid.sum())
    assert count == 132045
    start = time.monotonic_ns()
    corr = autocorrelation(valid)
    actual_ns = time.monotonic_ns() - start
    assert int(corr[0]) == count
    assert int(corr.sum()) == count * count
    assert np.all(corr[1:] % 2 == 0)
    actual = summary(corr, count)
    rng = np.random.default_rng(protocol['random_seed'])
    controls = []
    for _ in range(protocol['random_controls']):
        positions = rng.choice(N, size=count, replace=False)
        synthetic = np.zeros(N, dtype=np.uint8)
        synthetic[positions] = 1
        begin = time.monotonic_ns()
        control_corr = autocorrelation(synthetic)
        controls.append({'maximum_nonzero_shift': int(control_corr[1:].max()),
                         'minimum_nonzero_shift': int(control_corr[1:].min()),
                         'wall_ns': time.monotonic_ns() - begin})
    out = {'status': 'PASS_W20_VALID_CODE_XOR_AUTOCORRELATION',
           'candidate_id': None, 'source_sha256': protocol['source_sha256'],
           'protocol_sha256': sha(protocol_path), 'source': actual,
           'source_transform_ns': actual_ns, 'random_controls': controls,
           'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / 'autocorr_result.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(out['status'], actual['minimum_nonzero_shift'],
          actual['maximum_nonzero_shift'], [x['maximum_nonzero_shift'] for x in controls])


if __name__ == '__main__':
    main()

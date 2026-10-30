"""Load a pinned artifact and replay one D79 source-prefix case without H.build."""
import argparse
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

from sage.all import classical_modular_polynomial

import cache_codec

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST = json.loads((HERE / 'post_inputs.json').read_text())
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == POST['load_runner_sha256']
assert hashlib.sha256((HERE / 'cache_codec.py').read_bytes()).hexdigest() == PLAN['codec_sha256']


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def main(run_number, p):
    assert (run_number, p) == (run_number, PLAN['load_replay_order'][run_number-1])
    source = ROOT / PLAN['source_path']
    shared = ROOT / PLAN['shared_runner_path']
    prefix = ROOT / PLAN['prefix_runner_path']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == PLAN['source_sha256']
    assert hashlib.sha256(shared.read_bytes()).hexdigest() == PLAN['shared_runner_sha256']
    assert hashlib.sha256(prefix.read_bytes()).hexdigest() == PLAN['prefix_runner_sha256']
    assert hashlib.sha256((HERE / 'build-result.json').read_bytes()).hexdigest() == POST['build_result_sha256']
    build_receipt = json.loads((HERE / 'build-result.json').read_text())
    artifact = ROOT / build_receipt['artifact_path']
    H = module(source, f'hecke13_cache_load_r{run_number}')
    S = module(shared, f'hecke13_cache_shared_r{run_number}')
    P = module(prefix, f'hecke13_cache_prefix_r{run_number}')

    def forbidden_build(*_args, **_kwargs):
        raise AssertionError('H_BUILD_FORBIDDEN_IN_LOAD_REPLAY')

    H.build = forbidden_build
    total_start = time.perf_counter_ns()
    start = time.perf_counter_ns()
    funcs, jfun, size = cache_codec.load_artifact(
        artifact, POST['artifact_sha256'], H, PLAN['source_sha256'])
    load_ns = time.perf_counter_ns() - start
    assert S.build_digest(funcs, jfun) == PLAN['expected_function_digest']
    start = time.perf_counter_ns()
    S.MODPOLY = classical_modular_polynomial(13)
    modpoly_ns = time.perf_counter_ns() - start
    case = next(x for x in S.PLAN['cases'] if x['p'] == p)
    result = S.run_prime(case, H, P, funcs, jfun)
    assert result['p'] == p
    output = {'schema': 'hecke-d79-function-cache-load-replay-v1', 'status': 'PASS',
              'run_number': run_number, 'p': p, 'build_invocations': 0,
              'artifact_sha256': POST['artifact_sha256'], 'artifact_bytes': size,
              'function_digest': PLAN['expected_function_digest'],
              'load_wall_ns': load_ns, 'modpoly_wall_ns': modpoly_ns,
              'prime_result': result, 'total_measured_wall_ns': time.perf_counter_ns() - total_start,
              'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'candidate_id': None, 'target_online_ms': None}
    (HERE / f'load-r{run_number}-p{p}.json').write_text(
        json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'run_number': run_number, 'p': p, 'status': 'PASS',
                      'load_wall_ns': load_ns, 'source_count': result['source_count'],
                      'search_trials': result['search_trials']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-number', type=int, choices=[1, 2, 3, 4], required=True)
    parser.add_argument('--p', type=int, choices=[8597, 12197], required=True)
    args = parser.parse_args()
    main(args.run_number, args.p)

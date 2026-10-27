"""Execute one frozen cache-policy and D79 prefix replay case."""
import argparse
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

from sage.all import classical_modular_polynomial

from cache_api import resolve
from codec_v2 import CacheValidationError

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())


def pinned(path, sha):
    path = ROOT / path
    if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
        raise ValueError('PIN_MISMATCH:' + str(path))
    return path


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def main(run_id):
    run = next(x for x in PLAN['runs'] if x['id'] == run_id)
    H = module(pinned(PLAN['source_path'], PLAN['source_sha256']), 'hecke_cache_' + run_id.replace('-', '_'))
    S = module(pinned(PLAN['shared_runner_path'], PLAN['shared_runner_sha256']), 'shared_cache_' + run_id.replace('-', '_'))
    P = module(pinned(PLAN['prefix_runner_path'], PLAN['prefix_runner_sha256']), 'prefix_cache_' + run_id.replace('-', '_'))
    calls = []
    original_build = H.build
    def counted_build(degrees):
        calls.append(tuple(degrees))
        if run['fixture'] == 'valid' or run['policy'] == 'strict':
            raise RuntimeError('BUILD_FORBIDDEN')
        return original_build(degrees)
    H.build = counted_build
    path = ROOT / PLAN['artifact_path']
    if run['fixture'] == 'missing':
        path = HERE / 'fixtures' / 'absent.json'
        if path.exists():
            raise ValueError('MISSING_FIXTURE_EXISTS')
    elif run['fixture'] == 'invalid':
        path = HERE / 'fixtures' / ('hecke13-' + PLAN['artifact_sha256'] + '.json')
    start = time.perf_counter_ns()
    try:
        funcs, jfun, receipt = resolve(H, path, PLAN['artifact_sha256'],
                                       PLAN['source_sha256'], PLAN['function_digest'],
                                       S.build_digest, run['policy'])
    except CacheValidationError as exc:
        if run['policy'] != 'strict':
            raise
        status = 'REJECTED_MISSING' if exc.code == 'CACHE_MISSING' else 'REJECTED_INVALID'
        if status != run['expected'] or calls:
            raise ValueError('STRICT_CONTROL_FAILED')
        out = {'schema': 'hecke-d79-cache-interface-run-v1', 'run_id': run_id,
               'status': status, 'cause': exc.code, 'build_invocations': 0,
               'total_wall_ns': time.perf_counter_ns() - start,
               'prime_result': None, 'candidate_id': None, 'target_online_ms': None}
    else:
        if receipt['status'] != run['expected'] or len(calls) != receipt['build_invocations']:
            raise ValueError('POLICY_RESULT_MISMATCH')
        t0 = time.perf_counter_ns()
        S.MODPOLY = classical_modular_polynomial(13)
        modpoly_ns = time.perf_counter_ns() - t0
        case = next(x for x in S.PLAN['cases'] if x['p'] == run['p'])
        prime = S.run_prime(case, H, P, funcs, jfun)
        out = {'schema': 'hecke-d79-cache-interface-run-v1', 'run_id': run_id,
               **receipt, 'p': run['p'], 'function_digest': S.build_digest(funcs, jfun),
               'modpoly_wall_ns': modpoly_ns, 'prime_result': prime,
               'total_wall_ns': time.perf_counter_ns() - start,
               'candidate_id': None, 'target_online_ms': None}
    out['build_degrees'] = calls
    out['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (HERE / (run_id + '.json')).write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'run_id': run_id, 'status': out['status'],
                      'build_invocations': out['build_invocations']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', choices=[x['id'] for x in PLAN['runs']], required=True)
    main(parser.parse_args().run_id)

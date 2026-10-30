"""Independent coefficient audit and optimized-Python decoder controls."""
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

from codec_v2 import CacheValidationError, build_from_payload, load_artifact

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def expect(code, value, H):
    try:
        build_from_payload(value, H, PLAN['source_sha256'])
    except CacheValidationError as exc:
        if exc.code == code:
            return
        raise ValueError('WRONG_ERROR:' + exc.code) from exc
    raise ValueError('MISSING_ERROR:' + code)


def main():
    source = ROOT / PLAN['source_path']
    shared = ROOT / PLAN['shared_runner_path']
    if hashlib.sha256(source.read_bytes()).hexdigest() != PLAN['source_sha256']:
        raise ValueError('SOURCE_MISMATCH')
    if hashlib.sha256(shared.read_bytes()).hexdigest() != PLAN['shared_runner_sha256']:
        raise ValueError('SHARED_RUNNER_MISMATCH')
    H = module(source, 'hecke_cache_v2_audit')
    S = module(shared, 'hecke_cache_v2_digest')
    artifact = ROOT / PLAN['artifact_path']
    t0 = time.perf_counter_ns()
    fresh_funcs, fresh_jfun = H.build([13])
    fresh_ns = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    loaded_funcs, loaded_jfun, size = load_artifact(
        artifact, PLAN['artifact_sha256'], H, PLAN['source_sha256'])
    load_ns = time.perf_counter_ns() - t0
    if fresh_funcs != loaded_funcs or fresh_jfun != loaded_jfun:
        raise ValueError('COEFFICIENT_MISMATCH')
    digest = S.build_digest(fresh_funcs, fresh_jfun)
    if digest != PLAN['function_digest']:
        raise ValueError('FUNCTION_DIGEST_MISMATCH')
    value = json.loads(artifact.read_text())
    value['jfun']['x0'] = [32, 2]
    expect('RATIONAL_NONCANONICAL', value, H)
    value['jfun']['x0'] = [16, 1]
    value['source_sha256'] = '0' * 64
    expect('SOURCE_MISMATCH', value, H)
    out = {'schema': 'hecke-d79-cache-interface-audit-v1', 'status': 'PASS',
           'optimized_python': not __debug__, 'function_count': len(fresh_funcs),
           'function_digest': digest, 'artifact_bytes': size,
           'fresh_build_wall_ns': fresh_ns, 'load_wall_ns': load_ns,
           'negative_controls': ['RATIONAL_NONCANONICAL', 'SOURCE_MISMATCH'],
           'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / ('audit-optimized.json' if not __debug__ else 'audit-normal.json')).write_text(
        json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': out['status'], 'optimized_python': out['optimized_python']}))


if __name__ == '__main__':
    main()

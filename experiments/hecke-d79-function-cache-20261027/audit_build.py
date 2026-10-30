"""Independently rebuild and compare every cached degree-13 rational function."""
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

import cache_codec

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST = json.loads((HERE / 'post_inputs.json').read_text())
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == POST['audit_builder_sha256']
assert hashlib.sha256((HERE / 'cache_codec.py').read_bytes()).hexdigest() == PLAN['codec_sha256']


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def main():
    source = ROOT / PLAN['source_path']
    shared = ROOT / PLAN['shared_runner_path']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == PLAN['source_sha256']
    assert hashlib.sha256(shared.read_bytes()).hexdigest() == PLAN['shared_runner_sha256']
    assert hashlib.sha256((HERE / 'build-result.json').read_bytes()).hexdigest() == POST['build_result_sha256']
    build_receipt = json.loads((HERE / 'build-result.json').read_text())
    artifact = ROOT / build_receipt['artifact_path']
    assert build_receipt['artifact_sha256'] == POST['artifact_sha256']
    H = module(source, 'hecke13_cache_independent_audit')
    S = module(shared, 'hecke13_cache_shared_digest_audit')
    start = time.perf_counter_ns()
    funcs, jfun = H.build([13])
    fresh_build_ns = time.perf_counter_ns() - start
    start = time.perf_counter_ns()
    loaded_funcs, loaded_jfun, size = cache_codec.load_artifact(
        artifact, POST['artifact_sha256'], H, PLAN['source_sha256'])
    load_ns = time.perf_counter_ns() - start
    assert funcs == loaded_funcs and jfun == loaded_jfun
    assert size == build_receipt['artifact_bytes']
    digest = S.build_digest(funcs, jfun)
    assert digest == S.build_digest(loaded_funcs, loaded_jfun) == PLAN['expected_function_digest']
    out = {'schema': 'hecke-d79-function-cache-audit-v1', 'status': 'PASS',
           'artifact_sha256': POST['artifact_sha256'], 'artifact_bytes': size,
           'function_digest': digest, 'function_count': len(funcs),
           'fresh_build_wall_ns': fresh_build_ns, 'load_wall_ns': load_ns,
           'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / 'audit-build.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PASS', 'functions': len(funcs),
                      'artifact_sha256': out['artifact_sha256']}))


if __name__ == '__main__':
    main()

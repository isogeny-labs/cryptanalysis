"""Build and freeze one canonical content-addressed degree-13 function artifact."""
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
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == PLAN['builder_sha256']
assert hashlib.sha256((HERE / 'cache_codec.py').read_bytes()).hexdigest() == PLAN['codec_sha256']


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def main():
    source = ROOT / PLAN['source_path']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == PLAN['source_sha256']
    shared = ROOT / PLAN['shared_runner_path']
    assert hashlib.sha256(shared.read_bytes()).hexdigest() == PLAN['shared_runner_sha256']
    H = module(source, 'hecke13_cache_builder')
    S = module(shared, 'hecke13_shared_digest')
    t0 = time.perf_counter_ns()
    start = time.perf_counter_ns()
    funcs, jfun = H.build([13])
    build_ns = time.perf_counter_ns() - start
    assert S.build_digest(funcs, jfun) == PLAN['expected_function_digest']
    start = time.perf_counter_ns()
    raw = cache_codec.artifact_bytes(funcs, jfun, PLAN['source_sha256'])
    artifact_sha = hashlib.sha256(raw).hexdigest()
    encode_ns = time.perf_counter_ns() - start
    folder = HERE / 'artifacts'
    folder.mkdir(exist_ok=True)
    artifact = folder / f'hecke13-{artifact_sha}.json'
    start = time.perf_counter_ns()
    if artifact.exists():
        assert artifact.read_bytes() == raw
    else:
        artifact.write_bytes(raw)
    write_ns = time.perf_counter_ns() - start
    start = time.perf_counter_ns()
    loaded_funcs, loaded_jfun, loaded_size = cache_codec.load_artifact(
        artifact, artifact_sha, H, PLAN['source_sha256'])
    assert loaded_size == len(raw)
    assert loaded_funcs == funcs and loaded_jfun == jfun
    assert S.build_digest(loaded_funcs, loaded_jfun) == PLAN['expected_function_digest']
    roundtrip_ns = time.perf_counter_ns() - start
    receipt = {'schema': 'hecke-d79-function-cache-build-v1', 'status': 'COMPLETE',
               'artifact_path': str(artifact.relative_to(ROOT)),
               'artifact_sha256': artifact_sha, 'artifact_bytes': len(raw),
               'source_sha256': PLAN['source_sha256'],
               'function_digest': PLAN['expected_function_digest'],
               'build_wall_ns': build_ns, 'encode_wall_ns': encode_ns,
               'write_wall_ns': write_ns, 'roundtrip_wall_ns': roundtrip_ns,
               'total_measured_wall_ns': time.perf_counter_ns() - t0,
               'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'candidate_id': None, 'target_online_ms': None}
    (HERE / 'build-result.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': receipt['status'], 'artifact_sha256': artifact_sha,
                      'bytes': len(raw), 'function_digest': receipt['function_digest']}))


if __name__ == '__main__':
    main()

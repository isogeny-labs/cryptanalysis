"""Pinned degree-13 function cache with explicit strict or fresh-build fallback."""
import time

from codec_v2 import CacheValidationError, load_artifact


def resolve(H, path, artifact_sha256, source_sha256, function_digest,
            digest_function, policy):
    if policy not in ('strict', 'fallback'):
        raise ValueError('POLICY_INVALID')
    load_start = time.perf_counter_ns()
    try:
        funcs, jfun, size = load_artifact(path, artifact_sha256, H, source_sha256)
        if digest_function(funcs, jfun) != function_digest:
            raise CacheValidationError('FUNCTION_DIGEST_MISMATCH')
    except CacheValidationError as exc:
        load_ns = time.perf_counter_ns() - load_start
        if policy == 'strict':
            raise
        build_start = time.perf_counter_ns()
        funcs, jfun = H.build([13])
        build_ns = time.perf_counter_ns() - build_start
        if digest_function(funcs, jfun) != function_digest:
            raise CacheValidationError('FRESH_BUILD_DIGEST_MISMATCH') from exc
        status = 'FALLBACK_MISSING' if exc.code == 'CACHE_MISSING' else 'FALLBACK_INVALID'
        return funcs, jfun, {'status': status, 'cause': exc.code,
                             'artifact_bytes': None, 'load_wall_ns': load_ns,
                             'build_wall_ns': build_ns, 'build_invocations': 1}
    return funcs, jfun, {'status': 'CACHE_HIT', 'cause': None,
                         'artifact_bytes': size,
                         'load_wall_ns': time.perf_counter_ns() - load_start,
                         'build_wall_ns': 0, 'build_invocations': 0}

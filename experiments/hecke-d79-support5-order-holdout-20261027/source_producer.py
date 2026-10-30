"""Lift all degree-13 source fibers on the sealed prospective classes."""
import hashlib
import importlib.util
import json
import math
import resource
import sys
import time
from pathlib import Path

from sage.all import classical_modular_polynomial

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST = json.loads((HERE / 'post_class.json').read_text())
sys.path.insert(0, str(ROOT / 'experiments/hecke-d79-cache-interface-20261027'))
from cache_api import resolve


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def main():
    class_path = HERE / 'class-result.json'
    if hashlib.sha256(class_path.read_bytes()).hexdigest() != POST['sha256']['class_result']:
        raise ValueError('CLASS_RECEIPT_MISMATCH')
    classes = json.loads(class_path.read_text())
    source = ROOT / PLAN['source_path']
    prefix = ROOT / PLAN['prefix_runner_path']
    if hashlib.sha256(source.read_bytes()).hexdigest() != PLAN['source_sha256']:
        raise ValueError('SOURCE_MISMATCH')
    if hashlib.sha256(prefix.read_bytes()).hexdigest() != PLAN['prefix_runner_sha256']:
        raise ValueError('PREFIX_RUNNER_MISMATCH')
    H = module(source, 'hecke_d79_priority_source')
    P = module(prefix, 'hecke_d79_priority_prefix')
    shared_path = ROOT / 'experiments/hecke-d79-shared-build-20261027/run_shared.py'
    S = module(shared_path, 'hecke_d79_priority_digest')
    funcs25, jfun25 = H.build([2, 5])
    def forbidden_build(*_args, **_kwargs):
        raise RuntimeError('DEGREE13_BUILD_FORBIDDEN')
    H.build = forbidden_build
    funcs13, jfun13, cache_receipt = resolve(
        H, ROOT / PLAN['cache_artifact_path'], PLAN['cache_artifact_sha256'],
        PLAN['source_sha256'], PLAN['cache_function_digest'], S.build_digest, 'strict')
    if jfun13 != jfun25 or set(funcs25) & set(funcs13):
        raise ValueError('FUNCTION_MERGE_MISMATCH')
    funcs = {**funcs25, **funcs13}
    modpoly = classical_modular_polynomial(13)
    out = {'schema': 'hecke-d79-priority-source-v1', 'status': 'RUNNING',
           'cache': cache_receipt, 'cases': [], 'candidate_id': None,
           'target_online_ms': None}
    path = HERE / 'source-result.json'
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    for frozen in classes['cases']:
        p = frozen['p']
        if frozen['status'] != 'CLASS_READY':
            out['cases'].append({'p': p, 'status': 'CLASS_NOT_READY'})
            path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
            continue
        R = H.Reduced(p, funcs, jfun13, [2, 5, 13])
        E = R.E
        points = [E(x, y) for x, y in frozen['class_points']]
        if int(E.cardinality()) != frozen['curve_order']:
            raise ValueError('CURVE_ORDER_MISMATCH')
        cache = {}
        cell = {'p': p, 'status': 'RUNNING', 'degree13_sources': [],
                'priority_order': frozen['priority_order'],
                'ascending_order': frozen['ascending_order']}
        out['cases'].append(cell)
        path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
        for i, point in enumerate(points):
            t0 = time.perf_counter_ns()
            poly = R.neighbour_x(13, point)
            pattern = [[int(f.degree()), int(mult)] for f, mult in poly.factor()]
            d = math.lcm(*(degree for degree, _ in pattern))
            if d > 12 or any(mult != 1 for _, mult in pattern):
                entry = {'source': i, 'factor_pattern': pattern,
                         'splitting_degree': d, 'status': 'CENSORED_EXTENSION_OR_MULTIPLICITY'}
            else:
                entry, _ = P.lift_source(i, point, R, jfun13, points, {}, cache,
                                         modpoly, pattern)
            entry['lift_wall_ns'] = time.perf_counter_ns() - t0
            cell['degree13_sources'].append(entry)
            path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
        cell['status'] = 'COMPLETE' if all(x['status'] == 'OUTSIDE_CLASS_TRACE'
                                          for x in cell['degree13_sources']) else 'CENSORED'
        path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'p': p, 'status': cell['status'],
                          'sources': len(cell['degree13_sources'])}), flush=True)
    out['status'] = 'COMPLETE'
    out['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()

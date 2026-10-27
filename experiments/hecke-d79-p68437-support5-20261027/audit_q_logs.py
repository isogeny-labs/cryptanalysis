"""Curve-derived order-109 log vector for all support-five relation rows."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE/'inputs.json').read_text())
POST = json.loads((HERE/'post_run.json').read_text())


def pinned(name):
    item = PLAN['frozen'][name]
    raw = (ROOT/item['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('PARENT_PIN_MISMATCH:' + name)
    return json.loads(raw)


def main():
    raw = (HERE/'result.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != POST['result_sha256']:
        raise ValueError('RESULT_PIN_MISMATCH')
    result = json.loads(raw)
    cls = next(x for x in pinned('class-result.json')['cases'] if x['p'] == PLAN['p'])
    prior = next(x for x in pinned('analysis.json')['cases'] if x['p'] == PLAN['p'])
    E = EllipticCurve(GF(PLAN['p']), [0, -1, 1, -10, -20])
    if int(E.cardinality()) != PLAN['curve_order']:
        raise ValueError('CURVE_ORDER_MISMATCH')
    points = [E(x, y) for x, y in cls['class_points']]
    projected = [(PLAN['curve_order']//109)*P for P in points]
    generator = next(P for P in projected if P != E(0))
    lookup = {k*generator: k for k in range(109)}
    if len(lookup) != 109 or any(P not in lookup for P in projected):
        raise ValueError('SUBGROUP_NOT_CYCLIC_109')
    logs = [lookup[P] for P in projected]
    rows = [x['row'] for x in cls['base_rows']]
    rows += [x['row'] for x in prior['direct_candidates']]
    rows += [x['row'] for x in prior['hecke_candidates']]
    rows += [x['row'] for x in result['arms']['direct']['candidates']]
    rows += [x['row'] for x in result['arms']['hecke']['candidates']]
    if any(sum(int(coeff)*logs[int(i)] for i, coeff in row.items()) % 109
           for row in rows):
        raise ValueError('LOG_KERNEL_MISMATCH')
    out = {'schema': 'hecke-d79-p68437-support5-q-log-audit-v1', 'status': 'PASS',
           'q': 109, 'generator': [int(generator[0]), int(generator[1])],
           'class_log_vector': logs, 'nonzero_coordinates': sum(x != 0 for x in logs),
           'rows_checked': len(rows), 'combined_rank_mod_q': result['combined_rank_mod_q']}
    (HERE/'q-log-audit.json').write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','q':109,'nonzero_coordinates':out['nonzero_coordinates'],
                      'rows_checked':len(rows)}))


if __name__ == '__main__':
    main()

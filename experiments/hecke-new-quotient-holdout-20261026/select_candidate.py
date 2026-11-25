"""Apply the frozen mixed-quotient selector using checked Sage."""
import json
from collections import Counter
from pathlib import Path
from sage.all import BinaryQF, is_prime, is_squarefree, pari

HERE = Path(__file__).resolve().parent
SQUARES11 = {1, 3, 4, 5, 9}


def model(D):
    h1 = int(pari.qfbclassno(D))
    h3 = int(pari.qfbclassno(9*D))
    if h3 != 3*h1:
        return None, 'class_number_ratio'
    if 16*h1 > 800:
        return None, 'column_cap'
    a1 = BinaryQF(2, 1, (1-D)//8).form_class()
    a3 = BinaryQF(2, 1, (1-9*D)//8).form_class()
    ram = BinaryQF(3, 3, (9-D)//12).form_class()
    o1, o3 = int(a1.order()), int(a3.order())
    if o3 % o1 or o3//o1 not in (1, 3):
        return None, 'order_ratio'
    exponent = next((k for k in range(o1) if k*a1 == ram), None)
    lift = 3//(o3//o1)
    touches = lift*(1 if exponent is not None else 2)
    cycles = 2*h3//o3
    if 2*h3 % o3 or cycles % touches:
        return None, 'cycle_divisibility'
    components = cycles//touches
    mixed = exponent is not None and (o1//2)%2 == 0
    if not mixed:
        return None, 'not_mixed'
    if components < 4:
        return None, 'too_few_components'
    pairs = h1
    floor_rank = cycles + pairs
    return {'D': D, 'h1': h1, 'h3': h3, 'norm2_order_f1': o1,
            'norm2_order_f3': o3, 'ramified_exponent': exponent,
            'lift_kernel_image_size': lift, 'pair_cycle_touches': touches,
            'cycle_count': cycles, 'pair_count': pairs,
            'component_count': components, 'mixed_overlap': True,
            'balanced_component_count': 0, 'floor_direction_rank': floor_rank,
            'class_columns_predicted': 16*h1, 'rows_by_degree_predicted': {'2': 8*h1, '3': 4*h1},
            'full_rank_predicted': 10*h1,
            'nonfloor_rank_predicted': 10*h1-floor_rank}, None


def main():
    screened = []
    selected = None
    reasons = Counter()
    for d in range(1408, 10001):
        if d % 8 != 7 or d % 3 or not is_squarefree(d):
            continue
        D = -d
        if D % 11 not in SQUARES11:
            reasons['11_inert_or_ramified'] += 1
            screened.append({'d': d, 'reason': '11_inert_or_ramified'})
            continue
        forecast, reason = model(D)
        if reason:
            reasons[reason] += 1
            screened.append({'d': d, 'reason': reason})
            continue
        selected = forecast
        screened.append({'d': d, 'reason': 'selected'})
        break
    if selected is None:
        status = 'NO_ELIGIBLE_INSTANCE'
    else:
        d = -selected['D']
        field = next(({'p': v*v+9*d, 'u': 2*v, 'v': v}
                      for v in range(1, 317) if v*v+9*d <= 100000
                      and v*v+9*d not in (2, 3, 5, 11) and is_prime(v*v+9*d)), None)
        selected['field'] = field
        status = 'SELECTED' if field else 'NO_ELIGIBLE_FIELD_PRIME'
    output = {'status': status, 'selection': selected, 'screened': screened,
              'rejection_counts': dict(reasons)}
    (HERE / 'selection.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in output.items() if k != 'screened'}, sort_keys=True))


if __name__ == '__main__':
    main()

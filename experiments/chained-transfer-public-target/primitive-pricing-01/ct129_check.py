#!/usr/bin/env python3
"""Strict producer-side audit of CT129 source-vs-isogeny BSGS paired data.

This cannot turn producer timing or reported booleans into a PCC-signed result.
"""
import argparse
import copy
import hashlib
import json
import random
import statistics as stats
from pathlib import Path

SCALARS = (1, 2, 17, 12345, 2771710)
ORDER = (("source", "target", "target", "source"),
         ("target", "source", "source", "target"))

class InvalidEvidence(ValueError):
    pass

def require(value, message):
    if not value:
        raise InvalidEvidence(message)

def positive_int(n):
    return type(n) is int and n > 0

def norm(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'))

def validate(data):
    require(type(data) is dict, 'root object')
    require(data.get('schema') == 'ct129-isogeny-bsgs-screen/v1', 'schema')
    require(data.get('standing') == '[pcc:unverified]', 'standing')
    require((data.get('source_prime'), data.get('subgroup_prime'),
             data.get('full_group_order')) == (223, 2771711, 11086844), 'instance identity')
    require((data.get('source_field_degree'), data.get('destination_field_degree')) == (3, 6), 'field degrees')
    require(data.get('blocks_per_target') == 4, 'block count')
    require(data.get('speedup_claim') is False, 'no admitted speedup')
    require(data.get('source_and_target_inputs_identical_before_isogeny') is True, 'source input parity')
    require(data.get('setup_scope') == 'once per process; NOT included in per-target paired solver timing', 'setup scope')
    require(data.get('solve_algorithm') == 'fresh-table deterministic BSGS on source or mapped target; source scalar independently checked', 'method')
    require(data.get('scope') == 'elliptic isogeny plus cold BSGS tables; NOT complete Jacobian transfer, optimized rho or IC', 'scope')
    for field in ('original_instance_constructor_ns', 'full_geometry_runtime_setup_ns', 'memory_peak_linux_vm_hwm_kb'):
        require(positive_int(data.get(field)), field)
    rows = data.get('rows')
    require(type(rows) is list and len(rows) == 5, 'five public rows')
    require(tuple(r.get('scalar_fixture_only') for r in rows if type(r) is dict) == SCALARS,
            'ordered frozen scalars')
    source_keys, target_keys = [], []
    result = []
    for row, k in zip(rows, SCALARS):
        require(type(row) is dict and set(row) == {
            'scalar_fixture_only', 'primary_nontrivial_cohort', 'source_public',
            'destination_public', 'all_source_and_destination_logarithms_verified', 'blocks'
        }, 'row fields')
        require(row.get('primary_nontrivial_cohort') is (k not in (1, 2)), 'cohort separation')
        require(row.get('all_source_and_destination_logarithms_verified') is True, 'known answer not verified')
        for key, acc in [('source_public', source_keys), ('destination_public', target_keys)]:
            value = row.get(key)
            require(value is not None and type(value) in (list, dict) and len(value) > 0, key)
            acc.append(norm(value))
        blocks = row.get('blocks')
        require(type(blocks) is list and len(blocks) == 4, 'four complete blocks')
        ratios, aa = [], []
        for i, b in enumerate(blocks):
            require(type(b) is dict and set(b) == {
                'block', 'order', 'source_ns', 'target_ns',
                'source_table_entries', 'target_table_entries'
            }, 'block schema')
            require(type(b['block']) is int and b['block'] == i, 'block ID')
            require(tuple(b['order']) == ORDER[i % 2], 'ABBA or BAAB order')
            for label in ('source', 'target'):
                times = b.get(label + '_ns')
                counts = b.get(label + '_table_entries')
                require(type(times) is list and len(times) == 2 and all(map(positive_int, times)), 'timing duration')
                require(type(counts) is list and len(counts) == 2 and all(type(x) is int and 1600 <= x <= 1700 for x in counts), 'fresh baby-table size')
            s, t = stats.mean(b['source_ns']), stats.mean(b['target_ns'])
            ratios.append(s / t)
            aa.append((b['source_ns'][0] / b['source_ns'][1], b['target_ns'][0] / b['target_ns'][1]))
        result.append(dict(scalar=k, primary=k not in (1, 2), ratios=ratios,
                           aa=aa, ratio=stats.median(ratios)))
    require(len(set(source_keys)) == 5 and len(set(target_keys)) == 5,
            'same public point substituted')
    return result

def report(data):
    summaries = validate(data)
    primary = [r for r in summaries if r['primary']]
    # Resample WHOLE ABBA blocks within each scalar, never individual calls.
    rng = random.Random(129)
    boots = []
    for _ in range(2000):
        boots.append(stats.median([stats.median(rng.choices(r['ratios'], k=4))
                                   for r in primary]))
    boots.sort()
    return {
        'schema': 'ct129-producer-audit/v1',
        'primary_cohort': [r['scalar'] for r in primary],
        'median_baseline_over_isogeny': stats.median(r['ratio'] for r in primary),
        'within_fixed_fixture_block_bootstrap_95pct': [boots[49], boots[1949]],
        'by_scalar': [{'scalar':r['scalar'], 'source_over_isogeny':r['ratio'],
                       'source_AA': [a[0] for a in r['aa']],
                       'target_AA':[a[1] for a in r['aa']]} for r in summaries],
        'setup_source_instance_ns':data['original_instance_constructor_ns'],
        'setup_full_transfer_geometry_ns': data['full_geometry_runtime_setup_ns'],
        'process_peak_RSS_kb':data['memory_peak_linux_vm_hwm_kb'],
        'conclusion_scope':'paired post-setup BSGS proxy; NOT complete single-target ECDLP comparison',
        'standing':'[pcc:unverified]'
    }

def synthetic():
    return dict(schema='ct129-isogeny-bsgs-screen/v1', standing='[pcc:unverified]',
        source_prime=223, subgroup_prime=2771711, full_group_order=11086844,
        source_field_degree=3, destination_field_degree=6,
        original_instance_constructor_ns=100, full_geometry_runtime_setup_ns=200,
        memory_peak_linux_vm_hwm_kb=5000, blocks_per_target=4,
        setup_scope='once per process; NOT included in per-target paired solver timing',
        scope='elliptic isogeny plus cold BSGS tables; NOT complete Jacobian transfer, optimized rho or IC',
        source_and_target_inputs_identical_before_isogeny=True,
        solve_algorithm='fresh-table deterministic BSGS on source or mapped target; source scalar independently checked',
        speedup_claim=False, rows=[dict(
            scalar_fixture_only=k, primary_nontrivial_cohort=k not in (1, 2),
            source_public=[k, k + 1], destination_public=[2*k, 3*k],
            all_source_and_destination_logarithms_verified=True,
            blocks=[dict(block=i, order=list(ORDER[i%2]), source_ns=[1000+i,1001+i],
                         target_ns=[2000+i,2001+i], source_table_entries=[1665,1665],
                         target_table_entries=[1665,1665]) for i in range(4)])
          for k in SCALARS])

def selftest():
    good = synthetic()
    validate(good)
    require(report(good)['median_baseline_over_isogeny'] < 1, 'control ratio direction')
    mutations = {
        'bad_order': lambda x: x['rows'][0]['blocks'][0]['order'].__setitem__(0, 'target'),
        'missing_block': lambda x: x['rows'][1]['blocks'].pop(),
        'wrong_public': lambda x: x['rows'][2].update(source_public=x['rows'][0]['source_public']),
        'wrong_scalar': lambda x: x['rows'][3].update(scalar_fixture_only=2),
        'missing_memory': lambda x: x.pop('memory_peak_linux_vm_hwm_kb'),
        'false_speedup': lambda x: x.update(speedup_claim=True),
        'missing_time': lambda x: x['rows'][4]['blocks'][2]['source_ns'].pop(),
        'zero_duration': lambda x: x['rows'][2]['blocks'][3]['target_ns'].__setitem__(1, 0),
        'wrong_group': lambda x: x.update(subgroup_prime=2773073),
        'bad_table': lambda x: x['rows'][4]['blocks'][1]['source_table_entries'].__setitem__(0, 1),
        'false_scope': lambda x: x.update(scope='end-to-end ECDLP'),
        'wrong_cohort': lambda x: x['rows'][1].update(primary_nontrivial_cohort=True),
        'false_verification': lambda x: x['rows'][0].update(all_source_and_destination_logarithms_verified=False),
    }
    for name, mutate in mutations.items():
        v = copy.deepcopy(good)
        mutate(v)
        try:
            validate(v)
        except InvalidEvidence:
            continue
        raise RuntimeError(f'FAIL OPEN: {name}')
    return {'positive':'accepted', **{name:'rejected' for name in mutations}}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('input', nargs='?', type=Path)
    p.add_argument('--self-test', action='store_true')
    args = p.parse_args()
    if args.self_test:
        print(json.dumps(selftest(), sort_keys=True))
        return
    if args.input is None:
        p.error('input JSON required')
    raw = args.input.read_bytes()
    data = json.loads(raw)
    r = report(data)
    r['raw_input_sha256'] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(r, sort_keys=True, indent=2))

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Fail-closed CT126 ABBA primitive-price auditor; *not* a cold ECDLP validator.

Do not rely on assert for input validation: Python -O removes it entirely.
The report remains a producer-side diagnostic until separately verified PCC.
"""
import argparse
import copy
import hashlib
import json
import random
import statistics as st
from pathlib import Path

ARMS = ('original-1', 'reuse-1', 'reuse-2', 'original-2')
LABELS = ('C169', 'C13_first', 'C13_second', 'D', 'direct_warm', 'retained_warm')
SCALARS = (1, 2, 17, 12_345, 2_771_710)
SEQUENCE = ('original:original-1', 'reuse:reuse-1',
            'reuse:reuse-2', 'original:original-2')


class InvalidEvidence(ValueError):
    """A missing or corrupted input MUST fail under normal and optimized Python."""


def require(condition, message):
    if not condition:
        raise InvalidEvidence(message)


def exact_positive_integer(value):
    return type(value) is int and value > 0


def validate(x):
    require(type(x) is dict, 'record must be object')
    require(x.get('schema') == 'ct126-primitive-price/v1', 'schema')
    require(x.get('standing') == '[pcc:unverified]', 'standing')
    require((x.get('source_prime'), x.get('subgroup_prime'),
             x.get('complete_group_order')) == (223, 2_771_711, 11_086_844),
            'field/subgroup/complete-group identity')
    require((x.get('scalar_fixture_count'), x.get('rounds_recorded'),
             x.get('warmup_rounds')) == (5, 12, 4), 'sample dimensions')
    require(exact_positive_integer(x.get('setup_construct_ns')), 'setup ns')
    require(exact_positive_integer(x.get('linux_vm_hwm_kb')), 'peak resident memory missing')
    require(x.get('scope') == 'actual elliptic arithmetic in prebuilt geometry; NOT cold single-target ECDLP',
            'scope must explicitly exclude cold ECDLP')
    require(x.get('timing_order') == 'ABBA by block; original/optimized process ABBA must be external',
            'timing order')
    ids = x.get('identity_checks')
    require(type(ids) is list and len(ids) == 5, 'identity count')
    require(tuple(v.get('scalar_fixture_only') for v in ids if type(v) is dict) == SCALARS,
            'fixed scalar identities')
    # The JSON objects have no intrinsic curve verification; require at least
    # nonempty, distinct outputs so the all-constant substitution is not accepted.
    public_source, public_target = [], []
    for i, row in enumerate(ids):
        require(type(row) is dict and set(row) == {
            'scalar_fixture_only', 'source_public', 'output_public',
            'direct_equals_retained'}, f'identity schema {i}')
        require(row['direct_equals_retained'] is True, f'route disagreement {i}')
        for key, dest in (('source_public', public_source), ('output_public', public_target)):
            val = row[key]
            require(val is not None and type(val) in (list, dict, str)
                    and len(val) > 0, f'empty public key {i}:{key}')
            dest.append(json.dumps(val, sort_keys=True))
    require(len(set(public_source)) == 5 and len(set(public_target)) == 5,
            'non-distinct public keys')
    timed = x.get('timed')
    require(type(timed) is dict and set(timed) == set(LABELS), 'timed label set')
    for k in LABELS:
        z = timed[k]
        require(type(z) is dict and set(z) == {'repetitions_per_block', 'raw_block_ns'},
                f'timed schema {k}')
        require(type(z['repetitions_per_block']) is int and
                z['repetitions_per_block'] == (64 if k in LABELS[:4] else 5),
                f'repetitions {k}')
        samples = z['raw_block_ns']
        require(type(samples) is list and len(samples) == 12, f'samples {k}')
        require(all(exact_positive_integer(v) for v in samples), f'positive integer samples {k}')


def audit(runs):
    require(type(runs) is dict and set(runs) == set(ARMS), 'arm set')
    for arm, value in runs.items():
        try:
            validate(value)
        except InvalidEvidence as error:
            raise InvalidEvidence(f'{arm}: {error}') from error
    same = runs['original-1']['identity_checks']
    require(all(r['identity_checks'] == same for r in runs.values()),
            'public output mismatch across ABBA arms')

    def samples(arm, label):
        rec = runs[arm]['timed'][label]
        return [n / rec['repetitions_per_block'] for n in rec['raw_block_ns']]

    prices = {}
    for k in LABELS:
        a = samples('original-1', k) + samples('original-2', k)
        b = samples('reuse-1', k) + samples('reuse-2', k)
        ma, mb = st.median(a), st.median(b)
        rng = random.Random(126 + len(k))
        boots = sorted(st.median(rng.choices(a, k=len(a))) /
                       st.median(rng.choices(b, k=len(b))) for _ in range(500))
        prices[k] = {
            'original_median_ns_per_call': ma,
            'reuse_median_ns_per_call': mb,
            'original_over_reuse': ma / mb,
            'diagnostic_bootstrap_95_pct': [boots[12], boots[487]],
            'original_AA': st.median(samples('original-1', k)) / st.median(samples('original-2', k)),
            'reuse_AA': st.median(samples('reuse-1', k)) / st.median(samples('reuse-2', k)),
        }
    for arm in ('original', 'reuse'):
        prices['crossover_ns_' + arm] = (
            prices['C169'][arm + '_median_ns_per_call']
            - prices['C13_first'][arm + '_median_ns_per_call']
            - prices['C13_second'][arm + '_median_ns_per_call'])
    return {
        'schema': 'ct126-paired-diagnostic/v1',
        'public_fixture_count': 5,
        'prices': prices,
        'status': '[pcc:unverified]; microtiming and warm transfers only; NO cold ECDLP cost advantage'
    }


def fixture():
    rec = {
        'schema': 'ct126-primitive-price/v1', 'standing': '[pcc:unverified]',
        'source_prime': 223, 'subgroup_prime': 2_771_711,
        'complete_group_order': 11_086_844,
        'scalar_fixture_count': 5, 'rounds_recorded': 12,
        'warmup_rounds': 4, 'setup_construct_ns': 10,
        'linux_vm_hwm_kb': 1024,
        'scope': 'actual elliptic arithmetic in prebuilt geometry; NOT cold single-target ECDLP',
        'timing_order': 'ABBA by block; original/optimized process ABBA must be external',
        'identity_checks': [
            {'scalar_fixture_only': k, 'source_public': [k],
             'output_public': [k + 1], 'direct_equals_retained': True}
            for k in SCALARS
        ],
        'timed': {
            k: {'repetitions_per_block': 64 if k in LABELS[:4] else 5,
                'raw_block_ns': [1000 + i for i in range(12)]}
            for k in LABELS
        },
    }
    return {arm: copy.deepcopy(rec) for arm in ARMS}


def selftest():
    runs = fixture()
    require(audit(runs)['public_fixture_count'] == 5, 'positive replay failed')
    mutations = {
        'mutated_output': lambda x: x['reuse-1']['identity_checks'][0].update(output_public=[999]),
        'missing_sample': lambda x: x['original-2']['timed']['D']['raw_block_ns'].pop(),
        'negative_duration': lambda x: x['reuse-2']['timed']['C169']['raw_block_ns'].__setitem__(0, -1),
        'false_schema': lambda x: x['original-1'].update(schema='ct126-cold-ecdlp/v1'),
        'missing_memory': lambda x: x['original-1'].pop('linux_vm_hwm_kb'),
        'wrong_scalar': lambda x: x['reuse-1']['identity_checks'][0].update(scalar_fixture_only=2),
        'constant_public': lambda x: [row.update(output_public=[1]) for row in x['reuse-1']['identity_checks']],
        'false_scope': lambda x: x['original-1'].update(scope='complete ECDLP speedup'),
    }
    for name, mutate in mutations.items():
        bad = copy.deepcopy(runs)
        mutate(bad)
        try:
            audit(bad)
        except InvalidEvidence:
            continue
        raise RuntimeError(f'MUTATION ACCEPTED: {name}')
    return {'positive': 'pass', **{name: 'rejected' for name in mutations}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', nargs='?', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(selftest(), sort_keys=True))
        return
    if args.directory is None:
        parser.error('directory required')
    directory = args.directory
    require((directory / 'sequence.txt').read_text().splitlines() == list(SEQUENCE),
            'ABBA sequence mismatch')
    host = (directory / 'host.txt').read_text()
    require(bool(host.strip()) and 'rustc' in host and 'cargo' in host,
            'host/toolchain receipt missing')
    paths = [directory / (arm + '.json') for arm in ARMS]
    runs = {arm: json.loads(path.read_text()) for arm, path in zip(ARMS, paths)}
    report = audit(runs)
    report['raw_input_sha256'] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    report['host_sha256'] = hashlib.sha256((directory / 'host.txt').read_bytes()).hexdigest()
    (directory / 'diagnostic.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()

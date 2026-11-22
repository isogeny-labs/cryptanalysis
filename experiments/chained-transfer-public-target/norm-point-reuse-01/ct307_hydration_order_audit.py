#!/usr/bin/env python3
"""CT307 read-only check: classify pinned-model hydration order, never S3 custody."""
import argparse
import json
import re
from pathlib import Path

MODEL = 'docs/research-artifacts/chained-transfer/nondual-models-18'
PIN = '3de8c174cf65e6b34bf8579d97b817b8f5dc2ded'
BLOB = 'c49cd3de885c5b4292c283eb85e4327b872529ed'
STEP = re.compile(r'^\s{6}- name: (.+)$', re.M)
PULL = re.compile(r'(?:[\w./-]*artifacts\.py)\s+pull\b')


def audit(text, lane):
    if lane not in ('ct200', 'ct245') or PIN not in text or BLOB not in text:
        raise ValueError('unknown lane or missing exact historical pin')
    matches = list(STEP.finditer(text))
    if not matches:
        raise ValueError('workflow steps unavailable')
    calls = []
    for i, match in enumerate(matches):
        block = text[match.end():matches[i+1].start() if i+1 < len(matches) else len(text)]
        block = '\n'.join(s for s in block.splitlines() if not s.lstrip().startswith('#'))
        block = re.sub(r'\\\s*\n\s*', ' ', block)
        for p in PULL.finditer(block):
            cmd = block[p.start():].split('\n', 1)[0]
            if MODEL in cmd:
                calls.append((match.group(1), cmd,
                              f'_ct{lane[2:]}_artifact_tools/tools/artifacts/artifacts.py' in cmd,
                              block))
    pinned = [i for i, c in enumerate(calls) if c[2]]
    if len(pinned) != 1:
        raise ValueError('missing or ambiguous pinned-model call')
    n = pinned[0]
    prior = calls[:n]
    block = calls[n][3]
    sts = ('sts get-caller-identity' in block and
           block.index('sts get-caller-identity') <
           block.index(f'_ct{lane[2:]}_artifact_tools/tools/artifacts/artifacts.py pull')
           and 'exit 42' in block)
    if lane == 'ct200':
        if not any('tools/artifacts/artifacts.py pull' in c[1] and not c[2]
                   for c in prior):
            raise ValueError('CT200 hazard classification changed; manual review required')
    elif prior or not sts:
        raise ValueError('CT245 acquired prehydration or lost STS-first guard')
    return {
        'lane': lane,
        'source_only': True,
        'class': ('known_pre_hydration_hazard' if lane == 'ct200'
                  else 'sts_first_no_observed_literal_prefetch'),
        'earlier_model_pull_step_names': [c[0] for c in prior],
        'sts_precedes_historical_pull_in_step': sts,
        'remote_s3_requests_observed': None,
        'authenticated_model_custody': False,
        'native_executions': 0,
        'pcc': 'unverified',
    }


def selftest():
    def source(lane, before=''):
        return (f'jobs:\n  x:\n    steps:\n'
                f'      - name: source\n        with:\n          ref: {PIN}\n'
                + before + f'      - name: model\n        run: |\n'
                + f'          test x = {BLOB}\n'
                + ('          aws sts get-caller-identity || exit 42\n' if lane == 'ct245' else '')
                + f'          python3 _{lane}_artifact_tools/tools/artifacts/artifacts.py pull --jobs 2 \\\n'
                + f'            {MODEL}\n')
    prefetch = (f'      - name: unapproved prefetch\n        run: |\n'
                f'          python3 tools/artifacts/artifacts.py pull {MODEL}\n')
    a = source('ct200', prefetch)
    b = source('ct245')
    if audit(a, 'ct200')['class'] != 'known_pre_hydration_hazard':
        raise AssertionError('CT200 hazard positive failed')
    if audit(b, 'ct245')['class'] != 'sts_first_no_observed_literal_prefetch':
        raise AssertionError('CT245 structural positive failed')
    failures = [(source('ct245', prefetch), 'ct245'),
                (b.replace('sts get-caller-identity', 'echo mock-identity'), 'ct245'),
                (b.replace('exit 42', 'exit 0'), 'ct245'),
                (b.replace(BLOB, '0'*40), 'ct245'),
                (b.replace(PIN, 'main'), 'ct245'),
                (source('ct200'), 'ct200'),
                (a.replace('_ct200_artifact_tools/tools/artifacts/artifacts.py pull',
                           'echo fake-original'), 'ct200'),
                (b.replace(MODEL, 'unrelated-path'), 'ct245')]
    for n, (text, lane) in enumerate(failures):
        try:
            audit(text, lane)
        except ValueError:
            continue
        raise AssertionError(f'synthetic mutation {n} escaped')
    return {'synthetic_positives': 2, 'synthetic_mutations_rejected': len(failures),
            'native_executions': 0, 'pcc': 'unverified'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ct200', type=Path)
    parser.add_argument('--ct245', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(selftest(), sort_keys=True))
    if args.ct200 or args.ct245:
        if not args.ct200 or not args.ct245:
            parser.error('both exact workflow files required')
        print(json.dumps({'ct200': audit(args.ct200.read_text(), 'ct200'),
                          'ct245': audit(args.ct245.read_text(), 'ct245')},
                         indent=2, sort_keys=True))
    elif not args.self_test:
        parser.error('provide --self-test or both workflows')


if __name__ == '__main__':
    main()

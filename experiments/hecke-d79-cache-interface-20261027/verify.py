"""Check frozen inputs and all retained cache-policy receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST = json.loads((HERE / 'post_inputs.json').read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for stem in ('source', 'prefix_runner', 'shared_runner'):
        if digest(ROOT / PLAN[stem + '_path']) != PLAN[stem + '_sha256']:
            raise ValueError(stem + '_PIN_MISMATCH')
    if digest(ROOT / PLAN['artifact_path']) != PLAN['artifact_sha256']:
        raise ValueError('ARTIFACT_PIN_MISMATCH')
    if (ROOT / PLAN['artifact_path']).stat().st_size != PLAN['artifact_bytes']:
        raise ValueError('ARTIFACT_SIZE_MISMATCH')
    fixture = HERE / 'fixtures' / ('hecke13-' + PLAN['artifact_sha256'] + '.json')
    if digest(fixture) != POST['invalid_fixture_sha256']:
        raise ValueError('FIXTURE_PIN_MISMATCH')
    if (HERE / 'fixtures' / 'absent.json').exists():
        raise ValueError('MISSING_FIXTURE_EXISTS')
    for name, sha in POST['code_sha256'].items():
        if digest(HERE / name) != sha:
            raise ValueError(name + '_HASH_MISMATCH')
    audit = json.loads((HERE / 'audit-optimized.json').read_text())
    if (audit['status'], audit['optimized_python'], audit['function_count'],
        audit['function_digest'], audit['artifact_bytes']) != (
            'PASS', True, 28, PLAN['function_digest'], PLAN['artifact_bytes']):
        raise ValueError('AUDIT_MISMATCH')
    if audit['negative_controls'] != ['RATIONAL_NONCANONICAL', 'SOURCE_MISMATCH']:
        raise ValueError('NEGATIVE_CONTROLS_MISMATCH')
    for run in PLAN['runs']:
        result = json.loads((HERE / (run['id'] + '.json')).read_text())
        if result['status'] != run['expected'] or result['run_id'] != run['id']:
            raise ValueError(run['id'] + '_STATUS_MISMATCH')
        expected_builds = int(run['expected'].startswith('FALLBACK'))
        if result['build_invocations'] != expected_builds or len(result['build_degrees']) != expected_builds:
            raise ValueError(run['id'] + '_BUILD_COUNT_MISMATCH')
        if expected_builds and result['build_degrees'] != [[13]]:
            raise ValueError(run['id'] + '_BUILD_DEGREE_MISMATCH')
        if run['expected'].startswith('REJECTED'):
            if result['prime_result'] is not None:
                raise ValueError(run['id'] + '_UNEXPECTED_REPLAY')
            continue
        prime = result['prime_result']
        case = next(x for x in PLAN['cases'] if x['p'] == run['p'])
        frozen = json.loads((ROOT / case['prefix_result_path']).read_text())
        if digest(ROOT / case['prefix_result_path']) != case['prefix_result_sha256']:
            raise ValueError(run['id'] + '_FROZEN_PIN_MISMATCH')
        if (prime['p'] != run['p'] or
            prime['final_rank_qq'] != frozen['sources'][-1]['rank_qq'] or
            prime['final_rank_mod_q'] != frozen['sources'][-1]['rank_mod_q'] or
            prime['prefix_result_sha256'] != case['prefix_result_sha256'] or
            result['function_digest'] != PLAN['function_digest']):
            raise ValueError(run['id'] + '_REPLAY_MISMATCH')
    print(json.dumps({'status': 'PASS', 'runs': len(PLAN['runs']),
                      'optimized_audit': True, 'artifact_sha256': PLAN['artifact_sha256']}))


if __name__ == '__main__':
    main()

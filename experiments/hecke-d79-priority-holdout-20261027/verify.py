"""Cross-link the prospective selection, sealed class, source and audit receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE/'inputs.json').read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name, pin, key):
    path = HERE / name
    if sha(path) != pin['sha256'][key]:
        raise ValueError('PIN_MISMATCH:' + name)
    return json.loads(path.read_text())


def main():
    post_class = json.loads((HERE/'post_class.json').read_text())
    post_source = json.loads((HERE/'post_source.json').read_text())
    post_analysis = json.loads((HERE/'post_analysis.json').read_text())
    post_audit = json.loads((HERE/'post_audit.json').read_text())
    screen = read('prescreen.json', post_class, 'prescreen')
    classes = read('class-result.json', post_class, 'class_result')
    sources = read('source-result.json', post_source, 'source_result')
    analysis = read('analysis.json', post_analysis, 'analysis')
    audit = read('audit.json', post_audit, 'audit')
    for name, pin, key in [('prescreen.py', post_class, 'prescreen_script'),
                           ('class_producer.py', post_class, 'class_producer'),
                           ('source_producer.py', post_source, 'source_producer'),
                           ('analyze.py', post_analysis, 'analyzer'),
                           ('audit_sage.py', post_audit, 'audit_script')]:
        if sha(HERE/name) != pin['sha256'][key]:
            raise ValueError('CODE_PIN_MISMATCH:' + name)
    for name in ('source', 'prefix_runner'):
        if sha(ROOT/PLAN[name+'_path']) != PLAN[name+'_sha256']:
            raise ValueError('SOURCE_PIN_MISMATCH:' + name)
    if sha(ROOT/PLAN['cache_artifact_path']) != PLAN['cache_artifact_sha256']:
        raise ValueError('ARTIFACT_PIN_MISMATCH')
    if [x['p'] for x in screen['selected']] != [63317, 68437]:
        raise ValueError('PRESCREEN_SELECTION_MISMATCH')
    if any(x['status'] != 'COMPLETE' for x in (screen, classes, sources, analysis)) or audit['status'] != 'PASS':
        raise ValueError('STAGE_NOT_COMPLETE')
    if sources['cache']['status'] != 'CACHE_HIT' or sources['cache']['build_invocations'] != 0:
        raise ValueError('CACHE_MISMATCH')
    for selected in screen['selected']:
        p = selected['p']
        cls = next(x for x in classes['cases'] if x['p'] == p)
        src = next(x for x in sources['cases'] if x['p'] == p)
        ana = next(x for x in analysis['cases'] if x['p'] == p)
        au = next(x for x in audit['cases'] if x['p'] == p)
        if (cls['status'] != 'CLASS_READY' or cls['class_size'] != 40 or
            src['status'] != 'COMPLETE' or len(src['degree13_sources']) != 40 or
            ana['status'] != 'COMPLETE' or au['status'] != 'PASS' or
            cls['curve_order'] != selected['curve_order'] or
            cls['largest_prime_factor'] != selected['largest_prime_factor']):
            raise ValueError('CASE_LINK_MISMATCH')
        if sorted(cls['priority_order']) != list(range(40)):
            raise ValueError('PRIORITY_NOT_PERMUTATION')
        for label, order in [('ascending', cls['ascending_order']),
                             ('priority', cls['priority_order'])]:
            path = ana['paths'][label]
            steps = path['steps']
            if path['source_count'] != len(steps) or [x['source'] for x in steps] != order[:len(steps)]:
                raise ValueError('ORDER_PATH_MISMATCH')
            if any(steps[i]['rank_qq'] < steps[i-1]['rank_qq'] for i in range(1, len(steps))):
                raise ValueError('NONMONOTONE_RANK')
            if path['status'] == 'RANK40_STOP' and (steps[-1]['rank_qq'] != 40 or
                any(x['rank_qq'] >= 40 for x in steps[:-1])):
                raise ValueError('STOP_MISMATCH')
            if path['status'] == 'CAP40' and (len(steps) != 40 or steps[-1]['rank_qq'] >= 40):
                raise ValueError('CAP_MISMATCH')
        if au['direct_candidates'] != ana['direct_candidate_count'] or au['hecke_candidates'] != ana['hecke_candidate_count']:
            raise ValueError('AUDIT_COUNT_MISMATCH')
    if not (HERE/'sage-runtime-info.txt').is_file():
        raise ValueError('RUNTIME_INFO_MISSING')
    print(json.dumps({'status':'PASS','cases':[x['p'] for x in screen['selected']],
                      'audit':'PASS'}))


if __name__ == '__main__':
    main()

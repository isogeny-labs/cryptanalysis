"""Check the five frozen case receipts and emit a compact panel summary."""
import hashlib
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
PLAN = json.loads((HERE / 'panel-inputs.json').read_text())


def load(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cases = []
    assert digest(REPO / 'experiments/hecke-d79-coset-q-panel-20261027/class-result.json') == PLAN['parent_class_sha256']
    assert digest(REPO / 'experiments/ecdlp-hecke-floor-rank-20261012/tools/hecke11.py') == PLAN['source_sha256']
    for item in PLAN['cases']:
        p = item['p']
        folder = HERE / f'p{p}'
        inputs = load(folder / 'inputs.json')
        post = load(folder / 'post_inputs.json')
        producer = load(folder / 'result.json')
        analysis = load(folder / 'analysis.json')
        audit = load(folder / 'audit.json')
        q_audit = load(folder / 'q-log-audit.json')
        assert producer['status'] == audit['status'].replace('PASS', 'COMPLETE')
        assert q_audit['status'] == 'PASS'
        assert producer['p'] == p == analysis['p'] == q_audit['p']
        assert producer['curve_order'] == item['ambient_order']
        assert producer['largest_prime_factor'] == item['q']
        assert producer['class_size'] == 40
        assert len(producer['degree13_sources']) == 40
        assert all(s['factor_pattern'] == item['factor_pattern'] for s in producer['degree13_sources'])
        assert producer['degree13_statuses'] == {'OUTSIDE_CLASS_TRACE': 40}
        assert post['class_receipt_sha256'] == digest(folder / 'result.json')
        assert analysis['source_receipt_sha256'] == post['class_receipt_sha256']
        assert audit['ranks'] == analysis['ranks']
        assert inputs['source_sha256'] == PLAN['source_sha256']
        assert inputs['parent_class_sha256'] == PLAN['parent_class_sha256']
        assert analysis['direct']['trials'] == analysis['hecke']['trials'] == 772240
        assert len(analysis['measurements']) == 3
        assert all(row['direct']['verified_candidates'] == len(analysis['direct']['candidates']) and
                   row['hecke']['verified_candidates'] == len(analysis['hecke']['candidates'])
                   for row in analysis['measurements'])
        counts = {arm: analysis[arm]['candidate_counts'] for arm in ('direct', 'hecke')}
        timings_ms = {arm: median(row[arm]['enumeration_wall_ns'] for row in analysis['measurements']) / 1e6
                      for arm in ('direct', 'hecke')}
        cases.append({'p': p, 'v': item['v'], 'curve_order': item['ambient_order'], 'q': item['q'],
                      'class_size': 40, 'source_count': 40, 'factor_pattern': item['factor_pattern'],
                      'direct_counts': counts['direct'], 'hecke_counts': counts['hecke'],
                      'direct_rows': len(analysis['direct']['candidates']),
                      'hecke_rows': len(analysis['hecke']['candidates']),
                      'ranks': analysis['ranks'], 'exploratory_median_enumeration_ms': timings_ms,
                      'producer_total_measured_wall_ms': producer['total_measured_wall_ns'] / 1e6,
                      'audit_status': audit['status'], 'q_log_status': q_audit['status'],
                      'receipt_sha256': {name: digest(folder / name) for name in
                                         ('inputs.json', 'result.json', 'post_inputs.json',
                                          'analysis.json', 'audit.json', 'q-log-audit.json')}})
    output = {'schema': 'hecke-d79-remaining-five-summary-v1', 'status': 'COMPLETE',
              'candidate_id': None, 'target_online_ms': None,
              'parent_class_sha256': PLAN['parent_class_sha256'],
              'source_sha256': PLAN['source_sha256'], 'cases': cases}
    (HERE / 'panel-result.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    for c in cases:
        r = c['ranks']
        print(c['p'], c['direct_rows'], c['hecke_rows'],
              r['base_direct_mod_q'], r['base_hecke_mod_q'], r['base_both_mod_q'],
              r['base_direct_qq'], r['base_hecke_qq'], r['base_both_qq'])


if __name__ == '__main__':
    main()

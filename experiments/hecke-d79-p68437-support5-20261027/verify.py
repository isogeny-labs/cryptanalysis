"""Cross-link frozen inputs, indexed producer and exhaustive Sage audit."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE/'inputs.json').read_text())
PRE = json.loads((HERE/'pre_run.json').read_text())
POST = json.loads((HERE/'post_run.json').read_text())
POST_AUDIT = json.loads((HERE/'post_audit.json').read_text())
POST_Q_AUDIT = json.loads((HERE/'post_q_audit.json').read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if sha(HERE/'inputs.json') != PRE['inputs_sha256']:
        raise ValueError('INPUTS_PIN_MISMATCH')
    if (sha(HERE/'produce.py') != PRE['producer_sha256'] or
            PRE['producer_sha256'] != POST['producer_sha256']):
        raise ValueError('PRODUCER_PIN_MISMATCH')
    if sha(HERE/'result.json') != POST['result_sha256']:
        raise ValueError('RESULT_PIN_MISMATCH')
    if sha(HERE/'audit.json') != POST_AUDIT['audit_sha256'] or sha(HERE/'audit_sage.py') != POST_AUDIT['audit_script_sha256']:
        raise ValueError('AUDIT_PIN_MISMATCH')
    if (sha(HERE/'q-log-audit.json') != POST_Q_AUDIT['q_audit_sha256'] or
            sha(HERE/'audit_q_logs.py') != POST_Q_AUDIT['q_audit_script_sha256']):
        raise ValueError('Q_AUDIT_PIN_MISMATCH')
    for name, item in PLAN['frozen'].items():
        if sha(ROOT/item['path']) != item['sha256']:
            raise ValueError('PARENT_PIN_MISMATCH:' + name)
    result = json.loads((HERE/'result.json').read_text())
    audit = json.loads((HERE/'audit.json').read_text())
    q_audit = json.loads((HERE/'q-log-audit.json').read_text())
    if result['status'] != 'COMPLETE' or audit['status'] != 'PASS':
        raise ValueError('INCOMPLETE')
    if result['baseline_rank_qq'] != 34 or result['baseline_rank_mod_q'] != 34:
        raise ValueError('BASELINE_MISMATCH')
    for arm, expected_count, expected_rank in [('direct', 196, 39), ('hecke', 87, 40)]:
        x, a = result['arms'][arm], audit['arms'][arm]
        if (x['status'] != 'COMPLETE' or a['status'] != 'PASS' or
            x['signed_patterns'] != math.comb(40,5)*16 or
            a['patterns'] != math.comb(40,5)*16 or
            x['candidate_count'] != expected_count or
            a['candidates'] != expected_count or
            x['raw_index_hits'] != 6*expected_count or
            x['rank_qq'] != expected_rank or a['rank_qq'] != expected_rank or
            x['rank_mod_q'] != 39 or a['rank_mod_q'] != 39):
            raise ValueError('ARM_MISMATCH:' + arm)
    if (result['combined_rank_qq'], result['combined_rank_mod_q']) != (40,39):
        raise ValueError('COMBINED_RESULT_MISMATCH')
    if (audit['combined_rank_qq'], audit['combined_rank_mod_q']) != (40,39):
        raise ValueError('COMBINED_AUDIT_MISMATCH')
    if (q_audit['status'] != 'PASS' or q_audit['rows_checked'] != 699 or
            q_audit['nonzero_coordinates'] != 38 or
            q_audit['combined_rank_mod_q'] != 39):
        raise ValueError('Q_LOG_AUDIT_MISMATCH')
    if not (HERE/'sage-runtime-info.txt').is_file():
        raise ValueError('RUNTIME_INFO_MISSING')
    print(json.dumps({'status':'PASS','patterns_per_arm':math.comb(40,5)*16,
                      'direct':196,'hecke':87,'combined_rank_qq':40,
                      'combined_rank_mod_q':39}))


if __name__ == '__main__':
    main()

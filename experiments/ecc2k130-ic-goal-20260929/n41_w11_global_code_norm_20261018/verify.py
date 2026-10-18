"""Audit all frozen global-norm runs against the native complete N41 census."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INPUT = ROOT / 'n41_w11_freecode_resultant_20261018/resultant_input.tsv'
NATIVE = ROOT / 'n41_w11_freecode_resultant_20261018/census_result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(suffix):
    name = '_' + suffix if suffix else ''
    proto = json.loads((HERE / ('protocol' + name + '.json')).read_text())
    receipt = json.loads((HERE / ('receipt' + name + '.json')).read_text())
    result = json.loads((HERE / ('result' + name + '.json')).read_text())
    assert proto['source_sha256']['resultant_input.tsv'] == sha(INPUT)
    assert proto['source_sha256']['sage_runtime_info.json'] == sha(HERE / 'sage_runtime_info.json')
    script = HERE / ('oracle_v1.py' if suffix == 'v1' else 'oracle.py')
    assert proto['source_sha256']['oracle.py'] == sha(script)
    if 'run.py' in proto['source_sha256']:
        assert proto['source_sha256']['run.py'] == sha(HERE / 'run.py')
    assert receipt['protocol_sha256'] == sha(HERE / ('protocol' + name + '.json'))
    assert receipt['result_sha256'] == sha(HERE / ('result' + name + '.json'))
    assert receipt['stdout_sha256'] == sha(HERE / ('stdout' + name + '.txt'))
    assert receipt['stderr_sha256'] == sha(HERE / ('stderr' + name + '.txt'))
    assert receipt['status'] == result['status'] == 'COMPLETE_GLOBAL_VALID_CODE_NORM'
    assert receipt['exit_code'] == 0 and receipt['stop_reason'] is None
    assert not receipt['monitor_degraded']
    assert receipt['sampled_peak_combined_rss_bytes'] < proto['rss_cap_bytes']
    assert result['protocol_sha256'] == receipt['protocol_sha256']
    assert result['source_vanisher_degree'] == result['valid_codes'] == 281
    assert result['target_indices'] == proto['target_indices']
    native = json.loads(NATIVE.read_text())
    for row in result['results']:
        reference = native['rows'][row['index']]
        assert row['point'] == reference['target_point']
        assert row['norm_degree'] == 1124
        assert row['code_pair_hits'] == reference['zero_pairs']
        assert row['first_code_hits'] == sorted({p for p, _ in row['code_pair_hits']})
        assert row['gcd_degree'] == len(row['first_code_hits'])
    return receipt, result


def main():
    first = json.loads((HERE / 'attempt0.json').read_text())
    assert first['status'] == 'PRODUCER_FAILURE'
    assert first['runner_sha256'] == sha(HERE / 'run_v1.py')
    assert first['protocol_sha256'] == sha(HERE / 'protocol_v1.json')
    for suffix in ('v1', 'v2', ''):
        audit(suffix)
    receipt, result = audit('')
    assert len(result['results']) == 25
    assert sum(len(row['code_pair_hits']) for row in result['results']) == 1
    assert result['results'][0]['code_pair_hits'] == [[253, 63]]
    assert all(not row['code_pair_hits'] for row in result['results'][1:])
    print(json.dumps({'status': 'PASS_GLOBAL_N41_NORM_AUDIT',
                      'target_rows': 25, 'positive_pairs': 1,
                      'ordinary_zero_gcd_rows': 24,
                      'wall_seconds': receipt['wall_ns']/1e9}, sort_keys=True))


if __name__ == '__main__':
    main()

"""Independent replay of the second-case N41 certificate and prior root control."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_n131_interleaved_block_macaulay_20261019'
spec = importlib.util.spec_from_file_location('prior_n41_replay', PRIOR / 'verify_n41.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cfg = json.loads((HERE / 'query_protocol_n41.json').read_text())
    receipt = json.loads((HERE / 'n41_t1_a4.receipt.json').read_text())
    summary = json.loads((HERE / 'query_result_n41.json').read_text())
    assert receipt['status'] == 'REJECT_CERTIFICATE' and receipt['exit_code'] == 0
    assert receipt['stop_reason'] is None and receipt['wall_seconds'] < 180
    assert receipt['sampled_peak_combined_rss_bytes'] < 4294967296
    assert receipt['stdout_sha256'] == sha(HERE / 'n41_t1_a4.stdout')
    assert receipt['stderr_sha256'] == sha(HERE / 'n41_t1_a4.stderr')
    assert receipt['input_sha256'] == cfg['inputs']['n41_t1_a4']['sha256']
    assert receipt['protocol_sha256'] == sha(HERE / 'query_protocol_n41.json')
    assert summary['status'] == 'COMPLETE_PANEL' and summary['statuses'] == ['REJECT_CERTIFICATE']
    for rec in [*cfg['inputs'].values(), *cfg['dependencies'].values()]:
        assert sha(rec['path']) == rec['sha256']
    rows = prior.equations(HERE / 'n41_t1_a4.eqs')
    count = prior.replay_certificate((HERE / 'n41_t1_a4.stdout').read_text().splitlines(), rows)
    prior_positive = json.loads((PRIOR / 'n41_t0_a252.receipt.json').read_text())
    assert prior_positive['status'] == 'UNRESOLVED_AT_DEGREE6'
    assert json.loads((PRIOR / 'verify_n41.stdout').read_text())['status'] == 'PASS_N41_INTERLEAVED_GATE'
    result = {'status':'PASS_SPLIT_N41_GATE','candidate_id':None,
              'ordinary_anchor':4,'certificate_rows':count,'xor_support':[0],
              'known_root_control':[253,63],
              'ordinary_receipt_sha256':sha(HERE / 'n41_t1_a4.receipt.json'),
              'positive_receipt_sha256':sha(PRIOR / 'n41_t0_a252.receipt.json'),
              'script_sha256':sha(__file__)}
    (HERE / 'verification_n41.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__ == '__main__':
    main()

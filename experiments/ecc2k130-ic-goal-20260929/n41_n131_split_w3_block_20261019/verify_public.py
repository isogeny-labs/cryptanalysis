"""Replay the second-case certificate and archive censored outcomes exactly."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_n131_interleaved_block_macaulay_20261019'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def equations(path):
    with Path(path).open() as stream:
        assert stream.readline().split() == ['EQS', '34', '131', '4', '2']
        rows = []
        for bit in range(131):
            line = [int(x) for x in stream.readline().split()]
            assert line[0] == bit and line[1] == len(line) - 2
            assert line[2:] == sorted(set(line[2:]))
            assert all(mask < 1 << 34 and mask.bit_count() <= 4 for mask in line[2:])
            rows.append(line[2:])
        assert not stream.read().strip()
    return rows


def replay(lines, rows):
    terminals = [line for line in lines if line.startswith('REJECT_CERTIFICATE ')]
    certs = [line for line in lines if line.startswith('CERT_ROWS')]
    assert len(terminals) == len(certs) == 1
    parts = terminals[0].split()
    pairs = [tuple(map(int, item.split(':'))) for item in certs[0].split()[1:]]
    assert len(pairs) == int(parts[4]) and len(set(pairs)) == len(pairs)
    parity = set()
    for bit, factor in pairs:
        assert 0 <= bit < 131 and 0 <= factor < 1 << 34 and factor.bit_count() <= 2
        for monomial in rows[bit]:
            value = monomial | factor
            if value in parity:
                parity.remove(value)
            else:
                parity.add(value)
    assert parity == {0}
    return {'rows_processed':int(parts[1]),'rank_at_certificate':int(parts[2]),
            'row_reductions':int(parts[3]),'certificate_rows':len(pairs),
            'xor_support':[0]}


def main():
    cfg = load(HERE / 'query_protocol_n131_public.json')
    summary = load(HERE / 'query_result_n131_public.json')
    receipt = load(HERE / 'n131_t1_a4.receipt.json')
    first = load(PRIOR / 'verification_result.json')
    prepared = load(HERE / 'prepare_result.json')
    audit = load(HERE / 'audit_result.json')
    source = load(ROOT / 'n131_w33_freecode_resultant_20261018' / 'coefficients.json')
    assert cfg['status'] == 'FROZEN_BEFORE_SPLIT_N131_PUBLIC'
    assert cfg['candidate_id'] is None and cfg['labels'] == ['n131_t1_a4']
    assert cfg['case_partition'] == {'first_left_codes':[0,1,2,3],
                                     'second_left_codes':[4,5,6,7],
                                     'right_code_range':[0,4294967295]}
    assert cfg['worker_count'] == 1 and cfg['wall_cap_seconds'] == 390
    assert cfg['rss_cap_bytes'] == 4294967296
    assert source['curve_id'] == cfg['curve_id']
    assert source['rows'][1]['name'] == 'frozen_public_raw_point'
    assert source['rows'][1]['point'] == [
        877610862732227974378969808549299291499,
        2063336771837286479337213121437715536874]
    assert prepared['status'] == 'PASS_SPLIT_PREPARATION'
    assert audit['status'] == 'PASS_SPLIT_SAGE_AUDIT'
    assert prepared['outputs'][1]['label'] == 'n131_t1_a4'
    assert prepared['outputs'][1]['target_index'] == 1
    assert prepared['outputs'][1]['anchor'] == 4
    assert audit['checks'][1]['input_sha256'] == cfg['inputs']['n131_t1_a4']['sha256']
    assert sha(HERE / 'supervise_public.py') == cfg['public_supervisor_sha256']
    assert sha(HERE / 'supervise.py') == cfg['supervisor_sha256']
    assert sha(cfg['binary']['path']) == cfg['binary']['sha256']
    for rec in [*cfg['inputs'].values(), *cfg['dependencies'].values()]:
        assert sha(rec['path']) == rec['sha256']
    assert load(HERE / 'verification_n41.json')['status'] == 'PASS_SPLIT_N41_GATE'
    assert first['status'] == 'PASS_N131_PUBLIC_BLOCK_CERTIFICATE_REPLAY'
    assert first['xor_support'] == [0]
    assert receipt['protocol_sha256'] == sha(HERE / 'query_protocol_n131_public.json')
    assert receipt['input_sha256'] == cfg['inputs']['n131_t1_a4']['sha256']
    assert receipt['binary_sha256'] == cfg['binary']['sha256']
    assert receipt['stdout_sha256'] == sha(HERE / 'n131_t1_a4.stdout')
    assert receipt['stderr_sha256'] == sha(HERE / 'n131_t1_a4.stderr')
    assert receipt['sampled_peak_combined_rss_bytes'] < 4294967296
    assert summary['block_status'] == receipt['status']
    assert summary['protocol_sha256'] == sha(HERE / 'query_protocol_n131_public.json')
    assert abs(summary['composite_target_wall_seconds'] -
               (first['parent_wall_seconds'] + receipt['wall_seconds'])) < 0.001
    lines = (HERE / 'n131_t1_a4.stdout').read_text().splitlines()
    if receipt['status'] == 'REJECT_CERTIFICATE':
        assert receipt['exit_code'] == 0 and receipt['stop_reason'] is None
        cert = replay(lines, equations(cfg['inputs']['n131_t1_a4']['path']))
        status = 'PASS_SPLIT_WIDTH3_PUBLIC_CERTIFICATE_REPLAY'
    elif receipt['status'] in ('WALL_CAP','RSS_CAP'):
        assert receipt['stop_reason'] == receipt['status']
        assert not any(line.startswith(('CERT_ROWS','REJECT_CERTIFICATE ')) for line in lines)
        cert = {}
        status = 'PASS_SPLIT_WIDTH3_PUBLIC_CENSORED_ARCHIVE'
    else:
        raise AssertionError(f'unhandled status: {receipt["status"]}')
    progress = [line.split() for line in lines if line.startswith('PROGRESS ')]
    result = {'status':status,'candidate_id':None,'curve_id':cfg['curve_id'],
              'first_half_status':first['block_status'],'second_half_status':receipt['status'],
              'first_half_left_codes':[0,1,2,3],'second_half_left_codes':[4,5,6,7],
              'prior_parent_wall_seconds':first['parent_wall_seconds'],
              'second_parent_wall_seconds':receipt['wall_seconds'],
              'composite_parent_wall_seconds':summary['composite_target_wall_seconds'],
              'sampled_peak_combined_rss_bytes':receipt['sampled_peak_combined_rss_bytes'],
              'last_progress_rows':int(progress[-1][1]) if progress else None,
              'last_progress_rank':int(progress[-1][2]) if progress else None,
              'last_progress_reductions':int(progress[-1][3]) if progress else None,
              **cert,'protocol_sha256':sha(HERE / 'query_protocol_n131_public.json'),
              'receipt_sha256':sha(HERE / 'n131_t1_a4.receipt.json'),
              'stdout_sha256':sha(HERE / 'n131_t1_a4.stdout'),
              'script_sha256':sha(__file__)}
    (HERE / 'verification_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__ == '__main__':
    main()

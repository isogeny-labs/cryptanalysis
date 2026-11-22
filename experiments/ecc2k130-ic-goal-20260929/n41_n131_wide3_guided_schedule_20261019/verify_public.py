"""Read-only verification of the bounded wide-three public query."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def main():
    cfg = load(HERE / 'query_protocol_n131_public.json')
    summary = load(HERE / 'query_result_n131_public.json')
    receipt = load(HERE / 'n131_t1_a0_w3.receipt.json')
    controls = load(HERE / 'control_verification.json')
    assert cfg['status'] == 'FROZEN_BEFORE_N131_PUBLIC_BLOCK'
    assert cfg['candidate_id'] is None and cfg['left_free_bits'] == 3
    assert cfg['curve_id'] == 'EC1N131Ckb1heb5f1998f20b'
    assert cfg['row_order'] == 'certificate_guided_factor_then_field_coordinate'
    assert cfg['labels'] == ['n131_t1_a0_w3']
    assert cfg['worker_count'] == 1 and cfg['wall_cap_seconds'] == 390
    assert cfg['rss_cap_bytes'] == 4294967296
    assert sha(HERE / 'supervise_public.py') == cfg['public_supervisor_sha256']
    assert sha(HERE / 'supervise.py') == cfg['supervisor_sha256']
    assert sha(cfg['binary']['path']) == cfg['binary']['sha256']
    assert sha(cfg['schedule']['path']) == cfg['schedule']['sha256']
    for rec in [*cfg['inputs'].values(), *cfg['dependencies'].values()]:
        assert sha(rec['path']) == rec['sha256']
    assert controls['status'] == 'PASS_GUIDED_WIDE3_N41_AND_N131_POSITIVE_GATES'
    assert controls['script_sha256'] == sha(HERE / 'verify_controls.py')
    assert controls['n41_ordinary_certificate_rows'] > 0
    assert summary['status'] == 'PARTIAL_PUBLIC_BLOCK'
    assert summary['label'] == 'n131_t1_a0_w3'
    assert summary['block_status'] == 'WALL_CAP'
    assert summary['protocol_sha256'] == sha(HERE / 'query_protocol_n131_public.json')
    assert summary['public_supervisor_sha256'] == sha(HERE / 'supervise_public.py')
    assert receipt['status'] == 'WALL_CAP' and receipt['stop_reason'] == 'WALL_CAP'
    assert receipt['exit_code'] != 0 and 390 <= receipt['wall_seconds'] <= 391
    assert 0 < receipt['sampled_peak_combined_rss_bytes'] < 4294967296
    assert receipt['protocol_sha256'] == sha(HERE / 'query_protocol_n131_public.json')
    assert receipt['supervisor_sha256'] == sha(HERE / 'supervise.py')
    assert receipt['input_sha256'] == cfg['inputs']['n131_t1_a0_w3']['sha256']
    assert receipt['binary_sha256'] == cfg['binary']['sha256']
    assert receipt['schedule_sha256'] == cfg['schedule']['sha256']
    stdout = HERE / 'n131_t1_a0_w3.stdout'
    stderr = HERE / 'n131_t1_a0_w3.stderr'
    assert receipt['stdout_sha256'] == sha(stdout)
    assert receipt['stderr_sha256'] == sha(stderr)
    lines = stdout.read_text().splitlines()
    assert not any(line.startswith(('REJECT_CERTIFICATE ', 'UNRESOLVED_AT_DEGREE6 '))
                   for line in lines)
    progress = [line for line in lines if line.startswith('PROGRESS ')]
    assert progress
    last = progress[-1].split()
    assert len(last) == 8
    _, rows, rank, reductions, largest_row, largest_trace, seconds, raw_peak = last
    rows, rank, reductions, largest_row, largest_trace, raw_peak = map(
        int, (rows, rank, reductions, largest_row, largest_trace, raw_peak))
    assert 0 < rows < 82661
    assert rank <= rows and reductions >= 0
    assert 0 < float(seconds) < receipt['wall_seconds']
    assert raw_peak <= receipt['sampled_peak_combined_rss_bytes']
    assert receipt['wall_seconds'] + cfg['charged_prior_w2_parent_wall_seconds'] < 600
    result = {'status': 'PASS_GUIDED_WIDE3_PUBLIC_CENSORED_ARCHIVE',
              'candidate_id': None, 'block_status': 'WALL_CAP',
              'last_checkpoint_rows': rows, 'last_checkpoint_rank': rank,
              'last_checkpoint_reductions': reductions,
              'last_checkpoint_largest_row': largest_row,
              'last_checkpoint_largest_trace': largest_trace,
              'parent_wall_seconds': receipt['wall_seconds'],
              'charged_prior_w2_parent_wall_seconds': cfg['charged_prior_w2_parent_wall_seconds'],
              'composite_parent_wall_seconds': receipt['wall_seconds'] +
                  cfg['charged_prior_w2_parent_wall_seconds'],
              'sampled_peak_combined_rss_bytes': receipt[
                  'sampled_peak_combined_rss_bytes'],
              'protocol_sha256': sha(HERE / 'query_protocol_n131_public.json'),
              'receipt_sha256': sha(HERE / 'n131_t1_a0_w3.receipt.json'),
              'stdout_sha256': sha(stdout), 'script_sha256': sha(__file__)}
    (HERE / 'verification_result.json').write_text(
        json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()

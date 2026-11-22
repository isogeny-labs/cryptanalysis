"""Audit a frozen interval continuation and the earlier public block prefix."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def loaded(label):
    protocol_path = HERE / f'protocol_{label}.json'
    receipt = json.loads((HERE / f'receipt_{label}.json').read_text())
    protocol = json.loads(protocol_path.read_text())
    assert receipt['protocol_sha256'] == sha(protocol_path)
    assert receipt['stdout_sha256'] == sha(HERE / f'stdout_{label}.txt')
    assert receipt['stderr_sha256'] == sha(HERE / f'stderr_{label}.txt')
    assert receipt['candidate_id'] is None and protocol['candidate_id'] is None
    assert protocol['worker_count'] == 1 and protocol['wall_cap_seconds'] == 600
    assert protocol['rss_cap_bytes'] == 4 * 1024**3
    assert not receipt['monitor_degraded']
    assert receipt['sampled_peak_combined_rss_bytes'] < protocol['rss_cap_bytes']
    return protocol, receipt


def parsed_public_blocks(receipt):
    blocks = [line.split() for line in receipt['block_lines'] if line.startswith('BLOCK 1 ')]
    assert receipt['source_line'] and len(blocks) == len(receipt['block_lines'])
    for b in blocks:
        index = int(b[2])
        assert int(b[3]) == (973 if index == 32 else 4096)
        assert int(b[4]) == 4 * int(b[3])
        assert b[5:7] == ['0', '0']
    return blocks


def main():
    prior_cfg, prior = loaded('132045_b4096')
    cfg, receipt = loaded('public_remainder')
    files = {
        'block_norm_resume.cpp': HERE / 'block_norm_resume.cpp',
        'block_norm_resume': HERE / 'block_norm_resume',
        'run_resume.py': HERE / 'run_resume.py',
        'field.hpp': ROOT / 'n131_w20_paired_raw_quotient_20261016/field.hpp',
        'support_w20.tsv': ROOT / 'n131_w20_sevenpair_gate_20261010/support_w20.tsv',
        'coefficients.tsv': HERE / 'coefficients.tsv',
        'sage_runtime_info.json': HERE / 'sage_runtime_info.json',
        'GF2EX.h': Path('/opt/homebrew/opt/ntl/include/NTL/GF2EX.h'),
        'GF2E.h': Path('/opt/homebrew/opt/ntl/include/NTL/GF2E.h'),
        'libntl.dylib': Path('/opt/homebrew/opt/ntl/lib/libntl.dylib'),
        'libgmp.dylib': Path('/opt/homebrew/opt/gmp/lib/libgmp.dylib'),
    }
    assert cfg['source_sha256'] == {name: sha(path) for name, path in files.items()}
    assert cfg['completed_prefix_receipt_sha256'] == sha(HERE / 'receipt_132045_b4096.json')
    assert cfg['curve_id'] == prior_cfg['curve_id']
    assert cfg['selected_count'] == prior_cfg['selected_count'] == 132045
    assert cfg['block_size'] == prior_cfg['block_size'] == 4096
    assert cfg['target_index'] == 1 and (cfg['begin_block'], cfg['end_block']) == (20, 33)
    assert cfg['command'] == [str(HERE / 'block_norm_resume'),
                              str(ROOT / 'n131_w20_sevenpair_gate_20261010/support_w20.tsv'),
                              str(HERE / 'coefficients.tsv'), '132045', '4096', '1', '20', '33']
    assert prior['status'] == 'BOUNDED_UNKNOWN' and prior['stop_reason'] == 'WALL_CAP'
    assert prior['exit_code'] == -15 and not prior['done_line']
    assert len(prior['source_line']) == len(receipt['source_line']) == 1
    assert prior['source_line'][0].split()[1:3] == ['132045', '132045']
    assert receipt['source_line'][0].split()[1:3] == ['132045', '132045']
    prior_blocks = parsed_public_blocks({'block_lines': [line for line in prior['block_lines']
                                                           if line.startswith('BLOCK 1 ')],
                                         'source_line': prior['source_line']})
    remaining_blocks = parsed_public_blocks(receipt)
    assert [int(b[2]) for b in prior_blocks] == list(range(20))
    observed_indices = [int(b[2]) for b in remaining_blocks]
    assert observed_indices == list(range(20, 20 + len(remaining_blocks)))
    assert len(remaining_blocks) <= 13
    covered = sum(int(b[3]) for b in prior_blocks + remaining_blocks)
    if receipt['status'] == 'COMPLETE_NATIVE_NTL_PUBLIC_REMAINDER_BLOCK_NORM':
        assert receipt['exit_code'] == 0 and receipt['stop_reason'] is None
        assert len(remaining_blocks) == 13 and observed_indices[-1] == 32
        assert len(receipt['row_lines']) == len(receipt['done_line']) == 1
        assert receipt['row_lines'][0].split()[:5] == ['ROW', '1', '20', '33', '0']
        assert covered == 132045
        result = 'EMPTY_EXACT_PUBLIC_TWO_PAIR_RESIDUAL'
    else:
        assert receipt['status'] == 'BOUNDED_UNKNOWN' and receipt['stop_reason'] in ('WALL_CAP', 'RSS_CAP')
        assert receipt['exit_code'] == -15 and not receipt['row_lines'] and not receipt['done_line']
        assert covered < 132045
        result = 'BOUNDED_UNKNOWN'
    print(json.dumps({'audit': 'PASS_PUBLIC_REMAINDER', 'classification': result,
                      'first_run_blocks': len(prior_blocks),
                      'continuation_blocks': len(remaining_blocks),
                      'unique_second_codes_covered': covered,
                      'source_second_codes': 132045}, sort_keys=True))


if __name__ == '__main__':
    main()

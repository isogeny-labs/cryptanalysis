"""Audit exact coverage, root preservation, caps and source hashes."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
NORM = ROOT / 'n131_w20_ntl_global_norm_20261018'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(public):
    return {
        ('block_norm_public.cpp' if public else 'block_norm.cpp'): HERE / ('block_norm_public.cpp' if public else 'block_norm.cpp'),
        ('block_norm_public' if public else 'block_norm'): HERE / ('block_norm_public' if public else 'block_norm'),
        ('run_public.py' if public else 'run.py'): HERE / ('run_public.py' if public else 'run.py'),
        'field.hpp': ROOT / 'n131_w20_paired_raw_quotient_20261016/field.hpp',
        'support_w20.tsv': ROOT / 'n131_w20_sevenpair_gate_20261010/support_w20.tsv',
        'coefficients.tsv': HERE / 'coefficients.tsv',
        'sage_runtime_info.json': HERE / 'sage_runtime_info.json',
        'GF2EX.h': Path('/opt/homebrew/opt/ntl/include/NTL/GF2EX.h'),
        'GF2E.h': Path('/opt/homebrew/opt/ntl/include/NTL/GF2E.h'),
        'libntl.dylib': Path('/opt/homebrew/opt/ntl/lib/libntl.dylib'),
        'libgmp.dylib': Path('/opt/homebrew/opt/gmp/lib/libgmp.dylib'),
    }


def check(label, public=False):
    p = HERE / f'protocol_{label}.json'
    cfg = json.loads(p.read_text())
    receipt = json.loads((HERE / f'receipt_{label}.json').read_text())
    assert cfg['source_sha256'] == {name: sha(path) for name, path in files(public).items()}
    assert cfg['worker_count'] == 1 and cfg['candidate_id'] is None
    assert receipt['protocol_sha256'] == sha(p)
    assert receipt['stdout_sha256'] == sha(HERE / f'stdout_{label}.txt')
    assert receipt['stderr_sha256'] == sha(HERE / f'stderr_{label}.txt')
    assert receipt['sampled_peak_combined_rss_bytes'] < cfg['rss_cap_bytes'] == 4*1024**3
    assert not receipt['monitor_degraded']
    assert receipt['source_line'] and receipt['source_line'][0].split()[2] == '132045'
    blocks = [line.split() for line in receipt['block_lines']]
    for target in set(int(row[1]) for row in blocks):
        indexed = [row for row in blocks if int(row[1]) == target]
        assert [int(row[2]) for row in indexed] == list(range(len(indexed)))
        assert all(int(row[3]) == cfg['block_size'] or
                   (int(row[2]) == len(indexed)-1 and int(row[3]) == cfg['selected_count'] % cfg['block_size'])
                   for row in indexed)
        assert sum(int(row[3]) for row in indexed) <= cfg['selected_count']
    return cfg, receipt, blocks


def main():
    small_cfg, small, small_blocks = check('4096_b1024')
    full_cfg, full, full_blocks = check('132045_b4096')
    public_cfg, public, public_blocks = check('public_full', True)
    assert small['status'] == 'COMPLETE_NATIVE_NTL_BLOCK_NORM'
    assert small['row_lines'][0].split()[:5] == ['ROW','0','4','1','3,16722']
    assert small['row_lines'][1].split()[:4] == ['ROW','1','4','0']
    assert small_cfg['comparison_sha256']['independent_direct_4096_receipt'] == sha(NORM/'direct_receipt_4096.json')
    assert full['status'] == public['status'] == 'BOUNDED_UNKNOWN'
    assert full['stop_reason'] == public['stop_reason'] == 'WALL_CAP'
    assert full['exit_code'] == public['exit_code'] == -15
    assert full['row_lines'] == ['ROW 0 33 1 3,16722 0.472355 13.101 396.662 410.315 258621440']
    pos = [row for row in full_blocks if row[1] == '0']
    first_public = [row for row in full_blocks if row[1] == '1']
    only_public = [row for row in public_blocks if row[1] == '1']
    assert len(pos) == 33 and sum(int(row[3]) for row in pos) == 132045
    assert sum(int(row[6]) for row in pos) == 1
    assert pos[1][5:7] == ['1','1']
    assert len(first_public) == 20 and all(row[5:7] == ['0','0'] for row in first_public)
    assert len(only_public) == 6 and all(row[5:7] == ['0','0'] for row in only_public)
    assert not public['row_lines'] and not public['done_line']
    assert "error:" not in (HERE/'lean_check.log').read_text()
    assert "does not depend on any axioms" in (HERE/'lean_check.log').read_text()
    print(json.dumps({'status':'PASS_BLOCK_NORM_AUDIT',
                      'positive_codes_covered':132045,'positive_pairs':1,
                      'public_blocks_first_attempt':len(first_public),
                      'public_blocks_second_attempt':len(only_public),
                      'public_full_status':public['status']},sort_keys=True))


if __name__ == '__main__':
    main()

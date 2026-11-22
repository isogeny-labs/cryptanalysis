"""Read-only audit of frozen native norm and independent direct scans."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PILOT = ROOT / 'n131_w20_global_norm_pilot_20261018'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files():
    return {
        'native_norm.cpp': HERE / 'native_norm.cpp',
        'native_norm': HERE / 'native_norm',
        'run.py': HERE / 'run.py',
        'field.hpp': ROOT / 'n131_w20_paired_raw_quotient_20261016/field.hpp',
        'support_w20.tsv': ROOT / 'n131_w20_sevenpair_gate_20261010/support_w20.tsv',
        'coefficients.tsv': HERE / 'coefficients.tsv',
        'sage_runtime_info.json': HERE / 'sage_runtime_info.json',
        'GF2EX.h': Path('/opt/homebrew/opt/ntl/include/NTL/GF2EX.h'),
        'GF2E.h': Path('/opt/homebrew/opt/ntl/include/NTL/GF2E.h'),
        'libntl.dylib': Path('/opt/homebrew/opt/ntl/lib/libntl.dylib'),
        'libgmp.dylib': Path('/opt/homebrew/opt/gmp/lib/libgmp.dylib'),
    }


def check(label):
    p = HERE / f'protocol_{label}.json'
    cfg = json.loads(p.read_text())
    receipt = json.loads((HERE / f'receipt_{label}.json').read_text())
    assert cfg['source_sha256'] == {name: sha(path) for name, path in source_files().items()}
    assert cfg['candidate_id'] is None and cfg['worker_count'] == 1
    assert cfg['rss_cap_bytes'] == 4 * 1024**3
    assert receipt['protocol_sha256'] == sha(p)
    assert receipt['stdout_sha256'] == sha(HERE / f'stdout_{label}.txt')
    assert receipt['stderr_sha256'] == sha(HERE / f'stderr_{label}.txt')
    assert receipt['source_line'] and receipt['source_line'][0].split()[2] == '132045'
    assert receipt['sampled_peak_combined_rss_bytes'] <= cfg['rss_cap_bytes']
    assert not receipt['monitor_degraded']
    return cfg, receipt


def main():
    cfg256, r256 = check('256')
    cfg4096, r4096 = check('4096')
    cfgfull, rfull = check('132045')
    for cfg, receipt in ((cfg256, r256), (cfg4096, r4096)):
        assert receipt['status'] == 'COMPLETE_NATIVE_NTL_GLOBAL_NORM'
        assert receipt['exit_code'] == 0 and receipt['stop_reason'] is None
        assert receipt['row_lines'][0].split()[:5] == ['ROW', '0', str(4*cfg['selected_count']), '1', '1']
        assert receipt['row_lines'][0].split()[5] == '3,16722'
        assert receipt['row_lines'][1].split()[:5] == ['ROW', '1', str(4*cfg['selected_count']), '0', '0']
    assert rfull['status'] == 'BOUNDED_UNKNOWN'
    assert rfull['stop_reason'] == 'WALL_CAP' and rfull['exit_code'] == -15
    assert not rfull['row_lines'] and not rfull['done_line']
    direct_cfg = json.loads((HERE / 'direct_protocol_4096.json').read_text())
    direct = json.loads((HERE / 'direct_receipt_4096.json').read_text())
    assert direct['status'] == 'COMPLETE_INDEPENDENT_DIRECT_4096'
    assert direct['protocol_sha256'] == sha(HERE / 'direct_protocol_4096.json')
    assert direct['stdout_sha256'] == sha(HERE / 'direct_stdout_4096.txt')
    assert direct['stderr_sha256'] == sha(HERE / 'direct_stderr_4096.txt')
    assert direct['lines'] == ['ROW 0 1 3,16722', 'ROW 1 0']
    assert direct['exit_code'] == 0 and not direct['monitor_degraded']
    assert direct_cfg['source_sha256']['direct_audit'] == sha(PILOT / 'direct_audit')
    print(json.dumps({'status': 'PASS_NATIVE_NTL_NORM_AUDIT',
                      'completed_counts': [256, 4096],
                      'independent_complete_pair_scan': 4096,
                      'full_source': rfull['status']}, sort_keys=True))


if __name__ == '__main__':
    main()

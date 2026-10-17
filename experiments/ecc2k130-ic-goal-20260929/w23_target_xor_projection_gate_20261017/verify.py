"""Read-only terminal check of the public code-XOR projection screen."""
import hashlib
import json
from pathlib import Path

import code_only
import peel_cert
import screen

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = load('protocol.json')
    first = load('result.json')
    code_protocol = load('code_protocol.json')
    code = load('code_result.json')
    peel_protocol = load('peel_protocol.json')
    peel = load('peel_result.json')
    failure = load('leaf_attempt1.json')
    assert protocol['status'] == 'FROZEN_N41_N131_PUBLIC_XOR_CODE_PROJECTION'
    assert protocol['source_sha256'] == {k: sha(v) for k, v in screen.sources().items()}
    assert first['status'] == 'PASS_N41_N131_XOR_CODE_PROJECTION_SCREEN'
    assert first['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert code_protocol['source_sha256'] == code_only.sources()
    assert code['status'] == 'PASS_CODE_BOUNDARY_XOR_ELIMINATION'
    assert code['protocol_sha256'] == sha(HERE / 'code_protocol.json')
    assert peel_protocol['source_sha256'] == {k: sha(v) for k, v in peel_cert.inputs().items()}
    assert peel['status'] == 'PASS_ORDERED_XOR_PEEL_AUDIT'
    assert peel['protocol_sha256'] == sha(HERE / 'peel_protocol.json')
    expected = {'n41': (3689, 42, 1319, 64110592),
                'n131': (38657, 132, 11370, 366739456)}
    for label, (original, wires, residual, rss) in expected.items():
        first_row = next(x for x in first['rows'] if x['label'] == label)
        code_row = next(x for x in code['rows'] if x['label'] == label)
        peel_row = next(x for x in peel['rows'] if x['label'] == label)
        assert first_row['original_xor_rows'] == original
        assert first_row['residual_xor_rows'] == residual
        assert first_row['code_wires'] == wires
        assert first_row['code_only_residual_rows'] == 0
        assert first_row['peak_self_rss_raw'] == rss
        assert first_row['total_ns'] < 180*10**9
        source_xcnf = (screen.N41 / 'public.xcnf' if label == 'n41'
                       else screen.N131 / 'ordinary.xcnf')
        assert first_row['rebuilt_sha256'] == sha(source_xcnf)
        assert code_row['code_only_xor_rows'] == code_row['contradictions'] == 0
        assert code_row['private_pivots'] == original
        assert code_row['row_additions'] == 0
        assert code_row['elapsed_ns'] < 180*10**9
        assert peel_row['ordered_exclusive_pivots'] == original
        assert peel_row['unpeeled_rows'] == 0
        assert all(row['peak_self_rss_raw'] < 4*1024**3
                   for row in (first_row, code_row, peel_row))
    # Bind the N131 formula to its archived query receipt without modifying it.
    n131_query = json.loads((screen.N131 / 'result.json').read_text())
    assert first['rows'][1]['rebuilt_sha256'] == n131_query['formula_sha256']
    assert failure['status'] == 'PRODUCER_FAILURE' and failure['exit_code'] == 1
    assert failure['source_sha256'] == sha(HERE / 'leaf_cert.py')
    assert failure['protocol_sha256'] == sha(HERE / 'leaf_protocol.json')
    assert failure['stderr_sha256'] == sha(HERE / 'leaf_run.stderr')
    assert failure['stdout_sha256'] == sha(HERE / 'leaf_run.stdout')
    assert 'ModuleNotFoundError: No module named' in (HERE / 'run.stderr').read_text()
    assert 'AssertionError' in (HERE / 'leaf_run.stderr').read_text()
    for name in ('run_v2.stderr', 'code_run.stderr', 'peel_run.stderr', 'lean.stderr'):
        assert not (HERE / name).read_bytes()
    assert load('sage_runtime_info.json')['status'] == 'verified'
    assert (HERE / 'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.34.1'
    lean = (HERE / 'PeelExtension.lean').read_text()
    assert all(marker not in lean for marker in ('sorry', 'admit', 'sorryAx', 'native_decide'))
    assert "'PeelExtension.target_xor_any_rhs_satisfiable' depends on axioms: [propext]" \
        in (HERE / 'lean.stdout').read_text()
    print('PASS_W23_TARGET_XOR_PROJECTION_VERIFY', expected['n41'][0], expected['n131'][0])


if __name__ == '__main__':
    main()

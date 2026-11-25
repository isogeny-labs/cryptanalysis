"""Independent polynomial-gcd check of the nearby same-class control."""
import json
import runpy
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'control_result': HERE / 'control_result.json',
    'fast_gate_source': ROOT / 'experiments/hecke-432-j1728-fast-local-root-gate-20261026/run.py',
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'coordinate_map': ROOT / 'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json',
    'resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
}


def main():
    path = HERE / 'control_audit_protocol.json'
    protocol = json.loads(path.read_text())
    for name, source in INPUTS.items():
        assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    registered = json.loads(INPUTS['control_result'].read_text())['row']
    p = int(registered['prime'])
    field = json.loads(INPUTS['factor_certificate'].read_text())
    coord = json.loads(INPUTS['coordinate_map'].read_text())['source_j']
    resolvent = json.loads(INPUTS['resolvent'].read_text())['terms']
    gate = runpy.run_path(str(INPUTS['fast_gate_source']))
    roots, sources, undefined = gate['source_points'](p, field, coord)
    expected = sorted([int(v) for v in item['C_point']] for item in registered['rows'])
    assert sources == expected and not undefined
    xroots = 0
    pairs = 0
    multiplications = 0
    for row in registered['rows']:
        x, y = map(int, row['C_point'])
        counted = gate['fiber_gate'](p, x, y, resolvent)
        assert counted['rational_x_E_roots'] == row['rational_x_E_roots']
        assert counted['rational_CE_pairs'] == len(row['pairs'])
        xroots += counted['rational_x_E_roots']
        pairs += counted['rational_CE_pairs']
        multiplications += counted['arithmetic_counts']['polynomial_multiplications']
    assert len(roots) == len(sources) == 18 and xroots == 72 and pairs == 0
    out = {'status': 'PASS_INDEPENDENT_SAME_CLASS_CONTROL_GCD_AUDIT',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'prime': str(p), 'source_points': len(sources),
           'rational_x_E_roots': xroots, 'rational_CE_pairs': pairs,
           'polynomial_multiplications': multiplications}
    (HERE / 'control_audit_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()

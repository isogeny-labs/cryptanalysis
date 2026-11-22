#!/usr/bin/env python3
"""Untimed native positive controls, using explicitly synthetic unit costs."""
import argparse
import json
import subprocess
from pathlib import Path
from counterfactual_checks import check, equal
CELLS = ('mitm-counterfactual-ip', 'mitm-setup-observed', 'mitm-setup-reserved', 'mitm-setup-gathered')

P = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--binary', type=Path, required=True)
a = p.parse_args()
D = P/'setup-cell-smoke-001'
D.mkdir(exist_ok=False)
rows = []
for index, inst in enumerate(json.loads((P/'instances.json').read_text())):
    units = {k: 1.0 for k in ['ns_per_add', 'ns_per_double', 'ns_per_lookup', 'ns_per_row_op']}
    units.update({k: None for k in ['ns_per_sqrt', 'ns_per_as_solve', 'ns_per_s4_pair', 'ns_per_word_xor', 'ns_per_legendre', 'ns_per_inversion', 'ns_per_frobenius', 'ns_per_canon']})
    units['pinned_units'] = []
    cal = D/f'units-{index}.json'
    cal.write_text(json.dumps(dict(curve_id=inst['curve_id'], calibration=units))+'\n')
    first = None
    for cell in CELLS:
        label = f'{index}-{cell}'
        argv = [str(a.binary.resolve()), str(P/'instances.json'), str(index), cell, '0', str(cal)]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=20)
        (D/(label+'.stdout')).write_text(result.stdout)
        (D/(label+'.stderr')).write_text(result.stderr)
        rows.append(dict(label=label, argv=argv, exit_code=result.returncode))
        (D/'commands.json').write_text(json.dumps(rows, indent=2)+'\n')
        assert result.returncode == 0, label
        raw = json.loads(result.stdout)
        assert raw['mode'] == cell
        check(dict(raw, mode='mitm-counterfactual-ip'), 'ip')
        assert raw['curve_id'] == inst['curve_id'] and raw['calibration'] == units
        if first is not None:
            equal(first, raw)
            left = first['report']['Ok']['decomposition']['setup']['native']
            right = raw['report']['Ok']['decomposition']['setup']['native']
            assert {k:v for k,v in left.items() if not k.endswith('_ns')} == {k:v for k,v in right.items() if not k.endswith('_ns')}
        else:
            first = raw
(D/'summary.json').write_text(json.dumps(dict(status='pass', answers=20, synthetic_units=True, native_clock_evidence=False), indent=2)+'\n')
print('20 setup-state pipeline controls passed; no timing inference')

"""Freeze the five-code, five-output S3-middle solver control."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
protocol=json.loads((HERE/'fixed_build_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


assert protocol['script_sha256']==sha(__file__)
for source,digest in protocol['sources'].items():
    assert sha(source)==digest,source
assert not (HERE/'fixed_formula.xcnf').exists()
fixture=json.loads(Path(protocol['fixture']).read_text())
wires=json.loads((HERE/'n41_input_wires.json').read_text())
base=(HERE/'n41_formula.xcnf').read_text()
header,body=base.split('\n',1)
parts=header.split()
assert parts[:2]==['p','cnf'] and len(parts)==4
units=[]
codes=[]
for slot,row in enumerate(fixture['pairs']):
    mask=row['masks'][0]
    code=sum(((mask>>bit)&1)<<index for index,bit in enumerate(wires['source_bits']))
    codes.append(code)
    for index,wire in enumerate(wires['mask'][slot]):
        units.append(f'{wire if code>>index&1 else -wire} 0')
    output=row['output_reciprocal']
    for index,wire in enumerate(wires['out'][slot]):
        units.append(f'{wire if output>>index&1 else -wire} 0')
assert len(units)==5*(10+41)
path=HERE/'fixed_formula.xcnf'
path.write_text(f'p cnf {parts[2]} {int(parts[3])+len(units)}\n'
                +'\n'.join(units)+'\n'+body)
result={'status':'PASS_N41_FUNCTIONAL_S3_FIXED_CODES_OUTPUTS_CONTROL_BUILD',
        'candidate_id':None,'curve_id':protocol['curve_id'],
        'fixed_codes':codes,'fixed_outputs':[row['output_reciprocal'] for row in fixture['pairs']],
        'additional_unit_clauses':len(units),
        'formula_bytes':path.stat().st_size,'formula_sha256':sha(path),
        'base_formula_sha256':sha(HERE/'n41_formula.xcnf'),
        'protocol_sha256':sha(HERE/'fixed_build_protocol.json')}
(HERE/'fixed_build_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))

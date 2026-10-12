"""Check every XCNF row against independently built N131 source points."""
import hashlib,json,time
from pathlib import Path
from fourpair import build,check_assignment,field_config
h=Path(__file__).resolve().parent
p=json.loads((h/'n131_check_protocol.json').read_text())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
paths={'script':h/'check_n131_control.py','builder':h/'fourpair.py',
       'fixture':h/'n131_control_fixture.json',
       'support':h.parent/'n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv'}
assert {k:sha(v) for k,v in paths.items()}==p['sha256']
assert not (h/'n131_control_check.json').exists()
f=json.loads(paths['fixture'].read_text())
field,_,rotations=field_config('n131')
start=time.monotonic_ns();c,wires,meta=build('n131',int(f['target_reciprocal']))
built=time.monotonic_ns();check=check_assignment(c,wires,f,field,rotations)
checked=time.monotonic_ns()
path=h/'n131_control.xcnf';assert not path.exists();c.write(path)
end=time.monotonic_ns()
check.update({'curve_id':f['curve_id'],'source_fixture_sha256':sha(paths['fixture']),
              'formula_sha256':sha(path),'formula_bytes':path.stat().st_size,
              'build_ns':built-start,'check_ns':checked-built,'write_ns':end-checked,
              'metadata':meta,'protocol_sha256':sha(h/'n131_check_protocol.json')})
(h/'n131_control_check.json').write_text(json.dumps(check,sort_keys=True,indent=2)+'\n')
print(check['status'],check['variables'],flush=True)

from pathlib import Path
import hashlib
import json
import re
import subprocess

BASE = Path(__file__).resolve().parent
NATIVE = BASE / 'native-40828001123'
ROOT = NATIVE / 'artifact'
HEAD = '42fb95ed95a6bbf06ea38422b32cc3e22988b08d'
NATIVE_SHA = '2e5184f9febb3bb0cb5e52a782708bfdf3c56319'
REPO = '/home/ec2-user/cryptanalysis-known-label-native-types-20261029'
SOURCE = 'docs/known-label-next-leads-20261028/Algebra.lean'
gate_hash = 'f84a1c1307e10453d558331ac10e7923b47ef07a3b4663eb245ec141b3692789'
records = []
for path in sorted(ROOT.glob('*/record.json')):
    record = json.loads(path.read_text())
    for name, expected in record['files'].items():
        assert '/' not in name and name not in ['.', '..']
        assert hashlib.sha256((path.parent / name).read_bytes()).hexdigest() == expected
    if 'argv' in record:
        assert record['returncode'] == 0 and record['timed_out'] is False
        assert record['github_sha'] == NATIVE_SHA and record['gate_sha256'] == gate_hash
    records.append((path, record))
module_path, module = next((p, d) for p, d in records if p.parent.name.startswith('module-inputs-'))
object_path, obj = next((p, d) for p, d in records if p.parent.name.startswith('compiled-object-'))
types_path, types = next((p, d) for p, d in records if p.parent.name.startswith('type-output-'))
wrapper_path, wrapper = next((p, d) for p, d in records if p.parent.name.startswith('type-wrapper-'))
assert module['source'] == SOURCE
assert module['gate_sha256'] == gate_hash and obj['gate_sha256'] == gate_hash
assert module['auditor_sha256'] == obj['auditor_sha256']
assert module['source_sha256'] == obj['source_sha256']
names = {'KnownLabelLeads.' + n for n in ['triangle_identity', 'signed_second_moment', 'signed_third_moment', 'positive_pair_product']}
assert set(types['names']) == set(wrapper['names']) == names
stdout = (types_path.parent / 'stdout.txt').read_bytes()
found = re.findall(rb'^@?([A-Za-z_][A-Za-z0-9_.]*?)(?:\.\{[^}\n]+\})?\s*:\s*\S', stdout, re.M)
assert len(found) == 4 and {n.decode() for n in found} == names
selected = [(p, d) for p, d in records if 'argv' in d and any(SOURCE in a or 'CollectedTypes.lean' in a or str(module_path.parent.name) + '/Audit' in a for a in d['argv'])]
assert len(selected) == 3, [(str(p), d['argv']) for p, d in selected]
compile_p, compile_d = next((p,d) for p,d in selected if d['argv'][0] == 'lake')
audit_p, audit_d = next((p,d) for p,d in selected if '--run' in d['argv'])
type_p, type_d = next((p,d) for p,d in selected if any('CollectedTypes.lean' in x for x in d['argv']))
assert (type_p.parent / 'stdout.bin').read_bytes() == stdout
compile_out = (compile_p.parent / 'stdout.bin').read_text()
audit_out = (audit_p.parent / 'stdout.bin').read_text()
assert len(re.findall(r'^\x27KnownLabelLeads\.', compile_out, re.M)) == 4
assert 'audited 4 theorems; 0 failing, 0 trusted' in audit_out
assert {n for n in re.findall(r'^ok    (\S+)  \[', audit_out, re.M)} == names
files = {SOURCE: module_path.parent/'Source.lean', 'tools/lean/AuditHeckeAxioms.lean': module_path.parent/'AuditHeckeAxioms.lean'}
for n in ['lean-toolchain', 'lakefile.toml', 'lake-manifest.json']:
    files['experiments/hecke-432-formal-ci-20261025/' + n] = module_path.parent/n
raw = subprocess.run(['git','cat-file','--batch'], cwd=REPO, input=''.join(HEAD+':'+n+'\n' for n in files).encode(),capture_output=True,check=True,timeout=90).stdout
pos = 0
for name, retained in files.items():
    end = raw.index(b'\n',pos);header=raw[pos:end].split();assert len(header)==3 and header[1]==b'blob'
    size=int(header[2]);pos=end+1;content=raw[pos:pos+size];pos+=size+1
    assert content == retained.read_bytes(), name
result = {'schema':'known-label-native-evidence-binding/v1','pr_head':HEAD,'native_checkout':NATIVE_SHA,
          'run':40828001123,'attempt':1,'job':123295387820,'artifact':12877004890,
          'artifact_sha256':hashlib.sha256((NATIVE/'evidence.zip').read_bytes()).hexdigest(),
          'retained_records_verified':len(records),'successful_command_records':sum('argv' in d for p,d in records),
          'known_label_commands':[{'record':str(p.relative_to(ROOT)), 'argv':d['argv'], 'returncode':d['returncode']} for p,d in selected],
          'source_and_pin_files_matched_to_head':list(files),'source_sha256':module['source_sha256'],
          'gate_sha256':gate_hash,'auditor_sha256':module['auditor_sha256'],'compiled_object_digests':obj['sha256'],
          'theorem_names':sorted(names),'type_stdout_sha256':hashlib.sha256(stdout).hexdigest(),
          'native_status':'passed under declared Lean/Lake/runner trust','semantic_fidelity':'not_reviewed',
          'limitations':['Compiled object bytes are not retained; hashes and successful phase-boundary checks are recorded.','No independent kernel or dependency binary rechecker.','No graph/group/probability, implementation or historical execution bridge supplied.']}
(NATIVE/'binding.json').write_text(json.dumps(result,indent=2)+'\n')
(NATIVE/'elaborated-types.txt').write_bytes(stdout)
(NATIVE/'compile-axioms.txt').write_text(compile_out)
(NATIVE/'module-audit.txt').write_text(audit_out)
print(json.dumps(result,indent=2))

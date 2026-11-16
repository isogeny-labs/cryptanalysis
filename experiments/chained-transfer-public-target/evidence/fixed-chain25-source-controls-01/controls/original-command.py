"""Actual compiled I/O-only auditor controls on whole genuine22 data."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';build=Path('/workspace/scratch/ct85-ci25-auditor-build-01');out=build.with_name('ct85-ci25-geometry-auditor-controls-01');out.mkdir()
assert(build/'geometry-auditor-compile.exit').read_text().strip()=='0'
subprocess.run(['python3',str(s/'ci_fixed_chain/capture_auditor.py'),str(build),'compiled','geometry-auditor','audit-three-fixed-geometries'],cwd=r,check=True)
exe=Path((build/'geometry-auditor-actual-path.txt').read_text().strip())
for source,name in [(s/'paired-fourth-preflight/expected-native-01.json.xz','old16.json'),(s/'fixed-jacobian-chain-01/expected-native-01.json.xz','expected13.json'),(s/'evidence/fixed-chain-geometry-native-01/whole-positive-native.txt.xz','whole-native.txt')]:
 (out/name).write_bytes(lzma.decompress(source.read_bytes()))
shutil.copyfile(__file__,out/'original-command.py')
def run(name,wanted,inputpath,destination):
 q=subprocess.run(['timeout','120',str(exe),'--compare',str(out/'old16.json'),str(out/'expected13.json'),str(inputpath),str(destination)],cwd=r,capture_output=True)
 (out/(name+'.txt')).write_bytes(q.stdout+q.stderr);(out/(name+'.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==wanted;print(name,q.returncode,flush=True)
run('whole-thirteen',0,out/'whole-native.txt',out/'whole-thirteen-accepted.json')
assert json.loads((out/'whole-thirteen-accepted.json').read_text())==json.loads((out/'expected13.json').read_text())
text=(out/'whole-native.txt').read_text()
for tag in ['N4_CHAIN_OLD_LITERAL_PARITY','N4_CHAIN_FIXED_GEOMETRY']:
 path=out/(tag+'-entire-actual-records-omitted.txt');path.write_text(''.join(line for line in text.splitlines(keepends=True)if tag+' 'not in line));destination=out/(tag+'-must-not-accept.json');run(tag+'-omission',101,path,destination);assert not destination.exists()
subprocess.run(['python3',str(s/'ci_fixed_chain/capture_auditor.py'),str(build),'runtime','geometry-auditor','audit-three-fixed-geometries'],cwd=r,check=True)
(out/'observation.json').write_text(json.dumps(dict(original_genuine_fixture='genuine22/de10d7',actual_compile=0,whole13_record_positive=0,old_whole_constructor_data_compared=True,actual_whole_old_parity_omission=101,actual_all_three_whole_geometry_record_omission=101,no_accepted_negative_outputs=True,whole_compiled_runtime_auditor_bytes_equal=True,scope='New I/O-only replay auditor controls, no mathematical test rerun or new CI pass/price/execution promotion.'),indent=2)+'\n')

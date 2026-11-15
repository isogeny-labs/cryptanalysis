"""Cargo-reported executable custody and byte copying only."""
from pathlib import Path
import hashlib,json,re,shutil,sys
out,cache=map(Path,sys.argv[1:]);compiled=(out/'compile.txt').read_text();executed=(out/'native.txt').read_text()
a=re.search(r'Executable unittests src/lib.rs \(([^\n]+)\)',compiled);b=re.search(r'Running unittests src/lib.rs \(([^\n]+)\)',executed)
assert a and b and a[1]==b[1]
files={'native-test':Path(a[1]),'audit-native':cache/'release/audit_native','halving-identity':cache/'release/halving_identity'}
rows={}
for name,source in files.items():
 dest=out/(name+'.bin');shutil.copyfile(source,dest);rows[name]={'built_path':str(source),'executed_path':str(source),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
rows['native-test']['Cargo_compile_runtime_paths_equal']=True
(out/'actual-binaries.json').write_text(json.dumps(rows,indent=2)+'\n')

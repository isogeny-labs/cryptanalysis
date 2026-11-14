"""Whole-byte guards and actually executed Cargo binary custody only."""
from pathlib import Path
import hashlib,json,re,shutil
o=Path('/workspace/scratch/ct74-norm-halving-native-05');before=json.loads((o/'before.json').read_text());after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest()for p in before};changed=[p for p in before if before[p]!=after[p]]
(o/'after.json').write_text(json.dumps(after,indent=2)+'\n');(o/'guards.json').write_text(json.dumps(dict(count=len(before),changed=changed),indent=2)+'\n');(o/'guard.exit').write_text(str(int(bool(changed)))+'\n')
compile_text=(o/'compile.txt').read_text()if(o/'compile.txt').exists()else'';native_text=(o/'native.txt').read_text()if(o/'native.txt').exists()else''
a=re.search(r'Executable unittests src/lib.rs \(([^\n]+)\)',compile_text);b=re.search(r'Running unittests src/lib.rs \(([^\n]+)\)',native_text)
if a and b:
 assert a[1]==b[1];source=Path(a[1]);dest=o/'actual-test-executable.bin';shutil.copyfile(source,dest);(o/'binary-custody.json').write_text(json.dumps(dict(compiled_path=a[1],executed_path=b[1],same_compiled_and_executed=True,bytes=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()),indent=2)+'\n')
raise SystemExit(bool(changed))

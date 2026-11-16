"""Exact compiler/runtime and input-source bytes only; no research arithmetic."""
from pathlib import Path
import hashlib,json,shutil,sys
pkg,build,bins,out=map(Path,sys.argv[1:]);assert(build/'fourth-compile.exit').read_text().strip()=='0';assert(bins/'original.exit').read_text().strip()=='0'
source=[]
for p in sorted((build/'actual-source').rglob('*')):
 if p.is_file():
  current=pkg/p.relative_to(build/'actual-source');assert p.read_bytes()==current.read_bytes(),str(current);source.append(dict(path=str(current),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
test=json.loads((build/'fourth-compiled-binary.json').read_text());records=[('test',Path(test['actual_path']),build/'fourth-original-compiled-test.bin')]
for label,name in [('auditor','audit-paired-fourth'),('control','paired-fourth-old-dual-control')]:
 record=json.loads((bins/(name+'-executable.json')).read_text());p=Path(record['actual_path']);copy=Path(record['actual_copy']);assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'];records.append((label,p,copy))
rows=[]
for label,p,copy in records:
 assert p.read_bytes()==copy.read_bytes();dest=out/('actual-'+label+'-runtime.bin');shutil.copy2(p,dest);assert dest.read_bytes()==copy.read_bytes();(out/(label+'-actual-path.txt')).write_text(str(p)+'\n');rows.append(dict(label=label,actual_Cargo_path=str(p),actual_compiled_copy=str(copy),actual_runtime_copy=str(dest),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),whole_bytes_equal=True))
(out/'runtime-custody.json').write_text(json.dumps(dict(all_previous_actual_compiled_sources=source,all_actual_executables=rows,new_non_Rust_files='new proof/native-orchestration files do not change the retained compiled Rust modules',scope='exact byte/input custody, no mathematical or signed execution acceptance'),indent=2)+'\n')

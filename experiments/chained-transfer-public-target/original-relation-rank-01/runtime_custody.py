"""I/O-only comparison of compiler artifacts and the accepted full capture."""
from pathlib import Path
import hashlib,json,shutil,sys
pkg,build,out=map(Path,sys.argv[1:4])
assert (build/'all-bins-compile.exit').read_text().strip()=='0'
for p in sorted((build/'actual-source').rglob('*')):
 if p.is_file():assert p.read_bytes()==(pkg/p.relative_to(build/'actual-source')).read_bytes()
receipt=json.loads((build/'compiled-binaries.json').read_text())
assert set(receipt)=={'producer','replay','controls'}
for label,row in receipt.items():
 actual=Path(row['actual_path']);body=actual.read_bytes()
 assert body==Path(row['copy']).read_bytes() and len(body)==row['bytes'] and hashlib.sha256(body).hexdigest()==row['sha256']
 shutil.copy2(actual,out/('actual-before-'+label+'.bin'));(out/(label+'-actual-path.txt')).write_text(str(actual)+'\n')
trace=Path('/workspace/scratch/ct101-original-relation-kernel-native-01/whole60-passive-trace.json')
gate=trace.parent/'whole60-accepted-capture.json'
v=json.loads(gate.read_text());assert v['whole_calls']==60 and v['whole_journal_events']==660 and v['all60full_reports_inputs_scalar_checks_counters_nontime_values_match_original'] is True
assert any(row['sha256']==hashlib.sha256(trace.read_bytes()).hexdigest()for row in v['whole_inputs'])
(out/'whole-native-inputs.json').write_text(json.dumps({str(p):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [trace,gate]},indent=2)+'\n')
(out/'runtime-custody.json').write_text(json.dumps(receipt,indent=2)+'\n')

"""Complete compiler/runtime/prepared-copy and original fixture byte custody."""
from pathlib import Path
import hashlib,json,lzma,os,shutil,sys
pkg,build,out=map(Path,sys.argv[1:4]);assert(build/'original.exit').read_text().strip()=='0'
members={}
for p in sorted((build/'actual-source').rglob('*')):
 if p.is_file():
  rel=p.relative_to(build/'actual-source');assert p.read_bytes()==(pkg/rel).read_bytes(),str(rel)
  members[str(rel)]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
binaries={}
for label in ['chain','auditor','native-auditor']:
 assert(build/(label+'-compile.exit')).read_text().strip()=='0'
 row=json.loads((build/(label+'-compiled-custody.json')).read_text());p=Path(row['actual_path']);data=p.read_bytes()
 assert data==Path(row['copy']).read_bytes()and len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256']
 shutil.copy2(p,out/('actual-before-native-'+label+'.bin'));(out/(label+'-actual-path.txt')).write_text(str(p)+'\n');binaries[label]=row
assert json.loads((build/'engine-reused.json').read_text())['actual_reuse']is True
for row in json.loads((build/'engine-prepared.json').read_text())['files']:assert Path(row['actual_path']).read_bytes()==Path(row['copy']).read_bytes()
compressed=pkg.parent/'paired-fourth-preflight/expected-native-01.json.xz';prior=Path('/workspace/scratch/ct82-fixed-chain-evaluator-native-01/old-sixteen.json')
data=lzma.decompress(compressed.read_bytes());assert data==prior.read_bytes();os.link(prior,out/'old-sixteen.json')
compressed_IC=pkg.parent/'original-fixed-model-ic-01/expected-native-01.json.xz';closed_IC=Path('/workspace/scratch/ct96-original-fixed-model-IC-native-01/all-whole-compared.json')
body=lzma.decompress(compressed_IC.read_bytes());assert body==closed_IC.read_bytes();os.link(closed_IC,out/'original-IC-whole100-baseline.json')
(out/'runtime-custody.json').write_text(json.dumps(dict(compiled_source_members=members,binaries=binaries,all_original_field_prepared_bytes_equal=True,old16=dict(source=str(compressed),compressed_sha256=hashlib.sha256(compressed.read_bytes()).hexdigest(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),whole_decompression_comparison_before_closed_link=True),scope='unsigned complete source/binary/fixture/prepared-byte custody; no mathematical projection'),indent=2)+'\n')

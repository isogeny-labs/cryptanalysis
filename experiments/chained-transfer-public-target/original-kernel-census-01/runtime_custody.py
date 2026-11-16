"""Whole compiler/runtime/source/input byte custody; no finite-space arithmetic."""
from pathlib import Path
import hashlib,json,shutil,sys
pkg,build,out=map(Path,sys.argv[1:4]);assert(build/'original.exit').read_text().strip()=='0'
members={}
for p in sorted((build/'actual-source').rglob('*')):
 if p.is_file():
  rel=p.relative_to(build/'actual-source');assert p.read_bytes()==(pkg/rel).read_bytes(),str(rel)
  members[str(rel)]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
binaries={}
for label in ['chain','auditor']:
 assert(build/(label+'-compile.exit')).read_text().strip()=='0'
 row=json.loads((build/(label+'-compiled-custody.json')).read_text());p=Path(row['actual_path']);copy=Path(row['copy'])
 assert p.read_bytes()==copy.read_bytes() and p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
 shutil.copy2(p,out/('actual-before-native-'+label+'.bin'));(out/(label+'-actual-path.txt')).write_text(str(p)+'\n');binaries[label]=row
dest=out/'fixtures';dest.mkdir();pins=json.loads((pkg/'input-pins.json').read_text())
for name,row in pins.items():
 source=pkg.parent/row['source'];b=source.read_bytes();assert len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256']
 shutil.copyfile(source,dest/name);assert(dest/name).read_bytes()==b
(out/'runtime-custody.json').write_text(json.dumps(dict(compiled_source_members=members,binaries=binaries,all_whole_compressed_inputs=pins,whole_source_binary_and_input_copy_equality=True,field_engine='none; finite revalidation of already genuine coordinate certificates',scope='unsigned byte custody; no mathematical projection'),indent=2)+'\n')

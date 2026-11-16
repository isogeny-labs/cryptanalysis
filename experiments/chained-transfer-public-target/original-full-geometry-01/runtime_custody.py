"""Whole source, executables, prepared bytes and genuinely pinned fixture I/O."""
from pathlib import Path
import hashlib,json,lzma,os,shutil,sys
pkg,build,out=map(Path,sys.argv[1:4]);assert(build/'original.exit').read_text().strip()=='0'
members={}
for p in sorted((build/'actual-source').rglob('*')):
 if p.is_file():
  rel=p.relative_to(build/'actual-source');assert p.read_bytes()==(pkg/rel).read_bytes(),str(rel)
  members[str(rel)]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
binaries={}
for label in ['chain','auditor']:
 assert(build/(label+'-compile.exit')).read_text().strip()=='0'
 row=json.loads((build/(label+'-compiled-custody.json')).read_text());p=Path(row['actual_path']);b=p.read_bytes()
 assert b==Path(row['copy']).read_bytes()and len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256']
 shutil.copy2(p,out/('actual-before-native-'+label+'.bin'));(out/(label+'-actual-path.txt')).write_text(str(p)+'\n');binaries[label]=row
assert json.loads((build/'engine-reused.json').read_text())['actual_reuse']is True
for row in json.loads((build/'engine-prepared.json').read_text())['files']:
 assert Path(row['actual_path']).read_bytes()==Path(row['copy']).read_bytes()
fixtures=out/'fixtures';fixtures.mkdir();inputs={}
for name,row in json.loads((pkg/'input-pins.json').read_text()).items():
 p=pkg.parent/row['source'];compressed=p.read_bytes();assert hashlib.sha256(compressed).hexdigest()==row['sha256']and len(compressed)==row['bytes'];data=lzma.decompress(compressed)
 if name=='old-sixteen.json':
  retained=Path('/workspace/scratch/ct82-fixed-chain-evaluator-native-01/old-sixteen.json');assert data==retained.read_bytes();os.link(retained,fixtures/name)
 else:(fixtures/name).write_bytes(data)
 assert(fixtures/name).read_bytes()==data
 inputs[name]=dict(source=str(p),compressed_sha256=row['sha256'],bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
(out/'runtime-custody.json').write_text(json.dumps(dict(compiled_source_members=members,binaries=binaries,whole_fixture_copies=inputs,actual_prepared_library_copies_and_cache_equal=True,whole_source_binary_and_fixture_bytes_equal=True,scope='I/O and unsigned byte custody only'),indent=2)+'\n')

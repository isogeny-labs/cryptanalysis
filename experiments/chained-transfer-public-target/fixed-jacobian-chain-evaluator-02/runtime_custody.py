"""Complete compiler/source/runtime and original fixture byte custody; I/O only."""
from pathlib import Path
import hashlib,json,shutil,sys,lzma,os
pkg,build,out=map(Path,sys.argv[1:4]);assert(build/'original.exit').read_text().strip()=='0'
source=build/'actual-source';members={}
for p in sorted(source.rglob('*')):
 if p.is_file():
  rel=p.relative_to(source);assert p.read_bytes()==(pkg/rel).read_bytes(),str(rel)
  members[str(rel)]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
binaries={}
for label in ['chain','auditor','deriver']:
 assert(build/(label+'-compile.exit')).read_text().strip()=='0'
 row=json.loads((build/(label+'-compiled-custody.json')).read_text());p=Path(row['actual_path']);b=p.read_bytes();assert b==Path(row['copy']).read_bytes();assert len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256']
 shutil.copy2(p,out/('actual-before-native-'+label+'.bin'));(out/(label+'-actual-path.txt')).write_text(str(p)+'\n');binaries[label]=row
assert json.loads((build/'engine-reused.json').read_text())['actual_reuse']is True
# The old whole fixtures are independently decompressed and compared in full
# before exact-byte hardlinks save a second copy. No mathematical projection.
fixtures=[]
for compressed,retained,name in [
 (pkg.parent/'fixed-jacobian-chain-evaluator-01/expected-native-01.json.xz',Path('/workspace/scratch/ct82-fixed-chain-evaluator-native-01/all695-expected.json'),'baseline695.json'),
 (pkg.parent/'paired-fourth-preflight/expected-native-01.json.xz',Path('/workspace/scratch/ct82-fixed-chain-evaluator-native-01/old-sixteen.json'),'old-sixteen.json')]:
 assert retained.is_file(),str(retained)
 h=hashlib.sha256();size=0
 with lzma.open(compressed,'rb')as a,retained.open('rb')as b:
  while True:
   x=a.read(1048576);y=b.read(1048576);assert x==y,str(compressed)
   if not x:break
   h.update(x);size+=len(x)
 dest=out/name;os.link(retained,dest);assert dest.read_bytes()==retained.read_bytes()
 fixtures.append(dict(original_compressed=str(compressed),compressed_sha256=hashlib.sha256(compressed.read_bytes()).hexdigest(),retained_raw=str(retained),runtime_path=str(dest),whole_decompressed_equal=True,bytes=size,sha256=h.hexdigest(),hardlink_after_full_independent_comparison=True))
(out/'runtime-custody.json').write_text(json.dumps(dict(compiled_source_members=members,binaries=binaries,fixtures=fixtures,scope='Every compiled member and whole binary exact; full genuine fixture decompression comparison before hardlink; unsigned custody only'),indent=2)+'\n')

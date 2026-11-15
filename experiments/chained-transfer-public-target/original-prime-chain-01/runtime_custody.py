"""Whole compiler/runtime and original fixture byte custody; no arithmetic."""
from pathlib import Path
import hashlib,json,shutil,sys,lzma,os
pkg,build,out=map(Path,sys.argv[1:4]);assert(build/'original.exit').read_text().strip()=='0'
source=build/'actual-source';members={}
for p in sorted(source.rglob('*')):
 if p.is_file():
  rel=p.relative_to(source);assert p.read_bytes()==(pkg/rel).read_bytes(),str(rel);members[str(rel)]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
binaries={}
for label in ['chain','auditor']:
 assert(build/(label+'-compile.exit')).read_text().strip()=='0';row=json.loads((build/(label+'-compiled-custody.json')).read_text());p=Path(row['actual_path']);b=p.read_bytes();assert b==Path(row['copy']).read_bytes();assert len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256'];shutil.copy2(p,out/('actual-before-native-'+label+'.bin'));(out/(label+'-actual-path.txt')).write_text(str(p)+'\n');binaries[label]=row
assert json.loads((build/'engine-reused.json').read_text())['actual_reuse']is True
compressed=pkg.parent/'paired-fourth-preflight/expected-native-01.json.xz';retained=Path('/workspace/scratch/ct82-fixed-chain-evaluator-native-01/old-sixteen.json');h=hashlib.sha256();size=0
with lzma.open(compressed,'rb')as a,retained.open('rb')as b:
 while True:
  x=a.read(1048576);y=b.read(1048576);assert x==y
  if not x:break
  h.update(x);size+=len(x)
os.link(retained,out/'old-sixteen.json')
fixtures=[];dest=out/'fixtures';dest.mkdir()
for label in ['originalE2','originalE3','originalE4']:
 p=pkg.parent/'evidence/original-prime-alternative-kernel-review-01'/(label+'-whole-six-rows.json.xz');b=lzma.decompress(p.read_bytes());q=dest/(label+'-whole-six-rows.json');q.write_bytes(b);fixtures.append(dict(source=str(p),compressed_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),runtime_path=str(q),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
(out/'runtime-custody.json').write_text(json.dumps(dict(compiled_source_members=members,binaries=binaries,old16=dict(original_compressed=str(compressed),retained_raw=str(retained),bytes=size,sha256=h.hexdigest(),whole_independent_decompression_comparison_before_hardlink=True),all_original_row_fixtures=fixtures,scope='whole source/binary/fixture custody; no mathematical projection or signed standing'),indent=2)+'\n')

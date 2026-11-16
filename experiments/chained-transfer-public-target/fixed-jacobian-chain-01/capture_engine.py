"""Cargo engine artifact/profile and exact-byte custody only, no research arithmetic."""
from pathlib import Path
import hashlib,json,shutil,sys
out,producer=map(Path,sys.argv[1:3]);mode=sys.argv[3]
name='original-engine-preparation.txt'if mode=='prepared'else'geometry-compile.txt'
rows=[]
for line in(out/name).read_text().splitlines():
 try:row=json.loads(line)
 except json.JSONDecodeError:continue
 if row.get('reason')=='compiler-artifact'and row.get('target',{}).get('name')=='isogeny_algos':rows.append(row)
assert len(rows)==1
artifact=rows[0];assert Path(artifact['manifest_path']).resolve()==(producer/'isogeny_algos/Cargo.toml').resolve()
assert artifact['target']['kind']==['lib']and artifact['profile']['opt_level']=='3'and not artifact['profile']['test']
if mode=='prepared':
 dest=out/'actual-prepared-original-engine';dest.mkdir();files=[]
 for filename in artifact['filenames']:
  p=Path(filename);q=dest/p.name;shutil.copyfile(p,q);files.append(dict(actual_path=str(p),copy=str(q),bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest()))
 (out/'engine-prepared.json').write_text(json.dumps(dict(Cargo_artifact=artifact,files=files,scope='original engine compiled in explicit900s setup phase; not a test or runtime price'),indent=2)+'\n')
else:
 assert mode=='reused'and artifact['fresh']is True,'prepared engine must actually be reused'
 original=json.loads((out/'engine-prepared.json').read_text())
 for key in ['package_id','manifest_path','target','profile','features','executable']:
  assert artifact[key]==original['Cargo_artifact'][key],key
 # Cargo names a selected primary library at release/libname.rlib and its
 # dependency alias at release/deps/libname-HASH.rlib. Keep both actual paths
 # and compare their COMPLETE bytes to the copy made before the test build.
 prior={}
 for entry in original['files']:
  suffix=Path(entry['actual_path']).suffix;assert suffix not in prior
  prior[suffix]=entry
 assert set(prior)=={'.rlib','.rmeta'}
 aliases=[];seen=set()
 for filename in artifact['filenames']:
  p=Path(filename);suffix=p.suffix;assert suffix in prior and suffix not in seen;seen.add(suffix)
  entry=prior[suffix];b=p.read_bytes();before=Path(entry['copy']).read_bytes()
  assert b==before and b==Path(entry['actual_path']).read_bytes()
  assert len(b)==entry['bytes']and hashlib.sha256(b).hexdigest()==entry['sha256']
  aliases.append(dict(prepared_path=entry['actual_path'],dependency_path=str(p),same_path=str(p)==entry['actual_path'],bytes=len(b),sha256=entry['sha256'],whole_before_and_after_bytes_equal=True))
 assert seen==set(prior)
 (out/'engine-reused.json').write_text(json.dumps(dict(Cargo_artifact=artifact,actual_aliases=aliases,actual_prepared_bytes_unchanged=True,actual_reuse=True,scope='exact wholeRLIB/RMETA bytes across actual Cargo aliases; no full cold120s claim'),indent=2)+'\n')

"""Whole GitHub artifact/log custody; no mathematical computation."""
from pathlib import Path
import json,urllib.request,hashlib,subprocess,zipfile,shutil,os
out=Path('/workspace/scratch/ct86-fixed-chain25-CI-acceptance-01');out.mkdir()
for name in ['jobs','artifacts']:shutil.copyfile('/workspace/scratch/ct86-ci25-'+name+'-api.json',out/(name+'-api.json'))
a=json.loads(Path('/workspace/scratch/private-ct86-ci25-download-api.json').read_text())['structuredContent'];u=a['file_uri']['download_url']
with urllib.request.urlopen(u,timeout=120)as src,(out/'whole-original-artifact.zip').open('wb')as dest:shutil.copyfileobj(src,dest)
p=out/'whole-original-artifact.zip';assert p.stat().st_size==44978600 and hashlib.sha256(p.read_bytes()).hexdigest()=='4ba6c96eac32a6fb8884bdd7a6270e42e5e48992461b63245fc6d1d9771b2558'
# Whole exact-byte candidates are closed original raw, never active cache files.
roots=[Path('/workspace/scratch/ct82-fixed-chain-evaluator-native-01'),Path('/workspace/scratch/ct82-fixed-chain-geometry-native-01'),Path('/workspace/scratch/ct82-fixed-chain-evaluator-build-02'),Path('/workspace/scratch/ct82-fixed-chain-geometry-build-02')]
by_size={}
for root in roots:
 for q in root.rglob('*'):
  if q.is_file()and q.stat().st_size>1000000:by_size.setdefault(q.stat().st_size,[]).append(q)
rows=[];links=[]
with zipfile.ZipFile(p)as z:
 assert len(z.namelist())==len(set(z.namelist()))
 for info in z.infolist():
  name=Path(info.filename);assert not name.is_absolute()and'..'not in name.parts
  dest=out/'whole-artifact'/name
  if info.is_dir():dest.mkdir(parents=True,exist_ok=True);rows.append(dict(name=info.filename,directory=True,bytes=0));continue
  dest.parent.mkdir(parents=True,exist_ok=True);matched=None
  for candidate in by_size.get(info.file_size,[]):
   equal=True;h=hashlib.sha256()
   with z.open(info)as a,candidate.open('rb')as b:
    while True:
     x=a.read(1048576);y=b.read(1048576)
     if x!=y:equal=False;break
     if not x:break
     h.update(x)
   if equal:matched=candidate;break
  if matched:
   os.link(matched,dest);digest=h.hexdigest();links.append(dict(member=info.filename,existing_closed_raw=str(matched),bytes=info.file_size,sha256=digest,entire_zip_payload_compared_before_link=True))
  else:
   h=hashlib.sha256()
   with z.open(info)as a,dest.open('wb')as b:
    while x:=a.read(1048576):h.update(x);b.write(x)
   digest=h.hexdigest()
  assert dest.stat().st_size==info.file_size
  rows.append(dict(name=info.filename,bytes=info.file_size,sha256=digest))
(out/'all-unfiltered-artifact-members.json').write_text(json.dumps(rows,indent=2)+'\n');(out/'closed-full-byte-links.json').write_text(json.dumps(links,indent=2)+'\n')
print('Entire artifact verified/extracted:',len(rows),'members;',len(links),'full-byte links',flush=True)
with(out/'whole-runlogs.zip').open('wb')as dest,(out/'private-runlogs.stderr').open('wb')as err:q=subprocess.run(['gh','api','repos/isogeny-labs/cryptanalysis/actions/runs/43674526503/logs'],stdout=dest,stderr=err)
(out/'runlogs-download.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
rows=[]
with zipfile.ZipFile(out/'whole-runlogs.zip')as z:
 for info in z.infolist():
  name=Path(info.filename);assert not name.is_absolute()and'..'not in name.parts
  b=z.read(info);dest=out/'whole-runlogs'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);rows.append(dict(name=info.filename,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
(out/'all-unfiltered-runlog-members.json').write_text(json.dumps(rows,indent=2)+'\n');print('Entire runlogs:',len(rows),'members',flush=True)

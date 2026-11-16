"""Whole original CI byte custody and complete ZIP member census only."""
from pathlib import Path,PurePosixPath
import hashlib,io,json,shutil,urllib.request,zipfile
s=Path('/workspace/scratch');o=s/'ct80-B4-new22-CI-acceptance-01';o.mkdir()
for name in ['source-terminal-api','new22-jobs-api','new22-artifacts-api','other21-job-apis','new22-whole-log-api']:
 shutil.copyfile(s/('ct80-B4-CI-'+name+'.json'),o/(name+'.json'))
api=json.loads((s/'private-ct80-B4-new22-download-api.json').read_text());data=api['structuredContent']
with urllib.request.urlopen(data['file_uri']['download_url'],timeout=120) as response:raw=response.read(64*1024*1024)
assert len(raw)==34823262 and hashlib.sha256(raw).hexdigest()=='2dcafafd1682141eafccdd7116a3487d09ac90372ecaf41fc52a1ed187880bba'
(o/'whole-original-artifact.zip').write_bytes(raw);members={};extracted=[]
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 assert len(z.namelist())==len(set(z.namelist()))
 for info in z.infolist():
  path=PurePosixPath(info.filename);assert not path.is_absolute() and '..' not in path.parts and info.file_size<128*1024*1024
  assert not info.is_dir();b=z.read(info)
  members[str(path)]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
  if info.file_size<=4*1024*1024 or path.suffix in ['.txt','.json','.pipe-exits','.exit']:
   p=o/'members'/str(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);extracted.append(str(path))
(o/'whole-original-members.json').write_text(json.dumps(members,indent=2)+'\n')
(o/'convenience-extracted-paths.json').write_text(json.dumps(extracted,indent=2)+'\n')
runs=json.loads((o/'source-terminal-api.json').read_text())['structuredContent']['workflow_runs']
assert len(runs)==23 and len({r['name'] for r in runs})==22 and all(r['conclusion']=='success' for r in runs)
(o/'custody.json').write_text(json.dumps(dict(source='b4e3543018ddc5ed70a34ee17280f23b8848484c',run=43638366601,job=132580094399,artifact=14130459991,artifact_bytes=len(raw),artifact_sha256=hashlib.sha256(raw).hexdigest(),whole_members=len(members),all_original_member_bytes_retained_in_zip=True,success_runs=23,distinct_workflows=22,duplicate='two actual pcc-gate occurrences; never23 distinct workflows',signing='both sign jobs skipped, no signed standing',native_independent_whole_artifact_audit='NOTRUN; API/job status and I/O custody only'),indent=2)+'\n')
shutil.copyfile(__file__,o/'original-capture-command.py');print('wholeCIcapture',len(members),'members;',len(raw),'bytes;',23,'runs/',22,'distinct; nativeauditNOTRUN')

"""Import only a genuinely downloaded original receipt into exactly matching state."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import hashlib,io,json,shutil,subprocess,tarfile,urllib.request,zipfile
r=Path('/workspace/cryptanalysis');source='39e9db95506b8cdfa0fea37c3d2716b511651b84'
o=Path('/workspace/scratch/ct69-original-checkpoint-transport-01');o.mkdir()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==source
status=subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=r);assert not status
(o/'before-Git-status.txt').write_bytes(status)
for label in ['jobs','artifacts','whole-log','download']:
    shutil.copyfile('/workspace/scratch/ct69-checkpoint-transport-'+label+'-api.json',o/(label+'-api.json'))
jobs=json.loads((o/'jobs-api.json').read_text())['structuredContent']['jobs'];assert len(jobs)==1 and jobs[0]['id']==132245064560 and jobs[0]['conclusion']=='success'
artifacts=json.loads((o/'artifacts-api.json').read_text())['structuredContent']['artifacts'];assert len(artifacts)==1 and artifacts[0]['id']==14087750072 and artifacts[0]['workflow_run']['head_sha']==source
api=json.loads((o/'download-api.json').read_text());data=api.get('structuredContent',api)
if 'file_uri'not in data:data=data['structuredContent']
with urllib.request.urlopen(data['file_uri']['download_url'],timeout=120)as response:raw=response.read(4*1024*1024)
assert len(raw)==87453 and hashlib.sha256(raw).hexdigest()=='19053dfdbcb1123a405aa4a28f09244418683f6798adfa836ccecde6afb7ae3c'
(o/'whole-original-GitHub-artifact.zip').write_bytes(raw);members={}
with zipfile.ZipFile(io.BytesIO(raw))as z:
    assert len(set(z.namelist()))==len(z.namelist())
    for info in z.infolist():
        name=PurePosixPath(info.filename);assert not name.is_absolute() and '..'not in name.parts and info.file_size<4*1024*1024
        assert not info.is_dir()
        value=z.read(info);p=o/'members'/str(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value);members[str(name)]=dict(bytes=len(value),sha256=hashlib.sha256(value).hexdigest())
(o/'whole-members.json').write_text(json.dumps(members,indent=2)+'\n');m=o/'members'
assert(m/'source-head.txt').read_text().strip()==source
assert(m/'source-branch.txt').read_text().strip()=='research/chained-transfer-public-target-20261113'
for label in ['original-gate','readback-pack','readback-resume','readback-meta']:assert(m/(label+'.exit')).read_text().strip()=='0',label
assert(m/'original-RESUME.md').read_bytes()==(r/'.resume/RESUME.md').read_bytes()==(m/'remote-RESUME.md').read_bytes()==(m/'pack-RESUME.md').read_bytes()
meta=json.loads((m/'remote-meta.json').read_text());assert meta['head']==source and meta['repo']=='cryptanalysis' and meta['branch']=='research/chained-transfer-public-target-20261113'
assert(m/'remote-meta.json').read_bytes()==(m/'pack-meta.json').read_bytes()
with tarfile.open(m/'remote-checkpoint.tar.gz','r:gz')as t:
    assert t.extractfile('./RESUME.md').read()==(r/'.resume/RESUME.md').read_bytes()
    assert t.extractfile('./meta.json').read()==(m/'remote-meta.json').read_bytes()
for line in(m/'source-inputs.sha256').read_text().splitlines():
    h,p=line.split('  ',1);assert hashlib.sha256((r/p).read_bytes()).hexdigest()==h,p
assert hashlib.sha256((r/'scripts/checkpoint.sh').read_bytes()).hexdigest()=='3c4192168bbc390bf94be46c765914a419a4eff8c30e3f52f5b94ea432738056'
receipt=(m/'original-last-push.txt').read_bytes();fields=receipt.decode().split();assert len(fields)==3 and len(fields[0])==64 and fields[2]==meta['s3']
existing=r/'.resume/.last-push'
if existing.exists():shutil.copyfile(existing,o/'previous-local-last-push.txt')
shutil.copyfile(m/'original-last-push.txt',existing)
assert existing.read_bytes()==receipt and subprocess.run(['git','check-ignore','-q','.resume/.last-push'],cwd=r).returncode==0
for label,command in [('original-local-status',['bash','scripts/checkpoint.sh','status']),('original-local-gate',['timeout','120','bash','scripts/checkpoint.sh','gate'])]:
    p=subprocess.run(command,cwd=r,capture_output=True);(o/(label+'.log')).write_bytes(p.stdout+p.stderr);(o/(label+'.exit')).write_text(str(p.returncode)+'\n');print(label,p.returncode,flush=True)
    assert p.returncode==0,(p.stdout+p.stderr).decode()[:1200]
    if label=='original-local-status':assert b'last push : current'in p.stdout
    if label=='original-local-gate':assert b'checkpoint: unchanged since'in p.stdout
assert subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=r)==status
(o/'after-Git-status.txt').write_bytes(status)
(o/'observation.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),source=source,protocol='16bb06/4c55 published before workflow39e9/d4f874/f6b616',run=43530006697,job=132245064560,artifact=14087750072,artifact_bytes=len(raw),artifact_sha256=hashlib.sha256(raw).hexdigest(),whole_members=len(members),original_tool='consumer3de8checkpoint.sh/SHA3c419216',original_remote_gate=0,original_remote_checkpoint_readback='pack/Resume/meta0/wholebyteequality/sourcehash',genuine_original_receipt_imported_exactly=True,original_local_status=0,original_local_gate=0,matching_clean_source_and_original_resume_tool=True,tracked_untracked_Git_status_unchanged=True,keys_or_upload_token_exported=False,host_namespace_exits={name:int((m/(name+'.exit')).read_text())for name in ['boot-id','time-namespace','time-offsets']},scope='original checkpoint transport PASSES for this exact clean committedstate;later changes stale it;NOT livebudget/capacity/isolation/counter/reference/performance/globalroot acceptance'),indent=2)+'\n')
shutil.copyfile(__file__,o/'original-import-command.py');print(json.dumps(dict(source=source,whole_members=len(members),remote_gate=0,local_gate=0,exact_original_receipt=True,Git_status_unchanged=True)),flush=True)

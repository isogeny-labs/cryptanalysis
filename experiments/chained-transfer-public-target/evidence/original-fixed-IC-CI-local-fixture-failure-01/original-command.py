"""Fresh isolated precommit CI replay in RAM; orchestration, source copying and hashing only."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess,yaml
w=Path('/workspace');raw=w/'scratch/ct100-original-fixed-IC-CI-local-01';raw.mkdir()
layout=Path('/dev/shm/ct100-original-fixed-IC-CI-layout-01');layout.mkdir()
shutil.copyfile(__file__,raw/'original-command.py');commands=[]
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',PATH='/home/agent/.cargo/bin:/home/agent/.elan/bin:'+os.environ['PATH'])
def run(name,cmd,cwd):
    with(raw/(name+'.txt')).open('xb')as f:q=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
    (raw/(name+'.exit')).write_text(str(q.returncode)+'\n');commands.append(dict(name=name,command=cmd,cwd=str(cwd),actual_exit=q.returncode));print(name,q.returncode,flush=True)
    assert q.returncode==0,(name,q.returncode)
consumer=w/'cryptanalysis';head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=consumer,env=env,text=True).strip();assert head=='2920181e2a8bcae3238f14007660d1a61480555f'
pin=(consumer/'experiments/chained-transfer-public-target/upstream-commit.txt').read_text().strip()
workflow=Path('.github/workflows/chained-transfer-original-fixed-ic.yml')
config=yaml.safe_load((consumer/workflow).read_text());steps=config['jobs']['original-fixed-ic']['steps']
patterns={step['with']['path']:step['with']['sparse-checkout'].splitlines()for step in steps if'with'in step and'sparse-checkout'in step['with']and step['with']['path']in['crypto','cryptanalysis']}
assert set(patterns)=={'crypto','cryptanalysis'}
for name,revision in [('crypto',pin),('cryptanalysis',head)]:
    source=w/name;dest=layout/name
    run(name+'-worktree',['git','worktree','add','--detach','--no-checkout',str(dest),revision],source)
    run(name+'-sparse',['git','sparse-checkout','set','--no-cone',*['/'+p+('/'if(source/p).is_dir()else'')for p in patterns[name]]],dest)
    run(name+'-checkout',['git','checkout','--detach',revision],dest)
src=consumer/'experiments/chained-transfer-public-target/ci_original_fixed_ic';dst=layout/'cryptanalysis'/src.relative_to(consumer)
shutil.copytree(src,dst,ignore=shutil.ignore_patterns('__pycache__'))
(layout/'cryptanalysis'/workflow).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(consumer/workflow,layout/'cryptanalysis'/workflow)
hydrated=[]
for manifest in sorted((layout/'cryptanalysis/docs/research-artifacts/chained-transfer').rglob('.artifacts.json')):
    original=consumer/manifest.relative_to(layout/'cryptanalysis');assert manifest.read_bytes()==original.read_bytes()
    for name,row in json.loads(manifest.read_text())['files'].items():
        relative=PurePosixPath(name);assert not relative.is_absolute()and'..'not in relative.parts
        source=original.parent/name;target=manifest.parent/name;assert source.is_file()
        h=hashlib.file_digest(source.open('rb'),'sha256').hexdigest();assert h==row['sha256']and source.stat().st_size==row['bytes']
        assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        assert target.read_bytes()==source.read_bytes();hydrated.append(dict(path=target.relative_to(layout/'cryptanalysis').as_posix(),bytes=row['bytes'],sha256=h,source='whole locally retained genuine canonical bytes; not a new remote read'))
(raw/'whole-canonical-fixture-copy-custody.json').write_text(json.dumps(hydrated,indent=2)+'\n')
manifest={p.relative_to(layout/'cryptanalysis').as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest())for p in sorted(dst.rglob('*'))+[layout/'cryptanalysis'/workflow]if p.is_file()}
(raw/'exact-precommit-driver-source.json').write_text(json.dumps(dict(consumer_parent=head,producer_exact_original=pin,source_files=manifest,source_scope='parent292 plus these exact untracked CI/workflow files; not a committed source or GitHub acceptance',worktrees_RAM=str(layout),raw_outputs_persisted_on_completion=True),indent=2)+'\n')
cmd=['timeout','3600','bash',str(dst/'check-01.sh'),str(layout/'crypto'),str(layout/'whole-output')]
(raw/'start.txt').write_text(datetime.now(timezone.utc).isoformat()+'\n')
with(raw/'actual-driver.txt').open('xb')as f:q=subprocess.run(cmd,cwd=layout/'cryptanalysis',env=env,stdout=f,stderr=subprocess.STDOUT)
(raw/'actual-driver.exit').write_text(str(q.returncode)+'\n');(raw/'finish.txt').write_text(datetime.now(timezone.utc).isoformat()+'\n')
# Preserve every output, including full prepared libraries, source snapshots and
# failure/control inputs, outside volatile RAM before interpreting the result.
if(layout/'whole-output').exists():
    shutil.copytree(layout/'whole-output',raw/'whole-output',symlinks=True)
    for p in sorted((layout/'whole-output').rglob('*')):
        if p.is_file():assert p.read_bytes()==(raw/'whole-output'/p.relative_to(layout/'whole-output')).read_bytes()
(raw/'outcome.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),actual_exit=q.returncode,command=cmd,consumer_parent=head,producer_original_pin=pin,precommit_source_manifest='exact-precommit-driver-source.json',preparatory_commands=commands,all_whole_outputs_copied_and_compared_before_interpretation=True,raw_cargo_cache='RAM derived cache retained, distinct from preserved full prepared/runtime copies',scope='fresh local precommit exact driver validation; no GitHub CI or timing standing'),indent=2)+'\n')
print('actual-driver',q.returncode,flush=True);assert q.returncode==0

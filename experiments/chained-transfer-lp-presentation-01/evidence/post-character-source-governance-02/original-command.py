"""Publish original compiler source dependencies and complete metadata."""
from pathlib import Path
from datetime import datetime, timezone
import base64, hashlib, json, lzma, os, shutil, subprocess
index_custody=Path('/dev/shm/ct236-consumer-entire-index-custody');index_custody.mkdir()
shutil.copyfile('/workspace/cryptanalysis/.git/index',index_custody/'entire-index-before')
shutil.copyfile('/workspace/cryptanalysis/.git/index',index_custody/'current-index')
os.environ['GIT_INDEX_FILE']=str(index_custody/'current-index')
os.environ['GIT_OPTIONAL_LOCKS']='0'

r = Path('/workspace/cryptanalysis')
base = '7b1cdfc62650ffcfcee1e4227c46f4021f3eb587'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=r, text=True).strip() == base
p = r / 'experiments/chained-transfer-lp-presentation-01'
g = p / 'evidence/post-character-source-governance-02'
g.mkdir()
shutil.copyfile(__file__, g / 'original-command.py')
scope = [str(p.relative_to(r)), 'experiments/chained-transfer-relation-diagnostics-03/evidence/whole-original-CI02-and-development-success-01', '.github/workflows/chained-transfer-lp-historical-development-01.yml', 'pcc/claims', 'pcc/ledger.jsonl', 'docs/session-logs/2026-11-16.md', '.resume/RESUME.md', '.gitattributes']

def paths():
    return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0')) | set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))) - {b''})

def run(name, command, expected=0):
    q = subprocess.run(command, cwd=r, capture_output=True)
    (g / (name+'.txt.xz')).write_bytes(lzma.compress(q.stdout+q.stderr))
    (g / (name+'.exit')).write_text(str(q.returncode)+'\n')
    print(name, q.returncode, flush=True)
    assert q.returncode == expected

protected_changes=set(subprocess.check_output(['git','diff','--name-only',base,'--','tools','scripts','suite','.github/workflows','.artifacts/config.json','experiments/chained-transfer-lp-presentation-01/native','experiments/chained-transfer-lp-presentation-01/lean','experiments/chained-transfer-lp-presentation-01/matrix-01'],cwd=r,text=True).splitlines())
assert protected_changes <= {'.github/workflows/chained-transfer-lp-historical-development-01.yml'}
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base])
run('authored-prose',['python3','tools/pcc/pcc.py','lint-prose',*[n.decode() for n in paths() if n.endswith(b'.md')]])
run('all1605-original-source-guards',['sha256sum','--check','experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256'])
run('benchrec',['python3','tools/benchrec.py','gate'])
run('wiring',['python3','tools/artifacts/wire_workflows.py','--check'])
run('report-Python',['python3','tools/ci/check_report_graph_python.py'])
run('historical-complete-source-guard',['sha256sum','--check','experiments/chained-transfer-lp-presentation-01/historical-01/source-01.sha256'])
run('new-workflow-actionlint',['/workspace/scratch/actionlint-bin/actionlint','-oneline','.github/workflows/chained-transfer-lp-historical-development-01.yml'])
run('new-driver-shell-syntax',['bash','-n','experiments/chained-transfer-lp-presentation-01/historical-01/run-development-01.sh'])

def stage():
    names=paths()
    f=Path('/workspace/scratch/ct236-source.paths0')
    f.write_bytes(b'\0'.join(n for n in names if n!=b'.resume/RESUME.md')+b'\0')
    # The21 literal prerequisites were explicitly added before the cold
    # reproduction. Re-add tracked files normally; no ignore rule changes.
    subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True)
    subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
    selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''}
    assert selected==set(names)
    for n in selected:
        if n.startswith(b'pcc/claims/'):
            for proof in json.loads((r/n.decode()).read_text()).get('proofs',[]):
                if proof.get('kind')=='attestation':
                    s=proof['subject']
                    assert hashlib.sha256((r/s['path']).read_bytes()).hexdigest()==s['sha256']
                    assert s['path'].encode() in selected or subprocess.run(['git','cat-file','-e',base+':'+s['path']],cwd=r,capture_output=True).returncode==0

stage()
run('cached-whitespace',['git','diff','--cached','--check'])
tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip()
run('immediate-parent-artifact-policy',['python3','tools/artifacts/artifacts.py','check',base,tree])
run('frozen-PR-base-artifact-policy-before-NEW28',['python3','tools/artifacts/artifacts.py','check','82617f14fb48843585137f0310f7d1fa9a5d8ea6',tree],1)
raw=lzma.decompress((g/'frozen-PR-base-artifact-policy-before-NEW28.txt.xz').read_bytes())
import re
found={(m.group(2).decode(),int(m.group(1).replace(b',',b''))) for m in re.finditer(rb'^ +([0-9,]+)  (.+)$',raw,re.M)}
expected={('experiments/chained-transfer-lp-presentation-01/evidence/historical-native-CI-success-01/entire-original-checkpoint-metadata/remote-RESUME.md.xz',109392)}
expected.update(('experiments/chained-transfer-relation-diagnostics-02/evidence/entire-CI02-source-guard-failure-01/entire-original-checkpoint-metadata/'+name+'-RESUME.md.xz',101396) for name in ['original','pack','remote'])
assert found==expected and b'4 data file(s)' in raw
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Separate finite post-character source governance: original immediate-parent prefix/prose/all1605/benchrec/wiring/reportPython/50-sourceguard/actionlint/shell/cached/immediate-artifact0. Frozen PR-base826 broader artifact1 remains exactly4 whole earlier CI RESUME archives,109392 and3x101396 bytes, pending genuineNEW28; no policy waiver or merge. Post compile-only/strict Clippy0 with15 total packages/14 dependencies and no field engine dac3e6/a16268; whole source/fixtures/count-observer correction retained. Updated checkpoint/readback-gated native post units/CLI remain prospective. Read-only existing-caller admission probe has3 offline metadata controls0 (525863), no live queries or paid launch yet; wrong-account reads stop and lane accounting unknown always blocks admission, original all-tenant pool script pinned unchanged. Original witness-auditor and360 replay require separate actual executions with full earlier engine/native/prepared custody f5be57, not a new cold120s claim. Scientific matrix/graph/proof sources and original tools/verifier/keyring/checkpoint/policy unchanged. No paid build/job/full historical population or signed/global/cost promotion. Normal source publication/fresh actual CI follow; full EKS runtime/config/admission and genuineNEW28 remain open.']
for f in sorted(g.iterdir()):
    cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
stage()
subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True)
subprocess.run(['git','commit','--quiet','-m','research: audit complete LP character residuals and explicit lifts after generation'],cwd=r,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()
shutil.copyfile(index_custody/'current-index',r/'.git/index')
assert hashlib.sha256((r/'.git/index').read_bytes()).digest()==hashlib.sha256((index_custody/'current-index').read_bytes()).digest()
print(claim,head,flush=True)
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-lp-presentation-20261115','/workspace/scratch/ct236-historical-source-normal-publication-01'],cwd=r,capture_output=True)
Path('/workspace/scratch/ct236-historical-source-normal-caller01.txt').write_bytes(q.stdout+q.stderr)
print('normal-publication',q.returncode,flush=True)
assert q.returncode==0
env=os.environ.copy();n=int(env.get('GIT_CONFIG_COUNT','0'))
env.update({'GIT_CONFIG_COUNT':str(n+1),'GIT_CONFIG_KEY_'+str(n):'http.https://github.com/.extraheader','GIT_CONFIG_VALUE_'+str(n):'AUTHORIZATION: basic '+base64.b64encode(('x-access-token:'+env['GH_TOKEN']).encode()).decode(),'GIT_TERMINAL_PROMPT':'0'})
url='https://github.com/isogeny-labs/cryptanalysis.git'
out=Path('/workspace/scratch/ct236-historical-source-new-tag-01');out.mkdir()
ref='refs/tags/chained-transfer-lp-post-character-source-20261116-'+head[:12]
before=subprocess.run(['git','ls-remote','--tags',url,ref],cwd=r,env=env,capture_output=True,timeout=60)
(out/'before.txt').write_bytes(before.stdout+before.stderr)
assert before.returncode==0 and not before.stdout
pub=subprocess.run(['git','push','--no-force','--porcelain',url,head+':'+ref],cwd=r,env=env,capture_output=True,timeout=180)
(out/'actual-push.log.xz').write_bytes(lzma.compress(pub.stdout+pub.stderr));(out/'actual-push.exit').write_text(str(pub.returncode)+'\n')
assert pub.returncode==0
after=subprocess.run(['git','ls-remote','--tags',url,ref],cwd=r,env=env,capture_output=True,timeout=60)
(out/'after.txt').write_bytes(after.stdout+after.stderr)
assert after.returncode==0 and after.stdout.decode().split()[0]==head
(out/'receipt.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),source=head,new_tag=ref,actual_new_tag_push=0,exact_readback=True,normal_branch_publication_actual_exit=q.returncode,no_force=True,fresh_CI_unobserved=True),indent=2)+'\n')
print('new-tag0',ref,flush=True)

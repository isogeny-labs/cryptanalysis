"""Publish original compiler source dependencies and complete metadata."""
from pathlib import Path
from datetime import datetime, timezone
import base64, hashlib, json, lzma, os, shutil, subprocess

r = Path('/workspace/cryptanalysis')
base = 'fc52af709672e5503d78e322183da4ae72f16cde'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=r, text=True).strip() == base
p = r / 'experiments/chained-transfer-relation-diagnostics-03'
g = p / 'evidence/source-publication-governance-01'
g.mkdir()
shutil.copyfile(__file__, g / 'original-command.py')
scope = ['experiments/chained-transfer-lp-presentation-01', str(p.relative_to(r)), 'pcc/claims', 'pcc/ledger.jsonl', 'docs/session-logs/2026-11-16.md', '.resume/RESUME.md']

def paths():
    return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0')) | set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))) - {b''})

def run(name, command):
    q = subprocess.run(command, cwd=r, capture_output=True)
    (g / (name+'.txt.xz')).write_bytes(lzma.compress(q.stdout+q.stderr))
    (g / (name+'.exit')).write_text(str(q.returncode)+'\n')
    print(name, q.returncode, flush=True)
    assert q.returncode == 0

assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','scripts','suite','.github/workflows','.artifacts/config.json','experiments/chained-transfer-lp-presentation-01/native','experiments/chained-transfer-lp-presentation-01/lean','experiments/chained-transfer-lp-presentation-01/matrix-01'],cwd=r)
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base])
run('authored-prose',['python3','tools/pcc/pcc.py','lint-prose',*[n.decode() for n in paths() if n.endswith(b'.md')]])
run('all1605-original-source-guards',['sha256sum','--check','experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256'])
run('benchrec',['python3','tools/benchrec.py','gate'])
run('wiring',['python3','tools/artifacts/wire_workflows.py','--check'])
run('report-Python',['python3','tools/ci/check_report_graph_python.py'])

def stage():
    names=paths()
    f=Path('/workspace/scratch/ct159-source.paths0')
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
run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Source preparation03 governance for original CI dependencies1fd1d9: ledger, authored prose, full1605 original guards, benchrec, workflow wiring, report Python, cached whitespace and original artifact policy actual0. All new attestation subjects byte exact and staged or already parented. Existing mathematical sources and original drivers/workflows/tools/policy unchanged; exactly21 original captured source dependencies added at their declared paths. Cold fixture publication7ba01c preserved. No full historical mathematical population, timing or paid job; normal source publication and fresh actual CI follow.']
for f in sorted(g.iterdir()):
    cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
stage()
subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True)
subprocess.run(['git','commit','--quiet','-m','research: publish exact compiler prerequisites before original diagnostic guards'],cwd=r,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()
print(claim,head,flush=True)
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-lp-presentation-20261115','/workspace/scratch/ct159-exact-source-normal-publication-01'],cwd=r,capture_output=True)
Path('/workspace/scratch/ct159-exact-source-normal-caller01.txt').write_bytes(q.stdout+q.stderr)
print('normal-publication',q.returncode,flush=True)
assert q.returncode==0
env=os.environ.copy();n=int(env.get('GIT_CONFIG_COUNT','0'))
env.update({'GIT_CONFIG_COUNT':str(n+1),'GIT_CONFIG_KEY_'+str(n):'http.https://github.com/.extraheader','GIT_CONFIG_VALUE_'+str(n):'AUTHORIZATION: basic '+base64.b64encode(('x-access-token:'+env['GH_TOKEN']).encode()).decode(),'GIT_TERMINAL_PROMPT':'0'})
url='https://github.com/isogeny-labs/cryptanalysis.git'
out=Path('/workspace/scratch/ct159-exact-source-new-tag-01');out.mkdir()
ref='refs/tags/chained-transfer-exact-CI-sources-20261116-'+head[:12]
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

"""Checkpoint tested generic foundation and inspected report; no population run."""
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,json,lzma,os,shutil,subprocess
r=Path('/workspace/cryptanalysis');p=r/'experiments/chained-transfer-lp-presentation-01';base='6bb2516b64e7112356e58e45da590d60591c0461';assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
claim='previously recorded inspected foundation report'
g=p/'evidence/foundation-source-governance-02';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=[p.relative_to(r).as_posix(),'pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-15.md','.resume/RESUME.md','.gitattributes']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(n,c):
 q=subprocess.run(c,cwd=r,capture_output=True);b=q.stdout+q.stderr;(g/(n+('.txt.xz'if len(b)>60000 else'.txt'))).write_bytes(lzma.compress(b)if len(b)>60000 else b);(g/(n+'.exit')).write_text(str(q.returncode)+'\n');print(n,q.returncode,flush=True);assert q.returncode==0
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[n.decode()for n in paths()if n.endswith(b'.md')]]);run('whole1605-source-guards',['sha256sum','--check','experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256']);run('benchrec',['python3','tools/benchrec.py','gate']);run('report-Python',['python3','tools/ci/check_report_graph_python.py']);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('native-format',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',str(p/'native/src/lib.rs'),str(p/'native/src/bin/identities.rs')])
def stage():
 names=paths();f=Path('/workspace/scratch/ct137-foundation-source.paths0');f.write_bytes(b'\0'.join(n for n in names if n!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(names)
 for n in selected:
  if n.startswith(b'pcc/claims/'):
   for proof in json.loads((r/n.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     s=proof['subject'];assert hashlib.sha256((r/s['path']).read_bytes()).hexdigest()==s['sha256'];assert s['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+s['path']],cwd=r,capture_output=True).returncode==0
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree]);stage()
subprocess.run(['git','commit','--quiet','-m','research: prove finite LP projection and certify known cancellation identities'],cwd=r,check=True);head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip();print('source',head,'report',claim,flush=True)
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-lp-presentation-20261115','/workspace/scratch/ct137-foundation-source-normal-publication-01'],cwd=r,capture_output=True);Path('/workspace/scratch/ct137-foundation-source-normal-publication-caller01.txt').write_bytes(q.stdout+q.stderr);print('normalbranchpub',q.returncode,flush=True)
env=os.environ.copy();n=int(env.get('GIT_CONFIG_COUNT','0'));env.update({'GIT_CONFIG_COUNT':str(n+1),'GIT_CONFIG_KEY_'+str(n):'http.https://github.com/.extraheader','GIT_CONFIG_VALUE_'+str(n):'AUTHORIZATION: basic '+base64.b64encode(('x-access-token:'+env['GH_TOKEN']).encode()).decode(),'GIT_TERMINAL_PROMPT':'0'});url='https://github.com/isogeny-labs/cryptanalysis.git';out=Path('/workspace/scratch/ct137-foundation-source-new-tag-publication-01');out.mkdir();ref='refs/tags/chained-transfer-lp-foundation-20261115-'+head[:12]
before=subprocess.run(['git','ls-remote','--tags',url,ref],cwd=r,env=env,capture_output=True,timeout=60);(out/'before.txt').write_bytes(before.stdout+before.stderr);assert before.returncode==0 and not before.stdout
push=subprocess.run(['git','push','--no-force','--porcelain',url,head+':'+ref],cwd=r,env=env,capture_output=True,timeout=180);(out/'actual-push.log.xz').write_bytes(lzma.compress(push.stdout+push.stderr));(out/'actual-push.exit').write_text(str(push.returncode)+'\n');assert push.returncode==0
after=subprocess.run(['git','ls-remote','--tags',url,ref],cwd=r,env=env,capture_output=True,timeout=60);(out/'after.txt').write_bytes(after.stdout+after.stderr);assert after.returncode==0 and after.stdout.decode().split()[0]==head
(out/'receipt.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),source=head,new_tag=ref,new_tag_push=0,exact_readback=True,branch_publication_actual_exit=q.returncode,no_force=True,no_fixed_population_run=True),indent=2)+'\n');print('newsource-tag0',ref,flush=True)

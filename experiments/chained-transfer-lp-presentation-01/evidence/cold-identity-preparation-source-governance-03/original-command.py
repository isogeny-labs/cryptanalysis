"""Checkpoint cold fixture preparation and whole failed CI evidence."""
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,json,lzma,os,shutil,subprocess
r=Path('/workspace/cryptanalysis');p=r/'experiments/chained-transfer-lp-presentation-01';base='66d2b8664633ef1a6bf0bc7ceaf7f9e9b2539f2a'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
g=p/'evidence/cold-identity-preparation-source-governance-03';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=[p.relative_to(r).as_posix(),'pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-16.md','.resume/RESUME.md','.gitattributes']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(n,c):
 q=subprocess.run(c,cwd=r,capture_output=True);b=q.stdout+q.stderr;(g/(n+'.txt.xz')).write_bytes(lzma.compress(b));(g/(n+'.exit')).write_text(str(q.returncode)+'\n');print(n,q.returncode,flush=True);assert q.returncode==0
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','scripts','suite','.github/workflows','.artifacts/config.json',str(p/'native'),str(p/'lean'),str(p/'matrix-01')],cwd=r)
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base])
rawprefix=(p.relative_to(r)/'evidence/whole-development-CI-missing-original-identity-fixture-01/all85-original-members').as_posix()+'/'
mds=[n.decode() for n in paths() if n.endswith(b'.md')]
raw=[n for n in mds if n.startswith(rawprefix)];authored=[n for n in mds if n not in raw]
assert set(n[len(rawprefix):] for n in raw)=={'entire-matrix-source/README.md','original-Consumer-proof-tools/README.md','original-Root-proof-tools/README.md'}
claim=json.loads((r/'pcc/claims/PCC-20261116-bec33b.json').read_text())
for proof in claim['proofs']:
 if proof.get('kind')=='attestation':
  s=proof['subject'];assert hashlib.sha256((r/s['path']).read_bytes()).hexdigest()==s['sha256']
q=subprocess.run(['python3','tools/pcc/pcc.py','lint-prose',*raw],cwd=r,capture_output=True)
(g/'captured-original-prose.txt.xz').write_bytes(lzma.compress(q.stdout+q.stderr));(g/'captured-original-prose.exit').write_text(str(q.returncode)+'\n');assert q.returncode==1
(g/'prose-scope.json').write_text(json.dumps(dict(authored=authored,captured_original=raw,captured_original_actual_exit=1,captured_original_expected_exit=1,all_bec33b_original_attestations_byte_exact=True,no_original_readme_edits=True),indent=2)+'\n')
run('prose',['python3','tools/pcc/pcc.py','lint-prose',*authored]);run('all1605-original-source-guards',['sha256sum','--check','experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256']);run('benchrec',['python3','tools/benchrec.py','gate']);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('report-Python',['python3','tools/ci/check_report_graph_python.py']);run('build-preparer-format',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',str(p/'native/build.rs')])
def stage():
 names=paths();f=Path('/workspace/scratch/ct154-cold-source.paths0');f.write_bytes(b'\0'.join(n for n in names if n!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(names)
 for n in selected:
  if n.startswith(b'pcc/claims/'):
   for proof in json.loads((r/n.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     s=proof['subject'];assert hashlib.sha256((r/s['path']).read_bytes()).hexdigest()==s['sha256'];assert s['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+s['path']],cwd=r,capture_output=True).returncode==0
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
c=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Coldoriginalidentityfixturepreparation4270a0 sourcegovernance: ledger/authored-prose/all1605/benchrec/wiring/reportPython/buildRustfmt/cachedwhitespace/artifact0; captured original README lint1 expected and whole-output-preserved; all original bec33b bytes exact; everynewsubjectexactstagedorparented. Onlynewnativebuild.rs datapreparation, existingnative/Lean/matrix/workflow/tools/policybyteexact. WholefailedCIbec33b/all85members preserved, cold24tests0andwholebadfixture1withoutoverwrite/runtimecustody retained. Normalnewsourcepublication/freshCI follows; no fixed60EKS/paidbuildjob/solve/cost/global/numericalLean/signedclaim.']
for f in sorted(g.iterdir()):c+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(c,cwd=r,text=True).strip();stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: restore immutable identity fixture before cold native compilation'],cwd=r,check=True);head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip();print(claim,head,flush=True)
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-lp-presentation-20261115','/workspace/scratch/ct154-cold-source-normal-publication-01'],cwd=r,capture_output=True);Path('/workspace/scratch/ct154-cold-source-normal-publication-caller01.txt').write_bytes(q.stdout+q.stderr);print('normalbranchpub',q.returncode,flush=True)
env=os.environ.copy();n=int(env.get('GIT_CONFIG_COUNT','0'));env.update({'GIT_CONFIG_COUNT':str(n+1),'GIT_CONFIG_KEY_'+str(n):'http.https://github.com/.extraheader','GIT_CONFIG_VALUE_'+str(n):'AUTHORIZATION: basic '+base64.b64encode(('x-access-token:'+env['GH_TOKEN']).encode()).decode(),'GIT_TERMINAL_PROMPT':'0'});url='https://github.com/isogeny-labs/cryptanalysis.git';out=Path('/workspace/scratch/ct154-cold-source-new-tag-publication-01');out.mkdir();ref='refs/tags/chained-transfer-lp-cold-fixture-20261116-'+head[:12]
before=subprocess.run(['git','ls-remote','--tags',url,ref],cwd=r,env=env,capture_output=True,timeout=60);(out/'before.txt').write_bytes(before.stdout+before.stderr);assert before.returncode==0 and not before.stdout
pub=subprocess.run(['git','push','--no-force','--porcelain',url,head+':'+ref],cwd=r,env=env,capture_output=True,timeout=180);(out/'actual-push.log.xz').write_bytes(lzma.compress(pub.stdout+pub.stderr));(out/'actual-push.exit').write_text(str(pub.returncode)+'\n');assert pub.returncode==0
after=subprocess.run(['git','ls-remote','--tags',url,ref],cwd=r,env=env,capture_output=True,timeout=60);(out/'after.txt').write_bytes(after.stdout+after.stderr);assert after.returncode==0 and after.stdout.decode().split()[0]==head
(out/'receipt.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),source=head,new_tag=ref,actual_new_tag_push=0,exact_readback=True,normal_branch_publication_actual_exit=q.returncode,no_force=True,fresh_CI_unobserved=True),indent=2)+'\n');print('newsource-tag0',ref,flush=True)

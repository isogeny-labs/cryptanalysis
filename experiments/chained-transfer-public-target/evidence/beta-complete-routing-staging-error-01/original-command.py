"""Repository governance and normal publication; no scientific calculations."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess,sys
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
label,message=sys.argv[1:3];base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()
g=s/'evidence'/('beta-'+label+'-governance-01');g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scopes=[str(s.relative_to(r)),'.github/workflows/chained-transfer-beta-rational-lift.yml','.github/workflows/chained-transfer-beta-complete.yml','.gitattributes','docs/research-artifacts/chained-transfer/beta-complete-rational-01','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-14.md','.resume/RESUME.md','problems/chained-transfer-odd-product-kernel-and-odd-factor.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scopes],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(n,c):
 q=subprocess.run(c,cwd=r,capture_output=True);raw=q.stdout+q.stderr;(g/(n+'.txt.xz'if len(raw)>60000 else n+'.txt')).write_bytes(lzma.compress(raw)if len(raw)>60000 else raw);(g/(n+'.exit')).write_text(str(q.returncode)+'\n');print(n,q.returncode,flush=True);assert q.returncode==0,raw[:2000]
for n,p in [('norm784','ci_norm_sampling/reference-01.sha256'),('arithmetic22','arithmetic-audit/reference-03.sha256')]:run(n,['sha256sum','--check',str(s/p)])
ref=s/'ci_beta_lift'/('reference-02.sha256'if(s/'ci_beta_lift/reference-02.sha256').exists()else'reference-01.sha256')
run('beta-reference',['sha256sum','--check',str(ref)])
run('complete-reference',['sha256sum','--check',str(s/'ci_beta_complete/reference-01.sha256')])
run('complete-shell',['bash','-n',str(s/'ci_beta_complete/check.sh')])
run('complete-actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-beta-complete.yml'])
run('complete-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'beta-complete-evaluator/src').rglob('*.rs'))]])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]])
run('whitespace',['git','diff','--check','--',*scopes]);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-beta-rational-lift.yml']);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate']);run('reportPython',['python3','tools/ci/check_report_graph_python.py'])
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','scripts','suite'],cwd=r)
def stage():
 ps=paths();p=Path('/workspace/scratch/ct73-'+label+'.paths0');p.write_bytes(b'\0'.join(x for x in ps if x!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(p),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for name in selected:
  if name.startswith(b'pcc/claims/'):
   for proof in json.loads((r/name.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     v=proof['subject'];assert hashlib.sha256((r/v['path']).read_bytes()).hexdigest()==v['sha256']
     if v['path'].encode()not in selected and subprocess.run(['git','cat-file','-e',base+':'+v['path']],cwd=r,capture_output=True).returncode!=0:
      allowed='experiments/chained-transfer-public-target/reports/beta-complete-rational-01/complete-diagram.png';assert v['path']==allowed,v['path']
      png=r/allowed;manifest=png.parent/'.artifacts.json';ignore=png.parent/'.gitignore';actual=Path('/workspace/crypto/research/chained_jacobian_transfers_20261110/evidence/public-n4-complete-beta-png-handoff-01/.artifacts.json')
      entry=json.loads(manifest.read_text())['files'][png.name];assert entry==json.loads(actual.read_text())['files'][png.name];assert entry==dict(bytes=png.stat().st_size,sha256=v['sha256'])
      assert manifest.relative_to(r).as_posix().encode()in selected and ignore.relative_to(r).as_posix().encode()in selected
      assert subprocess.run(['git','check-ignore','-q',allowed],cwd=r).returncode==0
      assert json.loads((r/'experiments/chained-transfer-public-target/evidence/genuine-complete-beta-PNG-publication-01/publication.json').read_text())['bot']=='e149ba385fd3539a58fada68f279e9f1b30f898e'
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),base=base,label=label,all_recorded_governance_exits=0,reference=ref.relative_to(r).as_posix(),exact_subject_hash_and_staging_checked=True,only_external_subject="none; PNG subject now tracked relative link to canonical docs original published object",original_tools_scripts_suite_unchanged=True,scope='unsigned governance; no mathematical or execution signed standing'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Beta '+label+' checkpoint governance: original784/current arithmetic22/current versioned beta plus881complete source guards0/shell/actionlint/rustfmt0; ledger/prose/working+cachedwhitespace/actionlint/artifact-wiring/benchrec/reportPython/artifact0; all new attestation subjects exact hashes and staged/inparent or exactsinglePNGoriginalgenuine-manifest projection withmanifest+ignorestaged; original tools/scripts/suite unchanged. Unsigned governance only, no CI pass inference or mathematical standing.']
for f in sorted(g.iterdir()):cmd+=['--proof','attestation:'+str(f.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();print(cl,flush=True);selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m',message],cwd=r,check=True);head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip();print(head,len(selected),flush=True)
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-public-target-20261113','/workspace/scratch/ct73-'+label+'-publication-01'],cwd=r,capture_output=True);Path('/workspace/scratch/ct73-'+label+'-publication-caller.txt').write_bytes(q.stdout+q.stderr);print('normalpub',q.returncode,flush=True);assert q.returncode==0

"""Publish finished failure evidence and prospective contract; leave unfinished CI sources unstaged."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess,os
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='2920181e2a8bcae3238f14007660d1a61480555f'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
g=s/'evidence/cross-run-comparison-protocol02-governance-01';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=[(s/'ORIGINAL_FIXED_IC_CROSS_RUN_COMPARISON_02.md').relative_to(r).as_posix(),(s/'evidence/original-fixed-IC-CI-local-fixture-failure-01').relative_to(r).as_posix(),(s/'evidence/original-fixed-IC-CI-historical-timing-failure-02').relative_to(r).as_posix(),g.relative_to(r).as_posix(),(s/'CHECKPOINT.md').relative_to(r).as_posix(),(s/'RESEARCH_QUEUE.md').relative_to(r).as_posix(),'.resume/RESUME.md','docs/session-logs/2026-11-15.md','pcc/ledger.jsonl','pcc/claims']
def paths():return sorted(set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))-{b''})
def run(name,args):
    p=subprocess.run(args,cwd=r,capture_output=True);b=p.stdout+p.stderr;(g/(name+'.txt.xz'if len(b)>60000 else name+'.txt')).write_bytes(lzma.compress(b)if len(b)>60000 else b);(g/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,b[:1000]
assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=r)
run('prior1487',['sha256sum','--check',str(s/'original-fixed-model-sampler-01/frozen-prior-inputs-01.sha256')])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]])
run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('reportPython',['python3','tools/ci/check_report_graph_python.py'])
def stage():
    ps=paths();f=Path('/workspace/scratch/ct100-comparison-protocol02.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
    selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
    assert not any(p.startswith(b'experiments/chained-transfer-public-target/ci_original_fixed_ic/')or p==b'.github/workflows/chained-transfer-original-fixed-ic.yml'for p in selected)
    for name in selected:
        if name.startswith(b'pcc/claims/'):
            for proof in json.loads((r/name.decode()).read_text()).get('proofs',[]):
                if proof.get('kind')=='attestation':
                    v=proof['subject'];assert hashlib.sha256((r/v['path']).read_bytes()).hexdigest()==v['sha256'];assert v['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+v['path']],cwd=r,capture_output=True).returncode==0
    return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),base=base,all_recorded_governance_exits=0,new_subjects_exact_and_staged_or_parented=True,original1487guards_pass=True,only_finished_failure_evidence_and_prospective_contract_staged=True,unfinished_new_CI_workflow_and_driver_explicitly_unstaged=True,scope='unsigned prospective operational checkpoint, not a CI pass'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Prospective comparison02 governance: original1487guards/ledger/prose/working-cachedwhitespace/wiring/reportPython/artifact0; exact new subjects staged or inparent. Only finished failure27191b/e4ff83 and prospectiveb5e431 with mutable checkpoint notes are committed; unfinished new CI driver/workflow explicitly unstaged. All actual source/raw/fullprepared/runtime/failure outputs held; original auditors/native/fixtures unchanged. New historical verifier/retry03 not implemented/run before this checkpoint. Unsigned operational publication.']
for p in sorted(g.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: preserve CI comparison failures and freeze cross-run timing contract'],cwd=r,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip();print(claim,head,len(selected),flush=True)
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-public-target-20261113','/workspace/scratch/ct100-cross-run-comparison-protocol02-publication-01'],cwd=r,capture_output=True);Path('/workspace/scratch/ct100-cross-run-protocol02-publication-caller.txt').write_bytes(q.stdout+q.stderr);print('normalpub',q.returncode,flush=True);assert q.returncode==0

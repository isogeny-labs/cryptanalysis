"""Orchestration-only checkpoint through original repository gates."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='827b37b4b41e3ccd9d64364306d62c9197e26915'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
d=s/'evidence/completed-integration-governance-01';d.mkdir();shutil.copyfile(__file__,d/'original-command.py')
scope=[str(s.relative_to(r)),'.github/workflows/chained-transfer-completed-descent.yml','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd):
    p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr
    if len(raw)>60000:z=lzma.compress(raw);assert lzma.decompress(z)==raw;(d/(name+'.txt.xz')).write_bytes(z)
    else:(d/(name+'.txt')).write_bytes(raw)
    (d/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,raw.decode()[:1600]
protected=['tools','suite','experiments/chained-transfer-reference',str((s/'native').relative_to(r)),str((s/'v2').relative_to(r)),str((s/'rho-accessor').relative_to(r)),str((s/'prime-field').relative_to(r)),str((s/'ci_v2').relative_to(r)),str((s/'completed-descent').relative_to(r)),'.github/workflows/chained-transfer-reference.yml','.github/workflows/chained-transfer-public-target.yml','.github/workflows/chained-transfer-completed-v2.yml','.github/workflows/pcc-gate.yml']
assert not subprocess.check_output(['git','diff','--name-only',base,'--',*protected],cwd=r)
lines=(s/'ci_completed/reference-01.sha256').read_text().splitlines();assert len(lines)==483
entry=f'''\n## {datetime.now(timezone.utc).isoformat()} — completed-descent independent integration source\n\nCandidate source827b37b4/treecb098007/parent093/93paths/d20a94 ACTUALLYnormalpublished0. Native5ff070 allfive candidate+baselineanswers/TENpairedattempts/2307guards0,reportef02ef TWO52101pagesALLinspected;alloriginal firstrelationfailures retained. Prospective74e00a waspublished093BEFOREcode/7823d2. Parentfull0815f7/CIb6c1db25native17digests settled. [pcc:unverified]\n\nNewaf83e1 ci_completed harness/thirdreadonlyworkflow pins483inputs347producer+136consumer;fiveorderedfetch/format/compile/native/JSON phasepairs0/0. ALL17nativeJSON equalnative01 excludingONLYrecordedbaseline/candidatewall+walltotal/rawretained. Fouractualnegativeadmission2/nooutput/restored and2100s cleanfull/freshoutsidecache/exact3dphysicalproducer stillpending;CIautoPRsync/exacthead. No scientific/native/verifier/oldworkflow edits. Afteractualnormalpublication materializecleanphysicalGit siblings fromthis483manifest+itself(484outerguards),runallfourcontrols,launchfull;collectexactnewCIWHOLElogs/nativeJSON/digests/guards. [pcc:unverified]\n\nNO nativeprocess in flight. AllNative5ff/parentfull andCIterminal0. Nextgenuinearchivehandoff mustinclude Native03,parentfull,V2partialCI01+complete02,candidateunit andnewcandidatefull/CI,allwholeindices;rootstale2283mapnotforfutureFF. Afterlaunchingisolatedcandidatefull,freeze actualJac(F223)two-primary structure scout beforecode;existingMumfordgenus2Richelot andprimefield-onlyplanePicard aredifferentengines,do notassumegenus3isogeny API. No costS/ratio/advantage;S3/livebudget/strongestrefs/fullformalgeometry/rootauthenticfixture/mainmerge/signing/frozenledger/reviews/vault/KB gaps persist. Nextglobal17:45UTCunlessconcretesignal. [pcc:unverified]\n'''
for p in [s/'CHECKPOINT.md',r/'.resume/RESUME.md',r/'docs/session-logs/2026-11-13.md']:
    with p.open('a')as f:f.write(entry)
run('parent468',['sha256sum','--check',str((s/'ci_v2/reference-01.sha256').relative_to(r))])
run('new483',['sha256sum','--check',str((s/'ci_completed/reference-01.sha256').relative_to(r))])
run('shell',['bash','-n',str(s/'ci_completed/check.sh')])
run('python-syntax',['python3','-m','py_compile',str(s/'ci_completed/replay_io.py'),str(s/'ci_completed/freeze_reference.py')])
run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-completed-descent.yml'])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base])
run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]])
run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
    ps=paths();f=Path('/workspace/scratch/ct58-completed-integration.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
    selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
    for p in ps:
        if p.startswith(b'pcc/claims/'):
            for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
                if proof.get('kind')=='attestation':
                    x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'];assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0
    return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(d/'custody.json').write_text(json.dumps(dict(base=base,all_scientific_inputs_verifiers_current_workflows_unchanged=True,source483_checks=0,originalledger_prose_whitespace_wiring_benchrec_actionlint_artifact=0,newsubject_hash_and_staging=True,fouractualadmission_full_and_ownCI='not yetrun',phase_policy='all5native/tee0/0;all17JSON exceptONLYrecordedwall/walltotal',scope='orchestration only;no newcost/fullformal claim'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Completed-descent integration sourcegovernanceown827:allscientific/native/verifier/currentworkflows unchanged;parent468/new483sourcehashes0. Originalledger/prose/workingcachedwhitespace/wiring/benchrec/actionlint/artifact0/newsubjecthashstaging. Newthirdreadonlyworkflow/fivepositivephasepairs/all17JSON compareONLYrecordedwallwalltotal excluded;fouractualadmission/2100sfreshcleanfull/exact3d/ownCIpending. Candidate5ff070 correctnessonly;no newcost/fullformalgeometry orspeedclaim.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','ci: replay completed-transfer individual descent with exact source guards'],cwd=r,check=True)
print(cl,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)

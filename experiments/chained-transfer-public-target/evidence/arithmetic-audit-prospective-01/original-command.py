from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='21afb40f425f89774fe3eaf77695f5f30342a186';at=datetime.now(timezone.utc).isoformat()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
p=s/'evidence/arithmetic-audit-prospective-01';p.mkdir();shutil.copyfile(__file__,p/'original-command.py')
for f in Path('/workspace/scratch/ct72-arithmetic-literature-01').iterdir():
 if f.is_file():shutil.copyfile(f,p/f.name)
review={}
for name in ['.github/workflows/isolab-failure-diagnosis.yml','.github/workflows/isolab.yml','taskq/deploy/eks-karpenter/budget-change-20261103.json']:
 x=Path('/workspace/crypto')/name;review[name]=dict(sha256=hashlib.sha256(x.read_bytes()).hexdigest(),bytes=x.stat().st_size)
(p/'admission-review.json').write_text(json.dumps(dict(at=at,sources=review,observation='fixed diagnosis only names three historical jobs; no generic budget/capacity route; ordinary isolab builds unrelated images',live_budget_remainder='unknown',live_capacity='unknown',paid_builds_or_jobs_launched=0,local_development_only=True),indent=2)+'\n')
c=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Prospective arithmetic-audit protocol BEFORE tap code: consumer21af/originalproducer3d/frozen784+self785; isolated Git-blob materialization and pure leaf hooks, literal patches/all86 wholeJSON except only declared ATTEMPT walls, unchanged solver bodies/final checks/RNG/legacy counts. Deterministic source-level primitive counts separate from API/nested/legacy aggregates; completebackend inventory, native primitive controls and actual omitted-hook negative, fresh bounded development cache900+900s/2GiB and120scontrols. No hardware instruction count, pricing, stagewin or computationaladvantage; cold separatearms/strongestreferences/admission stillowed. Existing333af1/42073d/66da4b settled unsigned; all15FB30failures retained. Fixed diagnosticworkflow only historicaljobs, no generic livebudgetcapacity route; no paidlaunch. OriginalKB/leadwrapper127 receipts are accesslimits, no novelty/absence; vault locked.']
for f in [s/'ARITHMETIC_AUDIT_PROTOCOL_01.md',*sorted(p.iterdir())]:c+=['--proof','attestation:'+str(f.relative_to(r))]
claim=subprocess.check_output(c,cwd=r,text=True).strip();Path('/workspace/scratch/ct72-arithmetic-protocol.claim').write_text(claim+'\n');print(claim,flush=True)
state=f'''# Arithmetic audit continuation — {at}

Settled source21afb40f: native9bc5e6, independent785full333af1, own17CI42073d/327native/60unique62actualcanonical checks. Originalcheckpoint66da4b remote+localgate0 exactclean21af/all28members; latermetadata stale. All15FB30failedpairs preserved. Genuine243bb9/9a7cf7 all15objects8S3+7Git/guard09released; nextartifactFF fresh10. All claims unsigned. [pcc:unverified]

Next implement ARITHMETIC_AUDIT_PROTOCOL_01.md, prospective {claim}, after normalpublication: isolated original785blobclosure and purehookderivative, unchanged classsolvers, Rust primitive controls/native JSON comparator, ALL86records only existingwalls masked. Budget900sbuild900snative2GiB;120scontrols; dedicatedoutsidecache. Originalcheckpoint before experiment; unit checks development/no timingclaim. Currentdisk296MiB. No tap code yet. [pcc:unverified]

Livebudget/capacity unknown; fixedhistoricaldiagnosis andunrelatedisolabimageworkflows do not provide generaladmission. No paidlaunch. Needmatched testedimagebindingBOTHrepos/strongestICrho-precomp-fixedbase/coldonlinecost beforegain. Root124clock101/mainledger/signing/reviews/conflict/formalgeometry/logextension/vault8edec422locked/KB127 remain. Raw333/420/66 closedawaitnextgenuinebatch. Continueafterrung. [pcc:unverified]
'''
for f in [s/'RESEARCH_QUEUE.md',r/'.resume/RESUME.md']:
 f.write_text(state+'\n---\n\n'+f.read_text())
with (r/'docs/session-logs/2026-11-14.md').open('a') as f:
 f.write(f'''\n## {at} — prospective arithmetic coverage audit\n\n### What was done (commands, files, features)\nPublished-scope candidate is settled under333af1/42073d/66da4b: all785fullinputs/tennative-teepairs0/17sourceworkflows327native60unique62actualcanonicalchecks/exactclean21af originalcheckpointall28members. All unsigned. Prospective {claim} pins isolatedmaterialization, primitivehooks, unchangedoriginals/solverbody/RNG/finalchecks/all86wholeJSON andanalytic/copiednegativecontrols BEFORE code. [pcc:unverified]\n\n### Decisions made (and why)\nUse source-levelprimitivecounts separatelyfrom API/legacyaggregates and explicitunpricedwork; no newgeometrytheorem orcostclaim. NativeRustcontrols/replay; thin shellbuild/materialization. Existingfixeddiagnosisworkflow targetsoldjobs only; unrelatedisolabworkflow buildsimages. Livebudget/capacity unknown; no paidlaunch. [pcc:unverified]\n\n### Open threads (unfinished, pick up next time)\nNormalpublishprotocol andsettlement; implementnativeaudit immediately. UpdateGitHubcheckpoint/rootmetadata; freshoriginalcheckpoint beforeexperiments. Nextgenuinewhole333/420/66batchneedsNEWguard10. Completecoldonlinecost/strongestrefs/globalbeta/formalbridges remain. [pcc:unverified]\n\n### Errors (what went wrong, how it was handled)\nNo newscientificfailure. KB+leadwrapper127 retained; vaultlocked. Existingroot124clock101/mainledger/review/conflict preserved. Currentdisk296MiB; closedderivedcompiler cachesonly maybereclaimedwithreceipt. [pcc:unverified]\n''')
g=s/'evidence/arithmetic-audit-protocol-governance-01';g.mkdir()
scopes=[str(s.relative_to(r)),'docs/chained-transfer-checkpoint-transport/acceptance-03','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-14.md','problems/chained-transfer-new-jacobian-ic-cost-coverage.md','.resume/RESUME.md']
def paths():return sorted(set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scopes],cwd=r).split(b'\0'))-{b''})
def run(label,cmd):
 q=subprocess.run(cmd,cwd=r,capture_output=True);b=q.stdout+q.stderr;(g/(label+'.txt.xz' if len(b)>60000 else label+'.txt')).write_bytes(lzma.compress(b) if len(b)>60000 else b);(g/(label+'.exit')).write_text(str(q.returncode)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,b[:2000]
run('reference784',['sha256sum','--check',str((s/'ci_norm_sampling/reference-01.sha256').relative_to(r))])
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','scripts','.github/workflows'],cwd=r)
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[x.decode() for x in paths() if x.endswith(b'.md')]])
run('whitespace',['git','diff','--check','--',*scopes]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
 ps=paths();fn=Path('/workspace/scratch/ct72-arithmetic-protocol.paths0');fn.write_bytes(b'\0'.join(x for x in ps if x!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(fn),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''}
 assert selected==set(ps),(len(selected),len(ps))
 for path in selected:
  if path.startswith(b'pcc/claims/'):
   for proof in json.loads((r/path.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'];assert x['path'].encode() in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0
 return selected
stage();run('reportPython',['python3','tools/ci/check_report_graph_python.py']);run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(base=base,prospective_claim=claim,settlement=['333af1','42073d','66da4b'],all784_frozen_source_bytes_unchanged=True,source_tools_workflows_unchanged=True,all_governance_actual_exit=0,new_subject_hashes_and_staging_checked=True,next='normalpublish then implement isolated audit withoutwaiting',scope='unsigned development/completecostunknown/no advantage'),indent=2)+'\n')
c=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Arithmetic audit prospective checkpoint governance: settlement333af1/42073d/66da4b and prospective protocol committed before any tapcode. Original784inputhashes unchanged; originaltools/scripts/workflows untouched; originalledger/prose/working+cachedwhitespace/wiring/benchrec/reportPython/artifact checks all0; newsubject hashes andstaging checked. Unsigned development only/no costgain/newbenchmark/admission/mergewaiver.']
for f in sorted(g.iterdir()):c+=['--proof','attestation:'+str(f.relative_to(r))]
cl=subprocess.check_output(c,cwd=r,text=True).strip();Path('/workspace/scratch/ct72-arithmetic-protocol-governance.claim').write_text(cl+'\n');stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: settle exact sampling replay and freeze arithmetic audit'],cwd=r,check=True)
print(subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),flush=True)

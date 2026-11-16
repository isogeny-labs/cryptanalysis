"""Additive native/proof replay integration; data custody remains explicit."""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,hashlib,lzma,shutil
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='6ccd4334ae64e1a3090d6e9a8c19dcc64b0c5229'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
d=s/'evidence/two-primary-integration-governance-01';d.mkdir();shutil.copyfile(__file__,d/'original-command.py')
source=Path('/workspace/scratch/ct59-two-primary-source-publication-01');pub=s/'evidence/two-primary-normal-publication-01';pub.mkdir()
enc=[]
for p in source.iterdir():
 raw=p.read_bytes()
 if p.suffix=='.log':
  z=lzma.compress(raw);assert lzma.decompress(z)==raw;(pub/(p.name+'.xz')).write_bytes(z);enc.append(dict(raw=p.name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),stored=p.name+'.xz',roundtrip=True))
 else:shutil.copyfile(p,pub/p.name)
(pub/'lossless-encodings.json').write_text(json.dumps(enc,indent=2)+'\n')
handoff=json.loads(Path('/workspace/crypto/research/chained_jacobian_transfers_20261110/evidence/public-n4-completed-raw-handoff-01/handoff.json').read_text());pending=set()
for row in handoff['attempts']:
 for name,size,digest in [('whole-raw.tar.xz',row['archive_bytes'],row['archive_sha256']),('members.json.xz',row['complete_index_xz_bytes'],row['complete_index_xz_sha256'])]:
  p=s/'evidence'/('closed-ct59-'+row['label'])/name;assert p.stat().st_size==size and hashlib.sha256(p.read_bytes()).hexdigest()==digest
  if size>65536:pending.add(str(p.relative_to(r)).encode())
assert len(pending)==13
(d/'pending-data.json').write_text(json.dumps(dict(paths=[x.decode()for x in sorted(pending)],scope='13 policy-eligible large raw objects physically retained/untracked here, owned root genuine publisher inprogress; custody and7smallwholeobjects in this checkpoint; no remoteavailability or policywaiver asserted'),indent=2)+'\n')
scope=[str(s.relative_to(r)),'.github/workflows/chained-transfer-two-primary.yml','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted(((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})-pending)
def run(name,cmd):
 p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr
 if len(raw)>60000:(d/(name+'.txt.xz')).write_bytes(lzma.compress(raw))
 else:(d/(name+'.txt')).write_bytes(raw)
 (d/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,raw.decode(errors='replace')[:1800]
protected=['tools','suite','experiments/chained-transfer-reference']+[str((s/n).relative_to(r))for n in ['native','v2','rho-accessor','prime-field','completed-descent','two-primary','ci_v2','ci_completed']]+['.github/workflows/'+n for n in ['chained-transfer-reference.yml','chained-transfer-public-target.yml','chained-transfer-completed-v2.yml','chained-transfer-completed-descent.yml','pcc-gate.yml']]
assert not subprocess.check_output(['git','diff','--name-only',base,'--',*protected],cwd=r)
guard=json.loads(Path('/workspace/crypto/research/chained_jacobian_transfers_20261110/evidence/public-n4-completed-current-guard-04/current-inputs.json').read_text());assert len(guard)==2334 and all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in guard.items())
entry=f'''\n## {datetime.now(timezone.utc).isoformat()} — own two-primary independent replay integration\n\nSource6ccd4334/140paths/a9893d normalpublication0. Plan4fef28 precedes additive ci_two_primary and separateworkflow;502portableinputs/347producer plusmanifestself. Eleven positive native+tee phases requireoneunfilteredactualtest/all4wholeJSON/bothoriginalfourtheoremgates/4exactPCCbindings. Fouractualadmissioncontrols/cleanphysicalfull/ownCI remainpending, not reported as complete. Alloldscientificsources/workflows/verifiers unchanged. [pcc:unverified]\n\nAllTENclosedrawtrees andTENcompleteindices packaged/everymemberhashroundtrip;rootcbab2b5d/47paths/5a6a22 normallypublished0. Actualartifactpublisher43453551818 observedinprogress once;13largeobjects genuineavailabilitypending,7smallwholeobjects ordinaryGit. Consumer13largephysicalfilesstayuntracked untilgenuineprojection;thiscommit recordsallcustodymetadata/claims/smallobjectswithout availabilitywaiver. Freshguard04/2334 actualselectedinputshelduntilexactbotFF/finalguards. Do notedit selectednative/Lean/CIbytes;cleanindependentfullusesphysicalGitclones. [pcc:unverified]\n\nNEXT: normalpublishthisintegration, materialize502+1 physicalsourceclosure atnewHEAD/pinned3dproducer, fouractualadmissionchecks andoriginalfull. Thenactualpublisherlog/remote-byte verification/exactFF/genuineprojection; nextcoordinateconstructionoverF223^6. Originalbudget/checkpoint/fullcost/geometricformal/main/globalfixture/vault/KB gapsremain. Newtwo-primary KBsearchesfailed127(executableabsent), retainwithoutabsenceinference. [pcc:unverified]\n'''
for p in [s/'CHECKPOINT.md',r/'.resume/RESUME.md',r/'docs/session-logs/2026-11-13.md']:
 with p.open('a')as f:f.write(entry)
for name,ref in [('old483','ci_completed/reference-01.sha256'),('new502','ci_two_primary/reference-01.sha256')]:run(name,['sha256sum','--check',str((s/ref).relative_to(r))])
run('shell',['bash','-n',str(s/'ci_two_primary/check.sh')]);run('python-syntax',['python3','-m','py_compile',str(s/'ci_two_primary/replay_io.py'),str(s/'ci_two_primary/freeze_reference.py')]);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-two-primary.yml'])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]]);run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
 ps=paths();f=Path('/workspace/scratch/ct59-two-primary-integration.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps) and selected.isdisjoint(pending)
 for p in ps:
  if p.startswith(b'pcc/claims/'):
   for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'];assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(d/'custody.json').write_text(json.dumps(dict(base=base,all2334_current_inputs_unchanged=True,all_old_scientific_sources_workflows_verifiers_unchanged=True,old483_new502_reference_checks=0,original_governance_checks=0,new_subject_hash_and_staging=True,phase_policy='11positive0/0;all4completeJSON;bothoriginal4gates/4bindings',four_admission_full_CI='pending',new_closed_data='10wholearchives+10completeindices;13largependinggenuinepublication/7smallinGit;custodyretained'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Two-primary independentintegration own6ccd:all2334currenthashes andold483/new502referencechecks0;oldscience/workflows/verifiersunchanged. Originalledger/prose/workingcachedwhitespace/wiring/benchrec/actionlint/artifact0/newsubjecthashstaging. Newseparatereadonlyworkflow/11positivephases/all4wholeJSON/bothoriginal4gates/4exactbindings;actualfouradmission/cleanfull/ownCIpending. TENclosedcaptures/all20indicesobjects custodyretained;13largephysicalobjectsawaitgenuinepublisher/7smallwholeGit, noavailabilitywaiver. Guard04 held;no fullformal/newnondualmap/costclaim.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','ci: replay actual q223 two-primary tables and four original proof bindings'],cwd=r,check=True)
print(cl,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)

"""Metadata/source-publication checkpoint; no compiled source or verifier change."""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,hashlib,shutil,lzma
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-reference';base='069644bf59499e4172eb8bcdce5de8a6665da93f'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
current='''# Canonical norm — complete native/full replay; exact-source CI receipt next

Scientific069644bf/tree6eebf810/parentc3b/184paths ACTUALLYpublished normalGit0/e326f2;pre-codeprotocolac58df/c3b/ready1521 remainsparent1520. FULL02 COMPLETE7b231c exact069/3d,original09:26:05→09:33:59UTC,all23outer+20producerpairs[0,0]/native+driver+portable+cleanliness+outerguards0/all438outerinputs unchanged. ALL12consumerJSON equalunit02 75275f/ALL24producer equalc162f3/3consumerCLIgoldens byteexact/twoORIGINAL13declarationgates0trusted/13new+11producerexactbindings. No local nativeprocess active. [pcc:unverified]

Fullnative fixeddomains148/356/1324/allsource+allJac/both2compositions/odd37,89,331scalars andexplicitcompletion/origin/nonreduced controls pass. Formalfbfa81/c88b36 remains partial:actualgeometry bridges written/native. Generalalladmissiblechart invariance written;native alternate8typicalclasses perfield explicit. Native16c9f6 THREE48,914-bytePDFpages andfulladdendumd99c38 ONE36,300-bytepage ALLinspected/editable. Failedstatic/Lean/compatibility/full01missingcontrol/helper129+127 preserved;no criteriaweakened. [pcc:unverified]

ALLSIX initialnative raw archives ACTUALLYpublished48e581/7cd6ea;BOTHwholefullarchives ACTUALLYpublished82e079/1dd28b via43403906430/job131813350314 beforebf9/directparent923f/exact7paths,includingwholefull01failure668940/full02success676560. Originalsource-reviewb992d8 WHOLE69520-bytearchive isACTUALLYpublished via43405549514/job131818908219 before006db8ec/directparentbeb9/exact6paths;genuineconsumerentry5327f4. Original12primarysources includeexistingN4/B2 complete solver,itsplanted-scalarAPI andqmod12=7 fieldconstraint;legacytimings notnewlyvalidated. [pcc:unverified]

Frozen451bc2 precedesONLYonesortedexactprimaryPCCsubject added toBOTHexistingPCCgate/sign artifactpull steps. Originalverifier/keyring/trust andALL437focusedinputs/WHOLE7workflow unchanged. Firstwiring1 becausemanifestuntracked retainedf347b7;stageOWNgenuinemanifest thenORIGINALwiringcheck0. b992originalPCCverify2/not_covered unsignedstatement isexpectedstanding,NOTproofvalidation. No newPCC orartifactpolicy. Nativefullunchanged;datareadcontrolqualifiescurrentmetadata delta. [pcc:unverified]

Own43400864083 onexact069 initialALLSEVENjobsinprogress/new131803082298;terminalNOTyetretrieved,next10:16UTC. Routine09:45snapshotd0f30b:root923/open/mergeablefalse/no returnedreviewsorthreads;stacked1521/1520/1519readyopen/unmerged. Nextglobal13:45unlessconcretesignal. Mainfrozenledger/signing/conflict/review gates remain. Rootglobal NOTgreen/missingoriginalecbenchfixture;originalAWS2nocredentials/anonymous403/add561. KBtoolabsent/sourcefallback/vault8edec422locked/no subagents/no paidbenchmarkadmission. No measuredcomputationaladvantage. [pcc:unverified]

NEXT:publish this fullcheckpoint bynormalexpected-head Git;updatePR1521/3877/queue3904;retrieveown7CIat10:16/wholelogs andactualstatuses. Thenfreeze/publish nextsolveradapterprotocol BEFOREnewcases/code. ReuseexistingN4/B2 viaa public-target API andgeometricfield/model/basepoint bridges;keepoldfixedadapter admission/proofsubjects immutable,versionadditivecontrols asneeded. Preservewithdrawnoldsubgroup-enumeration result;no generic-DLP fallback or costinference fromlegacy reports.
'''
(s/'G3_NORM_CHECKPOINT.md').write_text(current)
(r/'.resume/RESUME.md').write_text(current+'\n---\n\n'+(r/'.resume/RESUME.md').read_text())
with (r/'docs/session-logs/2026-11-13.md').open('a') as f:f.write(f'''\n## {datetime.now(timezone.utc).isoformat()} — complete norm full/raw/source-review checkpoint (Codex)

### What was done (commands, files, features)
- FULL02 7b231c/whole345e25 COMPLETE exact069/3d/all438guards0/23outer+20innerpairs0/clean0/12+24native-recordequal/CLIbyteexact/proofs+bindings. BOTHwholefullarchives ACTUALLYpublished82e079/genuine1dd28b;SIXearlierarchives48e581/7cd6ea complete. ONE36,300-bytefullPDFpage ALLinspected,d99c38,earlier3nativepages immutable. Original12primarysourcesb992d8 WHOLE69520bytearchive actuallypublished006db8ec/genuine5327f4. [pcc:unverified]

### Decisions made (and why)
- Frozen451bc2 precedesONLYoneexactsubjectread inBOTHoldPCCgate/signjobs;verifier/trust/native437inputs/whole7workflow unchanged. Originalwiringfirst1/untrackedmanifest retainedf347b7;afterOWNmanifest staging originalcheck0. Originalb992verify2/not_covered keptasunsignedstanding,not mathematicalverification. Nativechecks needno rerunforreadonlydatafetch.

### Open threads (unfinished, pick up next time)
- Normalpublication/PRandqueueupdate;own7CI43400864083 exact069 terminalreadscheduled10:16/wholeevidence;nextsource-backedpublictargetN4/B2protocol BEFOREnewcases/code. Mainledger/signing/conflict/reviews/rootfixtureaccess andbenchmarkadmission separate.

### Errors (what went wrong, how it was handled)
- Originalfull01missingproducerreference/hashguards0,helper129/127 andmetadataartifactexpected4/actual3 failures preserved;no policy ornativecriterion edits. SourceB2 supportsq7mod12;public-target API/field-model-basepoint bridges notyetimplemented. Oldq<=11pureICsmokeswithdrawn as subgroupenumeration;no newperformanceclaim.
''')
d=s/'evidence/g3-norm-full-metadata-governance-01';d.mkdir();shutil.copyfile(__file__,d/'original-command.py')
scope=[str(s.relative_to(r)),'.github/workflows/pcc-gate.yml','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd):
 v=subprocess.run(cmd,cwd=r,capture_output=True);data=v.stdout+v.stderr
 if len(data)>60000:z=lzma.compress(data,format=lzma.FORMAT_XZ);assert lzma.decompress(z)==data;(d/(name+'.txt.xz')).write_bytes(z)
 else:(d/(name+'.txt')).write_bytes(data)
 (d/(name+'.exit')).write_text(str(v.returncode)+'\n');print(name,v.returncode,flush=True);assert v.returncode==0,data.decode(errors='replace')[:1800]
run('portablehashes',['sha256sum','--check',str((s/'g3-norm-reference-01.sha256').relative_to(r))])
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','.github/workflows/chained-transfer-reference.yml',str((s/'g3-norm-checker').relative_to(r)),str((s/'check-g3-norm.sh').relative_to(r)),str((s/'g3-norm-reference-01.sha256').relative_to(r))],cwd=r)
before=(s/'evidence/g3-norm-primary-pcc-data-plan-01/before-workflow.yml').read_text();after=(r/'.github/workflows/pcc-gate.yml').read_text();newpath=' experiments/chained-transfer-reference/evidence/g3-norm-destination-primary-01/whole-primary.tar.xz';assert after.count(newpath)==2 and after.replace(newpath,'')==before
subjects=[]
for p in paths():
 if p.startswith(b'pcc/claims/'):
  for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
   if proof.get('kind')=='attestation':
    x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path'];subjects.append(x['path'])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode() for p in paths() if p.endswith(b'.md')]]);run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/pcc-gate.yml','.github/workflows/chained-transfer-reference.yml']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
 ps=paths();f=Path('/workspace/scratch/ct56-norm-full-metadata.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True);selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for p in subjects:
  if subprocess.run(['git','cat-file','-e',base+':'+p],cwd=r,capture_output=True).returncode==0 or p.encode() in selected:continue
  path=r/p;manifest=path.parent/'.artifacts.json';m=json.loads(manifest.read_text());entry=m['files'][path.name];assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'] and path.stat().st_size==entry['bytes'];assert str(manifest.relative_to(r)).encode() in selected;assert after.count(' '+p)==2,p
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(d/'custody.json').write_text(json.dumps(dict(base=base,ownledger_prose_whitespace_wiring_actionlint_benchrec_artifact=0,all437focusedinputs_unchanged=True,no_Rust_Lean_verifier_or_trust_change=True,ONLYPCCworkflowdelta='ONEexactgenuineb992artifactread inBOTHgate/sign;frozen451bc2',all_new_subjecthashes_andstaging_or_genuine_managedpaths_covered=True,native_full='7b231c COMPLETE',rawactual='48e581/82e079/1dd28b/5327f4',own7CI='pendingterminalread10:16',report='d99c38/ONE36300page ALLinspected',rootglobal='access/signing/ledger/conflictgaps remain'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','NormFULLmetadata governance own069ledger/prose/workingcachedwhitespace/wiring/actionlint/benchrec/artifact0/all437focusedinputs unchanged/newsubjecthash/stagingorGENUINEmanageddata coverage. ONLYPCCworkflowdelta frozen451bc2 exactb992sourcearchive read inBOTHexistinggate/sign;nativeRust/Lean/verifier/trust/whole7workflow unchanged. Completefull7b231c/ALL6+2nativearchivesactuallypublished/primary69520subjectgenuine/ONE36300inspectedfullPDFpage. Firstwiring1/untrackedmanifest andoriginalPCCnot_covered retained. Own7CIterminalpending10:16;mainledger/signing/conflict/rootfixture andcostadmission gaps notpromoted.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct56-norm-full-metadata-governance.claim').write_text(cl+'\n');selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: checkpoint full canonical norm replay and source-backed solver continuation'],cwd=r,check=True)
print(cl,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)

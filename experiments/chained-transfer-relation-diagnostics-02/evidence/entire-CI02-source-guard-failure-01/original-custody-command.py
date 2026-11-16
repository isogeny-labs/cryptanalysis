"""Retain complete public CI custody and source publication; no research execution."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess,tarfile,zipfile
r=Path('/workspace/cryptanalysis');p=r/'experiments/chained-transfer-lp-presentation-01'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()=='71ce8c85fd47b3144ce8e839a16bcfd51cc1426c'
def claim(statement,paths):
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
 for f in paths:cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
 return subprocess.check_output(cmd,cwd=r,text=True).strip()
d=p/'evidence/protocol-publication-01';d.mkdir()
for src,name in [(Path('/workspace/scratch/ct130-LP-protocol-normal-publication-01'),'normal-branch'),(Path('/workspace/scratch/ct130-LP-protocol-new-tag-publication-01'),'new-tag')]:shutil.copytree(src,d/name)
shutil.copyfile('/workspace/scratch/ct132-LP-protocol-pr-api.json',d/'ready-PR1587-api.json')
pub=claim('LPpresentation prospective protocol8f7bac/correctionb10aea/governance04a56b committed71ce8c85fd47b3144ce8e839a16bcfd51cc1426c, originalnormalbranchpublication0 andgenuinelynewtag chained-transfer-lp-protocol-20261115-71ce8c85fd47 normalpush0/exactreadback. ReadyopenConsumerPR1587 onpublishedcheckpointbase826. Originalprotocol/source-review/fixturepins/entirepriorqueue/report remainbyteexact; publicationprecededimplementation. No newnativealgorithm/proof/populationtrial/paidbuild/job/solve/rank/costclaim. Unsigned publicationmetadata.',sorted(f for f in d.rglob('*')if f.is_file()))
root=Path('/dev/shm/ct132-whole-CI02-failure-01');archive=root/'whole-original-relation-02-82617f14.zip';raw=root/'all-members'
assert archive.stat().st_size==1040067 and hashlib.sha256(archive.read_bytes()).hexdigest()=='58414a7baf2767ef3e5886dfc6ada207b9c3d7bced2ead4ff815ed741bb5f768'
e=r/'experiments/chained-transfer-relation-diagnostics-02/evidence/entire-CI02-source-guard-failure-01';e.mkdir(parents=True)
with zipfile.ZipFile(archive)as z:
 assert z.testzip()is None and len(z.infolist())==75
 members=[]
 for row in z.infolist():
  b=(raw/row.filename).read_bytes();assert b==z.read(row.filename)
  members.append(dict(path=row.filename,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),CRC=row.CRC))
o=raw/'n4-original-relation-output';c=raw/'n4-original-relation-checkpoint'
assert (o/'phases.txt').read_text()=='immediate-original-checkpoint-gate 0 0\ninitial-published-source-guards 0 1\n'
assert (o/'original.exit').read_text().strip()=='1'
for name in ['original-gate.exit','original-final-status.exit','readback-meta.exit','readback-pack.exit','readback-resume.exit']:assert(c/name).read_text().strip()=='0'
assert (c/'original-RESUME.md').read_bytes()==(c/'remote-RESUME.md').read_bytes()==(c/'pack-RESUME.md').read_bytes()
assert (c/'pack-meta.json').read_bytes()==(c/'remote-meta.json').read_bytes()
for f in o.rglob('*'):
 if f.is_file() and f.relative_to(o).parts[0]!='original-pre-native-checkpoint':
  dest=e/'entire-original-output-metadata'/f.relative_to(o);dest.parent.mkdir(parents=True,exist_ok=True)
  if f.stat().st_size>60000:dest=dest.with_name(dest.name+'.xz');dest.write_bytes(lzma.compress(f.read_bytes()))
  else:shutil.copyfile(f,dest)
for f in c.iterdir():
 if f.is_file()and f.name!='remote-checkpoint.tar.gz':
  dest=e/'entire-original-checkpoint-metadata'/f.name;dest.parent.mkdir(exist_ok=True)
  if f.stat().st_size>60000:dest=dest.with_name(dest.name+'.xz');dest.write_bytes(lzma.compress(f.read_bytes()))
  else:shutil.copyfile(f,dest)
for src,name in [('/workspace/scratch/ct132-ci02-jobs-api.json','jobs-api.json'),('/workspace/scratch/ct132-ci02-artifacts-api.json','artifacts-api.json')]:shutil.copyfile(src,e/name)
log=Path('/workspace/scratch/ct132-ci02-whole-job.log').read_bytes();(e/'whole-job.log.xz').write_bytes(lzma.compress(log))
missing=[]
for line in (o/'initial-published-source-guards.txt').read_text().splitlines():
 if line.endswith(': FAILED open or read'):missing.append(line.removesuffix(': FAILED open or read'))
assert missing and len(missing)==len(set(missing))
record=dict(at=datetime.now(timezone.utc).isoformat(),source='82617f14fb48843585137f0310f7d1fa9a5d8ea6',run=43766245639,job=132971869268,artifact=14182693363,whole_ZIP=dict(local=str(archive),bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),durable_API='https://api.github.com/repos/isogeny-labs/cryptanalysis/actions/artifacts/14182693363/zip'),every_member=members,whole_job_log=dict(bytes=len(log),sha256=hashlib.sha256(log).hexdigest()),all75_members_CRC_and_exact_extraction=True,all_three_original_remote_checkpoint_readbacks=0,original_gate=0,original_final_status=0,driver=1,source_guard=1,missing_generated_paths=missing,full_mathematical_replay_started=False,old_CI02_unchanged=True,signed_download_API_excluded=True,scope='unsigned complete failed-CI custody; whole archive and both full original packs remain at recorded RAM/GitHub locations, no claim of accepted new scientific run')
(e/'whole-custody.json').write_text(json.dumps(record,indent=2)+'\n');shutil.copyfile(__file__,e/'original-custody-command.py')
failure=claim('ActualfreshConsumerCI02 run43766245639/job132971869268 source826: originalgate0/finalstatus0/allthreewholeS3readbacks0; immediateoriginalgate0 theninitial1605sourceguards1 onmissinggenerated/derivedfiles before mathematicalphases. Driveroriginal.exit1/finalguard1/partialartifactuploadsuccess. Whole1040067B ZIP SHA58414a7baf2767ef3e5886dfc6ada207b9c3d7bced2ead4ff815ed741bb5f768 all75members/CRC/exactextraction/source-Resume-meta-packreadback retained, fullpubliclog/APIs/missingpathlist. Sparsecheckpointstatusfix02 passesitsintendedstatuscriterion, butfreshmathreplaynotaccepted. Nextversionmusthydrateallpinnedgeneratedsourcesbeforeunchangedguard, withoutomittingguardpaths. Originalworkflow01/workflow02/tools/policy/science unchanged. Unsigned failurecustody, no solve/rank/cost/executionverified claim.',sorted(f for f in e.rglob('*')if f.is_file()))
entry=f'''# Resume published LP protocol and preserve fresh CI02 failure

## What was done
{pub}: protocol source71ce and genuinely new tag published normally, ready PR1587. {failure}: complete CI02 failed artifact14182693363 retained, all75 members checked against whole ZIP and CRC; full log, checkpoint metadata and original missing-path guard output preserved. Original checkpoint gate/final status and all three remote readbacks are0; initial mathematical source guard is1 before arithmetic. [pcc:unverified]

## Decisions made
Continue the published LP component with Rust/Lean local development and meaningful synthetic graph units. Separately author CI03 to materialize the exact old generated/derived bytes before all unchanged guards. Do not rerun unchanged CI02 or change its pinned criterion. No fixed60call LP run or paid build/job before original EKS admission and known live budget/capacity. [pcc:unverified]

## Open threads
Generic cancellation/projection proof and native identity certificates; complete LP certificates and independent replay; source-fixed CI03; Root transport02 exact-source clone prepared952files and workflow publication; full scientific NEW28 and original frozen-ledger merge blockers. [pcc:unverified]

## Errors
CI02 reached the next real obstruction: twenty-four generated/derived source files were absent before its initial guard (exact list in whole-custody.json). Checkpoint final-status failure is no longer observed in02. New mathematical diagnostics have not run; preserve the failure and materialize rather than drop any protected path. KB remains unavailable and locked atlas unread. [pcc:unverified]
'''
# Derive the prose count from the actual complete guard output.
entry=entry.replace('twenty-four generated/derived source files',str(len(missing))+' generated/derived source files')
with(r/'docs/session-logs/2026-11-15.md').open('a')as out:out.write('\n'+datetime.now(timezone.utc).isoformat()+'\n\n'+entry+'\n---\n')
resume=r/'.resume/RESUME.md';resume.write_text(entry+'\n---\n\n'+resume.read_text())
print(pub,failure,'missing',len(missing),flush=True)

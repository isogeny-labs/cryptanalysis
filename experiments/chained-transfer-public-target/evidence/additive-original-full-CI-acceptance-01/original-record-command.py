"""Register complete CI03 acceptance, retaining whole evidence and every failed local attempt."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';raw=Path('/workspace/scratch/ct94-additive-original-full-CI-acceptance-01')
a=json.loads((raw/'acceptance.json').read_text());assert a['expected_phase_exits']==153 and a['all_unfiltered_artifact_members']==749
e=s/'evidence/additive-original-full-CI-acceptance-01';e.mkdir()
for name in ['acceptance.json','jobs-api.json','artifacts-api.json','zip-members-original-index.json','download-transport.json','whole-extraction-custody.json','independent-custody-checks.json','whole-runlog-transport02.json','whole-original-runlog-members.json','host-positive-exact-byte-links.json','host-controls-progress-resumed06.json','actual-host-auditor-resume-command-06.py']:
 shutil.copyfile(raw/name,e/name)
for gate in ['consumer-proofs','producer-proofs']:shutil.copytree(raw/'whole-artifact'/gate,e/gate)
for label in ['actual-downloaded-Rust-auditor-controls-01','actual-downloaded-Rust-auditor-controls-02']:
 d=e/label;d.mkdir()
 for f in sorted((raw/label).iterdir()):
  if f.suffix in ['.txt','.exit']:shutil.copyfile(f,d/f.name)
for f in sorted(Path('/workspace/scratch').glob('ct94_audit_complete_CI03_*.py')):shutil.copyfile(f,e/f.name)
for f in sorted(Path('/workspace/scratch').glob('ct94-whole-CI-audit-*')):
 if f.is_file():shutil.copyfile(f,e/f.name)
for directory in sorted(raw.glob('independent-audit-failed*')):shutil.copytree(directory,e/directory.name)
shutil.copyfile(__file__,e/'original-record-command.py')
inventory={}
for f in sorted(raw.rglob('*')):
 if f.is_file():
  with f.open('rb')as q:h=hashlib.file_digest(q,'sha256').hexdigest()
  inventory[f.relative_to(raw).as_posix()]=dict(bytes=f.stat().st_size,sha256=h)
(e/'whole-unfiltered-local-raw-inventory.json').write_text(json.dumps(dict(root=str(raw),all_retained_files=inventory,whole_ZIP_and_all749_original_members_retained=True,whole_runlog_ZIP_and_both_unfiltered_members_retained=True,future_custody='NEW26; no source, raw, whole population, native failure, actual executable or full prepared library is removed or filtered'),indent=2)+'\n')
(e/'REPORT.md').write_text('''# Complete additive original-source CI replay

At consumer25801fe and original producer3d49af7, run43700115169,
job132769186550 succeeded. Artifact14156900587 is99,483,928 bytes with
SHA256 06104f175a79f38aa22961cabb6467e33838724e9e87f9b037e3477defa970fb.
Every one of its749 members was streamed, CRC-checked, hashed and retained.
Whole-byte and mode comparisons preceded every closed-evidence hardlink;
all original paths remain. Both run-log ZIP members are retained, including
the complete63,261,451-byte job log. [pcc:unverified]

All153 phases have their original expected exits, with seven unfiltered
tests and whole13/695/695/1077/311/16/701 records. All24 original entire-class
omissions return101 without accepted output. Both unchanged original proof
gates audit70 module/declaration occurrences with zero trusted declarations:
54 distinct names plus16 historical copies in OriginalFullChain. All70 exact
statement bindings pass at25801fe. All1440 source guards, the actual compiled
and runtime test/auditor binaries, full prepared RLIB/RMETA copies, actual
fresh reuse and complete engine dependency/features/targets closure pass.
[pcc:unverified]

The actual seven downloaded Rust auditors were independently executed on
this host: all seven whole positives return0 and all24 original omission
inputs return101 without accepted output. Positive whole bytes were compared
before exact closed links. The original kernel auditor requires the existing
fixture environment: one host launch without that variable failed101 before
acceptance; its whole failure and corrected environment are preserved. The
first18 successful controls were retained and only the remaining13 resumed.
[pcc:unverified]

Earlier local custody scripts exposed metadata-projection mistakes (global
name uniqueness, PCC file-versus-canonical digest, checkout-specific provenance
paths and heterogeneous source-row keys). Every failed source/log/exit is
retained; no CI source, proof gate, formula, population or acceptance criterion
changed. All compiled and fixture inputs match exactly. One provenance-only
custody file matches after the explicitly recorded checkout-prefix projection,
with all applicable whole source/prefix/generated/decompressed hashes checked.
The initial direct job-log transport403 is retained; the complete run-log ZIP
transport succeeded. Credential-bearing transport stderr stays private locally.
[pcc:unverified]

This is unsigned bounded exact-source CI03 and downloaded-auditor acceptance.
It supplies no induced-transfer proof CI result, all-current/global CI result,
cold120 acceptance, calibrated computational advantage, new ECDLP algorithm or
signed standing. All original failures, raw logs, complete source, executables
and prepared copies remain intact for genuine NEW26. [pcc:unverified]
''')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Complete exact CI03 acceptance at25801fe/originalproducer3d49af7: run43700115169/job132769186550SUCCESS; whole99483928B artifact14156900587 SHA06104f175a79f38aa22961cabb6467e33838724e9e87f9b037e3477defa970fb/all749members streamed-CRC-hashed-retained/allpaths/fullZIP. Complete run-log ZIP/bothmembers/whole63261451Bjoblog retained. All153phases expected, sevenunfiltered tests0/whole13-695-695-1077-311-16-701 records/24actualentireclassomissions101-nooutput; bothoriginal70module-declarationchecks0trusted(54distinctnames+16historicalcopies)/all70exactbindings/all1440sourceguards. Actual compiled-runtime test/auditor wholebytes/fullRLIB-RMETA/Cargo freshreuse/completeclosure checked. ActualdownloadedsevenRust auditors onhost: sevenwholepositive0/all24actualomissions101-nooutput; first18controls retained, remaining13 resumed afterpreservedmissingkernel-fixture-env101. Alllocalcustodyprojection/transport failures preserved; onlyoneprovenancemetadatacheckoutprefix differs, allcompiled-fixturebytes exact. Wholepositivebytes independentlycompared beforeclosedlinks. Unsignedboundedreplayonly/no newinducedproofCI/global-currentCI/cold120/calibratedcost/ECDLPadvantage/signedpromotion. Allwholedata/source/exes/fullpreparedcopies retainedforNEW26.']
for f in sorted(e.rglob('*')):
 if f.is_file():cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct94-complete-CI-acceptance.claim.txt').write_text(claim+'\n');print(claim,flush=True)
cleanup=Path('/workspace/scratch/ct94-unheld-pip-download-cache-cleanup-13');d=s/'evidence/unheld-pip-download-cache-cleanup-13';shutil.copytree(cleanup,d)
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Storage13 removes126unheld pip HTTP downloadcache entries only:67063462logicalB/67354624allocatedB; free98832384to166178816B. All51583guard paths/everyPCC subject excluded, allthreeGitstatuses unchanged. Fullremoved-file hashinventory retained; no installedtool/package/source/researchraw/actualexecutable/fullpreparedlibrary removed. Unsignedstorageonly/no cold orperformanceacceptance.']
for f in sorted(d.iterdir()):cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct94-cleanup13.claim.txt').write_text(cl+'\n');print(cl,flush=True)
state='# Complete exact original full replay accepted; induced-transfer proof next\n\n'+claim+' accepts CI03 at25801fe: run43700115169/job132769186550/all749members;153expectedphases/sevenwholepopulations/24actualomissions/both70checks(54names+16historicalcopies)/all70bindings/1440guards/actualruntime-enginecustody. IndependentdownloadedRust auditors:sevenpositive0/all24omissions101. Every failed host/projection/transport attempt retained; no scientific criterion changed. [pcc:unverified]\n\n## What was done\nRetained whole99,483,928BZIP/all749paths andcomplete63,261,451Bjoblog. Closed-byte/mode reuse preserves813MB/allpaths. Cleanup12c9513d and13'+cl+' removeonlyunheldthirdparty/compiler-downloadcaches; actualscience/source/exes/fullpreparedlibraries stayintact. New induced-proof driver/workflow is being locally checked; proofeddc37/resultd90ad1 at5417e9d remains conditional standardalgebra/allnineexactbindings/both21declarations0trusted. [pcc:unverified]\n\n## Decisions made\nSingle consumer ledger remains onresearch/chained-transfer-induced-map-20261115. Normalfast-forward original research/chained-transfer-public-target-20261113 from258 to this branch latest checkpoint BEFORE any acceptance append there. No rebase/rechain/force/merge waiver. Newproofworkflow additive, original CI03 and allold guards unchanged. Whole newct92-95 material retained for genuineNEW26. [pcc:unverified]\n\n## Open threads\nFinish actualnewproof-driver validation/normalpublication/ordinarybranchFF, collectfreshproofCI; advanceoriginalfixedmodels prime-fieldIC usingexistingIC/normassistedsampling implementations; completeprimitive/setup/knownpoint/strongmatchedreference study. Cold120 remains18complete102missing/124; root124/clock101/livebudget-capacity-isolation-image/review/signing gaps unchanged. No calibrated/globalCI/ECDLPadvantage/signedpromotion. [pcc:unverified]\n\n## Errors\nFullactualkernelhostmissing-env101 preserved before successful corrected13remainingcontrols. Custody projection failures and initialjoblog403 preserved; completeCIartifactsource/mathematicsneverchanged. Oldfullnative693failure/test-onlyCRToraclecorrection andallpriornegativegeometry/proof/cold/mainledger results remain intact. [pcc:unverified]\n\n---\n\n'
for f in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']:f.write_text(state+f.read_text())
f=r/'docs/session-logs/2026-11-15.md';f.write_text(f.read_text().rstrip()+'\n\n'+state.split('\n---')[0].rstrip()+'\n')

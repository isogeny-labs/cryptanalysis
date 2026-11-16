"""Custody of actual CI/local build timeouts; no research arithmetic."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';e=s/'evidence/nondual22-cold-build-timeout-02';e.mkdir()
ci=Path('/workspace/scratch/ct78-nondual22-CI-build-failure-02');run=Path('/workspace/scratch/ct78-nondual22-full-01');cp=Path('/workspace/scratch/ct78-replay-current-original-checkpoint-02')
for name in ['jobs-api.json','artifacts-api.json','whole-members.json']:shutil.copyfile(ci/name,e/('CI-'+name))
(e/'CI-whole-job.log.xz').write_bytes(lzma.compress((ci/'whole-job.log').read_bytes()))
for name in ['phases.txt','original.exit','final-source-guards.exit','second-edge-compile.pipe-exits','start.txt','finish.txt','original-command.sh']:
 shutil.copyfile(run/name,e/('local-'+name))
for name in ['second-edge-compile.txt','initial-guards.txt','final-source-guards.txt']:
 (e/('local-whole-'+name+'.xz')).write_bytes(lzma.compress((run/name).read_bytes()))
for name in ['observation.json','original-local-status.exit','original-local-gate.exit','whole-members.json','original-import-command.py']:shutil.copyfile(cp/name,e/('checkpoint-'+name))
for p in [Path('/workspace/scratch/ct78-nondual22-immediate-gate-01.txt'),Path('/workspace/scratch/ct78-nondual22-immediate-gate-01.exit')]:shutil.copyfile(p,e/p.name)
assert(run/'second-edge-compile.pipe-exits').read_text().strip()=='124 0'
assert(run/'original.exit').read_text().strip()=='1'
assert(run/'final-source-guards.exit').read_text().strip()=='0'
assert not list(run.glob('*-native.txt'))
files=[]
for root in [ci,run,cp,Path('/workspace/scratch/ct78-nondual22-layout-01')]:
 for p in sorted(root.rglob('*')):
  if p.is_file()and p.name!='.git':files.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(e/'whole-raw-input-index.json.xz').write_bytes(lzma.compress((json.dumps(files,indent=2)+'\n').encode()))
zipfile=ci/'whole-original-artifact.zip';(e/'CI-whole-artifact.custody.json').write_text(json.dumps(dict(workspace_path=str(zipfile),bytes=zipfile.stat().st_size,sha256=hashlib.sha256(zipfile.read_bytes()).hexdigest(),artifact_id=14127577338,remote='https://api.github.com/repos/isogeny-labs/cryptanalysis/actions/artifacts/14127577338',publication='wholeoriginalZIP+allmembers retained; freshgenuine19 required'),indent=2)+'\n')
(e/'scope.json').write_text(json.dumps(dict(source='72c69becf32cb0a0246f66a724eeaffa5f17d4fa',CI=dict(run=43629921346,job=132554030366,conclusion='failure',compile_actual_exit=124,tee=0,stage='first cold second-edge no-run build120s'),local=dict(output=str(run),outer_exit=1,compile_actual_exit=124,tee=0,final976guards=0,stage='same120s cold no-run build; no native test launched'),checkpoint='automatic43629921517/job132554031315/artifact14127572013/whole220003B/all28members/localgate0 and immediate0; cleanexact72 before localrun',scientific='no native/model/counter output from either timeout; oldD12/D24 negatives and native6d2c97 unchanged',next='prospectively separate unchanged-engine cold compilation900 from original wrapperbuild120/native900, within original outer6000; preserve old fullcold120 criterion asnotmet. No scientific criterion/mathengine/profile/field/panel change.',manual_duplicates='first current-head API listings empty; later automatic22 appeared plus two explicitly dispatched originalcheckpoint/replay runs; all24 actual run occurrences retained, never counted as24distinctworkflows',scope='unsigned resource/setup outcome; no mathematical impossibility, ECDLP performance or signedexecution standing'),indent=2)+'\n')
shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Corrected launcher72c69bec CI43629921346/job132554030366 andfreshphysical localfull01 BOTHhit firstcold no-run build120s actual124/tee0; runners1/nativeNOTRUN, source976guards0. Whole195118charCIlog/67480BZIP14127577338/all20members andwholelocalsource/compilation/outcomes retained; no testexecutable emitted. Localoriginal automaticcheckpoint43629921517/job132554031315/artifact14127572013/220003B/all28/exactsourceResume-tool-receipt/localgate0 before actualrun. No scientificcounterexample: oldnative27fb3a/6d2c97/finiteproofscopes unchanged. Next separate coldunchangedengine preparation900 under NEWprospective resourceprotocol, wrapper120/native900/outer6000 unchanged; originalfullcold120 requirement remainsNOTMET. InitialAPIempty led two manualduplicates before22automaticappeared, preserveall24occurrences not24distinctworkflows. No math/profile/CIwaiver/calibratedgain/signedstanding.']
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)

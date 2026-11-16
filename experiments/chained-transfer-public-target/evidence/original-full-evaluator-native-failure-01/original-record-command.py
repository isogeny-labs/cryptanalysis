"""Preserve failed unfiltered run and exact whole-output/source/binary custody."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
raw=Path('/workspace/scratch/ct90-original-full-evaluator-native-01')
e=s/'evidence/original-full-evaluator-native-failure-01';e.mkdir()
assert (raw/'native.exit').read_text().strip()=='101'
assert (raw/'original.exit').read_text().strip()=='1'
assert Path('/workspace/scratch/ct90-original-full-evaluator-native-supervisor-01/worker.exit').read_text().strip()=='1'
summary=json.loads((raw/'failure-summary.json').read_text());assert summary['completed_whole_records']==693 and summary['actual_exceptional_records']==672
assert not (raw/'all701-expected.json').exists()
for name in ['after-failure-chain-bytes','after-failure-auditor-bytes','after-failure-all1270-prior']:
    assert (raw/(name+'.exit')).read_text().strip()=='0'
for p in sorted(raw.iterdir()):
    if p.is_file() and p.suffix!='.bin' and p.name not in ['old-sixteen.json','native.txt','completed-whole-records.json']:
        value=p.read_bytes();compressed=len(value)>60000
        if compressed:value=lzma.compress(value)
        if len(value)<65536:(e/(p.name+'.xz' if compressed else p.name)).write_bytes(value)
text=(raw/'native.txt').read_text();(e/'literal-panic-footer.txt').write_text(text[text.index("\nthread 'tests::"):])
roots=[raw,Path('/workspace/scratch/ct90-original-full-evaluator-native-supervisor-01'),Path('/workspace/scratch/ct90-current-original-checkpoint-18'),Path('/workspace/scratch/ct90-current-original-checkpoint-18-import-failed01')]
inventory={str(root):{p.relative_to(root).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest())for p in sorted(root.rglob('*'))if p.is_file()}for root in roots}
(e/'whole-unfiltered-raw-inventory.json').write_text(json.dumps(dict(all_roots_and_members=inventory,future_custody='NEW25; all full outputs, completed693, original28, failed importer, actual source/executables/prepared libraries retained'),indent=2)+'\n')
for p in [Path('/workspace/scratch/ct90-checkpoint18-importer-materialization-failure-01.txt'),Path('/workspace/scratch/ct90-checkpoint18-import-caller-02.txt')]:shutil.copyfile(p,e/p.name)
shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Original full-group PhaseB first unfilterednative atpublishede633524/build01/exactoriginalcheckpoint18 run43694827544/job132752953777/artifact14153688484/all28/immediategate0 fails101; driver/supervisor1. All693completed whole records retained, includingall672 exceptional descriptors/bothoutgoing/allfourhalves/duplicatecorrections/norms/13-169dualnorms/fullsourceinverse andconstructor/cofactorpanels; NO whole701acceptance/fixture/omissions. Failure atsrc/tests.rs148 independentprime-source recovery uses oldnu12 scalar1385856 in two testchecks. All1270postfailure hashes andactualtest-auditorbytes exact0. Narrowrepair derives4*inverse_original_prime(8), withmod4=0/inverse2modoriginalELL assertions, replaces onlytwo oracle literals; runtimefullhalving/correction/admission/norm/inverse, models/population/criteria unchanged. Entirefailed693/native/actualsource/executables/fullpreparedcopies/checkpoint28/importerfailures preserved forNEW25. Unsigned actualprogram/testfailure, notfullacceptance ormathematicalimpossibility; new compiledsource/freshcheckpoint/immediategate required before successor.']
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct90-full-native-failure01.claim.txt').write_text(claim+'\n');print(claim,flush=True)

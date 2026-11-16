from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');p=r/'experiments/chained-transfer-lp-presentation-01'
hold=Path('/dev/shm/ct301-consumer2c44-entire-native-and-cold-compiler-success')
base=hold/'all-entire-original-members/lp-historical-custody';build=base/'entire-prospective-pure-native-build'
g=p/'evidence/post-correction-whole-native-cold-build-CI-success-05';g.mkdir()
shutil.copyfile(__file__,g/'original-capture-command.py')
for name in ['actual-driver.exit','actual-prospective-build.exit','actual-Consumer434-graph-proof.exit','actual-Root435-graph-proof.exit','early-complete-population-source-guard.exit']:
    assert (base/name).read_text().strip()=='0'
for line in (build/'all-actual-build-phases.txt').read_text().splitlines():assert line.endswith(' 0')
for name in ['entire-original-job-log.txt','entire-original-member-inventory.json']:
    (g/(name+'.xz')).write_bytes(lzma.compress((hold/name).read_bytes()))
for f in sorted(base.rglob('*')):
    if not f.is_file():continue
    rel=f.relative_to(base)
    if 'entire-compiler-target' in rel.parts:continue
    if f.suffix in ['.stdout','.stderr','.exit','.time'] or f.name.endswith('.argv.json') or 'phases' in f.name:
        target=g/'entire-operational-files'/rel.with_name(rel.name+'.xz');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(lzma.compress(f.read_bytes()))
    elif f.suffix in ['.json','.jsonl'] and ('fixture' in str(rel) or 'control' in str(rel)):
        target=g/'entire-native-fixtures-and-controls'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
shutil.copyfile(build/'build-receipt.json',g/'entire-new-pure-build-receipt.json')
shutil.copyfile(build/'binary-pins.sha256',g/'entire-new-pure-native-byte-pins.sha256')
native=[]
for name in ['extract_public','historical_certificates','lp-post-character']:
    f=build/name;h=hashlib.sha256(f.read_bytes()).hexdigest()
    assert any(line==h+'  '+name for line in (build/'binary-pins.sha256').read_text().splitlines())
    entry=dict(name=name,bytes=f.stat().st_size,sha256=h,entire_original_member=str(f.relative_to(hold)))
    for label,args in [('file-header',['--file-header']),('dynamic',['--dynamic']),('version-info',['--version-info'])]:
        q=subprocess.run(['readelf',*args,str(f)],capture_output=True)
        (g/(name+'.'+label+'.stdout')).write_bytes(q.stdout);(g/(name+'.'+label+'.stderr')).write_bytes(q.stderr);(g/(name+'.'+label+'.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==0
    native.append(entry)
receipt=dict(at=datetime.now(timezone.utc).isoformat(),source='2c44ee2ebb0be9b5fc0375818cc18924cef82c41',run=43831541523,job=133177802798,artifact=14210025238,
    bytes=53419171,sha256='be85b978a90d873bcb91ac25f3faddc13f464a6052517ae19c422e67ed4ec181',whole_members=740,
    entire_archive_and_every_member=str(hold),new_cold_pure_native_files=native,
    original_checkpoint_and_all3_readbacks=0,early_source12_guard=0,native_development=0,eight_metadata_controls=0,
    fresh_pure_cold_compilers=0,both_original_graph_gates='10 audited/0 trusted each, actual current CI',
    native_executed_during_local_custody=False,source_built_OCI_or_EKS_ABI_qualification=False,old_engine_cold_120s_qualification=False,
    scope='whole uploaded archive/members; current gated development and fresh14/15-package pure release builds; no full historical population')
(g/'whole-archive-and-exact-current-scope.json').write_text(json.dumps(receipt,indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Actual corrected2c44 CI43831541523/job133177802798 succeeds after original checkpoint/all3 readbacks, early12-source closure0. Complete synthetic native development/14 independent raw cases/5 integration15 library2 post tests/strictClippy/builds/guards0, all8 process metadata controls correct and both unchanged original graph proof gates10 audited0 trusted. Fresh separate pure source build succeeds every phase under unchanged120s2GiB wrappers with exact14/15-package no-engine closures, actual Cargo release opt3/not-test artifacts, complete compiler outputs/dependencies/source archive and3 new native byte pins; resulting entrypoints not executed by compiler-only recipe. Entire53419171-byte740-member artifact14210025238/SHAbe85b978a90d873bcb91ac25f3faddc13f464a6052517ae19c422e67ed4ec181 and full job log preserved, every uploaded member CRC/SHA/extracted whole. Local source custody/readelf only, no mathematical executable invoked. Existing040 omitted-protocol failure97e351 remains complete; the correction changes no protocol/math/limit. New pure cold qualification is distinct from old original engine3m48/900s setup, source-built OCI/EKS ABI and full60 population/original360/witness auditor remain unqualified/unexecuted. Actual exhausted budgets e42949 still stop paid launches; no signed/global/cost promotion. Whole archive/runtime/checkpoint must enter genuine scientificNEW28 beyond RAM/GitHub holds.']
for f in sorted(g.rglob('*')):
    if f.is_file():cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();print(claim)
text=f'''\n---\n\n{datetime.now(timezone.utc).isoformat()}\n# Corrected cold source closure and actual fresh pure compiler CI succeed\n\n## What was done\n{claim}: current2c44 original checkpoint/all3 reads, early12-source guard/native development/8 metadata controls/fresh14/15-package pure release builds all0; original dual graph gates10/0. Whole53,419,171B archive/all740 complete uploaded members and full log retained, actual3 native byte pins/static readelf captured. Local executable invocation none. [pcc:unverified]\n\n## Decisions made\nAdvance source-built OCI/runtime source materialization using actual newly compiled pure entrypoints and separately unchanged old baseline capsule. Preserve old040 failure; no source/limit waiver or local fixed population. Root norm source44a3db/PR4413 currentCI next09:45 remains separate. [pcc:unverified]\n\n## Open threads\nFull1661-file runtime source closure snapshotee0ca3, OCI/source/native/actual Job/Pod/ABI/checkpoint custody and genuine all-rawNEW28. Full60/240/62/original360/witness auditor/7 controls/feedback/post notrun, paid launches blocked by e42949. Compiler cache/upload membership is not a new original-engine cold qualification. [pcc:unverified]\n\n## Errors\nNo current-source unit/compiler/proof failure. Prior040 protocol omission and all earlier negative/resource/source failures remain whole. Old01 unchanged checkpoint failure is not retried; repeated other suites are status-only unless full new artifacts explicitly collected. [pcc:unverified]\n'''
with (r/'docs/session-logs/2026-11-16.md').open('a') as f:f.write(text)
with (r/'.resume/RESUME.md').open('a') as f:f.write(text)

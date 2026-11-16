from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');p=r/'experiments/chained-transfer-lp-presentation-01'
hold=Path('/dev/shm/ct369-Consumer-adb-entire-OCI-source-CI')
base=hold/'all-entire-original-members/lp-historical-custody';build=base/'entire-prospective-pure-native-build'
g=p/'evidence/current-published-OCI-source-native-compiler-CI-success-07';g.mkdir()
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
        (g/(name+'.'+label+'.stdout.xz')).write_bytes(lzma.compress(q.stdout));(g/(name+'.'+label+'.stderr.xz')).write_bytes(lzma.compress(q.stderr));(g/(name+'.'+label+'.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==0
    native.append(entry)
receipt=dict(at=datetime.now(timezone.utc).isoformat(),source='adb8a8519990a3b85bf72267b23e984bdf9a57f2',run=43854808363,job=133256202360,artifact=14221092041,
    bytes=53450564,sha256='fda435c8e2ba626ce28d56022f2d288776bee481f53542e9c0705f9342d3d38f',whole_members=745,
    entire_archive_and_every_member=str(hold),new_cold_pure_native_files=native,
    original_checkpoint_and_all3_readbacks=0,early_source12_guard=0,native_development=0,eight_metadata_controls=0,
    fresh_pure_cold_compilers=0,both_original_graph_gates='10 audited/0 trusted each, actual current CI',
    native_executed_during_local_custody=False,source_built_OCI_or_EKS_ABI_qualification=False,old_engine_cold_120s_qualification=False,
    scope='whole uploaded archive/members; current gated development and fresh14/15-package pure release builds; no full historical population')
(g/'whole-archive-and-exact-current-scope.json').write_text(json.dumps(receipt,indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Actual published OCI-sourceadb8 CI43854808363/job133256202360 succeeds after original checkpoint/all3 whole readbacks, early12 guard, synthetic native14 independent cases/5 integration15 library2 post tests/builds/Clippy/guards,8 process metadata controls, fresh pure14/15-package release compiler phases and unchanged dual graph gates10 audited0 trusted. New8-source OCI recipe guard/shell syntax/full recipe capture present in complete53450564B artifact14221092041/SHAfda435c8e2ba626ce28d56022f2d288776bee481f53542e9c0705f9342d3d38f, all745 whole uploaded members CRC/SHA/materialized with full287833-character job log. Entire ZIP retained;665 byte-identical whole members share immutable original2c storage and6040180 changed bytes copied whole, no old file/hold deletion. Actual3 current compiled byte pins/static readelf captured; no local science execution and compiler-only recipe does not execute its output entrypoints. Original no-engine dependency/release profiles unchanged; this is not an image build/EKS ABI or old-engine120s cold qualification. Frozen60 LP/original360/witness/controls/feedback/post remains unexecuted and paid stop persists. Original empty draft/no-asset failures and proper source-archiveS3 work are separate. All other current old suites status-only except explicitly collected artifacts; old01 still known checkpoint failure, no unchanged retry/signing/global/cost promotion.']
for f in sorted(g.rglob('*')):
    if f.is_file():cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();print(claim)
text=f'''\n---\n\n{datetime.now(timezone.utc).isoformat()}\n# Corrected cold source closure and actual fresh pure compiler CI succeed\n\n## What was done\n{claim}: currentadb8 original checkpoint/all3 reads, early12-source guard/native development/8 metadata controls/fresh14/15-package pure release builds all0; original dual graph gates10/0. Whole53,450,564B archive/all745 complete uploaded members and full log retained, actual3 native byte pins/static readelf captured. Local executable invocation none. [pcc:unverified]\n\n## Decisions made\nAdvance source-built OCI/runtime source materialization using actual newly compiled pure entrypoints and separately unchanged old baseline capsule. Preserve old040 failure; no source/limit waiver or local fixed population. Root word proof47b94f is actually mergedc8aa after current dual27/0 CI96eb44 and8959-key guard89348c; normal configured Git fresh branch e77015 succeeds after invalid manual token failure. [pcc:unverified]\n\n## Open threads\nActual public2c clean Git/all guards/unpushed0/committedRESUME link repair08b4f7 is a separate completed metadata component; portable full helper, actual checkpoint/OCI/ABI/native/Job/Pod/admission and genuine all-rawNEW28 remain. Full60/240/62/original360/witness auditor/7 controls/feedback/post notrun, paid launches blocked by e42949. Compiler cache/upload membership is not a new original-engine cold qualification. [pcc:unverified]\n\n## Errors\nNo current-source unit/compiler/proof failure. Prior040 protocol omission and all earlier negative/resource/source failures remain whole. Old01 unchanged checkpoint failure is not retried; repeated other suites are status-only unless full new artifacts explicitly collected. [pcc:unverified]\n'''
with (r/'docs/session-logs/2026-11-16.md').open('a') as f:f.write(text)
with (r/'.resume/RESUME.md').open('a') as f:f.write(text)

from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');p=r/'experiments/chained-transfer-lp-presentation-01'
g=p/'evidence/population-driver-metadata-and-input-bytes-02';g.mkdir()
shutil.copyfile(__file__,g/'original-capture-command.py')
for name,source in [('whole-first-missing-time-failure','/dev/shm/ct255-population-phase-metadata-controls-01'),('whole-eight-process-controls','/dev/shm/ct257-population-phase-metadata-controls-02')]:
    shutil.copytree(source,g/name)
prep=Path('/dev/shm/ct258-whole-original-input-byte-preparation-01')
assert (prep/'original.exit').read_text().strip()=='0'
assert all(x.endswith(' 0') for x in (prep/'all-actual-byte-phases.txt').read_text().splitlines())
q=g/'whole-input-preparation-logs';q.mkdir()
for f in sorted(prep.iterdir()):
    if f.is_file() and f.name not in {x.name for x in prep.iterdir() if x.name.endswith(('.json','.jsonl','.xz'))}:
        assert f.stat().st_size<100_000;shutil.copyfile(f,q/f.name)
# Keep whole pins/capture in their already published original source paths;
# decoded original bytes remain complete in RAM with full input identities.
(g/'whole-input-byte-hold.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),whole_complete_input_hold=str(prep),
    actual_file_preparation_exit=0,all_six_compressed_and_decoded=True,full_capture=True,
    scientific_algorithm_executed=False,original_source='historical-whole-fixture-pins-01.json'),indent=2)+'\n')
tool=Path('/dev/shm/ct256-GNU-time-metadata-tool')
shutil.copyfile(tool/'entire-official-time_1.9-0.2_amd64.deb',g/'entire-GNU-time-official-package.deb')
shutil.copyfile(tool/'entire-official-pool-index.html',g/'entire-GNU-time-official-pool-index.html')
(g/'actual-time-tool-custody.json').write_text(json.dumps(dict(
    url='https://deb.debian.org/debian/pool/main/t/time/time_1.9-0.2_amd64.deb',
    entire_deb_sha256=hashlib.sha256((g/'entire-GNU-time-official-package.deb').read_bytes()).hexdigest(),
    native_time_sha256=hashlib.sha256((tool/'entire-package/usr/bin/time').read_bytes()).hexdigest(),
    first_native_metadata_command_exit=127,first_harness_tool_exit=1,
    first_cause='missing /usr/bin/time on this workspace; exact original failed harness/library retained',
    scientific_native_executed=False),indent=2)+'\n')
shutil.copytree(p/'population-01',g/'entire-actual-population-source')
checks=[('all-source-shell-syntax',['bash','-c','for source in experiments/chained-transfer-lp-presentation-01/population-01/*.sh;do bash -n "$source" || exit;done']),
 ('all50-original-pure-pins',['sha256sum','--check',str(p.relative_to(r))+'/historical-01/source-01.sha256']),
 ('all12-population-runtime-pins',['sha256sum','--check',str(p.relative_to(r))+'/population-01/source-01.sha256']),
 ('workflow-actionlint',['/workspace/scratch/actionlint-bin/actionlint','-oneline','.github/workflows/chained-transfer-lp-historical-development-01.yml'])]
for name,cmd in checks:
    actual=subprocess.run(cmd,cwd=r,capture_output=True)
    (g/(name+'.txt.xz')).write_bytes(lzma.compress(actual.stdout+actual.stderr))
    (g/(name+'.exit')).write_text(str(actual.returncode)+'\n')
    print(name,actual.returncode,flush=True);assert actual.returncode==0
statement='Prospective full-population driver source and metadata-only controls: all8 actual shell exit/timeout/signal/deadline/upload controls have their expected outcomes; whole first missing-GNU-time failure and exact final harness/phase library/package bytes retained. Complete all6 original compressed/decoded files/capture copied/decompressed and SHA/size checked with all original byte phases0, no mathematical/native algorithm run. Source review preserved full first draft, corrected external shell-function invocation and62-record replay completion count, then source/syntax/all50/all12/actionlint0. Driver connects strict public all60/240 production/replay,7 whole rejection constructors/replays, feedback, separate unchanged original360 and actual-norm auditor/fresh whole verdict equality, separate full post audit, original checkpoint/all3 readbacks,120/900s2GiB/frozen3600s/partial uploads and complete old/new runtime bytes. Cold pure build source records actual Cargo artifacts/release profiles/exact14/15 no-engine closures/whole compiler targets and sources, executes no resulting binaries; new build/current CI remains prospective. No complete launch request/OCI/ABI/Job admission qualification or historical LP computation. Exhausted budgets e42949 still stop paid builds/jobs; original protocol/policies/tools/verifiers/keyring and mathematical source code unchanged.'
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
for f in sorted(g.rglob('*')):
    if f.is_file():cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
text=f'''\n---\n\n{datetime.now(timezone.utc).isoformat()}\n# Prospective complete-population source and offline process controls\n\n## What was done\n{claim}: all8 shell process metadata controls have expected outcomes; full first missing-time failure/tool package/harness retained. Complete6 original compressed/decoded/capture byte preparation0 without math. Full first driver draft preserved; external function invocation and footer61→62 corrected before any population run. Shell/all50/all12/actionlint0. [pcc:unverified]\n\n## Decisions made\nPublish full driver/cold pure compiler source and original-checkpoint-adjacent CI metadata/cold-build integration. The build source executes no scientific binaries; source-built image/launch/config/external UID qualification remain open. No paid job/build under actual budget exhaustione42949. [pcc:unverified]\n\n## Open threads\nActual prospective pure build in CI; full60/240/62/seven whole controls/feedback/fresh original360/witness auditor/separate post remains unexecuted. Source-built OCI/ABI, future actual live headroom/reservations/capacity, genuine all-rawNEW28 and current applicable checks/review before merge. Root5ae1 next checkpoint uses fresh branch. [pcc:unverified]\n\n## Errors\nFirst metadata native wrapper127 because /usr/bin/time absent, first harness exit1 preserved. Official Debian package retained; exact GNU time used only for offline shell metadata successor. No scientific run/phase limit change or local historical substitute. Prior source review issues are source observations, not executed failures. [pcc:unverified]\n'''
with (r/'docs/session-logs/2026-11-16.md').open('a') as f:f.write(text)
with (r/'.resume/RESUME.md').open('a') as f:f.write(text)
pub=p/'evidence/complete-CI-runtime-normal-publication-03';pub.mkdir()
for f in Path('/workspace/scratch/ct253-consumer-normal-source-publication-01').iterdir():shutil.copyfile(f,pub/f.name)
print(claim)

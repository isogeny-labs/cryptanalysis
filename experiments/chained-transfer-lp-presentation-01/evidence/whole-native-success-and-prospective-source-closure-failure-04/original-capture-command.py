from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');p=r/'experiments/chained-transfer-lp-presentation-01'
hold=Path('/dev/shm/ct284-consumer040-entire-cold-source-closure-failure')
g=p/'evidence/whole-native-success-and-prospective-source-closure-failure-04';g.mkdir()
shutil.copyfile(__file__,g/'original-capture-command.py')
for name in ['entire-original-member-inventory.json','entire-original-job-log.txt']:
    (g/(name+'.xz')).write_bytes(lzma.compress((hold/name).read_bytes()))
base=hold/'all-entire-original-members/lp-historical-custody'
build=base/'entire-prospective-pure-native-build'
assert (base/'actual-driver.exit').read_text().strip()=='0'
assert (base/'actual-prospective-build.exit').read_text().strip()=='1'
assert (build/'initial-50-source-guard.exit').read_text().strip()=='0'
assert (build/'initial-population-source-guard.exit').read_text().strip()=='1'
assert b'PROTOCOL_01.md: No such file or directory' in (build/'initial-population-source-guard.stderr').read_bytes()
assert not (build/'historical-fetch.exit').exists()
for f in sorted(base.rglob('*')):
    if not f.is_file():continue
    rel=f.relative_to(base)
    if f.suffix in ['.stdout','.stderr','.exit','.time'] or f.name.endswith('.argv.json') or 'phases' in f.name:
        target=g/'entire-operational-files'/rel.with_name(rel.name+'.xz');target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(lzma.compress(f.read_bytes()))
    elif f.suffix in ['.json','.jsonl'] and ('fixture' in str(rel) or 'control' in str(rel)):
        target=g/'entire-native-fixtures-and-controls'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
receipt=dict(at=datetime.now(timezone.utc).isoformat(),source='0405429a2d81670dedda058207d72f419817aeac',run=43824008898,job=133153403704,artifact=14205294063,
    bytes=31149750,sha256='1bea194d119b0595331d76b0b22bb2a6a54a96fdce89bbae631c0a73198e521a',all_whole_members=502,
    whole_archive_and_every_whole_member=str(hold),durable_original='https://api.github.com/repos/isogeny-labs/cryptanalysis/actions/artifacts/14205294063/zip',
    native_development_exit=0,new_offline_process_controls_exit=0,prospective_pure_build_exit=1,
    initial_pure50_guard_exit=0,initial_population12_guard_exit=1,pure_compiler_started=False,
    actual_missing_file='experiments/chained-transfer-lp-presentation-01/PROTOCOL_01.md',
    unchanged_graph_proof_CI='skipped after prospective source guard failure; previous source5e80 dual gates remain separate',
    scope='complete original checkpoint/readback and synthetic native success; incomplete prospective compiler source closure, no fixed historical LP population')
(g/'whole-artifact-and-exact-failure-scope.json').write_text(json.dumps(receipt,indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Actual0405429a changed-source CI43824008898/job133153403704: original checkpoint/all3 readbacks and complete existing synthetic native development succeed0; all8 process metadata controls have expected outcomes. Prospective cold pure build fails1 before Cargo fetch/compiler because original12-source guard cannot read the unchanged PROTOCOL_01.md omitted from the CI sparse checkout;50-source guard0. Later graph proof step is skipped, not successful current-source proof execution. Complete31149750-byte artifact14205294063/SHA1bea194d119b0595331d76b0b22bb2a6a54a96fdce89bbae631c0a73198e521a and all502 members fully CRC/SHA/extracted; whole job log, operational outputs and entire synthetic fixtures/controls retained. This is a source-closure implementation failure, not a mathematical rejection, compiler120s timeout or cold qualification. Preserve it before fixing only sparse materialization and checking all12 source pins earlier. All frozen protocol/math/original gates/resources/old failures remain unchanged. No paid build/job or full historical population. Other repeated source040 suites are status-only, not all-new raw custody; old01 still fails its known checkpoint.']
for f in sorted(g.rglob('*')):
    if f.is_file():cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
text=f'''\n---\n\n{datetime.now(timezone.utc).isoformat()}\n# Preserve current synthetic success and prospective source-closure failure\n\n## What was done\n{claim}: actual040 CI43824008898 after original checkpoint/readbacks has native development0 and8 metadata controls correct; prospective pure build1 before compiler because sparse checkout omits frozen PROTOCOL_01.md. Complete31,149,750B ZIP/all502 members and whole logs retained. Current graph proof step skipped. [pcc:unverified]\n\n## Decisions made\nMaterialize the exact unchanged protocol in sparse checkout and run12-source metadata guard before native development; publish only that source-closure correction with updated manifest hashes. Do not rerun the unchanged failed source or weaken guards/resources. [pcc:unverified]\n\n## Open threads\nCorrected-source actual compiler/CI qualification; frozen60/240/62/original360/witness auditor/controls/feedback/post still unexecuted. Budgete42949 stops paid launches. Root cubic norm proof26ec43/12 bindings/inspected reportb203ad complete as local static component, source publication pending; Root current16929 genuine FF preserves8634 keys. [pcc:unverified]\n\n## Errors\nMissing original protocol file is the actual failure, not timeout or scientific outcome. All prior failures retained, and source5e80 graph gates remain historical scope. Entire raw archive/runtime and new failure require genuine scientificNEW28 beyond GitHub/RAM holds. [pcc:unverified]\n'''
with (r/'docs/session-logs/2026-11-16.md').open('a') as f:f.write(text)
with (r/'.resume/RESUME.md').open('a') as f:f.write(text)
print(claim)

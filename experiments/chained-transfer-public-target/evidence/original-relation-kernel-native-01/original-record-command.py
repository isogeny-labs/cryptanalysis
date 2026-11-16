"""Retain complete native custody and make an unsigned evidence record; I/O only."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';raw=Path('/workspace/scratch/ct101-original-relation-kernel-native-01')
source='6d823770ff5d57dfd71ac623d922cb5b6df200ae'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==source
assert (raw/'original.exit').read_text().strip()=='0'
phases=[line.split() for line in (raw/'phases.txt').read_text().splitlines()]
assert len(phases)==28 and all(want==actual for name,want,actual in phases)
verdict=json.loads((raw/'whole60-accepted-capture.json').read_text())
assert verdict['whole_calls']==60 and verdict['whole_journal_events']==660 and verdict['whole_original_native_records']==100
assert verdict['all60full_reports_inputs_scalar_checks_counters_nontime_values_match_original'] is True
for stage in ['available','selected','candidate','descent']:
 assert (raw/(stage+'-omission.exit')).read_text().strip()=='101'
 assert not (raw/(stage+'-must-not-accept.json')).exists()
e=s/'evidence/original-relation-kernel-native-01';e.mkdir()
shutil.copyfile(__file__,e/'original-record-command.py')
for name in ['original.exit','start.txt','finish.txt','original-command.sh','phases.txt','runtime-custody.json','whole60-accepted-capture.json','original-native-driver.sha256']:
 shutil.copyfile(raw/name,e/name)
for name in ['observation.json','whole-members.json','original-import-command.py']:
 shutil.copyfile(Path('/workspace/scratch/ct101-current-original-checkpoint-22')/name,e/('exact-checkpoint22-'+name))
shutil.copyfile('/workspace/scratch/ct89-original-relation-kernel-compiled-01-publication-01/receipt.json',e/'compiled-source-normal-publication.json')
inventory={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(raw.rglob('*')) if p.is_file()}
(e/'whole-raw-file-inventory.json').write_text(json.dumps(dict(root=str(raw),files=inventory,whole_files_retained=True,future_original_artifact_publication='genuine NEW27; not yet published',scope='custody only, no interpretation'),indent=2)+'\n')
(e/'outcome.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),source=source,protocol='8e7e1c published CBC before code',native_original_exit=0,phases=phases,whole_original_native_records=100,whole_calls=60,journal_events=660,all_reports_inputs_scalars_checks_counters_nontime_parity=True,elapsed_values_retained=True,explicit_provenance_metadata_change_checked=True,four_entire_stage_omissions=dict(actual_exit=101,accepted_output_absent=True,whole_inputs_retained=True),all_three_compiled_runtime_images_unchanged=True,all_prior_1503_current_17_driver_2_guards=0,rank_RREF_source_character_BSGS='NOT RUN',scope='unsigned complete passive capture and whole-report parity, not signed execution or rank interpretation'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Passive original relation capture native at normallypublished6d823770 after exact originalcheckpoint22 run43731578817/job132864971965/art14168526714: actual native0 and28orderedphases match; whole100native/60calls/660synced journal events complete; every full input/scalar/check/non-time report and counter matches original accepted IC under elapsed-onlyb5e431 with truthful declared provenance metadata. All four whole-stage omission controls actual101 with no accepted output; all1503prior17compiled2driver guards and all three original runtime/full prepared bytes hold. Every complete raw capture, journal, negative input and source/binary retained for genuineNEW27. Rank/RREF and source-character/norm/BSGS not yet run; unsigned finite correctness-custody only, no calibrated advantage or signed/global acceptance.']
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();print(claim,flush=True)
entry='''\n\n# Whole passive relation capture and report parity\n\n## What was done\n\nCLAIM: normallypublished6d823770/originalcheckpoint22 genuine28member download and exact remote/local originalgates0; full native0/28phases/all100original records/60calls/660journal events. All complete input/scalar/check/non-time reports and counters agree under elapsed-onlyb5e431. Four entire capture-stage omissions actual101/nooutput. All1503prior17compiled2driver guards and three runtime images/fullprepared copies hold. Whole raw trace/journal/controls retained at scratch/ct101-original-relation-kernel-native-01; exact source/build/import retained. [pcc:unverified]\n\n## Decisions made\n\nStrict passive-parity boundary passed as unsigned evidence. Begin full60call exact RREF certificates and separate replay without changing compiled observer or production solver. Retain all original failed FB30 candidates; no rank attribution yet. [pcc:unverified]\n\n## Open threads\n\nRank/full-active column certificates, independent row-operation replay and conditional Lean implications, then separate post-solver actual norm/BSGS character and descent checks under published8e7e1c. GenuineNEW27 must preserve all post26 source/build/raw/failed control/fullprepared/CI-artifact/joblog/proposal roots; Overlay capacity requires RAM staging for any large fetch. Root/ec632 and GitHub persistent queue need current exact consumer acceptance and observer updates. [pcc:unverified]\n\n## Errors\n\nNo native capture failure. Earlier compiled-governance inherited EOF whitespace failure remains preserved; exact per-path whitespace attribute preserved original bytes. All historical failures and unsigned standing remain. [pcc:unverified]\n'''.replace('CLAIM',claim)
with (r/'docs/session-logs/2026-11-15.md').open('a') as f:f.write(entry)
with (r/'.resume/RESUME.md').open('a') as f:f.write(entry)

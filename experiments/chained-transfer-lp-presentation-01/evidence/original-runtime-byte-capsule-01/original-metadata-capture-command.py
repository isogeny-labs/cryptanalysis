from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess

r = Path('/workspace/cryptanalysis')
p = r / 'experiments/chained-transfer-lp-presentation-01'
hold = Path('/dev/shm/ct251-complete-original-baseline-runtime-capsule-01')
g = p / 'evidence/original-runtime-byte-capsule-01'
g.mkdir()
assert (hold/'original.exit').read_text().strip() == '0'
assert all(line.endswith(' 0') for line in (hold/'all-actual-metadata-phases.txt').read_text().splitlines())
for f in sorted(hold.iterdir()):
    if f.is_file() and f.name != 'entire-original-artifact.zip':
        assert f.stat().st_size < 100_000
        shutil.copyfile(f,g/f.name)
shutil.copyfile(__file__,g/'original-metadata-capture-command.py')
manifest=json.loads((p/'runtime-01/manifest-01.json').read_text())
record=dict(at=datetime.now(timezone.utc).isoformat(),
    whole_capsule_hold=str(hold), entire_original_artifact=manifest['original_archive'],
    complete_selected_member_count=len(manifest['members_used_without_execution']),
    complete_selected_bytes=sum(x['bytes'] for x in manifest['members_used_without_execution']),
    actual_assembly_exit=0, old_native_executed=False,
    prospective_EKS_ABI_qualification=False, new_cold_120s_qualification=False,
    publication_scope='whole original archive retained at its original GitHub artifact, complete selected byte assembly and logs only; genuine scientific NEW28 pending')
(g/'whole-byte-hold-and-scope.json').write_text(json.dumps(record,indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data',
 '--statement','Unchanged original baseline runtime byte capsule: actual metadata assembler exit0, all12 recorded byte/profile/engine custody phases0. Entire original340729140-byte1242-member artifact14192302267 retains SHA4972d58159bd44cfcb39daf29d8e3813c3c6ead85d928b281e022d1c15ec4de3 before/after;56 complete selected members total69693424 bytes, both compiled/runtime native pairs and full original prepared RLIB/RMETA/source/closure/log receipts retained. Original Consumerb7b919 and upstream3d49af7 are exact earlier artifact provenance, distinct from new pure-tool2d46258. Entire original ZIP is held without replacing it by selections. No original binary executed, no new compilation, historical population, EKS ABI qualification or cold120s qualification. Old3m48/900s setup remains unchanged. Full original360 and actual-norm witness-auditor executions, source-built OCI and genuine all-rawNEW28 remain prospective; actual exhausted budgets e42949 stop paid launches.']
for f in sorted(g.iterdir()):
    cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
text=f'''\n---\n\n{record['at']}\n# Complete original baseline runtime byte capsule\n\n## What was done\n{claim}: all12 metadata byte/profile/engine phases0; entire original340729140B archive and56 complete selected native/source/prepared members69693424B retained. No original binary executed or new compilation. Originalb7/upstream3d49af7 provenance is distinct from new pure tools2d46258. [pcc:unverified]\n\n## Decisions made\nPublish this finished custody component plus actual latest5e80 native/post/proof CI8db45c and budget-stope42949. Continue full-population driver source with exact earlier binaries; no paid launch under exhausted daily/monthly budgets. [pcc:unverified]\n\n## Open threads\nFull60/240/62, separate unchanged360 and witness auditor, seven whole controls/feedback/post, actual source-built OCI/UID/runtime qualification and genuineNEW28. Root4401 merged5ae1; later source checkpoint must use a fresh owned branch. [pcc:unverified]\n\n## Errors\nEarlier wrong-upstream metadata draft stopped before manifest creation, retained in the prior log. Original cold compile3m48 under900s is not a new120s pass. Current full science and price advantages remain unestablished. [pcc:unverified]\n'''
with (r/'docs/session-logs/2026-11-16.md').open('a') as f:f.write(text)
with (r/'.resume/RESUME.md').open('a') as f:f.write(text)
print(claim)

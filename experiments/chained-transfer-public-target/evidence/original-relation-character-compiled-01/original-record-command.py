"""Record full compiler/source/runtime/prepared custody before any witnesses run."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'original-relation-character-01';b=Path('/workspace/scratch/ct103-original-relation-character-build-01');e=s/'evidence/original-relation-character-compiled-01';e.mkdir()
assert(b/'original.exit').read_text().strip()=='0'
for label in ['producer','auditor','control']:
 assert(b/(label+'-compile.exit')).read_text().strip()=='0';v=json.loads((b/(label+'-compiled-custody.json')).read_text());assert Path(v['actual_path']).read_bytes()==Path(v['copy']).read_bytes()
assert json.loads((b/'engine-reused.json').read_text())['actual_reuse']is True
for v in json.loads((b/'engine-prepared.json').read_text())['files']:assert Path(v['actual_path']).read_bytes()==Path(v['copy']).read_bytes()
for q in sorted((b/'actual-source').rglob('*')):
 if q.is_file():assert q.read_bytes()==(p/q.relative_to(b/'actual-source')).read_bytes()
shutil.copyfile(__file__,e/'original-record-command.py')
for q in sorted(b.iterdir()):
 if q.is_file()and not q.name.endswith('.bin'):
  body=q.read_bytes()
  if len(body)>60000:packed=lzma.compress(body);assert lzma.decompress(packed)==body;(e/(q.name+'.xz')).write_bytes(packed)
  else:shutil.copyfile(q,e/q.name)
for name in ['frozen-current-inputs-01.sha256','frozen-native-driver-01.sha256']:shutil.copyfile(p/name,e/name)
inventory={q.relative_to(b).as_posix():dict(bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest())for q in sorted(b.rglob('*'))if q.is_file()}
(e/'whole-build-source-runtime-inventory.json').write_text(json.dumps(dict(root=str(b),files=inventory,full_original_field_prepared_copies_retained=True,future_original_artifact_publication='genuineNEW27 pending'),indent=2)+'\n')
(e/'outcome.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),source_parent='4ec3401fce8a501ea40abb15fdf84947b7d7a111',published_protocol='8e7e1c/CBC before code',all_three_bins_first_compile=0,prior_guards=1532,compiled_subject_guards=11,native_driver_guards=2,whole_field_engine_closure_same=True,actual_fresh_engine_reuse=True,full_RLIB_RMETA_before_after_equal=True,native_witnesses_character_descent='NOT RUN',scope='unsigned compiled/source/runtime custody only; exact source publication/original checkpoint required before native'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Post-solver source-character package compiled01 under prospective8e7e1c after complete passive d118b9/rankc0479c/conditional proof19c467: allthree original closure/lockedoffline compiler bins firstattempt0,1532prior11compiled2driver guards, exact full original field-engine dependency-features-target graph and fullRLIB-RMETA bytes/actual freshreuse0; no second preparation. Producer computes complete post-solver cofactor4 norm-BSGS proposals for all60calls/allFB-graph-known-split points/eta-G-Q-three starting classes, complete baby tables and failure populations; no solving API/private scalar input. Separate auditor re-evaluates actual norm/projection/direct source scalar witnesses, independent geometric eta reconstruction, all matrix/column/known-log/descent comparisons with source point-group crosschecks and direct target checks; scalar witness mutation targets direct source equation. Native witness generation/actual character-descent result NOTRUN; compiled source normal publication/exact original receipt required before22phase native. Allwhole source/build/runtime/prepared copies heldfor genuineNEW27; unsigned compiled boundary only.'
]
for q in sorted(e.iterdir()):cmd+=['--proof','attestation:'+q.relative_to(r).as_posix()]
for q in sorted(p.rglob('*')):
 if q.is_file():cmd+=['--proof','attestation:'+q.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();print(claim,flush=True)
entry=f'''\n\n# Post-solver source-character tools compiled; native pending\n\n## What was done\n\n{claim}: original-relation-character-01/producer-auditor-control compiledfirst0 under8e7e1c; all1532prior11compiled2driver guards/full original dependency-features-target closure/fullpreparedRLIB-RMETA/actualfreshreuse0. Entire post-solver witness population/allthree BSGS tables and all60calls remain mandatory; separate actualnorm/directsourcegroup checks and whole scalar-witness mutation implemented. No witness/character/native measurement yet. [pcc:unverified]\n\n## Decisions made\n\nNormal-publish compiled source and import its exact original checkpoint, then22phase run-native-01.sh under900s2GiB percompleteproducer-auditor. No solving API or private target scalar input; compare finite character/matrix/knownlog/fullsplitwalk-descent evidence before causal interpretation. [pcc:unverified]\n\n## Open threads\n\nActual whole60witness/direct-source audit/scalar control, result visual/PDF, updated Root mirror/GitHub queue and genuineNEW27. Ranknativec0479c/proof19c467 normallypublished4ec3401; allnumericLean/globalcharacter/modelprogram/cost-liveadmission/reference obligations remain. [pcc:unverified]\n\n## Errors\n\nNo character compile failure. The temporary consumer root target proof-source duplicate became untracked; moved only that exact owned directory intact to scratch/ct102-consumer-proof-stage-custody-01 with byte-equality/hash/Git-state receipt. Canonical proof/raw gate copies remain unchanged; clean consumer state restored before character source work. Two failed Lean development attempts remain preserved. [pcc:unverified]\n'''
for file in [r/'docs/session-logs/2026-11-15.md',r/'.resume/RESUME.md']:
 with file.open('a')as f:f.write(entry)

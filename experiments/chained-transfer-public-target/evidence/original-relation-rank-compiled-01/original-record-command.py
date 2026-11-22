"""Freeze literal source/build receipts and append an unsigned compiled claim."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'original-relation-rank-01';b=Path('/workspace/scratch/ct102-original-relation-rank-build-02');e=s/'evidence/original-relation-rank-compiled-01';e.mkdir()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()=='df107ab15d413f1b8e414e61ea19d6dbb58097d8'
shutil.copyfile(__file__,e/'original-record-command.py')
for name in ['all-bins-compile.exit','all-bins-compile.stderr.txt','compiled-binaries.json','observation.json','final-source-guards.sha256','rustc-version.txt','cargo-metadata.exit']:
 shutil.copyfile(b/name,e/name)
for file in ['producer-compile.exit','replay-compile.exit']:
 assert (b.parent/'ct102-original-relation-rank-build-01'/file).read_text().strip()=='0'
 shutil.copyfile(b.parent/'ct102-original-relation-rank-build-01'/file,e/('first-'+file))
for name in ['all-bins-compile.jsonl','cargo-metadata.txt']:
 import lzma
 body=(b/name).read_bytes();compressed=lzma.compress(body);assert lzma.decompress(compressed)==body;(e/(name+'.xz')).write_bytes(compressed)
for v in json.loads((b/'compiled-binaries.json').read_text()).values():assert Path(v['actual_path']).read_bytes()==Path(v['copy']).read_bytes()
for q in sorted((b/'actual-source').rglob('*')):
 if q.is_file():assert q.read_bytes()==(p/q.relative_to(b/'actual-source')).read_bytes()
inventory={}
for root in [b,b.parent/'ct102-original-relation-rank-build-01']:
 inventory[str(root)]={q.relative_to(root).as_posix():dict(bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest())for q in sorted(root.rglob('*'))if q.is_file()}
(e/'whole-build-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
(e/'outcome.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),published_protocol='8e7e1c/CBC before source',prior_capture='d118b9/df107ab1 strict whole60call parity passed',all_three_compiler_bins_exit=0,producer_and_replay_first_compiles=0,source_guards=10,no_original_solver_or_observer_source_changed=True,all_compiled_source_and_actual_executable_bytes_pinned=True,rank_RREF_character_measurements='NOT RUN',conditional_Lean='pending',scope='unsigned source/compilation checkpoint only; exact normal publication/original receipt required before native'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Exact relation-rank package compiled under prospective8e7e1c after whole passive captured118b9: initial producer/replay compiles0 and final lockedoffline all-three-bin compile0; literal whole source, originalSHA, full compiler metadata and all three actual executable copies pinned. Producer retains all60calls/six matrices each/full sparse coefficients/dense projection/unknown inactive status/row operations/RREF/pivots/full basis/residual and exclusion population. Separate replay uses extendedEuclid arithmetic without importing producer elimination; whole coefficient and constrained-coordinate controls implemented. No rank/native/RREF/source-character result yet; conditional Lean implications and post-solver norm-BSGS remain pending. Exact source normal publication/original checkpoint required before22phase native. Whole builds/source/binaries heldfor genuineNEW27; unsigned compilation only.']
for q in sorted(e.iterdir()):cmd+=['--proof','attestation:'+q.relative_to(r).as_posix()]
for q in sorted(p.rglob('*')):
 if q.is_file():cmd+=['--proof','attestation:'+q.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();print(claim,flush=True)
entry=f'''\n\n# Exact rank certificate tools compiled; native pending\n\n## What was done\n\n{claim}: original-relation-rank-01/three Rust bins compiled0, lockedoffline serde-only graph/no field-engine import, complete compiler source/runtime copies/10sourceguards pinned. Separate producer/RREF and replay/extendedEuclid arithmetic; all60calls/six matrices each remain mandatory, unknown inactive coordinates retained, all row operations and full nullspace bases retained. Whole coefficient and constrained-coordinate controls implemented. Protocol8e7e1c preceded all code; capture d118b9 preceded interpretation. [pcc:unverified]\n\n## Decisions made\n\nNormal-publish compiled source, import exact original checkpoint, then22phase run-native-01.sh under900s2GiB. No rank or character measurement yet. Whole native JSONL and both whole controls staged in RAM only for capacity, then each losslessly XZ persisted with CRC and full decoded-byte comparison; no population reduction. [pcc:unverified]\n\n## Open threads\n\nComplete exact rank replay/controls; conditional Lean row-operation and finite-character implications; separate post-solver norm/BSGS/full known-log and descent checks. GenuineNEW27 and Root additive acceptance/capture mirror remain queued. Persistent GitHub3904/both PRs now reflect df107ab1/passive capture and fresh CI0b4ddb. [pcc:unverified]\n\n## Errors\n\nNo compiler failure. First build01 contains producer/replay before the additional control bin; finalbuild02 contains unchanged compiler subjects plus control bin, all three0, and preserves both whole source snapshots. Historical failures remain preserved. [pcc:unverified]\n'''
for file in [r/'docs/session-logs/2026-11-15.md',r/'.resume/RESUME.md']:
 with file.open('a')as f:f.write(entry)

"""I/O-only custody, source guard versioning, and persistent queue update."""
from pathlib import Path
import hashlib, json, lzma, shutil, subprocess
r=Path('/workspace/cryptanalysis'); s=r/'experiments/chained-transfer-public-target'
ref=s/'ci_nondual_preflight/reference-03.sha256'
rows=dict((p,h) for h,p in (x.split('  ',1) for x in ref.read_text().splitlines()))
for name in ['check.sh','capture_engine.py']:
 p=s/'ci_nondual_preflight'/name; rows[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
rows[ref.relative_to(r).as_posix()]=hashlib.sha256(ref.read_bytes()).hexdigest()
assert len(rows)==980
(ref.parent/'reference-04.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in sorted(rows.items())))
e=s/'evidence/observer-storage-build-03'; e.mkdir()
shutil.copyfile(__file__,e/'original-record-command.py')
for prefix,raw,files in [
 ('unit03',Path('/workspace/scratch/ct79-observer-unit-build-03'),['compile.jsonl','compile.stderr.txt','compile.exit','actual-binary.json','original-command.sh']),
 ('comparator01',Path('/workspace/scratch/ct79-observer-parity-build-01'),['compile.txt','compile.exit','lock.txt','lock.exit','binary.json'])]:
 for name in files:
  b=(raw/name).read_bytes(); (e/(prefix+'-'+name+('.xz' if len(b)>60000 else ''))).write_bytes(lzma.compress(b) if len(b)>60000 else b)
 assert (raw/'compile.exit').read_text().strip()=='0'
old=s/'norm-arithmetic-audit'; new=s/'norm-arithmetic-storage-02'; custody=[]
for line in (s/'observer-storage-prior-inputs-02.sha256').read_text().splitlines():
 h,name=line.split('  ',1); original=r/name; assert hashlib.sha256(original.read_bytes()).hexdigest()==h
 p=new/original.relative_to(old); equal=p.read_bytes()==original.read_bytes()
 assert equal or p.relative_to(new).as_posix() in ['README.md','taps/src/lib.rs']
 custody.append(dict(old=name,new=p.relative_to(r).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),literal_equal=equal))
assert len(custody)==24 and sum(x['literal_equal'] for x in custody)==22
(e/'literal-source-custody.json').write_text(json.dumps(custody,indent=2)+'\n')
allsource={p.relative_to(r).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(new.rglob('*')) if p.is_file()}
(e/'all-new-source.json').write_text(json.dumps(allsource,indent=2)+'\n')
(e/'scope.json').write_text(json.dumps(dict(unit03_compile=0,comparator01_compile=0,unit_execution='NOTRUN',math_parity='NOTRUN',whole_ledger_parity='NOTRUN',cold_panel='NOTRUN',source_scope='22 of baseline24 files byte-identical; only taps implementation and README differ. Comparator and conditional Lean proof are additive.',standing='unsigned; compile is not native or performance acceptance'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Observer-storage source03 and strict whole-packet comparator compile0; actual Cargo executable and comparator copies retained with complete byte hashes. Original24 source files unchanged; derivative22 are literal equal and only taps/README differ. Both source01 compiler failure and fixed02 binary retained; latest03 inlines only internal storage helpers. Unit/native math parity/hook controls/old whole-ledger parity/full cold panel NOTRUN. No signed execution or speedup standing.']
for p in sorted(e.iterdir()): cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip(); print(claim,flush=True)
entry='''# Replay alias correction and observer prototype ready for exact-source validation

Sourcea50 replay03: original-engine preparation0 and first wrapper compile0, then the old custody assertion rejects Cargo's different primary/dependency RLIB filenames before native execution. CI43632431402/job132561796938 retained the whole211046-char log and17171679B ZIP14128926813/all25 members (claim c32949). Local02 reproduces the same failure; post-failure diagnostics establish complete actual RLIB/RMETA alias-byte equality and retain the actual compiled test binary, which was NOTRUN. CI03 did not preserve its compiled test executable; no runtime-custody claim is made. [pcc:unverified]

Fix04 compares complete prepared/current/dependency library bytes and original package/source/profile/features with actual fresh reuse, retains both paths, and copies each compiled test executable before the next custody assertion. Actual-data positive0 and a changed RMETA-byte negative1/no receipt are retained under2b4dd0. Reference04 pins980 inputs and all prior references; mathematical4/6/5/9 records, whole omissions, actual old dual controls, proof gates and original900s2GiB native limits are unchanged. Full corrected replay and exact-head CI are NOTRUN. [pcc:unverified]

Observer prototype under previously published289a79/65433a now exists. New indexed counters/exact-key cache and first-entry TLS ownership affect only the additive taps implementation; baseline24 untouched and derivative22 literal equal. Failed first compilation and fixed02 preserved1ba2ca; source03 and whole-packet comparator compile0 ({claim}). Unit/native parity/actual hook controls/whole12-old-cold plus both60-reuse packet parity/full120cold census remain NOTRUN. Both original434/435 Lean gates pass6 declarations (two named conditional indexed-counter roots plus four generated helpers), zero trusted: summary3797ef, exact local bindings5997e5/00280b. Dynamic insertion/Vec/u64/TLS/bucket/full Rust bridges remain open; unsigned standing only. [pcc:unverified]

Immediate: normal-publish fix04+prototype, update issue3904/PR1523, obtain the original automatic exact clean-head checkpoint/all28 members/source Resume/tool/receipt equality/local gate0. Then run one unfiltered observer unit test and a fresh physical03 full22 replay from this head/producer3d49 with a NEW cache. Materialize the literal observer derivative and prepare its engine within the published900 setup bound; preserve wrapper120, four observer-OFF whole mathematical records, actual enabled/disabled/omitted-hook controls, then original120cold900 plus both60reuse combined900 and unchanged full analyzer. Compare ALL old whole packets/ledgers exactly using Rust and reject a real whole-packet omission. Preserve every failure/partial result; never price the operation census or waive the old cold120 compile requirement. [pcc:unverified]

Genuine18 settled0e8aa2/85aac5/root4b0871aa, all24853 guards23 links/owned bytes and complete20 roots416 members retained; subsequent whole data needs NEW19. D12/D24 matched-source negatives27fb3a/6d2c97 and finite residue68cd8c/ee88e7 remain unchanged. No new Jacobian map, fourth old-protocol edge, calibrated advantage or novelty claim. Root/main/geometry/benchmark/matched-reference/vault8edec422/KB127 limits remain; no paid launch or waiver. Continue the next unblocked research task after this validation. [pcc:unverified]

Raw latest: /workspace/scratch/ct79-nondual22-CI-failure-03, ct78-nondual22-full-02, ct79-Cargo-alias-correction-04, ct79-observer-unit-build-03, ct79-observer-parity-build-01, ct79-counter-storage-proof-01. Closed-derived cleanupct79-01 records369632108B/206 unguarded dependency files; actual executables (including root263MB), original source/raw/currentct57/sealedB caches retained. [pcc:unverified]

---

'''.replace('{claim}',claim)
for p in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']:
 p.write_text(entry+p.read_text())
session=r/'docs/session-logs/2026-11-14.md';session.write_text(session.read_text()+'\n'+entry)
helper=Path('/workspace/scratch/ct78_commit_engine_source_03.py').read_text().replace("ci_nondual_preflight/reference-03.sha256","ci_nondual_preflight/reference-04.sha256")
needle="run('observer-prior24',['sha256sum','--check',str(s/'observer-storage-prior-inputs-02.sha256')])"
assert needle in helper
helper=helper.replace(needle,needle+"\nrun('observer-new-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p) for p in sorted((s/'norm-arithmetic-storage-02').rglob('*.rs'))]])\nrun('observer-new-shell',['bash','-n',str(s/'norm-arithmetic-storage-02/quadratic-canary.sh'),str(s/'norm-arithmetic-storage-02/run-panels.sh')])")
Path('/workspace/scratch/ct80_commit_alias_observer_source_04.py').write_text(helper)

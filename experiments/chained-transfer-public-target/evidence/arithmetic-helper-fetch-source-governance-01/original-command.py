"""Versioned dependency-hydration remedy and governance; no research arithmetic in Python."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, lzma, shutil, subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='ca9b0626dd6b9811be8572562c8f9d14f61aea8d';at=datetime.now(timezone.utc).isoformat()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
g=s/'evidence/arithmetic-helper-fetch-source-governance-01';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
state=f'''# Arithmetic fresh replay complete; locked helper hydration correction — {at}

## Goal
Continue nontrivial DLP-preserving transfers, chained Jacobian maps, prime-field descent and computational comparisons; advance after each result. [pcc:unverified]

## State
Scientific source ca9b0626 normally published0 (governance eeea8a). Native8d0c27, vectors8c2406 and final three-page92135B report03cfb7 remain immutable. Fresh independent386296 checks source02/21+self22, original785 and all derived guards0; all14 ordered native+tee0/0, one unfiltered pass, all86 records exact under only frozen walls, entire7113-row census+all metadata exact with no masks, actual omitted-hook positive0/negative101 same algebra. Whole raw sources/results/binaries retained. All claims unsigned. [pcc:unverified]

Own ca9 CI5523a3: other17 workflows success/sign skipped; new18th run43563844912/job132353228514 actual1 before compilation, helper offline metadata101/tee0 missing separately locked serde1.0.229. Complete5293826B ZIP/all1555members and whole log retained. Prospective7b2367 before source remedy/control; focused34e2c1 genuinely empty CARGO_HOME offline101/locked fetch0/same offline0/all copied source+lock guards0. [pcc:unverified]

## Spec and next action
This correction adds only `fetch-taps` using unchanged helper Cargo.lock before offline `lock-taps`:15 ordered phases total, all existing14 criteria retained. Current reference03 has22 sources+self23, including the new protocol; historical01 and02 bytes unchanged. Taps, algebra, controls, solver, all86 comparisons, whole7113-row golden and every old17 workflow remain unchanged. Commit/push normally, then inspect automatic own-source18 CI full15-phase replay. Do not manually redispatch settled workflows. No second unchanged local science replay is needed: the ca9 full and focused clean-cache control address this dependency-only change; complete new CI must still pass. [pcc:unverified]

## Custody
Genuine92a00d/420904: eight remote replays before a0c/direct0a,14wholeobjects/8S3+6Git,guard10released. Genuine1f4cbc/877d0e: one remote replay before14fa/direct245, whole75764B control archive,guard11released. Future artifact FF requires NEWguard12. Fresh ca9 full/CI/empty-cache control large whole captures await that batch; complete local evidence preserved. Root14fa has pending latest-publication metadata; checkpoint it and update PR3877/1523/issue3904. [pcc:unverified]

## Next research
Review actual matched HLP(1,0) beta quotient and Frobenius/rational lifting before implementing complete rational-point evaluation or global coordinates. Continue admitted cold/online calibration and strongest references when live budget/capacity and matching image are established. Existing unpriced vectors show more products/fewer inversions. Root124/clock101/main ledger/signing/reviews/conflict, actual geometry/formal bridges and global log extension remain open. Vault8edec422 locked/KB unavailable, no novelty inference. [pcc:unverified]

## Runs in flight
No local science run. All14 ca9 phases and focused helper control terminal; automatic own-source18 CI will follow this normal publication. Raw /workspace/scratch/ct72-arithmetic-full-01, ct72-ca9-own-CI-01 and ct72-helper-empty-cache-control-01. Actual binaries/source/raw retained; only closed compiler incremental636495620B removed with whole580-file hash receipt. [pcc:unverified]
'''
for f in [s/'RESEARCH_QUEUE.md',s/'CHECKPOINT.md',r/'.resume/RESUME.md']:f.write_text(state+'\n---\n\n'+f.read_text())
with (r/'problems/chained-transfer-new-jacobian-ic-cost-coverage.md').open('a') as f:f.write('\n2026-11-14: unsigned386296 fresh ca9 full checks all14 native/tee0/0, one unfiltered pass, all86 exact under frozen walls, entire7113-row census+metadata exact without masks,21+self/original785/derived guards0. Own CI5523a3 dependency-only missing helper serde229 retained before compilation; prospective7b2367 plus focused34e2c1 empty-cache101/fetch0/offline0/lockguard0 supports version03 fetch-taps/new15 phases. Own corrected18 CI still pending. More products/fewer inversions remain unpriced; full calibrated cold/online costs/strongest references/admission remain open. [pcc:unverified]\n')
scopes=[str(s.relative_to(r)),'.github/workflows/chained-transfer-arithmetic-audit.yml','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-14.md','.resume/RESUME.md','problems/chained-transfer-new-jacobian-ic-cost-coverage.md','.gitattributes']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scopes],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(label,cmd):
 q=subprocess.run(cmd,cwd=r,capture_output=True);b=q.stdout+q.stderr;(g/(label+'.txt.xz' if len(b)>60000 else label+'.txt')).write_bytes(lzma.compress(b) if len(b)>60000 else b);(g/(label+'.exit')).write_text(str(q.returncode)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,b[:1600]
run('original784',['sha256sum','--check',str(s/'ci_norm_sampling/reference-01.sha256')]);run('current22',['sha256sum','--check',str(s/'arithmetic-audit/reference-03.sha256')])
for p in ['arithmetic-audit/reference-01.sha256','arithmetic-audit/reference-02.sha256','arithmetic-audit/taps/Cargo.lock','arithmetic-audit/controls.rs','arithmetic-audit/literal-hooks.patch','arithmetic-audit/expected-census-01.json.xz','arithmetic-audit/taps/src/bin/census.rs']:
 assert (s/p).read_bytes()==subprocess.check_output(['git','show',base+':'+str((s/p).relative_to(r))],cwd=r),p
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','scripts'],cwd=r)
assert subprocess.check_output(['git','diff','--name-only',base,'--','.github/workflows'],cwd=r,text=True).splitlines()==['.github/workflows/chained-transfer-arithmetic-audit.yml']
run('shell',['bash','-n',str(s/'arithmetic-audit/check.sh')]);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-arithmetic-audit.yml']);run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode() for p in paths() if p.endswith(b'.md')]]);run('whitespace',['git','diff','--check','--',*scopes]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate']);run('reportPython',['python3','tools/ci/check_report_graph_python.py'])
def stage():
 ps=paths();f=Path('/workspace/scratch/ct72-helper-source.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True);selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for name in selected:
  if name.startswith(b'pcc/claims/'):
   for proof in json.loads((r/name.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     v=proof['subject'];assert hashlib.sha256((r/v['path']).read_bytes()).hexdigest()==v['sha256'];assert v['path'].encode() in selected or subprocess.run(['git','cat-file','-e',base+':'+v['path']],cwd=r,capture_output=True).returncode==0
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(base=base,prospective='7b2367',focused_control='34e2c1',separate_original_full='386296/ca9/14phases',preserved_CI_failure='5523a3',all_original784_and_current22_hashes=0,historical01_02_taps_solver_controls_golden_and_original17_unchanged=True,all_recorded_governance_checks=0,new_subject_hashes_and_exact_staging_checked=True,scope='dependency-hydration-only/new15 phases; automaticown18 CIpending; unsigned'),indent=2)+'\n')
c=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Version03 locked helper-fetch correction governance: all original784/current22 source guards0, shell/actionlint/ledger/prose/working+cachedwhitespace/wiring/benchrec/reportPython/artifact0/exact subject hashes+staging checked. Historical01/02, taps/algebra/controls/solver/golden/all86masks and old17workflows unchanged; only fetch-taps plus protocol/sparse inclusion/currentmanifest03. Preserved ca9full386296 and CIfailure5523a3, prospective7b2367 and clean-cache34e2c1. Normal publication/automaticown18 CIpending; unsigned.']
for f in sorted(g.iterdir()):c+=['--proof','attestation:'+str(f.relative_to(r))]
cl=subprocess.check_output(c,cwd=r,text=True).strip();Path('/workspace/scratch/ct72-helper-source-governance.claim').write_text(cl+'\n');selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: hydrate locked arithmetic helper before offline replay'],cwd=r,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip();print(cl,head,len(selected),flush=True)
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-public-target-20261113','/workspace/scratch/ct72-helper-source-publication-01'],cwd=r,capture_output=True);Path('/workspace/scratch/ct72-helper-source-publication-caller.txt').write_bytes(q.stdout+q.stderr);print('normalpub',q.returncode,flush=True);assert q.returncode==0

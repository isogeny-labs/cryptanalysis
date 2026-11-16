"""Closed negative census/report/compiled-diagnostic I/O custody."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
def claim(name,raw,statement,files):
 e=s/'evidence'/name;e.mkdir();shutil.copyfile(__file__,e/'original-record-command.py')
 index={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(raw.rglob('*')) if p.is_file()};(e/'whole-closed-raw-members.json').write_text(json.dumps(index,indent=2)+'\n')
 for p in files:
  if not p.is_file() or p.suffix=='.bin':continue
  b=p.read_bytes();v=lzma.compress(b) if len(b)>60000 else b
  if len(v)>60000:continue
  dest=e/p.relative_to(raw);dest=dest.with_name(dest.name+('.xz' if len(b)>60000 else ''));dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(v)
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
 for p in sorted(e.rglob('*')):
  if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
 print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
raw=Path('/workspace/scratch/ct80-observer-validation-04')
for f,expected in [('panels/cold-panel.exit',124),('panels/reused-panel.exit',0),('full-panel-caller.exit',124),('full-analysis-caller.exit',101),('old-parity-caller.exit',101),('final-derived-source.exit',0),('final-original-785.exit',0),('orchestrator.exit',1)]:assert(raw/f).read_text().strip()==str(expected),f
assert not(raw/'accepted-full-analysis.json').exists() and not(raw/'accepted-old-whole-parity.json').exists()
success=[p for p in(raw/'panels').glob('cold-*.exit') if p.name!='cold-panel.exit' and p.read_text().strip()=='0'];assert len(success)==18
claim('observer-storage-cold-bound-negative-04',raw,'Detached observer04 after exact77 original checkpoint preserves passing prior math/unit/real-hook/mode controls and actual compiler bytes/modes. Enclosing supervisor survives the original900 deadline and records terminal outcomes: cold-panel124 with18 individual success receipts, BOTH separate60-case reuse streams0/combinedreuse0, original runner124. UNCHANGED full Rust analyzer101/no accepted output and original strict full-population parity checker101/no output; all785 original and complete derived-source guards0. Worker/supervisor1 denotes unmet full120cold criterion, NOT an observer arithmetic mismatch or claimed impossibility. Interrupted03 remains unknown17/no panel terminal, not relabeled124. Complete raw/source/executables retained for NEW19. RETROSPECTIVE partial old-whole-packet/vector diagnosis is NOTRUN; no source-vector interpretation, calibrated time/cost/observer speedup or ECDLP advantage claim.',list(raw.iterdir()))
raw=Path('/workspace/scratch/ct80-observer-partial-parity-build-04');assert(raw/'compile.exit').read_text().strip()=='0'
rows=[json.loads(x) for x in(raw/'compile.jsonl').read_text().splitlines()];bins=[x for x in rows if x.get('reason')=='compiler-artifact' and x.get('executable')];assert len(bins)==1;row=bins[0];p=Path(row['executable']);shutil.copy2(p,raw/'actual-diagnostic.bin');(raw/'actual-executable.json').write_text(json.dumps(dict(Cargo_artifact=row,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()),indent=2)+'\n')
claim('observer-storage-retrospective-diagnostic-build-04',raw,'Separate RETROSPECTIVE partial-observation Rust diagnostic compiles0 within120 after actual04cold124; actual source/Cargo executable bytes retained. Requires old/new actual cold124 and both reuse0, retains every actual new complete/missing cold case, compares ALL12 old cold and BOTH whole60-output reuse packets including EVERY cumulative ledger, no masks/dedup. Output explicitly full_cold_population_accepted=false; NEVER changes original full analyzer or strict complete120 parity checker. Native old-original partial analyzer/new old-packet parity/actual whole-packet omission controls NOTRUN, need fresh exact source checkpoint. Source-native count vectors remain unpriced; no full acceptance or performance claim.',list(raw.iterdir()))
report=s/'reports/twisted-pair-result-01';cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Fixed-twisted-pair actual-results report01: native2a0549, primary-source written derivation, allsix OLD-to-NEW HLP correspondence matrices and source-linked flow; final61121B TWO-page PDF visually inspected. Uses71014e eight ring/modular roots, f2d901 three inverse-factor roots,215bcc three conditional annihilator roots, each both originalgates/zero trusted/exact local bindings; no novelty aggregate. Explicit newell2771711/order11086844, oldell2773073 coprime obstruction conditional on actual HLP-Frobenius/cardinality/Lagrange bridge; complete Jacobian evaluator and original-log transport to twist absent. OriginalD12/D24 negatives remain. Entire first80460B draft/source retained outside report for NEW19; final uses native document-table text, separate originalSVG retained. No timing, calibrated cost/benchmark or signed execution claim.']
for p in [s/'TWISTED_PAIR_DERIVATION_01.md',*sorted(report.iterdir())]:
 if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)

"""Checkpoint actual refinement source through original repository governance."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='c37ad390a4e2ec21bc4e54a005c2642767099199'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
def claim(statement,d):
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
 for p in sorted(d.iterdir()):
  if p.is_file():cmd+=['--proof','attestation:'+str(p.relative_to(r))]
 print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
failed=s/'evidence/odd-product-refinement-source-governance-01'
assert(failed/'prose.exit').read_text().strip()=='1'
claim('Refinement source governance01 stops at originalproselint1:one planned problem checklist paragraph uses prove without an unverified tag. Originalreference702/shell/actionlint/format/reportPython/ledger0 and complete failed output retained. Add only unverified tags to that unfrozen problem checklist;all2514nativeinputs/702CIinputs/Lean/PCC subjects/report/verifiers unchanged. Resume mandatory governance in distinct02;no result promotion or waiver.',failed)
g=s/'evidence/odd-product-refinement-source-governance-02';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
def run(name,cmd):
 p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr
 (g/(name+'.txt.xz'if len(raw)>60000 else name+'.txt')).write_bytes(lzma.compress(raw)if len(raw)>60000 else raw);(g/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,raw.decode(errors='replace')[:1500]
before=json.loads(Path('/workspace/scratch/ct66-odd-product-refinement-native-01/before.json').read_text());assert len(before)==2514 and all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
changed=set(subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','.github/workflows','experiments/chained-transfer-reference',str((s/'odd-product-models').relative_to(r)),str((s/'odd-product-maps').relative_to(r)),str((s/'ci_odd_product').relative_to(r))],cwd=r,text=True).splitlines());assert changed<={'.github/workflows/chained-transfer-odd-refinement.yml'},changed
scope=[str(s.relative_to(r)),'.github/workflows/chained-transfer-odd-refinement.yml','pcc/claims','pcc/ledger.jsonl','problems/chained-transfer-odd-product-kernel-and-odd-factor.md','problems/chained-transfer-primefield-polarized-two-kernel.md','problems/chained-transfer-geometric-two-torsion.md','problems/chained-transfer-public-target-destination-bridge.md','problems/README.md','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
run('reference702',['sha256sum','--check',str((s/'ci_odd_refinement/reference-01.sha256').relative_to(r))]);run('shell',['bash','-n',str(s/'ci_odd_refinement/check.sh')]);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-odd-refinement.yml']);run('format',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'odd-product-refinements/src').glob('*.rs'))]])
run('reportPython',['python3','tools/ci/check_report_graph_python.py']);run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]])
run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
subprocess.run(['git','add','--sparse','-f','--',str((s/'odd-product-refinements/Cargo.lock').relative_to(r))],cwd=r,check=True)
def stage():
 ps=paths();f=Path('/workspace/scratch/ct66-refinement-source.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for p in ps:
  if p.startswith(b'pcc/claims/'):
   for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
     assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0,x['path']
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(base=base,native='147b66/all2514unchanged/oneunfiltered/7wholeJSON',written='active03f46ce2;citation01/02 preserved',formal='3exactfaithful/55total/bothoriginalgates3/zeroaxioms/zero trusted',report='1ca98b/TWO63907-byte finalPDFpages ALLinspected',new_CI='702portable/703outer/10phasepairs/7wholeJSON/3bindings/new12thworkflow',original675_inputs_engines_workflows_verifiers_unchanged=True,governance='ledger/prose/working+cachedwhitespace/wiring/benchrec/artifact/format/actionlint/shell/reportPython0',next='normalpublish/703full/fouractualcontrols/12CI108native55digests/solvercost/beta coordinates/genuinepublication;unsigned/noadvantage'),indent=2)+'\n')
claim('Refinement source governance:published579e08/c37ad390 beforecode;native147b66 all2514guards/7wholeJSON/oneunfiltered/actualtransported2kernels/all135/negativefree52control and exactsame sourceAPIall3/public5. Active written03f46ce2/full geometric types/matched global odddegree beta13^3,completebetacoordinatesopen;citation01/02 preserved. Three faithful exactbindings/bothoriginalgatesPASS3/noaxioms/0trusted/55total;wholeproofs6d04c3/4a41b4,inspectedTWO63907-byte PDFpages1ca98b. Prior675scienceinputs/elevenworkflows/originalengines/verifiers unchanged. New702inputstrict replay/703outer/10phasepairs/12thworkflow prepared;ownfull/fourcontrols/12CI108native55digests pending. Originalledger/prose/whitespace/cachedwhitespace/wiring/benchrec/artifact/format/actionlint/shell/reportPython0/allnewsubjects hash/staging covered. Unsigned/geometrypartial/no computational advantage/globalrootgreen/mergewaiver.',g)
selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: classify transported52 kernels and simplify source maps'],cwd=r,check=True)
print(subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)

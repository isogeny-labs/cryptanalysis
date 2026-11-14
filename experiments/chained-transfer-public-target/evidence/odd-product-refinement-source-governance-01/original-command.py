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
d=s/'evidence/odd-product-terminal-normal-publication-01';d.mkdir()
pub=Path('/workspace/scratch/ct65-terminal-protocol-publication-01');receipt=json.loads((pub/'receipt.json').read_text());assert receipt['original_exit']==0 and receipt['head']==base
for p in pub.iterdir():
 if p.is_file():
  if p.suffix=='.log':(d/(p.name+'.xz')).write_bytes(lzma.compress(p.read_bytes()))
  else:shutil.copyfile(p,d/p.name)
for label in ['pr','root','queue']:
 for suffix in ['.md','-update-api.json']:
  p=Path('/workspace/scratch/ct65-GitHub-2130-'+label+suffix);(d/(label+suffix+'.xz')).write_bytes(lzma.compress(p.read_bytes()))
claim('Normal nonforce c37ad390/treeae482890/direct45ee/66paths/governance51c88e originalpush0 BEFORErefinementcode. Persists full417921/676guards/11CI0ba3a0/101native52digests/rootcdfce1bb normalpub and prospective579e08. Actual GitHubPR1523/root3877/queue3904 updates succeed and whole bodies/API retained losslessXZ. No fullgeometry/performance/globalrootgreen/mergewaiver.',d)
ci=s/'evidence/odd-product-refinement-replay-plan-01';ci.mkdir()
(ci/'plan.json').write_text(json.dumps(dict(prospective='7705d9/579e08 beforeintegration',portable_inputs=702,producer_inputs=348,outer_inputs_with_manifest=703,ordered_positive_native_tee_pairs=10,unfiltered_tests=1,whole_native_JSON=7,original_gates='producer4.35/consumer4.34.1/3audited/0trusted',exact_bindings=3,own_CI_expected='12workflows/108native/55originalcanonicaldigests',fresh_hydration='prior genuine120752-byte fixture02/pinnedoriginaltool',controls='four actual exit2/nooutput/restored before full',current_full_and_own_CI='pending newsource publication;not completed',original_engines_workflows_verifiers='unchanged;one new additive workflow',scope='unsigned correctness/geometrypartial/no benchmark or cost advantage'),indent=2)+'\n')
claim('Refinement strict integration actual702portable/348producer+self703,tenpositive native+tee phases,oneunfilteredtest/ALL7wholeJSON/bothoriginal3declgates/3exactbindings. Previous eleven workflows/675scienceinputs/originalengines/verifiers unchanged;one additive12thworkflow/originalpinnedfixturehydration. Prospective7705d9/579e08 precedes integration;newsource independentfull/fouractualadmissioncontrols/12ownCI108native55canonicaldigests remain pending,not complete. No performance/globalrootgreen/signedexecution/fullgeometricformalization claim.',ci)
q='''# Current research queue — {at}

Source parentc37ad390. Actual refinement147b66/all2514guards/prospective579e08 beforecode;active written03f46ce2,3faithfulbindings/55total,report1ca98b/TWO63907-byte finalpagesinspected. New702input/703outer strict replay is prepared;its own clean full/12CI remain pending. Standing unsigned;no computational advantage. [pcc:unverified]

| Priority | Task | Discriminating next action |
| --- | --- | --- |
| 1 | Refinement normal source/full/CI | Normal commit/push;clean physical newsource/original3d siblings;genuine fixture readonly/materialization verify0;703guards/fouractualcontrols/10phasepairs/ALL7wholeJSON/bothoriginal3declgates/3canonicalbindings. Collect12workflows108native55digests. [pcc:unverified] |
| 2 | Actual target-solver/counter coverage | Inspect original publicIC/Jacobian interfaces;freeze native actual-public correctness/counter-coverage plan for all3 targets,retaining failures. Complete cold+online transport/setup/solver/verification counters and original admission precede any advantage claim. [pcc:unverified] |
| 3 | Complete odd-degree beta coordinates | Matched(1,0) has global written beta degree13^3/polarization13/both13/F=2beta. Investigate actual quotient correspondence/divisor descent;odd-subgroup halving is not complete coordinates. None of current3 kernels free52;all nonsquare free cases retained. [pcc:unverified] |
| 4 | Whole-data publication | New ct65 full/11CI and ct66 native/currentfull/currentCI wholecaptures/completeindices through unchanged genuine publisher. NEWguard07 includingnew702/703/laterwork before any botFF;old3241guard06 historical/released. [pcc:unverified] |
| 5 | Admission/formal/global/merge | Original S3 checkpoint/livebudget/capacity and strongest IC/rho/counter gates;55localbindings geometrypartial/signedexecutionopen. Implement materially different authenticated original rootfixture CI hydration;globalroot notgreen. Preserve mainledger/signing/reviews/conflict;vaultlocked/KBecdb unavailable. [pcc:unverified] |

Settled45ee:independentfull417921/676guards/12phases/17JSON/2bindings;ELEVENCI0ba3a0/101native52digests. Genuine768f4a/0bb0f5 all9captures+2fixtures20objects16S3+4Git. Rootcdfce1bb normalpush0. Preserved failedhistoricalnative/Lean/governance and currentcitation01/02 corrections;all scientific/code/Lean claims unchanged. Continue after each rung. [pcc:unverified]
'''.format(at=datetime.now(timezone.utc).isoformat())
p=s/'RESEARCH_QUEUE.md';p.write_text(q+'\n---\n\n'+p.read_text())
note='''
## {at} — transported52 kernels and identical-output source refinement

Published prospective579e08/c37ad390 beforecode. Native147b66:all2514guards0,oneunfiltered comprehensive test0/ALL7wholeJSON;actualgamma2/all3conjugates/all135intersections/independentGaussianrank,eligible d3,2,1/nonefree52,wronguntransportedfalsefree lastcase. Fresh FastSourceChain matches frozen45eeChain onall3/32odd+zero/public5/fullclasses/tags/recovery/negatives;structuralcallremoval,not speedup. Active written03f46ce2 gives full geometric type and matched global beta degree13^3/both13/F=2beta;completebeta coordinates open. Written01/02 citation mistakes preserved;primary Milne quotient/polarization sections actually read,math/code/Lean unchanged. [pcc:unverified]

Both original Lean gatesPASS3/noaxioms/0trusted;bindingsa08ad5/cc8b69/f8b42f,55total. Wholeproofs6d04c3/4a41b4;report1ca98b TWO63907-byte finalPDFpages ALLinspected. New strict702portable/348producer+self703,tenphasepairs/oneunfiltered/ALL7JSON/both3declgates/3bindings,12th additiveworkflow prepared afterprospective7705d9. Original675inputs/elevenworkflows/engines/verifiers unchanged. Ownnewsourcefull/12CI pending;queueacceptance explicit. [pcc:unverified]

NEXT normalpublish;fouractualadmissioncontrols/physical703full;all12 ownworkflow108native55canonicaldigests;actualtargetsolver/countercoverage and complete odddegreecoordinates;genuinewholepublication/NEWguard07. Originalperformance/global/formal/merge/vault/KB gaps remain. No process in flight;sourcefull hold starts only after its actual preparation. [pcc:unverified]
'''.format(at=datetime.now(timezone.utc).isoformat())
for p in [r/'docs/session-logs/2026-11-13.md',r/'.resume/RESUME.md']:
 with p.open('a')as f:f.write(note)
for name in ['chained-transfer-primefield-polarized-two-kernel.md','chained-transfer-geometric-two-torsion.md','chained-transfer-public-target-destination-bridge.md']:
 with(r/'problems'/name).open('a')as f:f.write('\n2026-11-13:45ee full417921/own11CI0ba3a0 settled;actual refinement147b66 transportsGold/all135intersections/givesd3,2,1 and nonefree52,matched written beta degree13^3 and same-output sourceAPI. Active03f46ce2/55partialbindings/report1ca98b. Complete beta coordinates/cost/fullformalgeometry remain open;see[chained-transfer-odd-product-kernel-and-odd-factor.md](chained-transfer-odd-product-kernel-and-odd-factor.md). [pcc:unverified]\n')
g=s/'evidence/odd-product-refinement-source-governance-01';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
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

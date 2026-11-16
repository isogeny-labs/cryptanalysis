"""Persist terminal correctness evidence and the next prospective protocol."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='45ee45d295b069a8425af423a26e1502219f88e7'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
def claim(statement,d):
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
 for p in sorted(d.iterdir()):
  if p.is_file():cmd+=['--proof','attestation:'+str(p.relative_to(r))]
 print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
d=s/'evidence/odd-product-root-metadata-publication-01';d.mkdir()
pub=Path('/workspace/scratch/ct65-root-final-metadata-publication-01');receipt=json.loads((pub/'receipt.json').read_text());assert receipt['original_exit']==0 and receipt['head']=='cdfce1bb4011d36a7c2512d6c5340f17bafd9b3b'
for p in pub.iterdir():
 if p.is_file():
  if p.suffix=='.log':(d/(p.name+'.xz')).write_bytes(lzma.compress(p.read_bytes()))
  else:shutil.copyfile(p,d/p.name)
claim('Normal nonforce root final-metadata publication cdfce1bb/tree ddd171fb/direct22d22eb0/source50paths/governance39b38f originalpush0. Actual genuine nine captures+two fixtures768f4a/0bb0f5 complete20objects16S3+4Git;3241 source inputs/both dirty trees preserved in actual botFF22d;hold06 released. Root343 original producer files unchanged;no global-root green or merge-requirement waiver.',d)
q='''# Current research queue — {at}

Actual source45ee45d2 is normally published,237paths/tree45a23a5f/governance545f18/publicationb2d415. Independent full417921 passes676 guards/12 phasepairs/TWO unfiltered tests/ALL17 JSON/two original proof gates/two canonical bindings/four actual admission controls. Own ELEVEN workflows0ba3a0 succeed with ALL101 native records/52 original canonical digests;new remote fixture hydration succeeds. Standing unsigned/geometry partial/no computational advantage. [pcc:unverified]

| Priority | Task | Discriminating next action |
| --- | --- | --- |
| 1 | Transported full52 kernels and same-output source API | Frozen579e08 beforecode. Additive refinement crate;actual gamma2/conjugate transport/all135 intersections/all9 rational cases/independent rank/untransported negative;full geometric kernel proof. Source candidate PhiNew gamma double matches frozenChain/all3/32odd+zero/public5/tags/recovery/negatives;faithful Lean/report/CI. [pcc:unverified] |
| 2 | Actual new-target solver/counter coverage | Inspect original publicIC/Jacobian interfaces;freeze exact public-target correctness and complete cost-coverage plan for ALL3 targets. Preserve failures and original admission;no assumed speedup. [pcc:unverified] |
| 3 | Whole-data publication | New ct65 full676/own11CI captures remain local whole originals plus small whole Git objects;pack unchanged standard whole archives/complete indices with later refinement captures. NEWguard07 required before any future botFF;old3241guard06 historical/released. [pcc:unverified] |
| 4 | Performance admission | Original S3 checkpoint/livebudget/capacity, complete cold+online transport/strongest IC/rho matched references. No correctness runtime supplies a performance conclusion. [pcc:unverified] |
| 5 | Formal/global/merge |52 faithful local bindings partial;actual geometry/degree/polarization/Picard/Galois and signed execution open. Materially different authenticated original root-fixture CI hydration remains to implement;globalroot notgreen. Preserve main ledger/signing/reviews/conflict;vaultlocked/KBecdb gaps. [pcc:unverified] |

Rootcdfce1bb39b38f normalpush0;genuine9captures+2fixtures768f4a/0bb0f5,20objects16S3+4Git. Odd-source b2b04d/5fee41 and older full/CI settled;all negative results/raw failures remain. No unchanged settled workflow redispatch. Continue after each rung. [pcc:unverified]
'''.format(at=datetime.now(timezone.utc).isoformat())
path=s/'RESEARCH_QUEUE.md';path.write_text(q+'\n---\n\n'+path.read_text())
note='''
## {at} — actual Jacobian52 replay settled; refinement protocol frozen

45ee45d2 source normalpush0/b2d415,rootcdfce1bb normalpush0. Full417921:676 unchanged guards,TWO unfiltered tests,ALL17 native JSON exact,both original2-declaration gates/two exact canonical bindings,12phasepairs0/0,four actual admission controls2/nooutput/restored. Already genuine fixture copied read-only/originaltoolverify0;no local new-remote-read claim. Own11CI0ba3a0:ALL101 native records,52 original canonical PCC digests,all11jobsSUCCESS;new fixture remote hydration stepSUCCESS. Whole captures retained;large new captures await next genuine unchanged whole-data publication. [pcc:unverified]

Next prospective579e08 precedes any odd-product-refinements crate/code:actual gamma2 transported full52 kernel census/proof and identical-output source PhiNew gamma double API with frozenChain parity. Existing675 science/CI/PCC inputs immutable. Conductor executable previously127 remains unavailable;scope expansion is additive study crate/protocol/proofs/reports/versionedCI/evidence and owned journal/problem/PCC metadata. Original engines/verifiers/oldworkflows stay frozen. KBfallback attemptedtwo fresh refinement queries;vault8edec422 remains locked/no unlock/read. No novelty/absence inference. Routine bounded Rust/Lean correctness only,not benchmark. Persistent queue carries original performance/global/formal/merge gaps. [pcc:unverified]
'''.format(at=datetime.now(timezone.utc).isoformat())
for path in [r/'docs/session-logs/2026-11-13.md',r/'.resume/RESUME.md']:
 with path.open('a')as f:f.write(note)
kb=s/'evidence/odd-product-refinement-prior-search-01';kb.mkdir()
for label,query in [('kernels','transport degree13 HLP gluing kernel C4 C2 C13 quotient factorization'),('source','Ciani pullback norm composition eliminate source pair same-output')]:
 p=subprocess.run(['scripts/research-kb','search',query],cwd='/workspace/crypto',capture_output=True)
 (kb/(label+'.log.xz')).write_bytes(lzma.compress(p.stdout+p.stderr));(kb/(label+'.exit')).write_text(str(p.returncode)+'\n');assert p.returncode==127
(kb/'scope.json').write_text(json.dumps(dict(queries=2,fallback='original scripts/research-kb',exit=127,reason='research KB executable absent;no source IDs returned',sources_checked=['odd-product/ODD_PRODUCT_CHAIN_DERIVATION_01.md:1fd6e7','chain-kernels/CHAIN_KERNEL_DERIVATION_01.md:2e21d5','odd-source/ODD_SOURCE_DERIVATION_01.md:b9a91f','immutable675 original source inventory'],atlas='vault8edec422 locked;no decrypt/read/write',inference='no novelty or absence inference'),indent=2)+'\n')
claim('Two fresh original research-kb fallback queries for transported kernels and same-output source-map simplification each exit127/executable absent. Read pinned local chain/oddsource/oddproduct written proofs and original sources instead;no KB source IDs,novelty or absence inference. Autoresearcher8edec422 vault remains locked and unchanged.',kb)
g=s/'evidence/odd-product-terminal-protocol-governance-01';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
def run(name,cmd):
 p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr
 (g/(name+'.txt.xz'if len(raw)>60000 else name+'.txt')).write_bytes(lzma.compress(raw)if len(raw)>60000 else raw);(g/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,raw.decode(errors='replace')[:1500]
scope=[str(s.relative_to(r)),'pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
run('reference675',['sha256sum','--check',str((s/'ci_odd_product/reference-01.sha256').relative_to(r))]);run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]])
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','.github/workflows','experiments/chained-transfer-reference',str((s/'odd-product-models').relative_to(r)),str((s/'odd-product-maps').relative_to(r)),str((s/'ci_odd_product').relative_to(r))],cwd=r)
run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
 ps=paths();f=Path('/workspace/scratch/ct65-terminal-protocol.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for p in ps:
  if p.startswith(b'pcc/claims/'):
   for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
     assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0,x['path']
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(source=base,full='417921',CI='0ba3a0/11success/101native/52canonical',protocol='579e08 beforecode',all675_inputs_unchanged=True,original_engines_oldworkflows_verifiers_unchanged=True,governance='ledger/prose/working+cachedwhitespace/wiring/benchrec/artifact0',root='cdfce1bb originalpush0',scope='unsigned correctness;partial formal;no computational advantage'),indent=2)+'\n')
claim('Odd-product terminal checkpoint45ee source:independent full417921/676guards/12phasepairs/ALL17wholeJSON/both2declgates/2canonicalbindings/fouractualcontrols;own11CI0ba3a0/101native52originalcanonicaldigests/fresh genuine fixture hydration. Rootcdfce1bb normalpush0. Prospective579e08 frozen before any refinementcode;all675 published science/CI inputs/original engines/workflows/verifiers unchanged. Originalledger/prose/whitespace/cachedwhitespace/wiring/benchrec/artifact0;new PCC subjects/staging covered. Full/CI whole captures retained awaiting next genuine wholepublication;unsigned/geometrypartial/no computational advantage/globalrootgreen/mergewaiver.',g)
selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: settle Jacobian52 replay and freeze transported-kernel refinement'],cwd=r,check=True)
print(subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)

from pathlib import Path
from datetime import datetime,timezone
import subprocess,hashlib,shutil,re,json
r=Path('/workspace/cryptanalysis');root=Path('/workspace/crypto');s=r/'experiments/chained-transfer-reference/src';e=s.parent/'evidence';base='93587b9dc75ff7ac9bf5b2d157b9179857d49bcd'
def old(name):return subprocess.check_output(['git','show',base+':'+str((s/(name+'.rs')).relative_to(r))],cwd=r,text=True)
def body(text,name):
 marker='fn '+name+'(';start=text.index(marker);brace=text.index('{',start);depth=1;i=brace+1
 while depth:
  if text[i]=='{':depth+=1
  elif text[i]=='}':depth-=1
  i+=1
 return text[brace:i]
def same(a,b,an,bn=None):assert body(a,an)==body(b,bn or an),(an,bn)
current={n:(s/(n+'.rs')).read_text() for n in ['quartic_norm','quartic_pullback','seven_chain','prime_field_psi','prime_field_adjoint','seven_successor_chain','prime_field_pipeline','prime_field_reverse','t2_quartic_adapters']}
for n in ['prime_field_psi','prime_field_adjoint']:
 assert current[n].replace('pub(crate)','pub(super)')==old(n),n
assert current['seven_chain'].replace('pub(super) mod','mod')==old('seven_chain')
for n in ['balanced','quartic_cover','quartic_lagrange','quartic_pullback_points']:assert (s/(n+'.rs')).read_text()==old(n),n
for n,methods in [('quartic_norm',['first','second','t1','point','finite','norm']),('quartic_pullback',['pull'])]:
 for name in methods:same(current[n],old(n),name)
 assert current[n][current[n].index('\n#[test]'):]==old(n)[old(n).index('\n#[test]'):],n+' oldtests'
pull=current['quartic_pullback'];start=pull.index('            (2, 0) => (');end=pull.index('            _ => panic!',start)
assert body(pull[:start]+pull[end:],'fixed')==body(old('quartic_pullback'),'fixed')
succ=current['seven_successor_chain'];prior=old('seven_successor_chain')
for name in ['quarter_phi','quarter_phi_generic','quarter_phi_with_norms','forward_generic','dual_generic','naive']:same(succ,prior,name)
same(succ,prior,'forward_reference','forward');same(succ,prior,'dual_reference','dual')
assert succ[succ.index('\n#[test]'):]==prior[prior.index('\n#[test]'):]
p=root/'research/chained_jacobian_transfers_20261110/evidence'
forward=(p/'prime-pipeline-33/ct30_prime_pipeline.rs').read_text();reverse=(p/'prime-reverse-01/ct32_prime_reverse_pipeline.rs').read_text();t2=(p/'t2-adapter-30/ct30_t2_quartic.rs').read_text();tnorm=(p/'t2-adapter-30/ct28_direct_norm.rs').read_text();tpull=(p/'t2-adapter-30/ct28_pullback.rs').read_text()
for name in ['second','two_hop','evaluate','complete']:same(current['prime_field_pipeline'],forward,name)
for name in ['new','evaluate','complete']:same(current['prime_field_reverse'],reverse,name)
same(current['quartic_norm'],tnorm,'t2');assert pull[start:end]==tpull[tpull.index('            (2, 0) => ('):tpull.index('            _ => panic!')]
for n,accepted in [('prime_field_pipeline',forward),('prime_field_reverse',reverse)]:
 for test in re.findall(r'#\[test\]\s*fn (\w+)',accepted):
  adapted=current[n].replace('old.forward_reference(', 'old.forward(').replace('old.dual_reference(', 'old.dual(')
  same(adapted,accepted,test)
for test in ['both_t2_direct_pullbacks_match_old_r2_p2_and_all_group_pairs','both_t2_direct_norms_match_all_old_h2_outputs_and_group_controls']:same(current['t2_quartic_adapters'],t2,test)
assert 'old.forward_reference(d)' in current['prime_field_pipeline'];assert 'old.dual_reference(d)' in current['prime_field_reverse']
receipt=e/'second-source-guards-02.txt';assert not receipt.exists();receipt.write_text('PASS exact old secondforward/dual bodies retained as explicit references;new tests explicitly call old references.\nPASS original second generic/quarter/naive methods and original test suffix byte-identical.\nPASS prior first-chain source visibility only;first forward/adjoint arithmetic byte-identical.\nPASS Balanced/cover/Lagrange/point sources byte-identical.\nPASS norm/pullback arithmetic and original tests unchanged;T2constructor/data exact frozen30.\nPASS accepted forward33/reverse01 constructor/evaluator/full controls byte-identical after paths/visibility/reference-name adaptations;two T2runtime tests exact frozen30.\nPASS no new interpolation wrapper;globalT2/firstpure dependencies explicit. Expanded complete25native/98reference+five/one historical ignored pending.\n')
names=['balanced','seven_chain','quartic_cover','quartic_lagrange','quartic_norm','quartic_pullback','quartic_pullback_points','prime_field_psi','prime_field_adjoint','seven_successor_chain','prime_field_pipeline','prime_field_reverse','t2_quartic_adapters'];manifest=[]
for name in names:
 source=s/(name+'.rs');dest=e/f'second-{name}-source-02.rs';assert not dest.exists();shutil.copyfile(source,dest);manifest.append(hashlib.sha256(source.read_bytes()).hexdigest()+'  '+str(source.relative_to(r)))
m=e/'second-source-02.sha256';m.write_text('\n'.join(manifest)+'\n');cl=e/'second-clippy-02.txt';shutil.copyfile('/workspace/scratch/ct34-second-clippy-02.txt',cl)
a=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Unsigned actual second/compressed integration02 strictClippy/exact source custody pass:old second forward/dual bodies retained explicit references and newly tested byname;all old generic/quarter/naive/tests/first-chain arithmetic unchanged. Accepted T2norm constructor/data and forward33/reverse01 constructors/evaluators/full acceptance controls byte-identical after paths/visibility/reference-name adaptations;existing engines only,no interpolation wrapper. All13source02 snapshots/hashmanifest frozen;complete25native/98reference+five/one historical ignored pending. Failure01a749e8 retained;ready1507/935 parent fixed,no timing claim.']
for q in [receipt,m,cl]:a+=['--proof','attestation:'+str(q.relative_to(r))]
claim=subprocess.run(a,cwd=r,capture_output=True,text=True,check=True).stdout.strip();print(claim)
now=datetime.now(timezone.utc).isoformat()
entry=f'''\n## {now} — actual second-hop source02 frozen (Codex)

### What was done (commands, files, features)
- Ready1507 fixed93587b9/tree0f032e full92 accepted/own focused dispatch09:23 initialrunlistempty,next10:13. Fresh second child starts935. Exact source custody/strictClippy{claim} passes:13source02 snapshots/hashmanifest;secondforward/dual now standalonepure contexts with exact old reference bodies explicitly called bynewtests. Oldquarter/generic/naive/testsuffix/first-chain arithmetic remain. Accepted T2data30/pipeline33/reverse01 bodies and full controls reused unchanged afterpaths/visibility/reference-name adaptations. [pcc:unverified]

### Decisions made (and why)
- Run one complete changed check.sh03 on frozen13sources,expected25native/98reference unit+five integrations/one historical ignored. Raw/workspace/scratch/ct34-second-complete-03.txt. No editing while active,no case filtering. T2reconstruction/globalcertificate remains upstream dependency;only2runtime T2tests plus4wholepipeline tests added. FocusedCI75min resourcebound for expandedcorpus,not timingcomparison.

### Open threads (unfinished, pick up next time)
- Complete03/afterhash/finalnewreport/written/readychild1507;root spectralLean/newreport/reverseproof/checkpoint and908CI09:40. Later bounded12hop ellipticcycle task. Full independent nonlinear map/kernel replay and admitted cold costs remain open.

### Errors (what went wrong, how it was handled)
- Initial missing reversechild registration E0433/a749e8 source/raw/nativeNOTRUN retained. Added existing module declaration only,no arithmetic or criterion changed. All older sources/proofs/reports/failedcases immutable.
'''
for repo in [r,root]:
 with (repo/'docs/session-logs/2026-11-12.md').open('a') as f:f.write(entry)

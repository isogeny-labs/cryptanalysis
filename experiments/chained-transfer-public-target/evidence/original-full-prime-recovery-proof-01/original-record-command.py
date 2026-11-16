"""Original Lean gates and exact PCC statement-binding custody."""
from pathlib import Path
import hashlib, importlib.util, json, os, shutil, subprocess, sys
r=Path('/workspace/cryptanalysis'); s=r/'experiments/chained-transfer-public-target'
e=s/'evidence/original-full-prime-recovery-proof-01';e.mkdir()
raw=Path('/workspace/scratch/ct90-original-full-prime-recovery-proof-01')
for side in ['consumer','producer']: assert (raw/(side+'.exit')).read_text().strip()=='0'
shutil.copytree(raw,e/'original-gates');shutil.copyfile(__file__,e/'original-record-command.py')
spec=importlib.util.spec_from_file_location('original_pcc',r/'tools/pcc/pcc.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
path=s/'original-full-evaluator-01/lean/PrimeRecovery.lean'
env=dict(os.environ,PATH='/home/agent/.elan/toolchains/leanprover--lean4---v4.34.1/bin:'+os.environ['PATH'])
names=[('OriginalFullPrimeRecovery',x) for x in ['recover_prime_summand','actual_original_prime_recovery_witnesses']]
scope='Conditional IntModule CRT recovery of the prime summand from2p plus arbitrary four-torsion; explicit ellannihilation andcofactor4annihilation. Ordinary Lean kernel checks actualoriginal scalar9705756=4*2426439, divisible4 andinverse2mod2773073, Bezout quotient-7. This repairs onlythe independent test oracle; not inverse2 onthefullgroup. Bothoriginalgates2roots0trusted; actualfield/HLP/program bridges explicit; unsigned.'
bindings=[]
for namespace,short in names:
    name=namespace+'.'+short;_,statement=m.lean_find_declaration([path],name)
    proof=dict(path=path.relative_to(r).as_posix(),theorem=name,decl_sha256=hashlib.sha256(statement.encode()).hexdigest())
    cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','theorem','--claim-type','interpretive','--statement',statement,'--scope',scope,'--proof','lean:'+json.dumps(proof)]
    claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
    q=subprocess.run(['python3','tools/pcc/pcc.py','verify',claim,'--json'],cwd=r,env=env,capture_output=True)
    label=namespace+'-'+short
    (e/(label+'-binding.json')).write_bytes(q.stdout);(e/(label+'-binding.stderr.txt')).write_bytes(q.stderr);(e/(label+'-binding.exit')).write_text(str(q.returncode)+'\n')
    assert q.returncode==0 and json.loads(q.stdout)['verdict']=='pass'
    bindings.append(dict(claim=claim,theorem=name,statement=statement));print(claim,name,'local binding pass; unsigned',flush=True)
(e/'bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Original full-group prime-recovery test-oracle proof01: both unchanged original434/435 gates2roots0trusted andboth exactlocalPCC bindings pass. Derives CRT recovery ofpell-torsion from2p plusarbitrary4torsion under explicitannihilationhypotheses; checks originalell2773073/scalar9705756=4*2426439/divisible4/inverse2modell/Bezoutquotient-7. Addresses actualnativefailure99d448 oldnu12scalar retainedintwotestchecks; no change tofull-group runtime orfrozenpopulation. Originalproducerfirstshelllaunch race exited1 beforegate dueoutputdirectorynotyetcreated, wholeobservationretained; rerunonlyproducerpass0. Unsignedconditionalalgebra only; no inverse2onfullgroup orsignedstanding.']
for p in sorted(e.rglob('*')):
    if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
Path('/workspace/scratch/ct90-full-prime-recovery-proof01.claim.txt').write_text(claim+'\n');print(claim,flush=True)

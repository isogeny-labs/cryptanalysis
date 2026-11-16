"""Original Lean gates and exact PCC statement-binding custody."""
from pathlib import Path
import hashlib, importlib.util, json, os, shutil, subprocess, sys
r=Path('/workspace/cryptanalysis'); s=r/'experiments/chained-transfer-public-target'
e=s/'evidence/original-full-chain-proof-01';e.mkdir()
raw=Path('/workspace/scratch/ct90-original-full-chain-proof-01')
for side in ['consumer','producer']: assert (raw/(side+'.exit')).read_text().strip()=='0'
shutil.copytree(raw,e/'original-gates');shutil.copyfile(__file__,e/'original-record-command.py')
spec=importlib.util.spec_from_file_location('original_pcc',r/'tools/pcc/pcc.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
path=s/'original-full-evaluator-01/lean/OriginalFullChain.lean'
env=dict(os.environ,PATH='/home/agent/.elan/toolchains/leanprover--lean4---v4.34.1/bin:'+os.environ['PATH'])
names=[('ChainDescent',x) for x in ['square_cube_fixed','image_fixed','rational_two_torsion_average','norm_half_difference_in_kernel','equal_images_equal_targets','corrected_half_choice_independent','corrected_output_fixed','rational_correction_complete']]
names += [('FullGroupNorm',x) for x in ['two_pair_norm','inverse_on_full_annihilator','actual_full_group_witnesses','full_group_coprime','retained_lift_chain']]
names += [('NormPointReuse',x) for x in ['corrected_lift_doubles','corrected_norm_reuse','factored_norm_reuse']]
names += [('OriginalFullChain',x) for x in ['known_point_representation','known_point_corrected_output','actual_original_full_witnesses']]
scope='Conditional IntModule algebra under explicit linearity/duality/kerneltransport/Frobenius/kernel-description/order-annihilation hypotheses. Sixteen old roots and hypotheses are literal unchanged source concatenation, including historical nu12-only numeric roots; those historical values are NOT original-order witnesses. Three additive roots derive p/zero knownpoint representation, knownpoint output from old half/correction independence (no assumed desired evaluator equality), and actual original ORDER11092292/gcd13-169/squares89-40-6/inverse13=3413013 inverse169=9648325 and IntBezout witnesses. Both unchanged original434/435 gates19roots0trusted. Actual field/HLP/geometricquotient/Frobenius/Picard/program/order bridges remain explicit; no signedstanding, cost or computational advantage.'
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
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Original full-group chain proof01: BOTH unchanged original434/435 gates pass NINETEENroots0trusted, all19exact localPCC statementbindings pass. Literal copies retain8ChainDescent+5FullGroupNorm+3NormPointReuse roots and everyhypothesis, including explicitly historicalnu12 numericwitnesses. Additive roots derive actualknownpoint p/zero half-correction representation and output fromkerneltransport/oldchoiceindependence, no inverse2 onfullgroup andno assumeddesired beta equality. Independent Lean kernel checks originalfullorder11092292=4*2773073, gcd13/169=1, selectedD116/39/36 roots89/40/6, inverse13=3413013/quotient-4 andinverse169=9648325/quotient-147. Sourcevalues forinverses literallyproject actualnative setup; no whole-native acceptance inferred here. ActualHLP/field/geometric/Frobenius/Picard/program/order bridges remainexplicit. Unsignedconditionalalgebra only; no calibrated/ECDLP orsignedpromotion.']
for p in sorted(e.rglob('*')):
    if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
Path('/workspace/scratch/ct90-full-chain-proof01.claim.txt').write_text(claim+'\n');print(claim,flush=True)

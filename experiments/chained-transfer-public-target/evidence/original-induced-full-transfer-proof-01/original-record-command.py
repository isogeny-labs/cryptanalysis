"""Original gates, all named statement bindings and complete source custody."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,subprocess,sys
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';raw=Path('/workspace/scratch/ct93-induced-transfer-proof-01')
path=s/'original-induced-transfer-01/lean/InducedFullTransfer.lean';e=s/'evidence/original-induced-full-transfer-proof-01';e.mkdir()
assert path.read_bytes()==(raw/'actual-source.lean').read_bytes()==Path('/workspace/crypto/target/ct93-induced-transfer-proof-stage-01/InducedFullTransfer.lean').read_bytes()
names=['representative_independence','induced_on_source','induced_additive','induced_integer_linear','induced_reverse_norms','induced_chain_collapse','recover_on_annihilator','injective_on_annihilator','actual_original_witnesses']
expected={'InducedFullTransfer.'+name for name in names};coverage={}
for side in ['consumer','producer']:
    assert (raw/(side+'.exit')).read_text().strip()=='0'
    audits=list((raw/side).rglob('audit.log'));assert len(audits)==1
    text=audits[0].read_text();decls=[line.split()[1] for line in text.splitlines() if line.startswith('ok    ')]
    assert len(decls)==21 and expected<=set(decls) and '0 failing, 0 trusted' in text
    extra=set(decls)-expected
    assert len(extra)==12 and all(name.startswith(('InducedFullTransfer.Presentation.','InducedFullTransfer.CompatibleEdge.'))for name in extra)
    coverage[side]=dict(actual_audited_declarations=21,nine_planned_named_roots=sorted(expected),additional_structure_declarations=sorted(extra),zero_trusted=True,all_planned_roots_present=True)
shutil.copytree(raw,e/'original-gates');(e/'exact-root-and-structural-coverage.json').write_text(json.dumps(dict(coverage=coverage,interpretation='Nine frozen substantive roots plus ten explicit proof-field projections and two generated sizeOf specifications; no root omitted, source criterion or gate weakened. Original gates audit all21; claim onlynine new named mathematical conclusions.'),indent=2)+'\n')
spec=importlib.util.spec_from_file_location('original_pcc',r/'tools/pcc/pcc.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
env=dict(os.environ,PATH='/home/agent/.elan/toolchains/leanprover--lean4---v4.34.1/bin:'+os.environ['PATH']);bindings=[]
scope='Conditional quotient algebra on geometric IntModules. Presentation explicitly supplies sourcePhi homomorphism identities and an arbitrary section withPhi(liftx)=x; CompatibleEdge explicitly supplies source elliptic homomorphism identities and full kernel transport. No induced transfer linearity/commuting square/dual norm/recovery/injectivity is a field or hypothesis. Both induced reverse norms derive from source elliptic dual identities; recovery/injectivity require annihilation only on the stated inputs and Bezout. No rational/linear/equivariant section or finite annihilation of every geometric point is assumed. Both unchanged original434/435 gates audit21declarations: nine planned named conclusions plus12 structural declarations, all0trusted; exact localbindings for allnine. ActualHLP/field/Frobenius/Picard/order/program/lift bridges remainexplicit. Standardquotientalgebra formalization, unsigned/no newcurve-DLP/cost/novelty/signedstanding.'
for short in names:
    name='InducedFullTransfer.'+short;_,statement=m.lean_find_declaration([path],name)
    proof=dict(path=path.relative_to(r).as_posix(),theorem=name,decl_sha256=hashlib.sha256(statement.encode()).hexdigest())
    cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','theorem','--claim-type','interpretive','--statement',statement,'--scope',scope,'--proof','lean:'+json.dumps(proof)]
    claim=subprocess.check_output(cmd,cwd=r,text=True).strip();q=subprocess.run(['python3','tools/pcc/pcc.py','verify',claim,'--json'],cwd=r,env=env,capture_output=True)
    (e/(short+'-binding.json')).write_bytes(q.stdout);(e/(short+'-binding.stderr.txt')).write_bytes(q.stderr);(e/(short+'-binding.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==0 and json.loads(q.stdout)['verdict']=='pass'
    bindings.append(dict(claim=claim,theorem=name,statement=statement));print(claim,name,'local binding pass; unsigned',flush=True)
(e/'bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
q=subprocess.run(['sha256sum','--check',str(s/'ci_fixed_chain/reference-03.sha256')],cwd=r,capture_output=True);assert q.returncode==0;(e/'all1440-source-guards.txt.xz').write_bytes(__import__('lzma').compress(q.stdout+q.stderr));(e/'all1440-source-guards.exit').write_text(str(q.returncode)+'\n')
pins=json.loads((r/'experiments/chained-transfer-reference/evidence/g3-norm-primary-01/upstream-current-inputs.json').read_text());assert len(pins)==343 and all(hashlib.file_digest((Path('/workspace/crypto')/name).open('rb'),'sha256').hexdigest()==h for name,h in pins.items())
(e/'producer-and-source-custody.json').write_text(json.dumps(dict(all343_original_producer_science_hashes_unchanged=True,all1440_reference03_paths_unchanged=True,source_sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),source_bytes=path.stat().st_size,actual_source_compiled_by_both_gates_equal=True,genInjectivity_false='suppresses redundant constructor injectivity generation only; original gates unchanged and auditall21remainingtheorems including12structuraldeclarations',prospective='2de4aa publisheada0ec881 beforemodule',future_custody='NEW26'),indent=2)+'\n')
shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Original-induced fulltransfer proof01 underprospective2de4aa publisheada0ec881 BEFOREsource: both unchanged original434/435 gates PASS21auditeddeclarations0trusted onfirstattempt; allNINEfrozen named mathematicalroots present plus12structuraldeclarations(tenexplicitproof-fieldprojections/two generatedsizeOfspecifications), allnineexactlocalPCC statementbindingspass. No population/gate/hypothesis waiver. DefinesT=Psi-g-arbitrarygeometricsection fromexplicitquotient/sourcehomomorphisms/fullkerneltransport, derivesrepresentativeindependence/sourcecommutingidentity/additivity/integerDLPlinearity/BOTHindividualquotientreversenorms fromsourceellipticduals/twoedgecollapse/fullperpointannihilatorrecovery/injectivity/originalinverseBezout-gcdwitnesses. DesiredTidentity/linearity/norm/injectivity neverinput; no rational-linear-equivariantsection orfiniteorderannihilationonallgeometricpoints. Whole source/actualbothgates/structuralcoverage/rawbindings retained; all1440oldreference and343producer sciencehashesunchanged. ActualHLP-field-Frobenius-Picard-order-program-lift bridges explicit; standardconditionalalgebra/no novelty/newcurve-DLP/cost/signedclaim. CurrentCI43700115169 remains separatelyscopedto258; singleconsumerledger onisolatedbranch untilnormalFF. FuturecustodyNEW26.']
for p in sorted(e.rglob('*')):
    if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
cmd+=['--proof','attestation:'+path.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct93-induced-proof01.claim.txt').write_text(claim+'\n');print(claim,flush=True)

"""Read-only terminal binding check for the N41 code-linear tower."""
import hashlib,json
from pathlib import Path

D=Path(__file__).resolve().parent
R=D.parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
load=lambda name:json.loads((D/name).read_text())
prior_dir=R/'n41_w8_quotient_first_pair_20261015'
tower_dir=R/'n41_w8_three_code_resultant_20261015'
build_sources={
    'states':R/'n41_n131_w29_rotation_alignment_20261017/aligned_states.json',
    'fixture':R/'n41_w9_implicit_fivepair_tower_20261017/fixture.json',
    'witness':D/'witness.json','tower':tower_dir/'tower_circuit.py',
    'prior':prior_dir/'circuit.py','norm':prior_dir/'norm_gate_early.py',
    'runtime':D/'sage_runtime_info.json',
    'selector':R/'n131_w20_selector_elimination_v2_20261013/selector.py',
    'linear':R/'n131_w20_output_inverse_linear_20261012/linear.py',
    'trace_runner':R/'n131_w20_inverse_trace_20261012/run.py',
    'ninepair_runner':R/'n131_fixed_seed_ninepair_cubic_20261011/run.py',
    'sevenpair':R/'n131_w20_sevenpair_gate_20261010/sevenpair_circuit.py',
    'fixed_pair':R/'n131_fixed_seed_eight_pair_circuit_20261010/fixed_pair_circuit.py',
    'sparse':R/'n41_basis_aware_quartic_20261011/sparse.py',
    'karatsuba':R.parent/'koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py',
    'field':R/'n41_basis_aware_quartic_20261011/replay.py'}
for name in ['witness_protocol.json','build_protocol.json',
             'build_expanded_protocol.json','query_protocol.json',
             'audit_protocol.json']:
    p=load(name)
    for key,digest in p.get('sources',p.get('source_sha256',{})).items():
        if key.startswith('/'):
            assert sha(key)==digest,(name,key)
    if name.startswith('build_'):
        build_sources['script']=D/('build_expanded.py' if name=='build_expanded_protocol.json' else 'build.py')
        assert {k:sha(path) for k,path in build_sources.items()}==p['source_sha256']
    if name=='query_protocol.json':
        query_sources={'script':D/'run_query.py','runtime':D/'sage_runtime_info.json',
            'formula':D/'formula.xcnf','build':D/'build_result.json',
            'wires':D/'input_wires.json',
            'fixture':R/'n41_w9_implicit_fivepair_tower_20261017/fixture.json',
            'witness':D/'witness.json','solver':Path('/opt/homebrew/bin/cryptominisat5'),
            'lean':D/'FinalPairResultant.lean','lean_output':D/'lean.stdout',
            'prior_early_build':R/'n41_w9_implicit_fivepair_tower_20261017/early_build_result.json'}
        assert {k:sha(path) for k,path in query_sources.items()}==p['source_sha256']
witness=load('witness.json')
assert witness['status']=='PASS_INTERMEDIATE_WITNESS'
factored=load('build_result.json');expanded=load('build_expanded_result.json')
prior=load('../n41_w9_implicit_fivepair_tower_20261017/early_build_result.json')
assert factored['status']=='PASS_N41_CODE_LINEAR_TOWER_BUILD'
assert expanded['status']=='PASS_N41_CODE_LINEAR_EXPANDED_BUILD'
assert factored['formula_sha256']==sha(D/'formula.xcnf')
assert expanded['formula_sha256']==sha(D/'formula_expanded.xcnf')
assert factored['and_gates']<expanded['and_gates']<prior['and_gates']
assert factored['witness_control']['all_clauses_and_xors_satisfied']
assert expanded['witness_control']['all_clauses_and_xors_satisfied']
lean=(D/'lean.stdout').read_text()
for theorem in ['resultant_linearized','code_map_additive',
                'resultant_split_identity','resultant_zero_iff_source_root']:
    assert f"'FinalPairResultant.{theorem}' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
assert 'error:' not in lean and (D/'lean.stderr').read_text()==''
assert all(word not in (D/'FinalPairResultant.lean').read_text()
           for word in ['sorry','admit','sorryAx'])
audit=load('audit_result.json')
assert audit['status']=='PASS_RESULTANT_SOURCE_EQUIVALENCE'
assert audit['identity_checks']==audit['common_root_checks']==audit['source_codes']*audit['charts']
assert audit['protocol_sha256']==sha(D/'audit_protocol.json')
query=load('query_result.json');qp=load('query_protocol.json')
assert query['protocol_sha256']==sha(D/'query_protocol.json')
assert query['stdout_sha256']==sha(D/'solver.stdout')
assert query['stderr_sha256']==sha(D/'solver.stderr')
assert query['one_worker'] and query['peak_sampled_process_tree_rss_bytes']<=qp['rss_cap_bytes']
if query['status']=='SAT_MODEL_UNVERIFIED':
    if (D/'model_audit_result.json').exists():
        model=load('model_audit_result.json')
        classification=('PASS_ORDINARY_RELATION' if model['status']=='PASS_N41_UNPINNED_ORDINARY_RELATION'
                        else 'UNVERIFIED_MODEL')
    else:classification='UNVERIFIED_MODEL'
elif query['status'] in ('WALL_CAP','INDETERMINATE_SOLVER_CAP'):
    classification='BOUNDED_UNKNOWN'
else:classification=query['status']
out={'status':classification,'candidate_id':None,
     'factored_and_gates':factored['and_gates'],
     'expanded_and_gates':expanded['and_gates'],
     'prior_and_gates':prior['and_gates'],
     'query_status':query['status'],
     'query_result_sha256':sha(D/'query_result.json'),
     'audit_result_sha256':sha(D/'audit_result.json')}
(D/'verification.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps(out,sort_keys=True))

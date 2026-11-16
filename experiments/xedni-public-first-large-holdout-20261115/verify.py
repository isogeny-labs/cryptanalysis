"""Check frozen inputs, audit amendment, raw events, stage counts and seal."""
import hashlib
import json
import ast
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    amendment = json.loads((HERE/'audit-amendment.json').read_text())
    result = json.loads((HERE/'result.json').read_text())
    audit = json.loads((HERE/'audit.json').read_text())
    assert protocol['schema']=='xedni-public-first-large-holdout-protocol-v1'
    assert result['status']==audit['status']=='PASS'
    assert protocol['field_panel']==[313,421,431,547,571,593,617,677]
    assert protocol['queries_per_field']==512 and protocol['target_scalar']==17
    for key,path in (
        ('admission_sha256',ROOT/'xedni-large-order-admission-20261115/result.json'),
        ('coordinate_control_sha256',ROOT/'xedni-rank-one-coordinate-control-20261115/result.json'),
        ('family_sha256',ROOT/'xedni-coefficient-optimization-20261115/family-selection.json'),
        ('rank_one_lean_source_sha256',ROOT/'xedni-vector-dependent-rank-one-lift-20261115/formal/VectorDependentRankOneLift.lean'),
        ('producer_sha256',HERE/'run_sage.py'),('audit_sha256',HERE/'audit_sage.py')):
        assert protocol[key]==sha(path),key
    assert amendment['base_protocol_sha256']==sha(HERE/'protocol.json')
    assert amendment['frozen_producer_result_sha256']==sha(HERE/'result.json')
    for key,path in (
        ('original_audit_sha256',HERE/'audit_sage.py'),
        ('failed_audit_stderr_sha256',HERE/'audit-v1.stderr'),
        ('failed_audit_output_sha256',HERE/'audit-v1.json'),
        ('audit_v2_sha256',HERE/'audit_sage_v2.py')):
        assert amendment[key]==sha(path),key
    assert b'KeyError: \'filtered_queries\'' in (HERE/'audit-v1.stderr').read_bytes()
    assert result['protocol_sha256']==audit['protocol_sha256']==sha(HERE/'protocol.json')
    assert result['source_sha256']==sha(HERE/'run_sage.py')
    assert audit['source_sha256']==sha(HERE/'audit_sage_v2.py')
    assert result['sage_runtime_sha256']==audit['sage_runtime_sha256']==sha(HERE/'sage-runtime-info.json')
    assert json.loads((HERE/'sage-runtime-info.json').read_text())['status']=='verified'
    assert (HERE/'run.stderr').read_bytes()==(HERE/'audit.stderr').read_bytes()==b''
    assert len(result['fields'])==len(audit['fields'])==8
    totals={}
    for row,checked,p in zip(result['fields'],audit['fields'],protocol['field_panel'],strict=True):
        assert row['field_prime']==checked['field_prime']==p
        assert row['subgroup_order']==checked['subgroup_order']
        c=row['counts']
        assert c['queries']==checked['queries']==512
        assert c['admitted_queries']+c.get('filtered_queries',0)==512
        assert c['public_vector_tests']==checked['public_vector_tests']==13*c['admitted_queries']
        assert c['public_hits']==c['verified']==checked['verified']
        assert c.get('failed',0)==0 and row['first_hit_query']==checked['first_hit_query']
        for key,multiple in [('modular_inverses',1),('public_scalar_multiplications',1),
                             ('curve_constructions',1),('rational_scalar_multiplications',2),
                             ('rational_relation_tests',1),('reduction_checks',2),('scalar_replays',1)]:
            assert c[key]==multiple*c['verified'],(p,key)
        raw=HERE/row['events_path']
        assert sha(raw)==row['events_sha256']
        events=[json.loads(x) for x in raw.read_text().splitlines()]
        assert len(events)==c['verified']
        assert all(e['status']=='verified' and e['recovered_scalar']==17 for e in events)
        assert row['first_hit_query']==min(e['query_index_one_based'] for e in events)
        for key,value in c.items():totals[key]=totals.get(key,0)+value
    assert totals==result['totals']
    assert totals['queries']==4096 and totals['public_vector_tests']==52936
    assert totals['public_hits']==totals['verified']==142
    post_protocol=json.loads((HERE/'post-protocol.json').read_text())
    post=json.loads((HERE/'post-result.json').read_text())
    post_audit=json.loads((HERE/'post-audit.json').read_text())
    assert post['status']==post_audit['status']=='PASS'
    assert post_protocol['parent_protocol_sha256']==sha(HERE/'protocol.json')
    assert post_protocol['parent_result_sha256']==sha(HERE/'result.json')
    for key,path in (
        ('family_sha256',ROOT/'xedni-coefficient-optimization-20261115/family-selection.json'),
        ('lean_source_sha256',ROOT/'xedni-coefficient-family-control-20261115/formal/CoefficientFamily.lean'),
        ('producer_sha256',HERE/'post.py'),('audit_sha256',HERE/'post_audit.py')):
        assert post_protocol[key]==sha(path),key
    assert post['post_protocol_sha256']==sha(HERE/'post-protocol.json')
    assert post['source_sha256']==sha(HERE/'post.py')
    assert post['vector_count']==13 and post['pairwise_determinants']==78
    assert post['max_abs_determinant']==60
    assert len(post['rows'])==8
    assert (HERE/'post.stderr').read_bytes()==(HERE/'post-audit.stderr').read_bytes()==b''
    assert post_audit['full_admissible_pairs']==1461174
    assert post_audit['full_relation_events']==43030
    assert post_audit['sample_hit_events']==142
    formal=HERE/'formal'
    assert sha(formal/'CoefficientFamily.lean')==sha(ROOT/'xedni-coefficient-family-control-20261115/formal/CoefficientFamily.lean')
    assert (formal/'lean-toolchain').read_text().strip()=='leanprover/lean4:v4.35.0-rc4'
    assert '021c46bdd042f67b538b9f9871d556a93713a9a9' in (formal/'lakefile.toml').read_text()
    proof=(formal/'FamilyCount.lean').read_text()
    assert all(s in proof for s in ('theorem family_event_count','theorem eventToHitPair_injective',
                                   'theorem family_hit_pair_count','admissible_hit_count',
                                   'distinct_directions_force_zero'))
    assert not any(token in proof for token in ('sorry', 'admit', 'sorryAx', 'native_decide'))
    build=(formal/'build-output.txt').read_text()
    assert 'Build completed successfully (9041 jobs)' in build
    assert "'XedniPublicFirstLargeHoldout.family_event_count' depends on axioms: [propext, Classical.choice, Quot.sound]" in build
    for name in ('eventToHitPair_injective','family_hit_pair_count'):
        assert f"'XedniPublicFirstLargeHoldout.{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in build
    panel=(formal/'Panel.lean').read_text()
    match=re.search(r'def selected .*?!\[(.*?)\]',panel,re.S)
    assert match is not None
    vectors=ast.literal_eval('['+match.group(1)+']')
    assert [list(v) for v in vectors]==json.loads((ROOT/'xedni-coefficient-optimization-20261115/family-selection.json').read_text())['selected']
    panel_build=(formal/'panel-build-output.txt').read_text()
    assert 'Build completed successfully (9042 jobs)' in panel_build
    assert not any(token in panel for token in ('sorry','admit','sorryAx','native_decide'))
    for q in (293,313,331,353,419,439,571,599):
        assert f'theorem count{q}' in panel
        assert f"'XedniPublicFirstLargeHoldout.count{q}' depends on axioms: [propext, Classical.choice, Quot.sound]" in panel_build
    admissible=(formal/'AdmissiblePairs.lean').read_text()
    assert all(name in admissible for name in ('theorem admissible_pair_count','theorem family_density_cross_mul',
                                              'theorem family_exact_fraction','theorem family_fraction_bound'))
    assert not any(token in admissible for token in ('sorry','admit','sorryAx','native_decide'))
    admissible_build=(formal/'admissible-build-output.txt').read_text()
    assert 'Build completed successfully (9043 jobs)' in admissible_build
    for name in ('admissible_pair_count','family_density_cross_mul','family_exact_fraction','family_fraction_bound'):
        assert f"'XedniPublicFirstLargeHoldout.{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in admissible_build
    family_bound=(formal/'FamilyBound.lean').read_text()
    assert all(name in family_bound for name in ('theorem family_hit_card_le','theorem family_fraction_le',
                                                'theorem family_size_needed'))
    assert not any(token in family_bound for token in ('sorry','admit','sorryAx','native_decide'))
    bound_build=(formal/'family-bound-build-output.txt').read_text()
    assert 'Build completed successfully (9044 jobs)' in bound_build
    for name in ('family_hit_card_le','family_fraction_le','family_size_needed'):
        assert f"'XedniPublicFirstLargeHoldout.{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in bound_build
    box=(formal/'BoxBound.lean').read_text()
    assert all(name in box for name in ('theorem coeff_box_card','theorem bounded_vector_card_le',
                                       'theorem bounded_vector_fraction_le','theorem coefficient_height_needed'))
    assert not any(token in box for token in ('sorry','admit','sorryAx','native_decide'))
    box_build=(formal/'box-build-output.txt').read_text()
    assert 'Build completed successfully (9045 jobs)' in box_build
    for name in ('coeff_box_card','bounded_vector_card_le','bounded_vector_fraction_le','coefficient_height_needed'):
        assert f"'XedniPublicFirstLargeHoldout.{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in box_build
    recovery_source=(formal/'PublicRecovery.lean').read_text()
    assert all(name in recovery_source for name in ('theorem public_relation_iff_recovered_scalar',
                                                   'theorem public_relation_target_unique'))
    assert not any(token in recovery_source for token in ('sorry','admit','sorryAx','native_decide'))
    recovery_build=(formal/'public-recovery-build-output.txt').read_text()
    assert 'Build completed successfully (9046 jobs)' in recovery_build
    recovery_build_normalized=re.sub(r'\s+',' ',recovery_build)
    for name in ('public_relation_iff_recovered_scalar','public_relation_target_unique'):
        assert f"'XedniPublicFirstLargeHoldout.{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in recovery_build_normalized
    group_source=(formal/'PublicGroupRecovery.lean').read_text()
    assert 'theorem public_group_relation_iff_recovered_scalar' in group_source
    assert not any(token in group_source for token in ('sorry','admit','sorryAx','native_decide'))
    group_build=(formal/'public-group-recovery-build-output.txt').read_text()
    assert 'Build completed successfully (9047 jobs)' in group_build
    assert "'XedniPublicFirstLargeHoldout.public_group_relation_iff_recovered_scalar' depends on axioms: [propext, Classical.choice, Quot.sound]" in re.sub(r'\s+',' ',group_build)
    prime_source=(formal/'PrimeOrderRecovery.lean').read_text()
    assert all(name in prime_source for name in ('theorem prime_order_public_relation_iff_recovered_scalar',
                                                'theorem torsion_public_relation_iff_recovered_scalar',
                                                'theorem cyclic_torsion',
                                                'theorem cyclic_public_relation_iff_recovered_scalar'))
    assert not any(token in prime_source for token in ('sorry','admit','sorryAx','native_decide'))
    prime_build=(formal/'prime-order-recovery-build-output.txt').read_text()
    assert 'Build completed successfully (9048 jobs)' in prime_build
    prime_build_normalized=re.sub(r'\s+',' ',prime_build)
    for name in ('prime_order_public_relation_iff_recovered_scalar',
                 'torsion_public_relation_iff_recovered_scalar',
                 'cyclic_public_relation_iff_recovered_scalar'):
        assert f"'XedniPublicFirstLargeHoldout.{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in prime_build_normalized
    assert "'XedniPublicFirstLargeHoldout.cyclic_torsion' depends on axioms: [propext]" in prime_build_normalized
    exceptional_source=(formal/'ExceptionalRelation.lean').read_text()
    assert all(f'theorem {name}' in exceptional_source for name in
               ('zero_sum_scalar_relation_iff','zero_sum_scalar_relation_iff_equal_offsets',
                'zero_sum_group_relation_iff_equal_offsets'))
    assert not any(token in exceptional_source for token in ('sorry','admit','sorryAx','native_decide'))
    exceptional_build=(formal/'exceptional-relation-build-output.txt').read_text()
    assert 'Build completed successfully (9049 jobs)' in exceptional_build
    exceptional_build_normalized=re.sub(r'\s+',' ',exceptional_build)
    assert "'XedniPublicFirstLargeHoldout.zero_sum_scalar_relation_iff' depends on axioms: [propext, Quot.sound]" in exceptional_build_normalized
    for name in ('zero_sum_scalar_relation_iff_equal_offsets','zero_sum_group_relation_iff_equal_offsets'):
        assert f"'XedniPublicFirstLargeHoldout.{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in exceptional_build_normalized
    distinct_source=(formal/'DistinctOffsetRecovery.lean').read_text()
    assert all(f'theorem {name}' in distinct_source for name in
               ('distinct_offset_public_hit_recovers_scalar',
                'distinct_offset_public_relation_iff_recovery'))
    assert not any(token in distinct_source for token in ('sorry','admit','sorryAx','native_decide'))
    distinct_build=(formal/'distinct-offset-recovery-build-output.txt').read_text()
    assert 'Build completed successfully (9050 jobs)' in distinct_build
    distinct_build_normalized=re.sub(r'\s+',' ',distinct_build)
    for name in ('distinct_offset_public_hit_recovers_scalar',
                 'distinct_offset_public_relation_iff_recovery'):
        assert f"'XedniPublicFirstLargeHoldout.{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in distinct_build_normalized
    curve_source=(formal/'ConcreteCurveRecovery.lean').read_text()
    assert all(f'theorem {name}' in curve_source for name in
               ('panelCurve_discriminant','panelCurve_isElliptic',
                'panelGenerator_nonzero','panel_curve_public_relation_iff_recovery'))
    assert 'q • panelGenerator p hp = 0' in curve_source
    assert not any(token in curve_source for token in ('sorry','admit','sorryAx','native_decide'))
    curve_build=(formal/'concrete-curve-recovery-build-output.txt').read_text()
    assert 'Build completed successfully (9051 jobs)' in curve_build
    curve_build_normalized=re.sub(r'\s+',' ',curve_build)
    for name in ('panelCurve_discriminant','panelCurve_isElliptic',
                 'panelGenerator_nonzero','panel_curve_public_relation_iff_recovery'):
        assert f"'XedniPublicFirstLargeHoldout.{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in curve_build_normalized
    probes=formal/'probes'
    probe=json.loads((probes/'probe-status.json').read_text())
    assert probe['schema']=='xedni-lean-order-probe-v1'
    assert probe['field_prime']==313 and probe['subgroup_order']==331
    assert probe['status']=='timeout' and probe['observed_exit_code']==124
    assert probe['lean_order_proved'] is False
    for key,name in (('source_sha256','OrderProbe.lean'),
                     ('sage_chain_source_sha256','sage_chain.py'),
                     ('sage_chain_result_sha256','sage_chain.json')):
        assert probe[key]==sha(probes/name)
    chain=json.loads((probes/'sage_chain.json').read_text())
    assert chain['field_prime']==313 and chain['subgroup_order']==331
    assert chain['q_multiple_is_identity'] is True
    assert [r['multiple'] for r in chain['doubling_chain']]==[2**i for i in range(9)]
    assert [r['point'] for r in chain['doubling_chain']]==[
        [2,2],[297,204],[65,226],[298,9],[211,223],
        [121,291],[218,5],[208,151],[258,173]]
    recovery_protocol=json.loads((HERE/'public-recovery-protocol.json').read_text())
    recovery_result=json.loads((HERE/'public-recovery-result.json').read_text())
    recovery_audit_protocol=json.loads((HERE/'public-recovery-audit-protocol.json').read_text())
    recovery_audit=json.loads((HERE/'public-recovery-audit.json').read_text())
    assert recovery_protocol['parent_result_sha256']==sha(HERE/'result.json')
    assert recovery_protocol['lean_source_sha256']==sha(formal/'PublicRecovery.lean')
    assert recovery_protocol['source_sha256']==sha(HERE/'public_recovery.py')
    assert recovery_result['protocol_sha256']==sha(HERE/'public-recovery-protocol.json')
    assert recovery_result['status']=='PASS' and recovery_result['total_public_hits_replayed']==142
    assert recovery_result['fixture_used_for_recovery'] is False
    assert recovery_audit_protocol['recovery_result_sha256']==sha(HERE/'public-recovery-result.json')
    assert recovery_audit_protocol['audit_source_sha256']==sha(HERE/'public_recovery_audit.py')
    assert recovery_audit['protocol_sha256']==sha(HERE/'public-recovery-audit-protocol.json')
    assert recovery_audit['status']=='PASS' and recovery_audit['total_unique_solutions_checked']==142
    assert [r['unique_solutions_checked'] for r in recovery_audit['rows']]==[f['counts']['public_hits'] for f in result['fields']]
    for old,row in zip(result['fields'],post['rows'],strict=True):
        q=old['subgroup_order']
        assert row['field_prime']==old['field_prime'] and row['subgroup_order']==q
        assert row['full_admissible_pairs']==(q-1)*(q-2)
        assert row['full_relation_events']==row['full_hit_pairs']==13*(q-1)
        assert row['overlap_pairs']==0
        assert row['sample_hit_events']==old['counts']['public_hits']
    sealed=(HERE/'SEAL.sha256').read_text().splitlines()
    for line in sealed:
        digest,rel=line.split('  ',1)
        assert sha(HERE/rel)==digest,rel
    print(json.dumps({'schema':'xedni-public-first-large-holdout-verify-v1',
                      'status':'PASS','fields':8,'queries':totals['queries'],
                      'public_vector_tests':totals['public_vector_tests'],
                      'verified_lifts':totals['verified'],'sealed_files':len(sealed)},sort_keys=True))

if __name__=='__main__':main()

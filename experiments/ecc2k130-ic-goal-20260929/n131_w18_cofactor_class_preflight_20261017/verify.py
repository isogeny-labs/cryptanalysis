"""Read-only frozen-source and cross-check verifier for class preflight."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import run
    protocol_path=HERE/'protocol.json';result_path=HERE/'result.json'
    audit_path=HERE/'audit_result.json'
    protocol=json.loads(protocol_path.read_text())
    result=json.loads(result_path.read_text())
    audit=json.loads(audit_path.read_text())
    assert protocol['status']=='FROZEN_W18_C4_CLASS_CENSUS_BEFORE_RUN'
    assert protocol['source_sha256']=={name:sha(path) for name,path in run.sources().items()}
    assert result['status']=='PASS_W18_C4_CLASS_PREFLIGHT'
    assert result['source_sha256']==protocol['source_sha256']
    assert result['protocol_sha256']==audit['sha256']['protocol']==sha(protocol_path)
    assert audit['status']=='PASS_INDEPENDENT_HALVING_C4_CLASS_AUDIT'
    assert audit['sha256']['producer']==sha(result_path)
    assert result['curve_id']==protocol['curve_id']=='EC1N131Ckb1heb5f1998f20b'
    assert result['workload_id']==protocol['workload_id']=='cc09e7eb202a'
    assert result['n131_raw_classes']==[0,2,1,3]
    assert sorted(result['n41']['raw_classes'])==[0,1,2,3]
    assert len(result['direct_residual_samples'])==20
    assert result['admissible_edge_pairs']==130
    assert result['edge_pair_class_support_size_histogram']=={'1':12,'2':118}
    assert len(result['edge_pair_classes'])==130
    assert audit['families_with_one_class']==12
    assert audit['families_with_two_classes']==118
    assert audit['state_choices_in_singleton_families']==192
    assert audit['n131_terminal_states_checked']==96
    assert audit['n131_joint_state_choices_checked']==2080
    assert result['elapsed_ns']<=protocol['wall_cap_seconds']*10**9
    assert result['peak_self_rss_bytes']<=protocol['rss_observation_cap_bytes']
    assert (HERE/'run.stderr').stat().st_size==0
    assert (HERE/'audit.stderr').stat().st_size==0
    assert (HERE/'run.stdout').read_text().strip().startswith('PASS_W18_C4_CLASS_PREFLIGHT')
    assert (HERE/'audit.stdout').read_text().strip().startswith('PASS_INDEPENDENT_HALVING_C4_CLASS_AUDIT')
    lean=(HERE/'lean_check.log').read_text()
    assert "'ClassBound.class_neg' does not depend on any axioms" in lean
    assert "'ClassBound.signed_x_fiber_has_at_most_two_classes' does not depend on any axioms" in lean
    assert "'ClassBound.public_raw_labels_bijective' depends on axioms: [propext, Quot.sound]" in lean
    assert 'sorry' not in (HERE/'ClassBound.lean').read_text()
    receipt={'status':'PASS_W18_C4_CLASS_TERMINAL_VERIFICATION',
             'curve_id':result['curve_id'],'workload_id':result['workload_id'],
             'admissible_edge_pairs':130,
             'singleton_edge_pairs':12,
             'double_edge_pairs':118,
             'max_extra_raw_choice_reduction_percent_given_free_class':'4.615384615',
             'sha256':{'script':sha(Path(__file__)),'protocol':sha(protocol_path),
                       'producer':sha(result_path),'independent_audit':sha(audit_path),
                       'lean':sha(HERE/'lean_check.log'),
                       'stdout':sha(HERE/'run.stdout'),'stderr':sha(HERE/'run.stderr')}}
    (HERE/'verification.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(receipt['status'],flush=True)


if __name__=='__main__':
    main()

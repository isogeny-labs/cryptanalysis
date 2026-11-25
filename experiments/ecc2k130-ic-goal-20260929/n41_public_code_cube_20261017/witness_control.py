"""Retrospectively check the archived relation in the exact public cube."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

D=Path(__file__).resolve().parent
OLD=D.parent/'n41_sixpair_shared_target_20261017'
sys.path.insert(0,str(OLD))
import circuit
spec=importlib.util.spec_from_file_location('archived_build',OLD/'build.py')
archived=importlib.util.module_from_spec(spec);spec.loader.exec_module(archived)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=json.loads((D/'witness_protocol.json').read_text())
    assert p['producer_sha256']==sha(Path(__file__))
    assert p['archive_sha256']==sha(OLD/'join_audit_result.json')
    assert p['formula_sha256']==sha(D/'rebuilt_public.xcnf')
    audit=json.loads((OLD/'join_audit_result.json').read_text())
    geometry=circuit.geometry()
    states=[];nodes=[]
    for slot,row in enumerate(audit['pair_rows']):
        state=geometry['blocks'][slot]['states'][row['state_id']]
        assert [state['a'],state['b']]==row['masks']
        assert state['raw_sum']==row['raw_sum']
        states.append(state);nodes.append(tuple(state['raw_sum']))
    middle=[]
    for left,right,out in circuit.BALANCED_LINKS:
        point=circuit.replay.add(circuit.F,nodes[left],nodes[right])
        assert point and point[0]
        if out==10:
            assert point==tuple(audit['raw_target'])
        else:
            assert out==len(nodes)
            nodes.append(point);middle.append(circuit.F.inv(point[0]))
    target=circuit.F.inv(audit['raw_target'][0])
    formula,wires,_=circuit.build(target)
    assert formula.and_count==26937
    initial=archived.control_assignment(wires,geometry,states,target,middle)
    complete=circuit.old.complete_assignment(formula,initial)
    check=circuit.old.check_assignment(formula,complete)
    assert check
    first_code=sum((complete[wire]&1)<<j for j,wire in enumerate(wires['codes'][0]))
    assert first_code==p['retrospective_witness_code']
    result={'status':'PASS_PUBLIC_WITNESS_ASSIGNMENT',
            'protocol_sha256':sha(D/'witness_protocol.json'),
            'first_code':first_code,'assignment_check':check,
            'raw_target':audit['raw_target'],
            'archive_sha256':sha(OLD/'join_audit_result.json'),
            'formula_sha256':sha(D/'rebuilt_public.xcnf')}
    (D/'witness_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()

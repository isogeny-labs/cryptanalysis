"""Complete constructed assignment check for bucket and reciprocal table clauses."""
import hashlib,json,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
BASE=ROOT/'n131_w18_allseed_fourpair_20261012'
TRACE=ROOT/'n131_w18_joint_pair_filter_20261012'
sys.path.insert(0,str(BASE));sys.path.insert(0,str(TRACE))
from fourpair_v2 import build,check_assignment,field_config
from trace_circuit import trace_extend

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    p=json.loads((HERE/'table_control_protocol.json').read_text())
    paths={'source':HERE/'check_table_control.py','fixture':HERE/'bucket_control_fixture.json',
           'builder':BASE/'fourpair_v2.py','trace_source':TRACE/'trace_circuit.py',
           'original_formula':TRACE/'ordinary.xcnf','bucket_formula':HERE/'bucket_00.xcnf',
           'table_formula':HERE/'bucket_00_table.xcnf','plan':HERE/'bucket_plan.json',
           'table_result':HERE/'table_gate_result.json'}
    assert {k:sha(v) for k,v in paths.items()}==p['sha256']
    fixture=json.loads(paths['fixture'].read_text())
    field,_,rotations=field_config('n41')
    circuit,wires,_=build('n41',int(fixture['target_reciprocal']))
    trace_extend(circuit,wires,field)
    assert (circuit.next_var-1,len(circuit.clauses),len(circuit.xors))==(14803,35810,2892)
    base_lines=paths['original_formula'].read_text().splitlines()
    bucket_lines=paths['bucket_formula'].read_text().splitlines()
    table_lines=paths['table_formula'].read_text().splitlines()
    plan=json.loads(paths['plan'].read_text())['plan'][0]
    units=[str(v)+' 0' for v in plan['unit_literals']]
    assert bucket_lines[1:13]==units and bucket_lines[13:]==base_lines[1:]
    extra_count=json.loads(paths['table_result'].read_text())['added_cnf_clauses']
    extra=table_lines[1:1+extra_count]
    assert table_lines[1+extra_count:]==bucket_lines[1:]
    circuit.clauses.extend(units);circuit.clauses.extend(extra)
    checked=check_assignment(circuit,wires,fixture,field,rotations)
    assert checked['status']=='PASS_COMPLETE_CONSTRUCTED_ASSIGNMENT'
    assert checked['clauses']==35810+12+extra_count
    result={'status':'PASS_N41_BUCKET_TABLE_COMPLETE_ASSIGNMENT',
            'variables':checked['variables'],'clauses':checked['clauses'],
            'xor_rows':checked['xor_rows'],'bucket_units':12,
            'table_clauses':extra_count,'sha256':{k:sha(v) for k,v in paths.items()},
            'protocol_sha256':sha(HERE/'table_control_protocol.json')}
    (HERE/'table_control_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(result['status'],result['clauses'],result['xor_rows'],flush=True)
if __name__=='__main__':main()

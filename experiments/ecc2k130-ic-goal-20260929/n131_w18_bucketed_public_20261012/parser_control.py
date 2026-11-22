"""Independent positive XCNF-to-pycryptosat semantics and model replay."""
import hashlib,json,sys,time
from pathlib import Path
from pycryptosat import Solver

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'n131_w18_allseed_fourpair_20261012'
TRACE=HERE.parent/'n131_w18_joint_pair_filter_20261012'
sys.path.insert(0,str(BASE));sys.path.insert(0,str(TRACE))
from fourpair_v2 import build,field_config
from trace_circuit import trace_extend

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    p=json.loads((HERE/'parser_control_protocol.json').read_text())
    paths={'source':HERE/'parser_control.py','formula':TRACE/'ordinary.xcnf',
           'fixture':BASE/'n41_diagonal/control_fixture.json',
           'builder':BASE/'fourpair_v2.py','trace_source':TRACE/'trace_circuit.py',
           'module':Path(p['pycryptosat_module_path'])}
    assert {k:sha(v) for k,v in paths.items()}==p['sha256']
    start=time.monotonic_ns()
    fixture=json.loads(paths['fixture'].read_text())
    field,_,rotations=field_config('n41')
    circuit,wires,_=build('n41',int(fixture['target_reciprocal']))
    trace_extend(circuit,wires,field)
    assumptions=[]
    def fixed(bits,value):
        assumptions.extend(v if (value>>i)&1 else -v for i,v in enumerate(bits))
    for pair,i in zip(fixture['masks'],range(0,8,2)):
        fixed(wires['masks'][i],pair[0]);fixed(wires['masks'][i+1],pair[1])
    for c,bits,rotation in zip(fixture['pair_reciprocals'],wires['pair_outputs'],rotations):
        fixed(bits,field.frob(int(c),(field.n-rotation)%field.n))
    for c,bits in zip(fixture['intermediate_reciprocals'],wires['middle']):fixed(bits,int(c))
    solver=Solver(threads=1);clauses=[];xors=[]
    with paths['formula'].open() as inp:
        header=inp.readline().split();assert header==['p','cnf','14803','38702']
        for line in inp:
            tokens=line.split()
            if not tokens:continue
            if tokens[0]=='x':
                assert tokens[-1]=='0';lits=list(map(int,tokens[1:-1]))
                rhs=(1+sum(v<0 for v in lits))%2
                solver.add_xor_clause([abs(v) for v in lits],bool(rhs))
                xors.append((lits,rhs))
            else:
                assert tokens[-1]=='0';lits=list(map(int,tokens[:-1]))
                solver.add_clause(lits);clauses.append(lits)
    assert (len(clauses),len(xors))==(35810,2892)
    sat,model=solver.solve(assumptions=assumptions,time_limit=p['solver_cap_seconds'])
    if sat is not True:
        print('CONTROL_STATUS',sat,'elapsed',(time.monotonic_ns()-start)/1e9,flush=True)
        raise RuntimeError('constructed positive assignment did not return SAT')
    assert len(model)==14804
    assert all(model[abs(v)]==(v>0) for v in assumptions)
    assert all(any(model[abs(v)]==(v>0) for v in row) for row in clauses)
    assert all((sum(bool(model[abs(v)]) for v in row)%2)==rhs for row,rhs in xors)
    result={'status':'PASS_PYCRYPTOSAT_FULL_MODEL_REPLAY','assumptions':len(assumptions),
            'variables':len(model)-1,'clauses':len(clauses),'xor_rows':len(xors),
            'wall_ns':time.monotonic_ns()-start,'protocol_sha256':sha(HERE/'parser_control_protocol.json')}
    (HERE/'parser_control_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(result['status'],result['wall_ns']/1e9,flush=True)
if __name__=='__main__':main()

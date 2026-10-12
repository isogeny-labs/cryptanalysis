"""One persistent native-XOR solver with target-ordered bucket assumptions."""
import hashlib,json,time
from pathlib import Path
from pycryptosat import Solver

HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,obj):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n');tmp.replace(path)

def main():
    p=json.loads((HERE/'incremental_protocol.json').read_text())
    paths={'worker':HERE/'incremental_worker.py','base_formula':HERE.parent/'n131_w18_joint_pair_filter_20261012/ordinary.xcnf',
           'plan':HERE/'bucket_plan.json','module':Path(p['pycryptosat_module_path'])}
    assert {k:sha(v) for k,v in paths.items()}==p['worker_sha256']
    plan=json.loads(paths['plan'].read_text())
    assert len(plan['plan'])==8
    start=time.monotonic_ns();solver=Solver(threads=1)
    cnf=xor=0
    with paths['base_formula'].open() as inp:
        header=inp.readline().split();assert header[:2]==['p','cnf']
        assert list(map(int,header[2:]))==[14803,38702]
        for line in inp:
            parts=line.split()
            if not parts:continue
            if parts[0]=='x':
                lits=list(map(int,parts[1:-1]));assert parts[-1]=='0'
                rhs=(1+sum(v<0 for v in lits))%2
                solver.add_xor_clause([abs(v) for v in lits],bool(rhs));xor+=1
            else:
                lits=list(map(int,parts[:-1]));assert parts[-1]=='0'
                solver.add_clause(lits);cnf+=1
    assert (cnf,xor)==(35810,2892)
    setup=time.monotonic_ns()-start
    rows=[]
    save(HERE/'incremental_progress.json',{'status':'LOADED','setup_ns':setup,
                                           'clauses':cnf,'xor_rows':xor,'attempts':rows})
    for row in plan['plan']:
        begin=time.monotonic_ns()
        sat,model=solver.solve(assumptions=row['unit_literals'],time_limit=p['per_bucket_solver_cap_seconds'])
        ended=time.monotonic_ns()
        status='SAT_PENDING_MODEL_AUDIT' if sat is True else 'UNSAT' if sat is False else 'BOUNDED_UNKNOWN'
        record={'rank':row['rank'],'bucket':row['bucket'],'status':status,
                'solve_wall_ns':ended-begin,'assumptions':row['unit_literals']}
        rows.append(record)
        if sat is True:
            signed=[i if model[i] else -i for i in range(1,len(model))]
            save(HERE/'incremental_model.json',{'bucket':row['bucket'],'rank':row['rank'],
                                                'signed_literals':signed})
        save(HERE/'incremental_progress.json',{'status':'RUNNING','setup_ns':setup,
                                               'clauses':cnf,'xor_rows':xor,'attempts':rows})
        print('BUCKET',row['rank'],status,(ended-begin)/1e9,flush=True)
        if sat is True:break
    print('WORKER_DONE',len(rows),(time.monotonic_ns()-start)/1e9,flush=True)

if __name__=='__main__':main()

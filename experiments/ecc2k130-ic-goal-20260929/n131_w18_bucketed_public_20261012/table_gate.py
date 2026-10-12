"""Encode the exact first-pair reciprocal fiber for public bucket 905."""
import hashlib,json,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
BASE=ROOT/'n131_w18_allseed_fourpair_20261012'
sys.path.insert(0,str(BASE))
from fourpair_v2 import build,field_config

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    p=json.loads((HERE/'table_gate_protocol.json').read_text())
    paths={'source':HERE/'table_gate.py','base_formula':HERE/'bucket_00.xcnf',
           'input':BASE/'n41_diagonal/pairs.tsv','builder':BASE/'fourpair_v2.py',
           'plan':HERE/'bucket_plan.json','fixture':BASE/'n41_diagonal/control_fixture.json',
           'hit_audit':HERE/'bucket_audit_result.json'}
    assert {k:sha(v) for k,v in paths.items()}==p['sha256']
    plan=json.loads(paths['plan'].read_text())
    assert plan['plan'][0]['low6_masks']==[9,14]
    fixture=json.loads(paths['fixture'].read_text())
    field,_,_=field_config('n41')
    circuit,wires,_=build('n41',int(fixture['target_reciprocal']))
    output_bits=wires['pair_outputs'][0];assert len(output_bits)==41
    states=[]
    for line in paths['input'].read_text().splitlines():
        v=line.split()
        if v[0]!='S' or int(v[1])!=0:continue
        a,b=int(v[3]),int(v[4])
        if sorted([a&63,b&63])!=[9,14]:continue
        states.append({'id':int(v[2]),'masks':[a,b],
                       'reciprocal':field.inverse(int(v[9]))})
    assert len(states)==4 and {tuple(s['masks']) for s in states}=={(142,201)}
    values=sorted({s['reciprocal'] for s in states});assert len(values)==2
    assert all(sum(v['reciprocal']==c for v in states)==2 for c in values)
    c0,c1=values;different=[i for i in range(41) if ((c0^c1)>>i)&1]
    assert different;pivot=different[0];lit0=output_bits[pivot]
    clauses=[]
    for i,wire in enumerate(output_bits):
        if i==pivot:continue
        b0=(c0>>i)&1;b1=(c1>>i)&1
        if b0==b1:clauses.append([wire if b0 else -wire])
        else:
            equal=b0==((c0>>pivot)&1)
            clauses.extend([[-lit0,wire],[lit0,-wire]] if equal else
                           [[-lit0,-wire],[lit0,wire]])
    hit=json.loads(paths['hit_audit'].read_text())
    hx=int(hit['pairs'][0]['point'][0]);assert field.inverse(hx) in values
    base=paths['base_formula'].read_bytes();header,body=base.split(b'\n',1)
    parts=header.split();assert parts[:2]==[b'p',b'cnf'] and int(parts[2])==14803
    block=b''.join((' '.join(map(str,row))+' 0\n').encode() for row in clauses)
    formula=b'p cnf '+parts[2]+b' '+str(int(parts[3])+len(clauses)).encode()+b'\n'+block+body
    path=HERE/'bucket_00_table.xcnf';assert not path.exists();path.write_bytes(formula)
    result={'status':'PASS_EXACT_N41_BUCKET_FIRST_PAIR_RECIPROCAL_GATE',
            'candidate_id':None,'bucket':905,'source_states':states,
            'reciprocals':values,'output_wires':output_bits,'pivot_bit':pivot,
            'added_cnf_clauses':len(clauses),'added_unit_clauses':sum(len(x)==1 for x in clauses),
            'formula_sha256':sha(path),'formula_bytes':len(formula),
            'sha256':{k:sha(v) for k,v in paths.items()},
            'protocol_sha256':sha(HERE/'table_gate_protocol.json')}
    (HERE/'table_gate_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(result['status'],values,len(clauses),flush=True)
if __name__=='__main__':main()

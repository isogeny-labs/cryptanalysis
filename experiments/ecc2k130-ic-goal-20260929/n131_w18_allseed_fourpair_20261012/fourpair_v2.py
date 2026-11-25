"""Exact all-seed four-pair reciprocal Boolean circuit for N41 and N131."""
import argparse,hashlib,json,sys,time
from collections import defaultdict
from itertools import combinations
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path[:0]=[str(ROOT/'n41_basis_aware_quartic_20261011'),str(HERE.parent.parent/'koblitz-polynomial-w-pair-20260925')]
from sparse import Algebra
from karatsuba_circuit import KaratsubaCircuit

class Field:
    def __init__(self,n,taps):
        self.n=n;self.modulus=(1<<n)|sum(1<<i for i in taps)
    def mul(self,a,b):
        out=0
        while b:
            if b&1:out^=a
            b>>=1;a<<=1
            if a>>self.n:a^=self.modulus
        return out
    def square(self,a):return self.mul(a,a)
    def frob(self,a,k):
        for _ in range(k):a=self.square(a)
        return a
    def inverse(self,a):
        assert a
        out=1;exp=(1<<self.n)-2
        while exp:
            if exp&1:out=self.mul(out,a)
            a=self.square(a);exp>>=1
        return out

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def bdd(codes,width):
    nodes={};uniq={}
    def visit(values,bit):
        if not values:return 0
        if len(values)==1<<(bit+1):return 1
        if bit<0:return 1
        low=[v for v in values if not(v>>bit&1)]
        high=[v for v in values if v>>bit&1]
        a,b=visit(low,bit-1),visit(high,bit-1)
        if a==b:return a
        key=(bit,a,b)
        if key not in uniq:
            code=len(uniq)+2;uniq[key]=code;nodes[code]=key
        return uniq[key]
    return visit(sorted(codes),width-1),nodes

def emit_bdd(circuit,bits,root,nodes):
    literals={0:0,1:-1}
    for node in sorted(nodes):
        bit,low,high=nodes[node]
        l,r=literals[low],literals[high]
        literals[node]=circuit.xor((l,circuit.and_(bits[bit],circuit.xor((l,r)))))
    circuit.clauses.append(str(literals[root])+' 0')

def support(field_name):
    if field_name=='n41':
        g=json.loads((ROOT/'n41_w7_entropy_cubic_20261011/w8/geometry.json').read_text())
        return {int(row['mask']):int(row['column']) for row in g['rows']}
    path=ROOT/'n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv'
    return {int(m):int(c) for m,c in (line.split() for line in path.read_text().splitlines())}

def field_config(name):
    return (Field(41,[0,3]),8,[0,7,14,21]) if name=='n41' else (Field(131,[0,1,2,13]),18,[0,32,64,96])

def build(name,target_reciprocal):
    field,width,rotations=field_config(name)
    columns=support(name);root,nodes=bdd(set(columns),width)
    assert target_reciprocal and len(columns)==(125 if name=='n41' else 131307)
    circuit=KaratsubaCircuit(field.n,[i for i in range(field.n) if field.modulus>>i&1])
    algebra=Algebra(circuit,field,dense_and_threshold=3000)
    masks=[];outs=[];points=[]
    for rotation in rotations:
        pair_masks=[]
        for _ in range(2):
            bits=[circuit.variable() for _ in range(width)]
            pair_masks.append(bits);masks.append(bits)
            emit_bdd(circuit,bits,root,nodes)
        c_bits=[circuit.variable() for _ in range(field.n)]
        circuit.clauses.append(' '.join(map(str,c_bits))+' 0')
        outs.append(c_bits)
        a,b=[algebra.expression((wire,1<<(i+1)) for i,wire in enumerate(bits))
             for bits in pair_masks]
        p=algebra.mul(a,b)
        c=algebra.from_bits(c_bits)
        cp=algebra.mul(c,p)
        eq=algebra.add(algebra.square(cp),cp,algebra.square(algebra.add(a,b)),algebra.square(c))
        circuit.require_zero(eq.bits())
        rotated=circuit.linear_element(c_bits,[field.frob(1<<i,rotation) for i in range(field.n)])
        points.append(algebra.from_bits(rotated))
    grouped=defaultdict(list)
    for mask,column in columns.items():grouped[column].append(mask)
    collision_pairs=[(a,b) for group in grouped.values() for a,b in combinations(sorted(group),2)]
    shield_clauses=0
    def mismatch(bits,code):
        return [(-wire if code>>i&1 else wire) for i,wire in enumerate(bits)]
    for i in range(len(masks)):
        for j in range(i+1,len(masks)):
            different=[circuit.xor((a,b)) for a,b in zip(masks[i],masks[j])]
            circuit.clauses.append(' '.join(map(str,different))+' 0')
            for a,b in collision_pairs:
                for left,right in ((a,b),(b,a)):
                    circuit.clauses.append(' '.join(map(str,mismatch(masks[i],left)+mismatch(masks[j],right)))+' 0')
                    shield_clauses+=1
    middle=[]
    for i in range(2):
        bits=[circuit.variable() for _ in range(field.n)]
        middle.append(bits);circuit.clauses.append(' '.join(map(str,bits))+' 0')
    def s3(a,b,z):
        ab=algebra.mul(a,b)
        abz=algebra.mul(ab,z)
        eq=algebra.add(algebra.square(abz),abz,
                       algebra.square(algebra.add(a,b)),algebra.square(z))
        circuit.require_zero(eq.bits())
    s3(points[0],points[1],algebra.from_bits(middle[0]))
    s3(points[2],points[3],algebra.from_bits(middle[1]))
    s3(algebra.from_bits(middle[0]),algebra.from_bits(middle[1]),
       algebra.expression(((-1,target_reciprocal),)))
    wiremap={'masks':masks,'pair_outputs':outs,'middle':middle}
    return circuit,wiremap,{'source_masks':len(columns),'bdd_nodes':len(nodes),
                             'same_column_mask_pairs':len(collision_pairs),
                             'folded_column_shield_clauses':shield_clauses,
                             'rotations':rotations,'width':width,'target_reciprocal':target_reciprocal,
                             'sparse_mul_calls':algebra.sparse_mul_calls,
                             'generic_mul_calls':algebra.generic_mul_calls}

def check_assignment(circuit,wires,fixture,field,rotations):
    values={}
    def put(bits,number):
        for i,v in enumerate(bits):values[v]=int(number)>>i&1
    for pair,bits in zip(fixture['masks'],[wires['masks'][i:i+2] for i in range(0,8,2)]):
        for m,b in zip(pair,bits):put(b,m)
    for number,bits,rotation in zip(fixture['pair_reciprocals'],wires['pair_outputs'],rotations):
        put(bits,field.frob(number,(field.n-rotation)%field.n))
    for number,bits in zip(fixture['intermediate_reciprocals'],wires['middle']):put(bits,number)
    gates=[]
    gates.extend((v,'and',key) for key,v in circuit.and_cache.items())
    gates.extend((v,'xor',key) for key,v in circuit.xor_cache.items())
    def value(v):return 1 if v==-1 else 0 if v==0 else values[v]
    for out,kind,key in sorted(gates):
        assert out not in values
        values[out]=(value(key[0])&value(key[1])) if kind=='and' else (
            key[1]^sum(value(v) for v in key[0])%2)
    assert len(values)==circuit.next_var-1
    for line in circuit.clauses:
        lits=[int(x) for x in line.split()[:-1]]
        assert any((value(abs(v)) if v>0 else 1-value(abs(v))) for v in lits),line
    for line in circuit.xors:
        lits=[int(x) for x in line.split()[1:-1]]
        assert sum(value(abs(v)) if v>0 else 1-value(abs(v)) for v in lits)%2==1,line
    return {'status':'PASS_COMPLETE_CONSTRUCTED_ASSIGNMENT','variables':len(values),
            'clauses':len(circuit.clauses),'xor_rows':len(circuit.xors)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('field',choices=['n41','n131']);ap.add_argument('mode',choices=['control','ordinary']);args=ap.parse_args()
    if args.field!='n41':raise SystemExit('N131 build awaits frozen N41 gate and source-bound projection')
    fixture=json.loads((HERE/'n41_diagonal/control_fixture.json').read_text())
    proto=json.loads((HERE/'protocol.json').read_text())
    assert proto['source_sha256']==sha(Path(__file__))
    assert proto['control_fixture_sha256']==sha(HERE/'n41_diagonal/control_fixture.json')
    start=time.monotonic_ns();circuit,wires,meta=build(args.field,fixture['target_reciprocal'])
    built=time.monotonic_ns()
    if args.mode=='control':
        field,_,rotations=field_config(args.field)
        check=check_assignment(circuit,wires,fixture,field,rotations)
        (HERE/'control_check.json').write_text(json.dumps(check,sort_keys=True,indent=2)+'\n')
    path=HERE/(args.field+'_'+args.mode+'.xcnf')
    assert not path.exists();circuit.write(path)
    done=time.monotonic_ns()
    result={'field':args.field,'mode':args.mode,'candidate_id':None,
            'variables':circuit.next_var-1,'and_gates':circuit.and_count,
            'clauses':len(circuit.clauses),'xor_rows':len(circuit.xors),
            'bytes':path.stat().st_size,'formula_sha256':sha(path),
            'build_ns':built-start,'write_ns':done-built,'metadata':meta,
            'protocol_sha256':sha(HERE/'protocol.json')}
    (HERE/(args.field+'_'+args.mode+'.json')).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()

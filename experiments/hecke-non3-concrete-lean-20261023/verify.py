"""Independent source-to-matrix and formal receipt audit."""
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'hecke-inert2-non3-cycle-20261023'/'full_matrix.json'

def sha(path): return sha256(path.read_bytes()).hexdigest()
def read(name): return json.loads((HERE/name).read_text())

def rank(matrix):
    a=[[Fraction(x) for x in row] for row in matrix]
    pivot=0
    for col in range(len(a[0])):
        row=next((i for i in range(pivot,len(a)) if a[i][col]),None)
        if row is None: continue
        a[pivot],a[row]=a[row],a[pivot]
        scale=a[pivot][col]
        a[pivot]=[v/scale for v in a[pivot]]
        for i in range(pivot+1,len(a)):
            factor=a[i][col]
            if factor:
                a[i]=[v-factor*w for v,w in zip(a[i],a[pivot])]
        pivot+=1
    return pivot

def main():
    protocol=read('SOURCE_PROTOCOL.json');encoding=read('block_encoding.json')
    build=read('formal/build.json');data=json.loads(SOURCE.read_text())
    assert protocol['status']=='FROZEN_BEFORE_CONCRETE_LEAN_GENERATION'
    assert protocol['source_sha256']==encoding['source_sha256']==sha(SOURCE)
    committed=subprocess.check_output(['git','show',
        protocol['source_commit']+':'+protocol['source_path']])
    assert sha256(committed).hexdigest()==protocol['source_sha256']
    assert committed==SOURCE.read_bytes()
    assert encoding['source_protocol_sha256']==sha(HERE/'SOURCE_PROTOCOL.json')
    assert encoding['generator_sha256']==sha(HERE/'generate.py')
    lean=HERE/'formal/ConcreteNonThreeBlock.lean'
    assert encoding['lean_sha256']==build['source_sha256']==sha(lean)
    assert build['status']=='CONCRETE_30_ROW_KERNEL_THEOREM_BUILT'
    assert build['toolchain_sha256']==sha(HERE/'formal/lean-toolchain')
    assert build['manifest_sha256']==sha(HERE/'formal/lake-manifest.json')
    assert build['output_sha256']==sha(HERE/'formal/build-output.txt')
    assert build['axioms']==["'ConcreteNonThreeBlock.blockRow_kernel_zero' depends on axioms: [propext, Classical.choice, Quot.sound]"]
    source=lean.read_text()
    assert all(token not in source for token in ('sorry','admit','sorryAx','axiom '))
    assert '#print axioms ConcreteNonThreeBlock.blockRow_kernel_zero' in source
    columns=[p['column'] for p in data['column_points'] if p['conductor']==2]
    assert columns==encoding['source_columns']==list(range(10,40))
    nonfloor={p['column'] for p in data['column_points'] if p['conductor']!=6}
    row_for={(m['source'],m['degree']):m['row'] for m in data['row_records']}
    expected_rows=[row_for[i,3] for i in columns]
    assert expected_rows==encoding['source_row_ids']
    expected_supports=[]
    for source_column,row_id in zip(columns,expected_rows):
        row=data['relation_rows'][row_id]
        assert all(int(k) in columns for k,v in row.items() if v and int(k) in nonfloor)
        retained={int(k)-10:int(v) for k,v in row.items() if int(k) in columns and v}
        assert len(retained)==3 and set(retained.values())=={1} and source_column-10 in retained
        expected_supports.append(sorted(retained))
    assert expected_supports==encoding['local_row_supports']
    extracted={int(i):[int(x) for x in re.findall(r'x (\d+)',expr)]
               for i,expr in re.findall(r'^  \| (\d+) => ([^\n]+)$',source,re.M)}
    assert sorted(extracted)==list(range(30))
    assert [extracted[i] for i in range(30)]==expected_supports
    matrix=[[int(j in support) for j in range(30)] for support in expected_supports]
    assert rank(matrix)==30
    cycles=encoding['local_cycles']
    assert len(cycles)==6 and sorted(len(c) for c in cycles)==[5]*6
    assert sorted(i for cycle in cycles for i in cycle)==list(range(30))
    for cycle in cycles:
        for k,i in enumerate(cycle):
            assert set(expected_supports[i])=={cycle[k-1],i,cycle[(k+1)%5]}
    out={'status':'PASS_CONCRETE_BLOCK_LEAN_BOUND_TO_SAVED_ROWS',
         'source_matrix_sha256':sha(SOURCE),'source_protocol_sha256':sha(HERE/'SOURCE_PROTOCOL.json'),
         'encoding_sha256':sha(HERE/'block_encoding.json'),
         'build_sha256':sha(HERE/'formal/build.json'),
         'validator_sha256':sha(HERE/'verify.py'),
         'row_count':30,'column_count':30,'exact_rational_rank':30,
         'cycle_lengths':[5]*6,'lean_theorem':'ConcreteNonThreeBlock.blockRow_kernel_zero',
         'candidate_id':None,'timing_claim':None}
    (HERE/'verification.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'exact_rational_rank':out['exact_rational_rank']},sort_keys=True))

if __name__=='__main__': main()

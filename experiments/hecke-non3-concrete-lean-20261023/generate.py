"""Generate an exact Lean block theorem from the sealed D=-227 matrix."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'hecke-inert2-non3-cycle-20261023'/'full_matrix.json'

def sha(path): return sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/'SOURCE_PROTOCOL.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_CONCRETE_LEAN_GENERATION'
    assert protocol['source_sha256']==sha(SOURCE)
    data=json.loads(SOURCE.read_text())
    assert data['status']=='NON3_CYCLE_FULL_MATRIX_PRODUCED'
    points=data['column_points'];rows=data['relation_rows'];meta=data['row_records']
    columns=[p['column'] for p in points if p['conductor']==2]
    assert columns==list(range(10,40))
    nonfloor={p['column'] for p in points if p['conductor']!=6}
    row_for={(m['source'],m['degree']):m['row'] for m in meta}
    triples=[];adj={}
    for source in columns:
        row=rows[row_for[source,3]]
        assert all(int(k) in columns for k,v in row.items() if v and int(k) in nonfloor)
        retained={int(k):int(v) for k,v in row.items() if int(k) in columns and v}
        assert len(retained)==3 and all(v==1 for v in retained.values())
        assert source in retained
        local=[k-10 for k in sorted(retained)]
        triples.append(local)
        adj[source-10]=set(local)-{source-10}
        assert len(adj[source-10])==2
    assert all(i in adj[j] for i,ns in adj.items() for j in ns)
    unseen=set(range(30));cycles=[]
    while unseen:
        start=min(unseen);cycle=[start];prev=start;current=min(adj[start])
        while current!=start:
            assert current not in cycle
            cycle.append(current)
            nxt=adj[current]-{prev}
            assert len(nxt)==1
            prev,current=current,next(iter(nxt))
        assert len(cycle)==5
        unseen.difference_update(cycle);cycles.append(cycle)
    assert len(cycles)==6
    lines=['module','',
           'public import Mathlib.Tactic.Linarith',
           'public import Mathlib.Tactic.FinCases',
           'public import Mathlib.Data.Rat.Init','',
           '/-! Exact 30 by 30 conductor-2 nonfloor block from the sealed D=-227 matrix.','    Source SHA-256: '+sha(SOURCE)+' -/','',
           'namespace ConcreteNonThreeBlock','',
           'public def blockRow (x : Fin 30 → ℚ) (i : Fin 30) : ℚ :=',
           '  match i.val with']
    for i,cols in enumerate(triples):
        lines.append(f'  | {i} => '+' + '.join(f'x {j}' for j in cols))
    lines+=['  | _ => 0','','private theorem fiveCycle (a b c d e : ℚ)',
            '    (h0 : a + b + e = 0) (h1 : b + a + c = 0)',
            '    (h2 : c + b + d = 0) (h3 : d + c + e = 0)',
            '    (h4 : e + d + a = 0) :',
            '    a = 0 ∧ b = 0 ∧ c = 0 ∧ d = 0 ∧ e = 0 := by']
    for variable in 'abcde':
        lines.append(f'  have h{variable} : {variable} = 0 := by linarith only [h0, h1, h2, h3, h4]')
    lines+=['  exact ⟨ha, hb, hc, hd, he⟩','','public theorem blockRow_kernel_zero (x : Fin 30 → ℚ)',
            '    (h : ∀ i, blockRow x i = 0) : ∀ i, x i = 0 := by']
    for c,cycle in enumerate(cycles):
        arg=' '.join(f'(x {i})' for i in cycle)
        lines.append(f'  have cycle{c} := fiveCycle {arg}')
        for i in cycle:
            lines.append(f'    (by have hx := h (⟨{i}, by decide⟩ : Fin 30); norm_num [blockRow] at hx; linarith only [hx])')
        lines.append(f'  rcases cycle{c} with ⟨'+', '.join(f'z{i}' for i in cycle)+'⟩')
    cases=' ∨ '.join(f'i.val = {j}' for j in range(30))
    lines+=['  intro i',f'  have hcases : {cases} := by omega',
            '  rcases hcases with '+' | '.join(f'h{j}' for j in range(30))]
    for j in range(30):
        lines.append(f'  · have hi : i = ({j} : Fin 30) := Fin.ext h{j}')
        lines.append(f'    simpa [hi] using z{j}')
    lines+=['',
            'end ConcreteNonThreeBlock','',
            '#print axioms ConcreteNonThreeBlock.blockRow_kernel_zero','']
    out=HERE/'formal'/'ConcreteNonThreeBlock.lean'
    out.write_text('\n'.join(lines))
    receipt={'status':'EXACT_PROJECTED_BLOCK_LEAN_GENERATED',
             'source_sha256':sha(SOURCE),'source_protocol_sha256':sha(HERE/'SOURCE_PROTOCOL.json'),
             'generator_sha256':sha(HERE/'generate.py'),'lean_sha256':sha(out),
             'source_columns':columns,
             'source_row_ids':[row_for[i,3] for i in columns],
             'local_row_supports':triples,'local_cycles':cycles,
             'candidate_id':None,'timing_claim':None}
    (HERE/'block_encoding.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'rows':len(triples),'cycles':cycles},sort_keys=True))

if __name__=='__main__': main()

"""Generate Lean arithmetic certificates for the F199 relation kernel."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
REPO=ROOT.parent.parent
PLAN=json.loads((ROOT/'inputs.json').read_text())
POST=json.loads((ROOT/'post_run.json').read_text())


def pinned(name):
    item=PLAN['frozen'][name]
    raw=(REPO/item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    return json.loads(raw)


def sparse(item):
    return {int(k):int(v) for k,v in item['row'].items() if v}


def lit(xs):
    return '['+', '.join(map(str,xs))+']'


def mat(xs):
    return '[\n'+',\n'.join('  '+lit(x) for x in xs)+'\n]'


def independent_indices(rows,q):
    pivots={}
    selected=[]
    for index,row in enumerate(rows):
        v={j:x%q for j,x in row.items() if x%q}
        while v:
            j=min(v)
            if j not in pivots:
                z=pow(v[j],-1,q)
                pivots[j]={k:x*z%q for k,x in v.items()}
                selected.append(index)
                break
            z=v[j]
            for k,x in pivots[j].items():
                y=(v.get(k,0)-z*x)%q
                if y:v[k]=y
                else:v.pop(k,None)
    return selected


def pivot_columns(matrix,q):
    M=[[x%q for x in row] for row in matrix]
    pivots=[]
    for col in range(40):
        i=len(pivots)
        j=next((j for j in range(i,len(M)) if M[j][col]),None)
        if j is None:continue
        M[i],M[j]=M[j],M[i]
        z=pow(M[i][col],-1,q)
        M[i]=[x*z%q for x in M[i]]
        for j in range(len(M)):
            if j!=i and M[j][col]:
                z=M[j][col]
                M[j]=[(x-z*y)%q for x,y in zip(M[j],M[i])]
        pivots.append(col)
    return pivots


def inverse(M,q):
    n=len(M)
    A=[[x%q for x in row]+[int(i==j) for j in range(n)] for i,row in enumerate(M)]
    for col in range(n):
        pivot=next(i for i in range(col,n) if A[i][col])
        A[col],A[pivot]=A[pivot],A[col]
        z=pow(A[col][col],-1,q)
        A[col]=[x*z%q for x in A[col]]
        for i in range(n):
            if i!=col and A[i][col]:
                z=A[i][col]
                A[i]=[(x-z*y)%q for x,y in zip(A[i],A[col])]
    return [row[n:] for row in A]


def main():
    raw=(ROOT/'result.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==POST['result_sha256']
    result=json.loads(raw)
    cls=pinned('class-result.json')['cases'][0]
    prior=pinned('analysis.json')['cases'][0]
    five=pinned('result.json')
    rows=[sparse(x) for x in cls['base_rows']+prior['direct_candidates']+prior['hecke_candidates']]
    rows += [sparse(x) for x in five['arms']['direct']['candidates']]
    rows += [sparse(x) for x in five['arms']['hecke']['candidates']]
    q=PLAN['q'];logs=result['q_logs']
    assert len(rows)==706 and len(logs)==40
    assert all(sum(v*logs[j] for j,v in row.items())%q==0 for row in rows)
    selected_indices=independent_indices(rows,q)
    assert len(selected_indices)==39
    selected=[[rows[i].get(j,0)%q for j in range(40)] for i in selected_indices]
    columns=pivot_columns(selected,q)
    assert len(columns)==39
    minor=[[r[j] for j in columns] for r in selected]
    inv=inverse(minor,q)
    assert all(sum(minor[i][k]*inv[k][j] for k in range(39))%q==int(i==j)
               for i in range(39) for j in range(39))
    chunks=[rows[i:i+32] for i in range(0,len(rows),32)]
    lines=['module','','public import Init','','namespace FiniteP73757',
           'set_option maxRecDepth 65536','set_option maxHeartbeats 0',
           'public def qLog : List Nat := '+lit(logs),
           'public theorem qLog_nonzero : qLog.any (· != 0) = true := by decide',
           'public def dot (a b : List Nat) : Nat := ((a.zip b).foldl (fun s x => s + x.1 * x.2) 0) % 199']
    for i,chunk in enumerate(chunks):
        lines += [f'public def rowChunk{i} : List (List Nat) := '+mat([[r.get(j,0)%q for j in range(40)] for r in chunk]),
                  f'public theorem rowChunk{i}_annihilates : rowChunk{i}.all (fun r => dot r qLog == 0) = true := by decide']
    lines += ['public def allRows : List (List Nat) := '+' ++ '.join(f'rowChunk{i}' for i in range(len(chunks))),
              'public theorem allRows_annihilate : allRows.all (fun r => dot r qLog == 0) = true := by',
              '  simp [allRows, List.all_append, '+', '.join(f'rowChunk{i}_annihilates' for i in range(len(chunks)))+']',
              'public def selectedIndices : List Nat := '+lit(selected_indices),
              'public def selected : List (List Nat) := '+mat(selected),
              'public theorem selected_in_allRows : ∀ i : Fin 39,',
              '  allRows.getD (selectedIndices.getD i.val 0) [] = selected.getD i.val [] := by decide',
              'public def pivotColumns : List Nat := '+lit(columns),
              'public def minor : List (List Nat) := '+mat(minor),
              'public def inverse : List (List Nat) := '+mat(inv),
              'public theorem minor_matches : ∀ i j : Fin 39,',
              '  (minor.getD i.val []).getD j.val 0 =',
              '    (selected.getD i.val []).getD (pivotColumns.getD j.val 0) 0 := by decide',
              'public theorem inverse_certificate : ∀ i j : Fin 39,',
              '  ((List.range 39).foldl (fun s k => s + (minor.getD i.val []).getD k 0 * (inverse.getD k []).getD j.val 0) 0) % 199 =',
              '    if i.val == j.val then 1 else 0 := by decide',
              '#print axioms qLog_nonzero',
              '#print axioms allRows_annihilate',
              '#print axioms selected_in_allRows',
              '#print axioms minor_matches',
              '#print axioms inverse_certificate']
    lines += [f'#print axioms rowChunk{i}_annihilates' for i in range(len(chunks))]
    lines += ['end FiniteP73757','']
    (HERE/'FiniteP73757.lean').write_text('\n'.join(lines))
    cert={'schema':'hecke-d79-p73757-kernel-finite-cert-v1','rows':len(rows),'q':q,
          'selected_row_indices':selected_indices,'pivot_columns':columns,
          'selected_minor_size':39,'q_log_vector_sha256':result['q_log_vector_sha256']}
    (HERE/'certificate.json').write_text(json.dumps(cert,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'rows':len(rows),'selected_minor_size':39,'chunks':len(chunks)}))


if __name__=='__main__':
    main()

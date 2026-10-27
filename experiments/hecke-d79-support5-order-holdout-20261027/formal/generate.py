"""Generate finite rank certificates for the p73757 holdout gates."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
REPO=ROOT.parent.parent
POST=json.loads((ROOT/'post_result.json').read_text())
DEPENDENCY=REPO/'experiments/hecke-d79-p68437-support5-prefix-20261027/formal/generate.py'
DEPENDENCY_SHA='d99d0cd53e5194429e4f08f317f0df839c8ac78062caffe240995d542153352f'


def pinned(name):
    raw=(ROOT/name).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=POST['sha256'][name]:
        raise ValueError('PIN_MISMATCH:'+name)
    return json.loads(raw)


def load_helpers():
    if hashlib.sha256(DEPENDENCY.read_bytes()).hexdigest()!=DEPENDENCY_SHA:
        raise ValueError('GENERATOR_DEPENDENCY_MISMATCH')
    spec=importlib.util.spec_from_file_location('hecke_d79_gate_helpers',DEPENDENCY)
    out=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def emit(name,before,after,K):
    modulus=next(p for p in (3,5,7,11,101,103,107) if len(K.choose(after,p))==40)
    minor=[[r.get(j,0)%modulus for j in range(40)] for r in K.choose(after,modulus)]
    inv=K.inverse(minor,modulus)
    assert all(sum(minor[i][k]*inv[k][j] for k in range(40))%modulus==int(i==j)
               for i in range(40) for j in range(40))
    lines=['module','','public import Init','','namespace '+name,
           'set_option maxRecDepth 65536','set_option maxHeartbeats 0']
    if before is not None:
        kernel=K.integer_kernel(before)
        lines+=['public def kernel : List Int := '+K.literal(kernel),
                'public def dot (a b : List Int) : Int := (a.zip b).foldl (fun s x => s + x.1 * x.2) 0']
        chunks=[before[i:i+32] for i in range(0,len(before),32)]
        for i,chunk in enumerate(chunks):
            lines+=[f'public def prior{i} : List (List Int) := '+K.matrix([[r.get(j,0) for j in range(40)] for r in chunk]),
                    f'public theorem prior{i}_annihilated : prior{i}.all (fun r => dot r kernel == 0) = true := by decide']
        lines+=['public theorem kernel_nonzero : kernel.any (· != 0) = true := by decide',
                '#print axioms kernel_nonzero']
        lines += [f'#print axioms prior{i}_annihilated' for i in range(len(chunks))]
    lines+=['public def selected : List (List Nat) := '+K.matrix(minor),
            'public def inverse : List (List Nat) := '+K.matrix(inv),
            'public theorem inverse_certificate : ∀ i j : Fin 40,',
            f'  ((List.range 40).foldl (fun s k => s + (selected.getD i.val []).getD k 0 * (inverse.getD k []).getD j.val 0) 0) % {modulus} =',
            '  if i.val == j.val then 1 else 0 := by decide',
            '#print axioms inverse_certificate','end '+name,'']
    (HERE/(name+'.lean')).write_text('\n'.join(lines))
    return {'module':name,'previous_rows':None if before is None else len(before),
            'terminal_rows':len(after),'auxiliary_prime':modulus,
            'kernel_nonzero':before is not None}


def main():
    K=load_helpers()
    cls=pinned('class-result.json')['cases'][0]
    prior=pinned('analysis.json')['cases'][0]
    result=pinned('result.json')
    base=[K.row(x) for x in cls['base_rows']+prior['direct_candidates']+prior['hecke_candidates']]
    direct=[K.row(x) for x in result['arms']['direct']['candidates']]
    hecke=result['arms']['hecke']['candidates']
    output=[]
    output.append(emit('GateDirectZero',None,base+direct,K))
    for order in ('ascending','priority'):
        count=result['paths'][order]['first_rank40']['support4']
        source_order=cls[order+'_order']
        def rows_at(n):
            seen=set(source_order[:n])
            return base+[K.row(x) for x in hecke if set(x['sources'])<=seen]
        output.append(emit('Gate'+order.capitalize()+'Base',rows_at(count-1),rows_at(count),K))
    (HERE/'certificates.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps(output))


if __name__=='__main__':
    main()

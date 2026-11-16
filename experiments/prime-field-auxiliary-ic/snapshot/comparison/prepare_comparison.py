"""Matched public targets and equal-size auxiliary/plain factor bases."""
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from prepare import Curve,chain


def write_dataset(folder,public,points):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'public.json').write_text(json.dumps(public|{'factor_base_representatives':points},indent=2)+'\n')
    P,Q=public['P'],public['Q']
    with (folder/'public.txt').open('w') as out:
        out.write(f"{public['p']} {public['n']} {public['a']} {public['b']}\n")
        out.write(f'{P[0]} {P[1]} {Q[0]} {Q[1]}\n{len(points)}\n')
        out.writelines(f'{x} {y}\n' for x,y in points)


def main():
    timings=[]
    for bits,source,s in [(31,ROOT.parent,10),(61,ROOT.parent/'run61',11)]:
        public=json.loads((source/'public.json').read_text())
        public={k:public[k] for k in ['p','n','a','b','P','Q']}
        original=json.loads((source/'public.json').read_text())
        K=len(original['factor_base_representatives'])
        h=original.get('cofactor',1)
        p=public['p']
        E=Curve(p,a4=public['a'],a6=public['b'])
        excluded={tuple(public['P']),E.neg(tuple(public['P'])),tuple(public['Q']),E.neg(tuple(public['Q']))}

        def lift(x):
            rhs=(x**3+public['a']*x+public['b'])%p
            y=pow(rhs,(p+1)//4,p)
            if y*y%p!=rhs:return None
            R=E.mul(h,(x,min(y,p-y)))
            if R is None:return None
            return R[0],min(R[1],p-R[1])

        start=time.perf_counter()
        aux,V=chain(p,s,enumerate_all=True)
        points=[];seen=set()
        for x in V:
            R=lift(x)
            if R is not None and R[0] not in seen:
                points.append(R);seen.add(R[0])
        auxiliary_seconds=time.perf_counter()-start
        assert points==[tuple(R) for R in original['factor_base_representatives']]
        assert len(points)==K
        write_dataset(ROOT/f'field{bits}'/'auxiliary',public,points)

        start=time.perf_counter()
        plain=[];seen=set();x=10
        while len(plain)<K:
            R=lift(x);x+=1
            if R is not None and R[0] not in seen and R not in excluded:
                plain.append(R);seen.add(R[0])
        plain_seconds=time.perf_counter()-start
        write_dataset(ROOT/f'field{bits}'/'plain',public,plain)
        # Rho receives only the target header and zero factor-base entries.
        write_dataset(ROOT/f'field{bits}'/'rho',public,[])
        timings.append(dict(field_bits=bits,factor_base_columns=K,
                            auxiliary_setup_seconds=auxiliary_seconds,
                            plain_setup_seconds=plain_seconds,
                            plain_x_start=10,plain_x_stop=x-1))
    (ROOT/'setup.json').write_text(json.dumps(timings,indent=2)+'\n')
    print(json.dumps(timings,indent=2))


if __name__=='__main__':main()

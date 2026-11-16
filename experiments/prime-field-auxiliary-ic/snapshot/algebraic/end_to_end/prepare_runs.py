"""Public fixtures and fixed, target-independent bases for complete attacks."""
import argparse
import json
from pathlib import Path
import random
import sys
import time

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from resultant_solver import Curve
from prepare import chain,order_in_hasse_interval
from sympy import isprime


def target(bits):
    if bits==31:
        data=json.loads((ROOT.parent.parent/'public.json').read_text())
        return {k:data[k] for k in ['p','n','a','b','P','Q']},123456789
    p=2**bits-1
    for b in range(1,1000):
        if (32+27*b*b)%p==0:continue
        E=Curve(p,a4=2,a6=b);P=E.point(1);n=order_in_hasse_interval(E,P)
        if n and n!=p and isprime(n):
            secret=321987%n;Q=E.mul(secret,P)
            return dict(p=p,n=n,a=2,b=b,P=P,Q=Q),secret
    raise RuntimeError('No prime-order curve found')


def write_input(path,public,points,maps,terminal):
    with path.open('w') as out:
        out.write(f"{public['p']} {public['n']} {public['a']} {public['b']}\n")
        out.write(' '.join(map(str,public['P']+public['Q']))+'\n')
        out.write(f'{len(points)} {len(maps)} {terminal}\n')
        out.writelines(f'{x} {y}\n' for x,y in points)
        out.writelines(f'{m["r"]} {m["A"]} {m["B"]}\n' for m in maps)


def prepare_run(bits,depth,base_seed=0):
    public,secret=target(bits);curve={k:public[k] for k in ['p','a','b']}
    E=Curve(public['p'],a4=public['a'],a6=public['b'])
    folder=ROOT/f'field{bits}_s{depth}_base{base_seed}';folder.mkdir(exist_ok=True)
    started=time.perf_counter();aux,V=chain(E.p,depth,enumerate_all=True)
    points=[]
    for x in V:
        rhs=(x**3+E.a4*x+E.a6)%E.p;y=pow(rhs,(E.p+1)//4,E.p)
        if y*y%E.p==rhs:points.append((x,min(y,E.p-y)))
    points.sort();aux_seconds=time.perf_counter()-started
    started=time.perf_counter();rng=random.Random(903111+base_seed);random_points=[];seen=set()
    while len(random_points)<len(points):
        x=rng.randrange(E.p)
        if x in seen:continue
        seen.add(x);rhs=(x**3+E.a4*x+E.a6)%E.p;y=pow(rhs,(E.p+1)//4,E.p)
        if y*y%E.p==rhs:random_points.append((x,min(y,E.p-y)))
    random_points.sort();random_seconds=time.perf_counter()-started
    assert 0<len(points)<=256
    manifest=dict(public=public,depth=depth,auxiliary=aux,structured_roots=V,
                  factor_base=points,random_factor_base=random_points,
                  auxiliary_basis_seconds=aux_seconds,random_basis_seconds=random_seconds,
                  base_seed=base_seed)
    (folder/'public.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # This separate file is used only by verification, never by native_ic.
    (folder/'expected.json').write_text(json.dumps(dict(secret=secret))+'\n')
    write_input(folder/'chain.txt',public,points,aux['maps'],aux['terminal_c'])
    write_input(folder/'same_base.txt',public,points,[],0)
    write_input(folder/'random.txt',public,random_points,[],0)
    print(bits,depth,'K',len(points),'folder',folder,flush=True)
    return folder


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bits',type=int,choices=[19,31],default=31)
    p.add_argument('--depths',type=int,nargs='+',default=[5,6,7,8])
    p.add_argument('--base-seed',type=int,default=0)
    args=p.parse_args()
    for depth in args.depths:prepare_run(args.bits,depth,args.base_seed)

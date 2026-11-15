"""Known-root candidate extraction: native isogeny-circuit evaluation, no gcd."""
from array import array
import ctypes as ct
from pathlib import Path
import subprocess

from resultant_solver import ROOT,Curve,signed_base
import time

U=ct.c_uint64


class ChainCandidates:
    def __init__(self,model,roots,*,native_source=None):
        self.handle=None
        p=model.curve['p']
        if model.encoding!='chain' or not model.auxiliary:
            raise ValueError('Native circuit extraction requires an auxiliary chain')
        roots=tuple(int(x)%p for x in roots)
        # Validates completeness and equality to the membership polynomial.
        points=signed_base(model,roots)
        if p not in [2**31-1,2**61-1]:raise ValueError('Native extraction supports the requested Mersenne fields')
        bits=31 if p==2**31-1 else 61
        source=Path(native_source) if native_source else ROOT/'end_to_end/native_ic.cpp'
        library=source.parent/f'chain{bits}.so'
        if not library.exists() or library.stat().st_mtime<source.stat().st_mtime:
            subprocess.run(['g++','-O3','-march=native','-std=c++17','-fPIC','-shared',
                            '-DBUILD_LIBRARY',f'-DFIELD_BITS={bits}','-o',str(library),str(source)],check=True)
        self.library=ct.CDLL(str(library))
        self.library.chain_create.argtypes=[ct.POINTER(U),ct.c_size_t,ct.POINTER(U),ct.c_size_t,U,U,U]
        self.library.chain_create.restype=ct.c_void_p
        self.library.chain_candidates.argtypes=[ct.c_void_p,U,ct.POINTER(U)]
        self.library.chain_candidates.restype=ct.c_size_t
        self.library.chain_values.argtypes=[ct.c_void_p,ct.POINTER(U)]
        self.library.chain_free.argtypes=[ct.c_void_p]
        a,b=model.curve['a'],model.curve['b']
        representatives={x:y for x,y in reversed(points)}
        xs=sorted(representatives)
        self.points={x:(x,representatives[x]) for x in xs}
        self.xs=tuple(xs);self.model=model
        self.root_buffer=array('Q',xs);self.map_buffer=array('Q',(step[k]%p for step in model.auxiliary['maps'] for k in ['r','A','B']))
        self.index_buffer=array('Q',[0])*len(xs);self.value_buffer=array('Q',[0])*len(xs)
        self.roots_view=(U*len(xs)).from_buffer(self.root_buffer)
        self.maps_view=(U*len(self.map_buffer)).from_buffer(self.map_buffer)
        self.indices_view=(U*len(xs)).from_buffer(self.index_buffer)
        self.values_view=(U*len(xs)).from_buffer(self.value_buffer)
        self.handle=self.library.chain_create(self.roots_view,len(xs),self.maps_view,len(model.auxiliary['maps']),
            model.auxiliary['terminal_c']%p,a,b)
        if not self.handle:raise MemoryError('Native chain allocation failed')

    def candidates(self,X):
        if not self.handle:raise RuntimeError('Native extractor is closed')
        count=self.library.chain_candidates(self.handle,int(X)%self.model.curve['p'],self.indices_view)
        return {self.xs[self.index_buffer[i]] for i in range(count)}

    def values(self):
        if not self.handle:raise RuntimeError('Native extractor is closed')
        self.library.chain_values(self.handle,self.values_view)
        return list(self.value_buffer)

    def close(self):
        if self.handle:self.library.chain_free(self.handle);self.handle=None

    def __del__(self):
        if getattr(self,'handle',None):self.close()

    def solve(self,target):
        """All verified signed 2-sums, using the circuit rather than a GCD.

        The factor base is known explicitly, as required by index calculus.
        Every circuit zero is checked by actual addition on the target curve.
        No pair sums are precomputed or stored.
        """
        p,a,b=(self.model.curve[k] for k in ['p','a','b'])
        E=Curve(p,a4=a,a6=b);target=tuple(int(v)%p for v in target)
        if not E.contains(target):raise ValueError('Target is not on curve')
        started=time.perf_counter();candidates=self.candidates(target[0])
        candidate_seconds=time.perf_counter()-started
        relations={}
        for x in candidates:
            point=self.points[x]
            for P in [point,E.neg(point)] if point[1] else [point]:
                Q=E.add(target,E.neg(P))
                if Q is None or Q[0] not in self.points:continue
                assert E.add(P,Q)==target
                relations[tuple(sorted([P,Q]))]=[list(P),list(Q)]
        elapsed=time.perf_counter()-started
        return dict(status='solved',engine='native-isogeny-circuit',encoding='chain',
                    elapsed_seconds=elapsed,algebraic_candidate_seconds=candidate_seconds,
                    elimination_seconds=0.0,gcd_seconds=0.0,
                    extraction_seconds=elapsed-candidate_seconds,
                    root_count=self.model.polynomial.degree(),candidates=len(candidates),
                    relations=list(relations.values()))

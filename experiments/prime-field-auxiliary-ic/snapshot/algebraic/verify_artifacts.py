"""Independently audit saved polynomial solutions, relations, and full runs."""
import json
from pathlib import Path
import sympy as sp
from solver import ROOT,Curve,validate_solution


def main():
    count=relations=0
    for folder in [ROOT/'tests',ROOT/'benchmarks',ROOT/'audit/benchmarks_corrected']:
        for path in folder.rglob('result.json'):
            result=json.loads(path.read_text())
            if result['status']!='solved':continue
            system=json.loads((path.parent/'system.json').read_text())
            p=system['curve']['p']
            equations=[sp.sympify(eq.replace('^','**')) for eq in system['equations']]
            for solution in result['solutions']:
                assigned={sp.Symbol(k):v for k,v in solution.items()}
                assigned[sp.Symbol('targetX')]=system['target'][0]
                assigned[sp.Symbol('curveA')]=system['curve']['a']
                assigned[sp.Symbol('curveB')]=system['curve']['b']
                assert all(int(eq.subs(assigned))%p==0 for eq in equations)
            E=Curve(p,a4=system['curve']['a'],a6=system['curve']['b'])
            for relation in result['relations']:
                R=None
                for P in relation:
                    P=tuple(P);assert E.contains(P);R=E.add(R,P)
                assert R==tuple(system['target'])
                relations+=1
            count+=1
    fixed_bases={}
    for path in (ROOT/'audit/benchmarks_corrected').rglob('case.json'):
        case=json.loads(path.read_text())
        assert case['bases_fixed_before_target'] and not case['planted_coordinates']
        key=(case['curve']['p'],case['depth'])
        pair=(case['structured_roots'],case['ordinary_roots'])
        if key in fixed_bases:assert fixed_bases[key]==pair
        fixed_bases[key]=pair
    completed=[]
    for path in (ROOT/'full_toy').glob('*/result.json'):
        result=json.loads(path.read_text())
        assert result['status']=='solved'
        public=json.loads((path.parent/'public.json').read_text())
        rels=json.loads((path.parent/'relations.json').read_text())
        n,p=public['n'],public['p']
        E=Curve(p,a4=public['a'],a6=public['b'])
        F=[tuple(P) for P in public['factor_base']]
        coeff=[0]*len(F);A=B=0
        for rel,w in zip(rels,result['weights']):
            raw=None
            for P in rel['raw_points']:raw=E.add(raw,tuple(P))
            assert raw==tuple(rel['target'])
            for col,sign in rel['codes']:coeff[col]+=w*sign
            A-=w*rel['a'];B-=w*rel['b']
        assert all(v%n==0 for v in coeff)
        assert A%n==result['dependency_A'] and B%n==result['dependency_B']!=0
        assert E.mul(result['recovered'],tuple(public['P']))==tuple(public['Q'])
        assert result['recovered']==37
        completed.append(path.parent.name)
    print(f'PASS: {count} saved algebraic solves, {relations} point relations,')
    print('and complete Groebner-based index-calculus runs:',', '.join(completed))


if __name__=='__main__':main()

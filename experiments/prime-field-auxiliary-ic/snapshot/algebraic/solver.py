"""Finite-field Semaev relation solving by actual Groebner bases.

No pair-sum table, factor-base enumeration search, or discrete-log oracle is
used by solve(). Explicit roots are only used by the expanded-polynomial
baseline and for independent post-solve verification.
"""
from __future__ import annotations
import itertools
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import sys
import time
import warnings

import sympy as sp

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from prepare import Curve


def backend():
    """Prefer a system Singular; otherwise use the local, unprivileged install."""
    env=os.environ.copy()
    executable=env.get('SINGULAR_BIN') or shutil.which('Singular')
    if executable:
        return executable,env
    prefix=ROOT/'vendor/root/usr'
    executable=prefix/'bin/Singular'
    if not executable.exists():
        raise RuntimeError('Singular is required; see algebraic/README.md')
    libraries=prefix/'lib/x86_64-linux-gnu'
    env['LD_LIBRARY_PATH']=str(libraries)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    env['SINGULARPATH']=str(prefix/'share/singular/LIB')
    env['SINGULAR_PROCS_DIR']=str(libraries/'singular/MOD')
    return str(executable),env


@lru_cache(maxsize=16)
def _root_polynomial_cached(roots,p):
    coefficients=[1]
    for root in roots:
        new=[0]*(len(coefficients)+1)
        for j,c in enumerate(coefficients):
            new[j]=(new[j]-root*c)%p
            new[j+1]=(new[j+1]+c)%p
        coefficients=new
    return tuple(coefficients)


def root_polynomial(roots,p):
    """Prepare membership once per base; never repeat it per target/variable."""
    return list(_root_polynomial_cached(tuple(roots),p))


def polynomial_string(coefficients,x):
    return '+'.join(f'{c}*{x}^{j}' for j,c in enumerate(coefficients) if c) or '0'


def s3(x,y,z,a,b):
    return (f'(({x})-({y}))^2*({z})^2'
            f'-2*((({x})+({y}))*(({x})*({y})+({a}))+2*({b}))*({z})'
            f'+(({x})*({y})-({a}))^2-4*({b})*(({x})+({y}))')


def s4(x,y,z,t,a,b):
    """Exact resultant of two quadratic S3 polynomials, including infinity."""
    def coefficients(u,v):
        return (f'(({u})-({v}))^2',
                f'(-2*((({u})+({v}))*(({u})*({v})+({a}))+2*({b})))',
                f'((({u})*({v})-({a}))^2-4*({b})*(({u})+({v})))')
    A,B,C=coefficients(x,y)
    D,E,F=coefficients(z,t)
    return f'(({A})*({F})-({C})*({D}))^2-(({A})*({E})-({B})*({D}))*(({B})*({F})-({C})*({E}))'


def make_system(curve,target,*,m=2,auxiliary=None,roots=None,encoding='chain',summation='direct'):
    """Build the slide's chain system, or explicit-root membership equations.

    curve is {p,a,b}; target is a finite point. For m=3 an intermediate sum
    coordinate w can optionally replace S4 with two quartics. The direct S4
    form also handles cancellations through an infinite intermediate sum.
    """
    p,a,b=(int(curve[k]) for k in ['p','a','b'])
    if not sp.isprime(p) or p<=3:raise ValueError('An odd prime field of characteristic >3 is required')
    a,b=a%p,b%p
    if (4*a**3+27*b*b)%p==0:raise ValueError('The target curve is singular')
    E=Curve(p,a4=a,a6=b)
    if target is None:raise ValueError('A finite target point is required')
    target=tuple(target)
    if not E.contains(target):raise ValueError('Target is not on the curve')
    if m not in [2,3]:raise ValueError('Supported decomposition lengths are 2 and 3')
    if summation not in ['direct','split']:raise ValueError('Unknown summation encoding')
    if encoding not in ['chain','expanded','plain']:raise ValueError('Unknown encoding')
    if encoding=='chain':
        if not auxiliary or auxiliary['p']!=p:raise ValueError('Auxiliary field mismatch')
        maps=auxiliary['maps']
        if not maps or any(step['B']%p==0 for step in maps):
            raise ValueError('A separable nonsingular 2-isogeny chain is required')
        if auxiliary.get('roots_checked')!=auxiliary['kernel_order']:
            # Complete root enumeration is not mathematically necessary, but
            # the root-count assertion itself must still be consistent.
            if auxiliary['root_count']!=2**len(maps):raise ValueError('Invalid root count')
    else:
        roots=[int(root)%p for root in roots] if roots else roots
        if not roots or len(set(roots))!=len(roots):raise ValueError('Distinct roots required')
        maps=[]
    variables=[]
    equations=[]
    paths=[]
    for i in range(1,m+1):
        path=[f'x{i}']+[f'z{i}j{j}' for j in range(2,len(maps)+1)]
        paths.append(path)
        variables.extend(path[1:])
        if encoding=='chain':
            for j,step in enumerate(maps):
                z=path[j]
                nxt=path[j+1] if j+1<len(path) else str(auxiliary['terminal_c'])
                u=f'({z}-({step["r"]}))'
                equations.append(f'{u}*(({nxt})-{u}-({step["A"]}))-({step["B"]})')
        else:
            equations.append(polynomial_string(root_polynomial(roots,p),f'x{i}'))
    if m==2:
        equations.append(s3('x1','x2','targetX','curveA','curveB'))
    elif summation=='split':
        variables.append('w')
        equations.extend([s3('x1','x2','w','curveA','curveB'),s3('w','x3','targetX','curveA','curveB')])
    else:
        equations.append(s4('x1','x2','x3','targetX','curveA','curveB'))
    variables.extend(f'x{i}' for i in range(m,0,-1))
    return dict(curve=dict(p=p,a=a,b=b),target=target,m=m,encoding=encoding,summation=summation,
                variables=variables,equations=equations,auxiliary=auxiliary,
                roots=roots,paths=paths)


def singular_script(system,algorithm='std'):
    p=system['curve']['p']
    if algorithm not in ['std','slimgb']:raise ValueError('Unknown Groebner algorithm')
    big=p>2147483647
    characteristic=f'(integer,{p})' if big else str(p)
    variables=','.join(system['variables'])
    # Singular's Z/pZ coefficient ring supports the 61-bit prime exactly.
    # Use grevlex for both; the 61-bit FGLM conversion runs over SymPy's
    # actual prime field because Singular disallows FGLM on its Z/pZ type.
    order='dp'
    # A polynomial constant forces finite-field arithmetic for targetX^2.
    # A bare integer literal squared would overflow Singular's machine int.
    lines=[f'ring source={characteristic},({variables}),{order};','short=0;',
           f'poly targetX={system["target"][0]};',
           f'poly curveA={system["curve"]["a"]};',
           f'poly curveB={system["curve"]["b"]};',
           'option(redSB);','ideal inputIdeal='+',\n'.join(system['equations'])+';',
           f'ideal G={"std" if big else algorithm}(inputIdeal);',
           'print("@@GB_DONE@@");','print("@@DIM@@"+string(dim(G)));']
    if not big:
        lines.extend([f'ring result={characteristic},({variables}),lp;',
                      'short=0;',
                      'ideal H=fglm(source,G);'])
    else:
        lines.append('ideal H=G;')
    lines.extend(['int ii;','for(ii=1;ii<=size(H);ii++){',
                  'print("@@POLY_BEGIN@@");','print(string(H[ii]));',
                  'print("@@POLY_END@@");','}',
                  'print("@@DONE@@");','quit;'])
    return '\n'.join(lines)+'\n'


def finite_solutions(basis,variables,p,deadline,max_solutions=10000):
    """Triangular lex-basis back substitution; retain only F_p roots."""
    symbols=sp.symbols(' '.join(variables),seq=True)
    local=dict(zip(variables,symbols))
    polys=[sp.sympify(poly.replace('^','**'),locals=local) for poly in basis]
    solutions=[]

    def descend(index,assigned):
        if time.monotonic()>deadline:raise TimeoutError('Finite-field extraction timed out')
        if len(solutions)>=max_solutions:raise RuntimeError('Finite-solution limit exceeded')
        if index<0:
            if all(int(poly.subs(assigned))%p==0 for poly in polys):
                solutions.append({str(k):int(v) for k,v in assigned.items()})
            return
        variable=symbols[index]
        gcd=None
        for poly in polys:
            expr=poly.subs(assigned)
            if expr.free_symbols-{variable}:continue
            if not expr.free_symbols:
                if int(expr)%p:return
                continue
            candidate=sp.Poly(expr,variable,modulus=p)
            if candidate.is_zero:continue
            gcd=candidate if gcd is None else sp.gcd(gcd,candidate)
            if gcd.degree()==0:return
        if gcd is None:
            raise RuntimeError(f'Non-triangular or positive-dimensional basis at {variable}')
        # SymPy currently warns about its own modular-factor sorting.
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',sp.utilities.exceptions.SymPyDeprecationWarning)
            factors=sp.factor_list(gcd)[1]
        for factor,_ in factors:
            if factor.degree()!=1:continue
            lead,constant=map(int,factor.all_coeffs())
            root=-constant*pow(lead,-1,p)%p
            descend(index-1,assigned|{variable:root})

    descend(len(symbols)-1,{})
    return solutions


def validate_solution(system,solution,all_lifts=False):
    """Check original rational equations, then lift and verify point signs."""
    p,a,b=(system['curve'][k] for k in ['p','a','b'])
    E=Curve(p,a4=a,a6=b)
    if system['encoding']=='chain':
        aux=system['auxiliary']
        for path in system['paths']:
            z=solution[path[0]]
            for j,step in enumerate(aux['maps']):
                u=(z-step['r'])%p
                if u==0:return None
                z=(u+step['A']+step['B']*pow(u,-1,p))%p
                if j+1<len(path) and z!=solution[path[j+1]]:return None
            if z!=aux['terminal_c']:return None
    else:
        allowed=set(system['roots'])
        if any(solution[f'x{i}'] not in allowed for i in range(1,system['m']+1)):
            return None
    options=[]
    for i in range(1,system['m']+1):
        x=solution[f'x{i}']
        rhs=(x**3+a*x+b)%p
        if p%4==3:
            y=pow(rhs,(p+1)//4,p)
            if y*y%p!=rhs:return None
        else:
            y=sp.sqrt_mod(rhs,p)
            if y is None:return None
            y=int(y)
        options.append([(x,y)] if y==0 else [(x,y),(x,-y%p)])
    target=tuple(system['target'])
    valid=[]
    for points in itertools.product(*options):
        total=None
        for P in points:total=E.add(total,P)
        if total==target:
            if not all_lifts:return [list(P) for P in points]
            valid.append([list(P) for P in points])
    return valid if all_lifts else None


def _solve_one(system,artifact_dir,*,timeout=30,memory_mib=2048,algorithm='std'):
    """Run a bounded actual GB computation and return audited decompositions."""
    artifact_dir=Path(artifact_dir)
    artifact_dir.mkdir(parents=True,exist_ok=True)
    (artifact_dir/'system.json').write_text(json.dumps(system,indent=2)+'\n')
    script=singular_script(system,algorithm)
    (artifact_dir/'system.sing').write_text(script)
    executable,env=backend()

    def limits():
        resource.setrlimit(resource.RLIMIT_AS,(memory_mib*1024**2,memory_mib*1024**2))
        resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(timeout)+1,math.ceil(timeout)+2))
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))

    started=time.monotonic()
    proc=subprocess.Popen([executable,'-q','--no-rc','--no-shell',str(artifact_dir/'system.sing')],
                          env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                          text=True,start_new_session=True,preexec_fn=limits)
    status='error'
    try:
        output,_=proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid,signal.SIGKILL)
        output,_=proc.communicate()
        status='timeout'
    backend_seconds=time.monotonic()-started
    (artifact_dir/'singular.log').write_text(output)
    result=dict(status=status,encoding=system['encoding'],p=system['curve']['p'],
                m=system['m'],variables=len(system['variables']),
                equations=len(system['equations']),backend_seconds=backend_seconds,
                timeout_seconds=timeout,memory_limit_mib=memory_mib,
                algorithm='std-dp-Zmodp-sympy-fglm' if system['curve']['p']>2147483647 else algorithm+'-dp-fglm',
                solutions=[],relations=[])
    if status!='timeout':
        if re.search(r'no more memory|out of memory|cannot allocate memory',output,re.I):
            result.update(status='memory_limit',returncode=proc.returncode)
        elif proc.returncode!=0 or '@@DONE@@' not in output or re.search(r'^\s*\?',output,re.M):
            result.update(status='backend_error',returncode=proc.returncode)
        else:
            dimension=re.search(r'@@DIM@@(-?\d+)',output)
            result['dimension']=int(dimension.group(1)) if dimension else None
            basis=[''.join(poly.split()) for poly in re.findall(r'@@POLY_BEGIN@@\s*(.*?)\s*@@POLY_END@@',output,re.S)]
            (artifact_dir/'basis.txt').write_text('\n'.join(basis)+'\n')
            try:
                extraction_input=dict(basis=basis,variables=system['variables'],
                                      p=system['curve']['p'],
                                      order='grevlex' if system['curve']['p']>2147483647 else 'lex')
                (artifact_dir/'extraction_input.json').write_text(json.dumps(extraction_input)+'\n')
                remaining=started+timeout-time.monotonic()
                if remaining<=0:raise TimeoutError('No time left for extraction')
                worker=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--extract',
                                         str(artifact_dir/'extraction_input.json'),
                                         str(artifact_dir/'extraction_output.json')],
                                        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
                                        preexec_fn=limits,start_new_session=True)
                try:
                    extraction_log,_=worker.communicate(timeout=remaining)
                except subprocess.TimeoutExpired:
                    os.killpg(worker.pid,signal.SIGKILL)
                    extraction_log,_=worker.communicate()
                    (artifact_dir/'extraction.log').write_text(extraction_log)
                    raise TimeoutError('Order conversion or extraction timed out')
                (artifact_dir/'extraction.log').write_text(extraction_log)
                if worker.returncode!=0:
                    raise RuntimeError(f'Extraction worker exited {worker.returncode}; see extraction.log')
                extracted=json.loads((artifact_dir/'extraction_output.json').read_text())
                result['lex_basis']=extracted['lex_basis']
                sols=extracted['solutions']
                relations={}
                for solution in sols:
                    for points in validate_solution(system,solution,all_lifts=True) or []:
                        key=tuple(sorted(tuple(P) for P in points))
                        relations[key]=points
                result.update(status='solved',solutions=sols,relations=list(relations.values()))
            except TimeoutError as exc:
                result.update(status='timeout',extraction_error=str(exc))
            except Exception as exc:
                result.update(status='extraction_error',extraction_error=str(exc))
    result['elapsed_seconds']=time.monotonic()-started
    (artifact_dir/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def _contains_target_x(system):
    x=system['target'][0]%system['curve']['p']
    if system['encoding']!='chain':return x in system['roots']
    p=system['curve']['p'];aux=system['auxiliary']
    for step in aux['maps']:
        u=(x-step['r'])%p
        if not u:return False
        x=(u+step['A']+step['B']*pow(u,-1,p))%p
    return x==aux['terminal_c']


def solve(system,artifact_dir,*,timeout=30,memory_mib=2048,algorithm='std'):
    """Solve relations, completing both projective charts for split S4.

    The finite-w chart misses x1=x2, x3=x(target), which represents
    P1+P2=O. Its infinity chart is an additional polynomial system, not a
    point-enumeration fallback. If target.x is outside the base this chart is
    provably empty and needs no additional computation.
    """
    kwargs=dict(timeout=timeout,memory_mib=memory_mib,algorithm=algorithm)
    split=system['m']==3 and system.get('summation')=='split'
    required=split and _contains_target_x(system)
    if not required:
        result=_solve_one(system,artifact_dir,**kwargs)
        if split:
            result.update(split_complete=result['status']=='solved',infinity_chart_required=False)
            (Path(artifact_dir)/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    started=time.monotonic()
    out=Path(artifact_dir);out.mkdir(parents=True,exist_ok=True)
    (out/'system.json').write_text(json.dumps(system,indent=2)+'\n')
    finite=_solve_one(system,out/'finite',**kwargs)
    remaining=timeout-(time.monotonic()-started)
    if finite['status']!='solved' or remaining<=0:
        result=finite|dict(split_complete=False,infinity_chart_required=True,
                           elapsed_seconds=time.monotonic()-started)
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    infinity=system|dict(variables=[v for v in system['variables'] if v!='w'],
                         equations=system['equations'][:-2]+['x1-x2','x3-targetX'],
                         summation='infinity')
    other=_solve_one(infinity,out/'infinity',timeout=remaining,
                     memory_mib=memory_mib,algorithm=algorithm)
    relations={tuple(sorted(tuple(P) for P in rel)):rel
               for answer in [finite,other] for rel in answer['relations']}
    result={k:v for k,v in finite.items() if k!='lex_basis'}
    result.update(status='solved' if other['status']=='solved' else other['status'],
                  split_complete=other['status']=='solved',infinity_chart_required=True,
                  solutions=finite['solutions'],infinity_solutions=other['solutions'],
                  finite_lex_basis=finite.get('lex_basis'),infinity_lex_basis=other.get('lex_basis'),
                  relations=list(relations.values()),
                  backend_seconds=finite['backend_seconds']+other['backend_seconds'],
                  elapsed_seconds=time.monotonic()-started,
                  dimension=max(finite.get('dimension',-1),other.get('dimension',-1)))
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def extraction_worker(input_path,output_path):
    data=json.loads(Path(input_path).read_text())
    basis=data['basis']
    if data['order']=='grevlex' and basis!=['1']:
        symbols=sp.symbols(' '.join(data['variables']),seq=True)
        local=dict(zip(data['variables'],symbols))
        exprs=[sp.sympify(f.replace('^','**'),locals=local) for f in basis]
        gb=sp.groebner(exprs,*symbols,modulus=data['p'],order='grevlex')
        lex=gb.fglm('lex')
        basis=[str(poly.as_expr()) for poly in lex.polys]
    solutions=finite_solutions(basis,data['variables'],data['p'],float('inf'))
    Path(output_path).write_text(json.dumps(dict(lex_basis=basis,solutions=solutions))+'\n')


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--extract':
        extraction_worker(sys.argv[2],sys.argv[3])
    else:
        raise SystemExit('Use the relation_solver CLI; --extract is an internal worker mode.')

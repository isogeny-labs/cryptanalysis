"""One algebraic relation search: Groebner or structure-aware resultants."""
import argparse
import json
from pathlib import Path
from solver import make_system,solve

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--public',type=Path,required=True)
    p.add_argument('--x',type=int,required=True)
    p.add_argument('--y',type=int,required=True)
    p.add_argument('--auxiliary',type=Path)
    p.add_argument('--roots',type=Path)
    p.add_argument('--encoding',choices=['chain','expanded','plain'],default='chain')
    p.add_argument('--m',type=int,choices=[2,3],default=3)
    p.add_argument('--engine',choices=['groebner','resultant','native'],default='groebner')
    p.add_argument('--gcd-blocks',type=int,default=0,metavar='SIZE',
                   help='For resultants: cached known-root remainder tree (e.g. 256)')
    p.add_argument('--summation',choices=['direct','split'],default='direct')
    p.add_argument('--timeout',type=float,default=30,help='Groebner subprocess wall limit')
    p.add_argument('--memory-mib',type=int,default=2048,help='Groebner subprocess memory limit')
    p.add_argument('--algorithm',choices=['std','slimgb'],default='std')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    public=json.loads(args.public.read_text())
    auxiliary=json.loads(args.auxiliary.read_text()) if args.auxiliary else None
    roots=json.loads(args.roots.read_text()) if args.roots else None
    curve={k:public[k] for k in ['p','a','b']}
    if args.engine in ['resultant','native']:
        from resultant_solver import prepare,solve as solve_resultant,solve_three,signed_base
        if args.m==3 and roots is None:p.error('--roots is required for the hybrid three-point resultant engine')
        model=prepare(curve,auxiliary=auxiliary,roots=roots,encoding=args.encoding)
        target=(args.x,args.y)
        if args.engine=='native':
            if args.m!=2 or args.encoding!='chain' or roots is None:
                p.error('--engine native requires --m 2 --encoding chain --roots and --auxiliary')
            from native_candidates import ChainCandidates
            extractor=ChainCandidates(model,roots)
            result=extractor.solve(target);extractor.close()
        else:
            plan=None
            if args.gcd_blocks:
                if roots is None:p.error('--gcd-blocks requires --roots')
                from known_root_gcd import KnownRootGCD
                plan=KnownRootGCD.for_model(model,roots,args.gcd_blocks)
            result=solve_resultant(model,target,root_plan=plan) if args.m==2 else solve_three(model,target,signed_base(model,roots),root_plan=plan)
        args.output.mkdir(parents=True,exist_ok=True)
        (args.output/'input.json').write_text(json.dumps(dict(curve=curve,target=target,m=args.m,
            auxiliary=auxiliary,roots=roots,encoding=args.encoding),indent=2)+'\n')
        (args.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    else:
        system=make_system(curve,(args.x,args.y),m=args.m,auxiliary=auxiliary,roots=roots,
            encoding=args.encoding,summation=args.summation)
        result=solve(system,args.output.resolve(),timeout=args.timeout,
                     memory_mib=args.memory_mib,algorithm=args.algorithm)
    print(json.dumps({k:v for k,v in result.items() if k not in ['lex_basis','solutions']},indent=2))

#!/usr/bin/env python3
"""Exercise WDSat's real -g hook with a held-out learned static coefficient order."""
import hashlib,itertools,json,os,random,resource,subprocess,sys,time,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
os.environ["WDSAT_BUILDS"]=str(HERE/"build/wdsat")
sys.path.insert(0,str(ROOT/"experiments/pdp-scaling"))
import symmodel
from collect import Collector,target_instance
from gf2n import GF2n,Curve
def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def save(n,x):(HERE/n).write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
def order(ell,policy,perm=None):
    if policy=="interleave":return [i*ell+j+1 for j in range(ell) for i in range(3)]
    if policy=="fixed-random":
        ids=list(range(1,3*ell+1));random.Random(f"20261018|{ell}").shuffle(ids);return ids
    if policy=="learned":
        jj=sorted(range(ell),key=lambda j:(perm.index(min(2,3*j//ell)),j))
        return [i*ell+j+1 for i in range(3) for j in jj]
    return list(range(1,3*ell+1))
def main():
    if (HERE/"sat-results.json").exists():raise SystemExit("Append-only run already exists")
    p=json.loads((HERE/"PROTOCOL.json").read_text())["sat"]
    source=Path("/workspace/toolchains/WDSat")
    rev=subprocess.check_output(["git","rev-parse","HEAD"],cwd=source,text=True).strip()
    assert rev=="61c6ff3f49445af2729274819edb27b85a89efc1"
    patched=HERE/"build/wdsat-source"
    shutil.copytree(source/"src",patched/"src",dirs_exist_ok=True)
    build_patch=json.loads((HERE/"SAT-BUILD-PATCH.json").read_text())
    for name,old,new in build_patch["owned_patch"]:
        f=patched/"src"/name;text=f.read_text();assert text.count(old)==1
        f.write_text(text.replace(old,new))
    files=[Path(__file__),HERE/"PROTOCOL.json",HERE/"SAT-AMENDMENT-01.json",HERE/"SAT-BUILD-PATCH.json"]+[ROOT/"experiments/pdp-scaling"/x for x in ["solve.py","collect.py","symmodel.py","gf2n.py","descend.py","sumpoly.py"]]+list((source/"src").glob("*.[ch]"))+list((patched/"src").glob("*.[ch]"))
    launch={"argv":sys.argv,"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"source_sha256":{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},"upstream_revision":rev,"gpu":{"devices":[]},"F4_F2_ECHELON":os.getenv("F4_F2_ECHELON"),"performance_tier":"unqualified exploratory CPU container","cpu_count":os.cpu_count()}
    save("sat-launch.json",launch)
    (HERE/"sat-inputs").mkdir(exist_ok=True)
    rows=[];setup=[];targets=[]
    collectors={}
    def collector(cell):
        key=(cell["n"],cell["ell"],cell["b"])
        if key not in collectors:
            t=time.process_time();wall=time.monotonic()
            c=Collector(cell["n"],3,cell["ell"],cell["b"],str(patched),False,"default")
            c.build_oracle();collectors[key]=c
            setup.append({"cell":cell,"build_model_and_compiler_wall_seconds":time.monotonic()-wall,"parent_setup_cpu_seconds":time.process_time()-t,"binary":str(Path(c.exe).relative_to(HERE)),"binary_sha256":hashlib.sha256(Path(c.exe).read_bytes()).hexdigest(),"actual_factor_base_points":len(c.fb),"build_params":c.params})
        return collectors[key]
    def attempt(cell,seed,policy,perm,phase):
        c=collector(cell);rng=random.Random(f"sat-target-20261018|{cell}|{seed}")
        R=c.E.random_point(rng);truth=c.decomposable(R)
        inst=target_instance(c.F,c.b,3,c.l,R.x)
        lines,info=symmodel.build_model(inst)
        ids=order(c.l,policy,perm)
        assert sorted(ids)==list(range(1,c.core+1))
        inp={"cell":cell,"seed":seed,"target":[R.x,R.y,R.inf],"field_modulus":c.F.mod,"model":"symmetrized S4 degree<=3 ANF","factor_base":[[P.x,P.y,P.inf] for P in c.fb],"input_law":"independent uniform lifted curve abscissa then random sign; not subgroup-uniform","exact_decomposable":truth}
        iid=sha(inp);ap=HERE/"sat-inputs"/(iid+".anf")
        if not ap.exists():ap.write_text("\n".join(lines)+"\n");targets.append({"input_sha256":iid,**inp,"anf_sha256":hashlib.sha256(ap.read_bytes()).hexdigest()})
        cmd=[c.exe,"-i",str(ap),"-n",str(c.n),"-l",str(c.l),"-m","3"]
        if policy=="paper":cmd.append("-b")
        else:cmd += ["-g",",".join(map(str,ids))]
        before=resource.getrusage(resource.RUSAGE_CHILDREN);wall=time.monotonic()
        try:
            run=subprocess.run(cmd,capture_output=True,text=True,timeout=p["timeout_seconds"],check=False)
            status="error";verified=False;conflicts=None;bits=None
            out=[x.strip() for x in run.stdout.splitlines() if x.strip() and not x.startswith("!!!")]
            if run.returncode==0 and len(out)>=2:
                conflicts=int(out[-1]);bits=out[-2]
                status="unsat" if bits=="UNSAT" else "sat"
                verified=(not truth) if status=="unsat" else c.verify(bits,R)
            stdout,stderr,rc=run.stdout,run.stderr,run.returncode
        except subprocess.TimeoutExpired as exc:
            status="timeout";verified=False;conflicts=None;bits=None;rc=None
            stdout=str(exc.stdout or "");stderr=str(exc.stderr or "")
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu=(after.ru_utime+after.ru_stime)-(before.ru_utime+before.ru_stime)
        agreement=(status=="sat" and truth and verified) or (status=="unsat" and not truth and verified)
        row={"phase":phase,"cell":cell,"seed":seed,"policy":policy,"permutation":perm,"branch_order":ids,"input_sha256":iid,"command":cmd,"status":status,"conflicts":conflicts,"cpu_seconds":cpu,"wall_seconds":time.monotonic()-wall,"returncode":rc,"verified":verified,"exact_decomposable":truth,"oracle_agreement":agreement,"stdout":stdout,"stderr":stderr,"assignment_bits":bits if status=="sat" else None}
        rows.append(row)
        with (HERE/"sat-raw.jsonl").open("a") as f:f.write(json.dumps(row,sort_keys=True)+"\n")
        if status in ("sat","unsat") and not agreement:raise RuntimeError("SAT semantic gate failed; preserve and stop")
        return row
    permutations=list(itertools.permutations(range(3)));scores=[];learnstart=time.process_time()
    for perm in permutations:
        rs=[attempt(cell,seed,"learned",list(perm),"train") for cell in p["training_cells"] for seed in p["training_seeds"]]
        scores.append({"permutation":list(perm),"conflicts":sum(r["conflicts"] or 0 for r in rs),"failures":sum(r["status"] not in ("sat","unsat") for r in rs),"training_child_cpu_seconds":sum(r["cpu_seconds"] for r in rs)})
    selected=min(scores,key=lambda x:(x["failures"],x["conflicts"],x["permutation"]))
    learnsec=time.process_time()-learnstart
    save("sat-selected-before-heldout.json",{"selected":selected,"all_candidate_scores":scores,"training_results_sha256":sha(rows),"parent_learning_cpu_seconds":learnsec,"training_child_cpu_seconds":sum(r["cpu_seconds"] for r in rows)})
    for cell in p["heldout_cells"]:
        for seed in p["heldout_seeds"]:
            # Alternating direction prevents one fixed policy always going first.
            policies=["paper","block","interleave","fixed-random","learned"]
            if seed%2:policies.reverse()
            for policy in policies:attempt(cell,seed,policy,selected["permutation"] if policy=="learned" else None,"heldout")
    save("sat-targets.json",targets)
    save("sat-setup.json",setup)
    summaries=[]
    for policy in ["paper","block","interleave","fixed-random","learned"]:
        rs=[r for r in rows if r["phase"]=="heldout" and r["policy"]==policy]
        summaries.append({"policy":policy,"attempts":len(rs),"verified_answers":sum(r["oracle_agreement"] for r in rs),"timeouts":sum(r["status"]=="timeout" for r in rs),"errors":sum(r["status"]=="error" for r in rs),"conflicts_total":sum(r["conflicts"] or 0 for r in rs),"solve_child_cpu_seconds_total":sum(r["cpu_seconds"] for r in rs),"solve_wall_seconds_total":sum(r["wall_seconds"] for r in rs),"max_conflicts":max((r["conflicts"] or 0) for r in rs)})
    save("sat-results.json",{"selected":selected,"training_calls":48,"heldout_calls":40,"summaries":summaries,"all_results_oracle_checked":all(r["oracle_agreement"] for r in rows if r["status"] in ("sat","unsat")),"training_child_cpu_seconds":sum(r["cpu_seconds"] for r in rows if r["phase"]=="train"),"parent_learning_cpu_seconds":learnsec,"scope":"static learned core order with real WDSat hook; no neural policy/cubing/XOR-CDCL/full IC run","unsat_scope":"exact group-law membership agreement on small factor bases, not a solver proof trace"})
    print(json.dumps(summaries))
if __name__=="__main__":main()

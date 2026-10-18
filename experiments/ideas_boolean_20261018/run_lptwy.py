#!/usr/bin/env python3
"""Execute the separately frozen LPTWY decision pilot, retain all failures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from run import write_new, truth_roots


def execute(out, inputs):
    protocol_path=HERE/"lptwy_protocol.json"
    protocol=json.loads(protocol_path.read_text())
    out.mkdir(parents=True,exist_ok=False)
    source=HERE/"lptwy_decision.cpp"
    binary=out/"lptwy-decision"
    build_command=["g++","-O3","-std=c++17",str(source),"-o",str(binary)]
    built=subprocess.run(build_command,capture_output=True,text=True,timeout=60)
    write_new(out/"build.json",{"argv":build_command,"returncode":built.returncode,
                               "stdout":built.stdout,"stderr":built.stderr})
    if built.returncode:raise RuntimeError("native build failed")
    provenance={"argv":sys.argv,"platform":platform.platform(),"gpu":{"devices":[],"F4_F2_ECHELON":os.environ.get("F4_F2_ECHELON")},
                "scope":"CPU-only correctness pilot; no performance claim",
                "sha256":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in [source,Path(__file__),protocol_path,inputs,binary]}}
    write_new(out/"provenance.json",provenance)
    resource.setrlimit(resource.RLIMIT_AS,(protocol["memory_limit_bytes"],)*2)
    trials=[]
    cases=json.loads(inputs.read_text())
    # Exact zero- and nonzero-root controls accompany descended systems.
    controls=[{"case_id":"control-sat","nvars":6,"equations":[[1,0],[2],[4]],"seed":20261018},
              {"case_id":"control-unsat","nvars":6,"equations":[[0]],"seed":20261019}]
    for case in controls+[c for c in cases if c["kind"]=="direct-Semaev"]:
        nv=case["nvars"];n0=max(1,nv//5);seed=case["seed"]+830;repeats=100*nv
        equations=case["equations"]
        data=f"{nv} {n0} {len(equations)} {repeats} {seed}\n"+"".join(
            f"{len(g)} {' '.join(map(str,g))}\n" for g in equations)
        roots,_=truth_roots(equations,nv)
        record={"case_id":case["case_id"],"nvars":nv,"n0":n0,"seed":seed,
                "input_sha256":hashlib.sha256(data.encode()).hexdigest(),
                "reference_root_count":roots.bit_count(),"reference_satisfiable":bool(roots)}
        try:
            process=subprocess.run([str(binary)],input=data,capture_output=True,text=True,
                                   timeout=protocol["timeout_seconds_per_case"])
            record.update({"returncode":process.returncode,"stdout":process.stdout,"stderr":process.stderr})
            if process.returncode==0:
                result=json.loads(process.stdout)
                record.update({"result":result,"status":"verified" if result["satisfiable"]==bool(roots) else "verification-failed"})
            else:record["status"]="error"
        except subprocess.TimeoutExpired as error:
            record.update({"status":"timeout","stderr":str(error.stderr),"stdout":str(error.stdout)})
        write_new(out/(case["case_id"]+".json"),record)
        print(case["case_id"],record["status"],flush=True)
        trials.append(record)
    write_new(out/"results.json",trials)
    print(json.dumps({"trials":len(trials),"verified":sum(t["status"]=="verified" for t in trials)}),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--inputs",type=Path,required=True)
    args=parser.parse_args()
    execute(args.out,args.inputs)

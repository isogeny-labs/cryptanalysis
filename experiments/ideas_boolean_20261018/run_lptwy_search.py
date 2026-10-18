#!/usr/bin/env python3
"""Charge all calls in the LPTWY randomized-decision-to-search reduction."""
from collections import Counter
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from run import write_new, truth_roots, poly_eval, group_roots


def restrict_first(equations, value):
    out=[];visits=0
    for polynomial in equations:
        terms=set()
        for monomial in polynomial:
            visits+=1
            if not (monomial & 1) or value:
                terms.symmetric_difference_update([monomial >> 1])
        out.append(sorted(terms))
    return out,visits


def main(out,inputs,binary):
    protocol=HERE/"lptwy_search_protocol.json"
    out.mkdir(parents=True,exist_ok=False)
    write_new(out/"provenance.json",{"argv":sys.argv,"gpu":{"devices":[],"F4_F2_ECHELON":os.environ.get("F4_F2_ECHELON")},
        "scope":"CPU-only correctness control; no performance claim",
        "sha256":{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [Path(__file__),protocol,inputs,binary]}})
    records=[]
    for case in json.loads(inputs.read_text()):
        if case["kind"]!="direct-Semaev":continue
        calls=[];counts=Counter();restrictions=0
        def decision(equations,nv,stage):
            if nv<=1:
                assignment=next((a for a in range(1 << nv) if all(poly_eval(g,a)==0 for g in equations)),None)
                calls.append({"free_variables":nv,"base_case":True,"satisfiable":assignment is not None})
                counts["base_term_evaluation_upper_bound"]+=(1 << nv)*sum(map(len,equations))
                return assignment is not None
            n0=max(1,nv//5);seed=case["seed"]+5830+100*stage
            text=f"{nv} {n0} {len(equations)} {100*nv} {seed}\n"+"".join(
                f"{len(g)} {' '.join(map(str,g))}\n" for g in equations)
            process=subprocess.run([str(binary)],input=text,capture_output=True,text=True,timeout=90)
            if process.returncode:raise RuntimeError(process.stderr)
            result=json.loads(process.stdout)
            calls.append({"free_variables":nv,"stage":stage,"input_sha256":hashlib.sha256(text.encode()).hexdigest(),"result":result,"stderr":process.stderr})
            counts.update(result["counts"])
            return result["satisfiable"]
        equations=case["equations"]
        try:
            exists=decision(equations,case["nvars"],0)
            assignment=None
            if exists:
                assignment=0
                for variable in range(case["nvars"]):
                    zero,cost=restrict_first(equations,0);restrictions+=cost
                    if decision(zero,case["nvars"]-variable-1,variable+1):
                        equations=zero
                    else:
                        equations,cost=restrict_first(equations,1);restrictions+=cost
                        assignment|=1 << variable
            original_roots,_=truth_roots(case["equations"],case["nvars"])
            anf_verified=assignment is not None and all(poly_eval(g,assignment)==0 for g in case["equations"])
            group_certificate=group_roots(case,1 << assignment) if anf_verified else None
            verified=(not exists and not original_roots) or (
                exists and anf_verified and group_certificate["group_verified_factor_x_tuples"]==1)
            result={"case_id":case["case_id"],"nvars":case["nvars"],"exists":exists,"assignment":assignment,
                    "status":"verified" if verified else "verification-failed",
                    "all_decision_calls":calls,"charged_counts":dict(counts),"restriction_term_visits":restrictions,
                    "final_anf_term_evaluations":sum(map(len,case["equations"])) if assignment is not None else 0,
                    "original_anf_verified":anf_verified,"independent_group_certificate":group_certificate,
                    "independent_reference_root_count":original_roots.bit_count(),
                    "group_verification_cost":"included as checked group certificate; field/group operation instrumentation remains uncalibrated"}
        except BaseException as error:
            result={"case_id":case["case_id"],"status":"timeout" if isinstance(error,subprocess.TimeoutExpired) else "error",
                    "error":repr(error),"partial_decision_calls":calls,"charged_counts":dict(counts)}
        write_new(out/(case["case_id"]+".json"),result)
        records.append(result)
        print(case["case_id"],result["status"],flush=True)
    write_new(out/"results.json",records)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--inputs",type=Path,required=True)
    parser.add_argument("--binary",type=Path,required=True)
    args=parser.parse_args()
    main(args.out,args.inputs,args.binary)

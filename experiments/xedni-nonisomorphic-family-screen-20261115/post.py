"""Post-screen exact family admission and generator checks."""
import gzip
import hashlib
import json
import os
import signal
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parent.parent
SCREEN=HERE/"result.json"
PARENT=HERE.parent/"xedni-fixed-curve-admission-20261115"/"result.json"

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/"post-protocol.json").read_text())
    assert sha(SCREEN)==protocol["parent_screen_result_sha256"]
    assert sha(PARENT)==protocol["parent_fixed_admission_result_sha256"]
    screen=json.loads(SCREEN.read_text())
    parent=json.loads(PARENT.read_text())
    extra={}
    for row in screen["rows"]:
        cand=row.get("candidate") or {}
        if row["u"]>1 and cand.get("rank_status")=="proved" and cand.get("rank")==1 and cand.get("torsion_order")==1:
            extra.setdefault(row["field_prime"],[]).append(cand)
    assert {(p,c["u"]) for p,items in extra.items() for c in items}=={(571,3),(677,3)}
    post_cells=[]
    for p,items in extra.items():
        for c in items:
            x,y=c["centered_point"]
            cmd=[str(REPO/"sage"),"-python",str(HERE/"post_worker.py"),str(p),str(c["u"]),str(x),str(y),str(c["curve_B"])]
            proc=subprocess.Popen(cmd,cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            try:
                out,err=proc.communicate(timeout=protocol["generator_completeness_cap_seconds"])
                status="completed" if proc.returncode==0 else "worker_failure"
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL)
                out,err=proc.communicate()
                status="timeout"
            name=f"p{p}-u{c['u']}-post"
            o=HERE/"cells"/(name+".stdout"); e=HERE/"cells"/(name+".stderr")
            o.write_bytes(out);e.write_bytes(err)
            cell={"field_prime":p,"u":c["u"],"status":status,"exit_code":proc.returncode,
                  "stdout_path":str(o.relative_to(HERE)),"stderr_path":str(e.relative_to(HERE)),
                  "stdout_sha256":sha(o),"stderr_sha256":sha(e)}
            if status=="completed":
                try:cell["result"]=json.loads(out.decode().strip().splitlines()[-1])
                except Exception as exc:cell["status"]="invalid_output";cell["parse_error"]=str(exc)
            post_cells.append(cell)
    fields=[]
    for old in parent["fields"]:
        p,q=old["field_prime"],old["subgroup_order"]
        base={((17-t)%q) for t in old["admitted_offsets"]}
        images=[base]+[{(k*c["u"])%q for k in range(-4,5)} for c in extra.get(p,[])]
        raw=HERE/"post-rows"/f"p{p}.jsonl.gz";raw.parent.mkdir(parents=True,exist_ok=True)
        count=0; baseline=0;extra_only=0
        with raw.open("wb") as fh:
            with gzip.GzipFile(fileobj=fh,mode="wb",filename="",mtime=0) as gz:
                for t1 in range(q):
                    s1=(17-t1)%q
                    for t2 in range(q):
                        s2=(17-t2)%q
                        mask=sum(1<<j for j,S in enumerate(images) if s1 in S and s2 in S)
                        count+=mask!=0;baseline+=bool(mask&1);extra_only+=bool(mask and not(mask&1))
                        gz.write((json.dumps({"t":[t1,t2],"mask":mask},sort_keys=True,separators=(",",":"))+"\n").encode())
        assert baseline==old["admitted_full_pair_support"]
        fields.append({"field_prime":p,"subgroup_order":q,
                       "qualified_models":1+len(extra.get(p,[])),
                       "image_sizes":[len(S) for S in images],
                       "pair_tests":q*q*len(images),"baseline_pairs":baseline,
                       "union_pairs":count,"additional_pairs":extra_only,
                       "raw_path":str(raw.relative_to(HERE)),"raw_sha256":sha(raw)})
    print(json.dumps({"schema":"xedni-nonisomorphic-family-post-result-v1",
                      "post_protocol_sha256":sha(HERE/"post-protocol.json"),
                      "source_sha256":sha(Path(__file__)),"worker_sha256":sha(HERE/"post_worker.py"),
                      "parent_screen_sha256":sha(SCREEN),"parent_admission_sha256":sha(PARENT),
                      "post_cells":post_cells,"fields":fields,
                      "totals":{"queries":sum(f["subgroup_order"]**2 for f in fields),
                                "pair_tests":sum(f["pair_tests"] for f in fields),
                                "baseline_pairs":sum(f["baseline_pairs"] for f in fields),
                                "union_pairs":sum(f["union_pairs"] for f in fields),
                                "additional_pairs":sum(f["additional_pairs"] for f in fields)}},
                      sort_keys=True,indent=2))

if __name__=="__main__":main()

"""Frozen one-worker run of the degree-two residual-output gate."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
GOAL=HERE.parent
PAIRS=GOAL/"n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/"protocol.json").read_text())
    assert protocol["status"]=="FROZEN_BEFORE_N41_DEGREE2_GATE"
    assert protocol["sha256"]=={"source":sha(HERE/"degree2.cpp"),
                               "binary":sha(HERE/"degree2"),"pairs":sha(PAIRS)}
    command=[str(HERE/"degree2"),str(PAIRS),str(HERE/"witnesses.tsv"),
             str(HERE/"native_result.json"),str(protocol["max_attempts"])]
    start=time.monotonic_ns()
    with (HERE/"stdout.log").open("x") as out,(HERE/"stderr.log").open("x") as err:
        child=subprocess.Popen(command,stdout=out,stderr=err)
        try: code=child.wait(timeout=protocol["parent_cap_seconds"])
        except subprocess.TimeoutExpired:
            child.kill(); child.wait(); code=child.returncode
    wall=time.monotonic_ns()-start
    receipt={"status":"COMPLETE" if code==0 else "PRODUCER_FAILURE_OR_CAP",
             "exit_code":code,"parent_wall_ns":wall,
             "protocol_sha256":sha(HERE/"protocol.json"),
             "stdout_sha256":sha(HERE/"stdout.log"),
             "stderr_sha256":sha(HERE/"stderr.log"),
             "command":command}
    with (HERE/"query_receipt.json").open("x") as file:
        json.dump(receipt,file,indent=2,sort_keys=True);file.write("\n")
    print(receipt["status"],wall/1e9)

if __name__=="__main__": main()

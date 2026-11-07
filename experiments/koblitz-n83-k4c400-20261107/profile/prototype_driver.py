import subprocess, json, os, sys, time
K="/tmp/claude-0/-home-user/db62bab2-798a-5439-886c-764eafc92fd6/scratchpad/kprime"
H="/home/user/cryptanalysis/experiments/koblitz-n83-rankfinder-20261021"
BIN="/home/user/cryptanalysis/experiments/koblitz-n83-fieldops-20261104/target-b/release/ic_online_fieldops_r770"
ARMS={"M38":(H+"/snapshots/closure/base_n83_closure_M38.jsonl",H+"/inputs/factor_logs_n83_closure_M38.json"),
 "a_K8_624":(K+"/base_a_K8_c128.jsonl",K+"/table_a_K8_c128.json"),
 "b_K4_612":(K+"/base_b_K4_c256.jsonl",K+"/table_b_K4_c256.json"),
 "c_K8_448":(K+"/base_c_K8_c96.jsonl",K+"/table_c_K8_c96.json"),
 "d_K4_400":(K+"/base_d_K4_c165.jsonl",K+"/table_d_K4_c165.json")}
names=list(ARMS)
def load():
    return open("/proc/loadavg").read().split()[0]
def run(kind,arm,seed,tag):
    base,table=ARMS[arm]
    env=dict(os.environ,BASE=base,TABLE=table)
    out=f"{K}/runs/{tag}"
    l0=load()
    subprocess.run(["taskset","-c","2","sh",f"{K}/run_{kind}.sh",BIN,str(seed),out],env=env,check=True,stdout=subprocess.DEVNULL)
    s=json.loads(open(out+".stdout.jsonl").read().strip().splitlines()[-1])
    t=s["timing_ms"]; d=s["index_digest"]
    ok_table=None
    if kind=="rank":
        lg=json.load(open(out+".logs.json"))["logs"]; ok_table = lg==json.load(open(table))["logs"]
    row=dict(kind=kind,arm=arm,seed=seed,round=tag,load_before=l0,load_after=load(),
      index_build=t["index_build"],selftest=s["scan_order_selftest"]["ms"],selftest_states=s["scan_order_selftest"]["states"],
      rank_stage=t["rank_stage"],online=t["targets_total"],setup_total=t["setup_total"],process_total=t["process_total"],
      entries=d["table_entries"],slots=s["root_table_slots"],stored=s["stored_states"],orbits=s["index_orbits"],cols=s["orbit_columns"],
      solved=s["targets_solved"],failed=s["targets_failed"],rank_failures=s.get("rank_failures"),rows_wo_gain=s.get("rank_rows_without_gain"),
      rank_attempts=s.get("rank_attempts"),rank_probes=s.get("rank_probes_total"),log_src=s["factor_log_table"]["source"],
      verified_cols=s["factor_log_table"].get("verified_columns"),table_equals_truncated_M38=ok_table,rss=s["peak_rss_bytes"])
    with open(K+"/rows.jsonl","a") as f: f.write(json.dumps(row)+"\n")
    print(row["round"],row["arm"],row["kind"],"build",round(row["index_build"]),"st",round(row["selftest"]),"rank",round(row["rank_stage"]),"on",round(row["online"]),"load",l0,flush=True)
os.makedirs(K+"/runs",exist_ok=True)
for r in range(3):
    order=names[r%5:]+names[:r%5]
    if r%2: order=order[::-1]
    for a in order:
        run("cold",a,1501,f"r{r}_cold_{a}")
        run("rank",a,1501,f"r{r}_rank_{a}")
for i,seed in enumerate(range(1502,1509)):
    order=names[(i+3)%5:]+names[:(i+3)%5]
    if i%2: order=order[::-1]
    for a in order: run("rank",a,seed,f"s{seed}_rank_{a}")

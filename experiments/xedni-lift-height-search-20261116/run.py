"""Frozen 27-candidate integral lift-height search per public event."""
import hashlib
import itertools
import json
import statistics
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
protocol=json.loads((HERE/"protocol.json").read_text())
source=ROOT/"xedni-common-preimage-lift-20261116"/"lifts.jsonl"
assert hashlib.sha256(source.read_bytes()).hexdigest()==protocol["source_lifts_sha256"]
events=[json.loads(line) for line in source.open()]
assert len(events)==159 and sum(x["public_relation"] for x in events)==127
deadline=time.monotonic()+protocol["run_cap_seconds"]


def add(P,Q,A):
    if P is None:
        return Q
    if Q is None:
        return P
    x,y=P
    u,v=Q
    if x==u and y+v==0:
        return None
    m=(3*x*x+A)/(2*y) if P==Q else (v-y)/(u-x)
    X=m*m-x-u
    return X,m*(x-X)-y


def mul(n,P,A):
    if n<0:
        P=(P[0],-P[1])
        n=-n
    R=None
    while n:
        if n&1:
            R=add(R,P,A)
        P=add(P,P,A)
        n>>=1
    return R


def residue(z,p):
    z=Fraction(z)
    if z.denominator%p==0:
        raise ValueError("denominator_divisible_by_p")
    return z.numerator*pow(z.denominator,-1,p)%p


def bits(z):
    z=Fraction(z)
    return max(abs(z.numerator).bit_length(),z.denominator.bit_length())


counts=Counter()
baseline=[]
best=[]
rows_path=HERE/"rows.jsonl"
winners_path=HERE/"winners.jsonl"
with rows_path.open("w") as rows, winners_path.open("w") as winners:
    for event_index,event in enumerate(events):
        p=event["field_prime"]
        a,b=event["vector"]
        x0,y0=event["T"]
        winner=None
        baseline_score=None
        for kx,ky,kA in itertools.product((-1,0,1),repeat=3):
            if time.monotonic()>=deadline:
                break
            counts["attempts"]+=1
            x,y=x0+kx*p,y0+ky*p
            A=-1+kA*p
            B=y*y-x*x*x-A*x
            record={"event_index":event_index,"field_prime":p,"target_index":event["target_index"],
                    "offsets":event["offsets"],"vector":[a,b],"public_relation":event["public_relation"],
                    "shift":[kx,ky,kA],"A":A,"B":B,"T":[x,y],"score_bits":None,
                    "P":None,"R":None,"P_reduction":None,"R_reduction":None,"status":None}
            try:
                if -16*(4*A**3+27*B**2)==0:
                    raise ValueError("singular")
                if A%p!=p-1 or B%p!=p-2 or (-16*(4*A**3+27*B**2))%p==0:
                    raise ValueError("bad_reduction")
                T=(Fraction(x),Fraction(y))
                P,R=mul(b,T,Fraction(A)),mul(-a,T,Fraction(A))
                if P is None or R is None:
                    raise ValueError("point_infinity")
                if add(mul(a,P,Fraction(A)),mul(b,R,Fraction(A)),Fraction(A)) is not None:
                    raise ValueError("rational_nonrelation")
                rP=[residue(z,p) for z in P]
                rR=[residue(z,p) for z in R]
                if rP!=event["U"] or (rR==event["V"])!=event["public_relation"]:
                    raise ValueError("wrong_reduction")
                score=max(bits(z) for z in P+R)
                record.update({"P":[str(z) for z in P],"R":[str(z) for z in R],
                               "P_reduction":rP,"R_reduction":rR,"score_bits":score,"status":"pass"})
                if (kx,ky,kA)==(0,0,0):
                    assert record["P"]==event["P"] and record["R"]==event["R"]
                    baseline_score=score
                key=(score,kx,ky,kA)
                if winner is None or key < winner[0]:
                    winner=(key,record)
            except Exception as error:
                record["status"]="failure"
                record["error"]=f"{type(error).__name__}: {error}"
            counts[record["status"]]+=1
            rows.write(json.dumps(record,sort_keys=True,separators=(",", ":"))+"\n")
        if winner is None or baseline_score is None:
            counts["incomplete_events"]+=1
        else:
            chosen=dict(winner[1])
            chosen["baseline_score_bits"]=baseline_score
            chosen["improvement_bits"]=baseline_score-chosen["score_bits"]
            chosen["source_U"]=event["U"]
            chosen["source_V"]=event["V"]
            winners.write(json.dumps(chosen,sort_keys=True,separators=(",", ":"))+"\n")
            counts["completed_events"]+=1
            counts["improved_events"]+=int(chosen["improvement_bits"]>0)
            if event["public_relation"]:
                baseline.append(baseline_score)
                best.append(chosen["score_bits"])
        if time.monotonic()>=deadline:
            break

status="complete" if counts["attempts"]==159*27 and counts["completed_events"]==159 and counts["failure"]==0 else "capped_or_failed"
result={"schema":"xedni-lift-height-search-result-v1","status":status,
        "counts":dict(sorted(counts.items())),
        "positive_score_bits":{"baseline_median":statistics.median(baseline),
                               "best_median":statistics.median(best),
                               "baseline_max":max(baseline),"best_max":max(best)},
        "protocol_sha256":hashlib.sha256((HERE/"protocol.json").read_bytes()).hexdigest(),
        "rows_sha256":hashlib.sha256(rows_path.read_bytes()).hexdigest(),
        "winners_sha256":hashlib.sha256(winners_path.read_bytes()).hexdigest()}
(HERE/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,indent=2,sort_keys=True))

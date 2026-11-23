from array import array
import csv
import ctypes as C
from pathlib import Path
import runpy
import sys
from time import perf_counter_ns, process_time_ns

here=Path(__file__).resolve().parent
ref=runpy.run_path(str(here.parent/"m31-native-layer/replay.py"))
fixture,ns=ref["fixture"],ref["ns"]
ns["_layer_walk"]=ref["native"]
p=2**31-1
word=C.c_uint32
ptr=C.POINTER(word)
lib=C.CDLL(sys.argv[3])
lib.m31_reciprocals.argtypes=[ptr,ptr,C.c_size_t]
lib.m31_fiber.argtypes=[ptr,C.c_size_t,ptr,C.c_size_t,word]
def buffer(values):
    a=array("I",values)
    assert a.itemsize==4
    return (word*len(a)).from_buffer(a)

def reciprocals(xs,mod):
    assert mod==p
    result=(word*len(xs))()
    if not lib.m31_reciprocals(buffer(xs),result,len(xs)):
        raise ValueError("zero has no field inverse")
    xs.extend(result)

def fiber(roots,maps,terminal,mod):
    assert mod==p
    steps=buffer(v for s in maps for v in (s["r"],s["A"],s["B"]))
    return bool(lib.m31_fiber(buffer(roots),len(roots),steps,len(maps),terminal))

old_inv,old_check=ns["_append_reciprocals"],ns["_check_sibling_fiber"]
for depth in (3,8,10,12,15):
    ns["_append_reciprocals"],ns["_check_sibling_fiber"]=old_inv,old_check
    info,roots=ns["chain"](p,depth)
    maps,terminal=info["maps"],info["terminal_c"]
    for index in (0,len(roots)//2,len(roots)-1):
        bad=roots.copy()
        bad[index]=(bad[index]+1)%p
        assert not old_check(bad,maps,terminal,p) and not fiber(bad,maps,terminal,p)
    for vals,steps,c in ((roots[:-1],maps,terminal),(roots,maps,(terminal+1)%p),
                         (roots,[dict(maps[0],B=0),*maps[1:]],terminal)):
        assert not old_check(vals,steps,c,p) and not fiber(vals,steps,c,p)
    ns["_append_reciprocals"],ns["_check_sibling_fiber"]=reciprocals,fiber
    assert ns["chain"](p,depth)==(info,roots)
for fn in (old_inv,reciprocals):
    xs=[1,0,2]
    try:fn(xs,p)
    except ValueError:pass
    else:raise AssertionError("zero accepted")
    assert xs==[1,0,2]

arms=[("baseline",old_inv,old_check),("reciprocals",reciprocals,old_check),
      ("fiber",old_inv,fiber),("both",reciprocals,fiber)]
w=csv.writer(sys.stdout,lineterminator="\n")
w.writerow(("block","arm","wall_ns","cpu_ns"))
for block in range(24):
    for idx in (0,1,3,2):
        arm,ns["_append_reciprocals"],ns["_check_sibling_fiber"]=arms[(idx+block)%4]
        wall,cpu=perf_counter_ns(),process_time_ns()
        points=fixture["run"]("filter_divisor")
        ct,wt=process_time_ns()-cpu,perf_counter_ns()-wall
        assert points==fixture["reference"]
        w.writerow((block,arm,wt,ct))

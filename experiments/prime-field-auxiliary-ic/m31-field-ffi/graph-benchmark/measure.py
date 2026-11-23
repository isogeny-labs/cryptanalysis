import ctypes as C
import csv
import random
import statistics
import time
from pathlib import Path

arms = ['default', 'coset', 'raw', 'signed']
functions = []
for arm in arms:
    fn = C.CDLL(str(Path(arm + '_stream.so').resolve())).repeat_inverse
    fn.argtypes = [C.POINTER(C.c_uint32)] * 2 + [C.c_size_t] * 2
    fn.restype = None
    functions.append(fn)

rng = random.Random(61123)
with open('stream.csv', 'x') as f:
    w = csv.writer(f)
    w.writerow(['n','round','calls',*arms])
    for n in (1,4,16,64,256,1024,4096,65539):
        k = max(3, 131072//max(32,n))
        x = (C.c_uint32*(n*k))(*(rng.getrandbits(32) for _ in range(n*k)))
        y = (C.c_uint32*(n*k))()
        want = [pow(v, 2147483645, 2147483647) for v in x]
        rows = []
        for rnd in range(-4,24):
            order = [0,1,3,2] if (rnd//4)%2==0 else [2,3,1,0]
            times = [0]*4
            for base in order:
                i = (base+rnd)%4
                t = time.perf_counter_ns()
                functions[i](x,y,n,k)
                times[i] = time.perf_counter_ns()-t
                assert list(y)==want
            if rnd>=0:
                w.writerow([n,rnd,k,*times])
                rows.append(times)
        print(n, [round(statistics.median(t[0]/t[i] for t in rows),3) for i in range(1,4)], flush=True)

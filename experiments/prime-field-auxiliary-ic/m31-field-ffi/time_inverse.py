import ctypes as C
import csv
import sys
import random
from time import perf_counter_ns
U=C.c_uint32
functions=[]
for lib in sys.argv[1:]:
    fn=C.CDLL(lib).m31_batch_inverse
    fn.argtypes=[C.POINTER(U),C.POINTER(U),C.c_size_t]
    fn.restype=None
    functions.append(fn)
rng=random.Random(8954)
assert len(functions) == 2
if __name__ == '__main__':
    w=csv.writer(sys.stdout, lineterminator="\n")
    w.writerow(['n','pair','calls','control_ns','candidate_ns'])
    for n in (64,255,256,257,512,4096,65539):
        inputs=(U*n)(*(rng.getrandbits(32) for _ in range(n)))
        outputs=(U*n)()
        want=[pow(x,2147483645,2147483647) for x in inputs]
        calls=max(4,131072//n)
        for rep in range(-2,24):
            times=[0,0]
            for arm in (rep%2,1-rep%2):
                fn=functions[arm]
                start=perf_counter_ns()
                for _ in range(calls): fn(inputs,outputs,n)
                times[arm]=perf_counter_ns()-start
                assert outputs[:]==want
            if rep>=0:
                w.writerow([n,rep,calls,*times])

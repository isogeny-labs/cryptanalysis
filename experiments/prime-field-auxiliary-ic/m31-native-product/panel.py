import ctypes as ct
import csv
import itertools
from pathlib import Path
import random
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent
word = ct.c_uint32
ptr = ct.POINTER(word)
p = 2**31-1
rng = random.Random(291221)
with tempfile.TemporaryDirectory() as tmp:
    functions = []
    for arm, flags in enumerate((["-DM31_PORTABLE"], ["-DM31_WIDEN"], [])):
        lib = Path(tmp)/f"arm{arm}.dylib"
        subprocess.run(["clang", "-O3", "-mcpu=native", "-std=c11", "-Wall", "-Wextra",
                        "-Werror", "-dynamiclib", *flags, root/"product.c", root/"timer.c",
                        "-o", lib], check=True)
        dll = ct.CDLL(str(lib))
        product = dll.m31_products
        product.argtypes = [ptr, ptr, ptr, ct.c_size_t]
        product.restype = None
        timer = dll.timed_products
        timer.restype = ct.c_uint64
        timer.argtypes = [ptr, ptr, ptr, ct.c_size_t, ct.c_size_t]
        functions.append((product,timer))
        product(None,None,None,0)
    for n in list(range(1,34))+[4095,4096]:
        vals = lambda: [rng.randrange(p) for _ in range(n)]
        x,y = vals(),vals()
        edges = [0,1,p//2,p-2,p-1]
        for i in range(min(n,25)):
            x[i],y[i] = edges[i//5],edges[i%5]
        expected = [a*b%p for a,b in zip(x,y)]
        for product,_ in functions:
            for alias in (0,1,2):
                a,b = (word*n)(*x),(word*n)(*y)
                out = ((word*n)(),a,b)[alias]
                product(a,b,out,n)
                assert list(out)==expected
    orders = list(itertools.permutations(range(3)))
    writer = csv.writer(sys.stdout)
    writer.writerow(["block","n","arm","reps","ns"])
    for block in range(36):
        for n in (32,4096):
            x,y = [rng.randrange(p) for _ in range(n)],[rng.randrange(p) for _ in range(n)]
            a,b,out = (word*n)(*x),(word*n)(*y),(word*n)()
            expected = [v*w%p for v,w in zip(x,y)]
            reps = 2**20//n
            for arm in orders[block%6]:
                product,timer = functions[arm]
                product(a,b,out,n)
                ns = timer(a,b,out,n,reps)
                assert list(out)==expected
                writer.writerow([block,n,arm,reps,ns])

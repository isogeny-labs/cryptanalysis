import contextlib, csv, os, runpy, sys
from pathlib import Path
mode=sys.argv.pop() if sys.argv[-1] in ("factorial", "width") else "phase"
from time import perf_counter_ns as now
sys.path.insert(0,str(Path('m31-packed-fiber').resolve()))
with open(os.devnull,'w') as sink, contextlib.redirect_stdout(sink):
    ctx=runpy.run_path('m31-packed-fiber/distinct_replay.py')
r=ctx['replay']
chain=ctx['candidate']
r.chain['chain']=chain
expected=r.baseline['fixture']['reference']
import ctypes as C
from time import process_time_ns
from hashlib import sha256
import struct
d=Path(sys.argv[2]).resolve().parent
assert sha256(b''.join(struct.pack('<II',*pt) for pt in expected)).hexdigest()=='d39f15d7880e241f9ac786e64d689719c9b905a3ebfd5a44ec1f92ad2d08a5f9'
control=C.CDLL(str(d/'control.so'))
candidate=C.CDLL(str(d/'stripes.so'))
if mode == "phase":
    arms = [(control, control), (candidate, control), (control, candidate), (candidate, candidate)]
else:
    names = (["one-rem", "one-fold", "four-rem", "stripes"] if mode == "factorial"
             else ["stripes", "width8", "width16", "width32"])
    variants = [C.CDLL(str(d / (name + ".so"))) for name in names]
    arms = [(lib, lib) for lib in variants]

for layer, recip in arms:
    layer.m31_translate.argtypes = r.fiber['ref']['translate'].argtypes
    recip.m31_reciprocals.argtypes = r.fiber['lib'].m31_reciprocals.argtypes

def install(layer, recip):
    r.fiber['ref']['translate'] = layer.m31_translate
    r.fiber['lib'] = recip

from itertools import permutations
orders=list(permutations(range(4)))
import random
rng=random.Random(31)
with contextlib.nullcontext(sys.stdout) as f:
    wr=csv.writer(f)
    wr.writerow(('block','arm','wall_ns','cpu_ns'))
    for repeat in range(5):
        rng.shuffle(orders)
        for idx,order in enumerate(orders):
            for arm in order:
                install(*arms[arm])
                cpu,wall=process_time_ns(),now()
                result=r.packed_setup()
                wall,cpu=now()-wall,process_time_ns()-cpu
                assert result==expected
                if repeat: wr.writerow(((repeat-1)*24+idx,arm,wall,cpu))

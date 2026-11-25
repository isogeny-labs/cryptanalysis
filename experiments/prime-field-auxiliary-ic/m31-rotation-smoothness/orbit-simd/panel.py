"""Process-wall panel covering all four smoothness bounds and exact output checks."""
import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import time

here = Path(__file__).resolve().parent
base = here.parent
product = base.parent / 'm31-native-product'
expected = (base / 'population.txt').read_bytes()
with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    obj = d/'product.o'
    subprocess.run(['clang','-O3','-mcpu=native','-std=c11','-c',product/'product.c','-o',obj],check=True)
    arms = [[], ['-DM31_BATCH_CENSUS',obj], ['-DM31_ORBIT_SIMD=0'], ['-DM31_ORBIT_SIMD=1']]
    for i, flags in enumerate(arms):
        subprocess.run(['clang++','-O3','-std=c++17','-mcpu=native','-Wall','-Wextra','-Werror',
                        base/'census.cpp',*flags,'-o',d/str(i)],check=True)
        assert subprocess.check_output([d/str(i)]) == expected
    writer = csv.writer(sys.stdout,lineterminator='\n')
    writer.writerow(['block','position','arm','seconds'])
    for block in range(12):
        for position, shift in enumerate((0,1,3,2)):
            i = (shift+block)%4
            start = time.perf_counter()
            out = subprocess.check_output([d/str(i)])
            elapsed = time.perf_counter()-start
            assert out == expected
            writer.writerow([block,position,i,elapsed])

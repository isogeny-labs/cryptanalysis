"""Cumulative BDD census for frozen two-pair reciprocal samples."""
import gzip
import hashlib
import importlib.util
import json
import random
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n131_w18_allseed_fourpair_20261012/fourpair_v2.py'
spec = importlib.util.spec_from_file_location('fourpair_v2', SOURCE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check_sample(rows):
    """Independent Python binary-curve arithmetic on fixed sampled witnesses."""
    f = mod.Field(41, [0, 3])
    states = [[], []]
    with (HERE.parent / 'n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv').open() as source:
        for line in source:
            parts = line.split()
            if parts and parts[0] == 'S' and int(parts[1]) < 2:
                slot = int(parts[1])
                states[slot].append((int(parts[5]), int(parts[6]), int(parts[9]), int(parts[10])))
    def add(a, b):
        x1,y1 = a; x2,y2 = b
        if x1 == x2:
            if y1 != y2 or x1 == 0: return None
            slope = x1 ^ f.mul(y1, f.inverse(x1))
            x3 = f.square(slope) ^ slope
            return x3, f.square(x1) ^ f.mul(slope ^ 1, x3)
        slope = f.mul(y1 ^ y2, f.inverse(x1 ^ x2))
        x3 = f.square(slope) ^ slope ^ x1 ^ x2
        return x3, f.mul(slope, x1 ^ x3) ^ x3 ^ y1
    rng = random.Random(0x51c7)
    picks = sorted(rng.sample(range(len(rows)), min(64,len(rows))))
    for index in picks:
        i,j,x,u = rows[index]
        a,b,xa,ya = states[0][i]
        c,d,xb,yb = states[1][j]
        assert len({a,b,c,d}) == 4
        result = add((xa,ya),(xb,yb))
        assert result is not None and result[0] == x
        assert f.mul(x,u) == 1
        assert f.square(result[1]) ^ f.mul(x,result[1]) == f.mul(f.square(x),x) ^ 1
    return {'checked':len(picks),'selection_seed':0x51c7}

def main():
    sample = HERE / 'samples.tsv'
    with sample.open() as source:
        header = next(source).strip()
        assert header == 'slot0_sid\tslot1_sid\tx\treciprocal_x'
        rows = [tuple(map(int,line.split())) for line in source]
    assert len(rows) == 200000
    values = [r[3] for r in rows]
    assert len(set(values)) == len(values)
    audit = check_sample(rows)
    rng = random.Random(0xbdd41)
    random_values = set()
    while len(random_values) < len(values):
        candidate = rng.randrange(1, 1<<41)
        random_values.add(candidate)
    random_values = list(random_values)
    curve_values = [int(line) for line in (HERE/'curve_control.tsv').read_text().splitlines()]
    assert len(curve_values) == len(set(curve_values)) == len(values)
    field = mod.Field(41,[0,3])
    for u in curve_values[:64]:
        x = field.inverse(u)
        z = x ^ u
        trace = 0
        for _ in range(41):
            trace ^= z
            z = field.square(z)
        assert trace == 0
    results = []
    for count in (25000,50000,100000,200000):
        entry = {'count':count}
        for label, group in (('pair',values[:count]),('uniform',random_values[:count]),
                             ('curve_valid',curve_values[:count])):
            start = time.perf_counter()
            root,nodes = mod.bdd(set(group),41)
            elapsed = time.perf_counter()-start
            blob = '\n'.join(str(v) for v in sorted(group)).encode()
            entry[label] = {'nodes':len(nodes),'nodes_per_value':len(nodes)/count,
                            'seconds':elapsed,'sorted_gzip_bytes':len(gzip.compress(blob,mtime=0)),
                            'root':root,'maxrss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        entry['node_ratio_pair_to_uniform'] = entry['pair']['nodes']/entry['uniform']['nodes']
        entry['node_ratio_pair_to_curve_valid'] = entry['pair']['nodes']/entry['curve_valid']['nodes']
        results.append(entry)
        print(json.dumps(entry,sort_keys=True),flush=True)
    record = {'input_sha256':sha(sample),'curve_control_sha256':sha(HERE/'curve_control.tsv'),
              'curve_control_cpp_sha256':sha(HERE/'curve_control.cpp'),
              'source_sha256':sha(SOURCE),
              'pair_table_sha256':sha(HERE.parent/'n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv'),
              'sample_cpp_sha256':sha(HERE/'sample.cpp'),
              'audit':audit,'comparison':'uniform nonzero 41-bit values and uniform valid curve x reciprocals, equal distinct count',
              'seed_uniform':0xbdd41,'results':results}
    (HERE/'result.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')

if __name__ == '__main__': main()

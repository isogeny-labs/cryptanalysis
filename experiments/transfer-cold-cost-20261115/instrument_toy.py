"""Guarded phase instrumentation of CT140; generate/build only until admission.

Frozen original sources stay untouched. The generated program has a new
schema and cannot be treated as the historical benchmark binary.
"""
import argparse
import csv
import hashlib
import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'chained-transfer-public-target/ct130-prime31'
INCLUDE_SHA = '5422e02524850bfb0f595901c063a07326079e9dd82a483e6085996ce97bbdb0'
GENERATOR_SHA = '54f4890af6d199f58f40f7d0175acd10d895dfbbe6828a3444b52130719d634d'
WIDTHS = (4, 16)


def replace_one(source, before, after):
    if source.count(before) != 1:
        raise ValueError(f'changed instrumentation boundary: {before!r}')
    return source.replace(before, after)


def generate(width):
    if width not in WIDTHS:
        raise ValueError('only the previously selected source/target widths are supported')
    if hashlib.sha256((BASE / 'ct135_native.cpp').read_bytes()).hexdigest() != INCLUDE_SHA:
        raise ValueError('frozen include changed')
    if hashlib.sha256((BASE / 'ct140_generate.py').read_bytes()).hexdigest() != GENERATOR_SHA:
        raise ValueError('frozen CT140 generator changed')
    spec = importlib.util.spec_from_file_location('ct140_source_generator', BASE / 'ct140_generate.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    source = mod.generate(width)  # also guards the original CT136 source
    source = replace_one(source, f'ct140-width{width}-cold-v1', f'cold-phase-width{width}-v1')
    source = replace_one(source,
        '       Curve c=trg?Curve{0,9}:Curve{SA,SB};\n       U iv0=inversions;\n       auto start=std::chrono::steady_clock::now();',
        '       auto start=std::chrono::steady_clock::now();\n       Curve c=trg?Curve{0,9}:Curve{SA,SB};\n       U iv0=inversions;\n       auto setup_end=std::chrono::steady_clock::now();')
    source = replace_one(source, '       Point g=trg?map2(G):G;',
                         '       Point g=trg?map2(G):G;\n       auto generator_end=std::chrono::steady_clock::now();')
    source = replace_one(source, '       Point h=trg?map2(pub):pub;',
                         '       Point h=trg?map2(pub):pub;\n       auto transport_end=std::chrono::steady_clock::now();')
    source = replace_one(source, '       Curve verify{SA,SB};',
                         '       auto solve_end=std::chrono::steady_clock::now();\n       Curve verify{SA,SB};')
    source = replace_one(source,
        '       U ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-start).count();',
        '''       auto finish=std::chrono::steady_clock::now();
       auto from_start=[&](auto t)->U{return std::chrono::duration_cast<std::chrono::nanoseconds>(t-start).count();};
       U s=from_start(setup_end),gtime=from_start(generator_end),h=from_start(transport_end),v=from_start(solve_end),ns=from_start(finish);
       std::cout<<"phase,"<<i<<','<<names[arm]<<','<<(j<5?0:1)<<','<<s<<','<<gtime-s<<','<<h-gtime<<','<<v-h<<','<<ns-v<<','<<ns<<'\\n';''')
    # Rename the h timestamp: h is already the public target point variable.
    source = source.replace('h=from_start(transport_end)', 'transport_ns=from_start(transport_end)')
    source = source.replace("<<h-gtime<<','<<v-h", "<<transport_ns-gtime<<','<<v-transport_ns")
    return source


def normalize(raw, width):
    """Validate phase bindings and return rows for the unchanged CT136 arithmetic auditor.

    This is not a provenance verifier. It supplies no original-prime evidence.
    """
    if width not in WIDTHS:
        raise ValueError('width')
    lines = raw.splitlines()
    if not lines or lines[0] != f'schema,cold-phase-width{width}-v1':
        raise ValueError('schema')
    out, pending, seen = ['schema,ct136-batched-cold-v1'], None, set()
    phases = []
    for line in lines[1:]:
        row = next(csv.reader([line]))
        if row and row[0] == 'phase':
            if pending is not None or len(row) != 10:
                raise ValueError('phase order/schema')
            values = list(map(int, row[3:]))
            repeat, *costs = values
            if repeat not in (0, 1) or min(costs) < 0 or sum(costs[:-1]) != costs[-1]:
                raise ValueError('phase units/sum')
            key = (row[1], row[2], repeat)
            if key in seen:
                raise ValueError('duplicate phase')
            seen.add(key)
            pending = row
            phases.append(row)
        else:
            if row and row[0] == 'row':
                if pending is None or len(row) != 14 or row[1:3] != pending[1:3] or row[7] != pending[-1]:
                    raise ValueError('phase not bound to actual timed row')
                pending = None
            elif pending is not None:
                raise ValueError('unbound phase')
            out.append(line.replace(f'source_batch{width}_rho', 'source_batch32_rho')
                       .replace(f'target_batch{width}_rho', 'target_batch32_rho'))
    if pending is not None or not phases:
        raise ValueError('missing timed rows')
    return '\n'.join(out) + '\n', phases


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    for width in WIDTHS:
        path = args.out / f'cold_phase_width{width}.cpp'
        path.write_text(generate(width))
        print(path, hashlib.sha256(path.read_bytes()).hexdigest())

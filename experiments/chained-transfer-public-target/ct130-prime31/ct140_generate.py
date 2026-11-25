#!/usr/bin/env python3
"""Guarded CT140 smaller-lane derivative; never overwrites CT136/CT138 sources."""
import argparse, hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent
SOURCE_SHA256='20b0305d0b291602dd141a278c00459c47e78608f17e33bea6395a3106438921'
WIDTHS=(2,4,8,16)
def one(s,before,after):
    if s.count(before)!=1:raise ValueError(f'unsafe replacement {before}: {s.count(before)}')
    return s.replace(before,after)
def generate(w):
    if w not in WIDTHS or 200000%w:raise ValueError('not preregistered')
    raw=(BASE/'ct136_native.cpp').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:raise ValueError('changed frozen source')
    s=raw.decode()
    for a,b in [ ('constexpr int LANES=32;', f'constexpr int LANES={w};'),
                 ('for(int round=0;round<6250;round++)', f'for(int round=0;round<{200000//w};round++)'),
                 ('ct136-batched-cold-v1',f'ct140-width{w}-cold-v1'),
                 ('"source_batch32_rho","target_batch32_rho"', f'"source_batch{w}_rho","target_batch{w}_rho"'),
                 ('std::stoi(argv[1]):8', 'std::stoi(argv[1]):32')]:s=one(s,a,b)
    return '// Generated CT140 from CT136 SHA256 '+SOURCE_SHA256+'\n'+s
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);ns=p.parse_args();ns.out.mkdir(parents=True,exist_ok=False)
    for w in WIDTHS:
        target=ns.out/f'ct140_width{w}.cpp';target.write_text(generate(w))
        print(f'width={w} max_transitions_per_trial=200000 sha256={hashlib.sha256(target.read_bytes()).hexdigest()}')

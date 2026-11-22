#!/usr/bin/env python3
"""CT138 generator: guarded, read-only CT136 -> width16/32/64 variants.

Outputs are ephemeral build inputs, never substitutes for frozen CT136 source.
"""
import argparse
import hashlib
from pathlib import Path

SOURCE_SHA256 = "20b0305d0b291602dd141a278c00459c47e78608f17e33bea6395a3106438921"
WIDTHS = (16, 32, 64)
BASE = Path(__file__).resolve().parent
SOURCE = BASE / "ct136_native.cpp"

def change_one(src, before, after):
    count = src.count(before)
    if count != 1:
        raise ValueError(f"expected one occurrence of {before!r}, saw {count}")
    return src.replace(before, after)

def generate(width):
    if width not in WIDTHS or 200000 % width:
        raise ValueError("unapproved width / transition budget")
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("CT136 native source does not match frozen SHA256")
    src = raw.decode("utf-8")
    src = change_one(src, "constexpr int LANES=32;", f"constexpr int LANES={width};")
    src = change_one(src, "for(int round=0;round<6250;round++)",
                     f"for(int round=0;round<{200000//width};round++)")
    src = change_one(src, "ct136-batched-cold-v1", f"ct138-width{width}-cold-v1")
    src = change_one(src, '"source_batch32_rho","target_batch32_rho"',
                     f'"source_batch{width}_rho","target_batch{width}_rho"')
    src = change_one(src, "std::stoi(argv[1]):8", "std::stoi(argv[1]):32")
    return "// Generated CT138; original CT136 SHA256 " + SOURCE_SHA256 + "\n" + src

def main():
    p=argparse.ArgumentParser()
    p.add_argument("out", type=Path)
    args=p.parse_args()
    if args.out.exists():
        raise ValueError("refuse overwrite existing generated source")
    args.out.mkdir(parents=True)
    for w in WIDTHS:
        target=args.out/f"ct138_width{w}.cpp"
        target.write_text(generate(w))
        print(f"width={w} transitions_per_trial={w*(200000//w)} sha256={hashlib.sha256(target.read_bytes()).hexdigest()}")
if __name__ == "__main__":
    main()

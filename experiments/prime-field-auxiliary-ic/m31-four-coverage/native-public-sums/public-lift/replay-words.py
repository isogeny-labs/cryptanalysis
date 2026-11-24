"""Run python3 replay-words.py [--openssl]. Prints paired basis setup times.

On macOS the default build uses CommonCrypto. Other systems and --openssl
use libcrypto via pkg-config. A C++17 compiler and a C99 compiler are needed.
"""
import argparse
import ctypes as ct
import hashlib
import os
from pathlib import Path
import shlex
import statistics
import subprocess
import sys
import tempfile
import time

from replay import CANARY, P, POINTER, WORD, build, reference


def words_python(prefix, start, count):
    return [int.from_bytes(hashlib.sha256(prefix + str(i).encode()).digest()[:4], 'big') & P
            for i in range(start, start + count)]


def build_words(tmp, openssl):
    lib = tmp / 'words.so'
    flags = ['-dynamiclib'] if sys.platform == 'darwin' else ['-shared', '-fPIC']
    if openssl:
        flags += ['-DM31_USE_OPENSSL'] + shlex.split(subprocess.check_output(
            ['pkg-config', '--cflags', '--libs', 'libcrypto'], text=True))
    subprocess.run([*shlex.split(os.environ.get('CXX', 'c++')), '-O3', '-std=c++17',
                    str(Path(__file__).with_name('public-words.cpp')), *flags, '-o', str(lib)], check=True)
    fn = ct.CDLL(str(lib)).public_words
    fn.argtypes = [ct.c_char_p, ct.c_size_t, ct.c_uint64, ct.c_size_t, POINTER]
    fn.restype = ct.c_int
    return fn


def basis(seed, size, lift, native=None):
    prefix = f'm31-smooth-census/{seed}/'.encode()
    points = {}
    cursor = 0
    while len(points) < size:
        width = min(256, max(32, (2 * (size - len(points)) // 32) * 32))
        buf = WORD * width
        if native is None:
            xs = buf(*words_python(prefix, cursor, width))
        else:
            xs = buf()
            if native(prefix, len(prefix), cursor, width, xs):
                raise RuntimeError('public_words failed')
        cursor += width
        invalid = [i for i, x in enumerate(xs) if x == P]
        for i in invalid:
            xs[i] = 0
        ys = buf()
        lift(xs, ys, width)
        for i in invalid:
            ys[i] = P
        for x, y in zip(xs, ys):
            if y != P:
                points[x] = y
    return list(points.items())[:size]


def oracle(seed, size):
    prefix = f'm31-smooth-census/{seed}/'.encode()
    result = {}
    cursor = 0
    while len(result) < size:
        x, = words_python(prefix, cursor, 1)
        cursor += 1
        if x != P and x not in result:
            y = reference(x)
            if y != P:
                result[x] = y
    return list(result.items())


def replay(openssl):
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        lift = build(tmp, 'fold', shlex.split(os.environ.get('CC', 'cc')))
        fn = build_words(tmp, openssl)
        for prefix in (b'', b'a\0b/', b'x' * 108):
            for start, count in ((0, 0), (9, 2), (99, 3), (2**32-1, 3), (2**64-32, 32)):
                out = (WORD * (count + 2))(*([CANARY] * (count + 2)))
                ptr = ct.cast(ct.byref(out, ct.sizeof(WORD)), POINTER)
                assert fn(prefix, len(prefix), start, count, ptr) == 0
                assert list(out) == [CANARY, *words_python(prefix, start, count), CANARY]
        assert fn(b'', 0, 2**64-1, 2, out) == -1
        assert fn(b'x'*109, 109, 0, 1, out) == -1
        for size in (132, 544):
            samples = [[], []]
            for seed in range(16000, 16128):
                expected = oracle(seed, size)
                for arm in ((0, 1) if seed % 2 else (1, 0)):
                    start = time.perf_counter_ns()
                    actual = basis(seed, size, lift, fn if arm else None)
                    samples[arm].append((time.perf_counter_ns() - start) / 1e6)
                    assert actual == expected
            speedup = statistics.median(x/y for x,y in zip(*samples))
            print(size, 'points, median ms (Python/native)', *(round(statistics.median(v), 4)
                  for v in samples), 'paired speedup', round(speedup, 3))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--openssl', action='store_true')
    replay(parser.parse_args().openssl or sys.platform != 'darwin')

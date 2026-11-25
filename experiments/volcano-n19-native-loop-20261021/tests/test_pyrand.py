"""The native MT19937 port (native/src/pyrand.rs) against this interpreter's `random` module.

    N19_LIB=PATH/libtau6loop.so python3 -m unittest -v tests/test_pyrand.py

The seeds are every rng seed string the protocol uses (panel, smoke points, the archived
tau6 seeds, the generator's 'gen:E0', the field check's) plus random and non-ASCII strings;
the calls are tauDlp's (randrange(1, r) twice, then shuffle of the persistent 19-list) and
the generator's randrange(1, 2^19). The runner's Sage image runs CPython 3.12.3; CI runs
this test there too (sage -python) and locally on the host Python.
"""
import ctypes
import json
import os
import random
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
LIB = os.environ.get('N19_LIB')
R = 130873


def seeds():
    with open(os.path.join(EXP, 'inputs', 'panel.json')) as f:
        panel = json.load(f)
    out = [p['rng_seed'] for p in panel['points'] + panel['smoke_points']]
    out += ['tau:tau6:%d' % i for i in range(10)] + ['gen:E0', 'native_binding.check_field', '', 'x',
                                                      'é∂ unicode ✓', 'a' * 300]
    rng = random.Random('test_pyrand')
    out += [''.join(chr(rng.randrange(32, 127)) for _ in range(rng.randrange(1, 40))) for _ in range(30)]
    return out


@unittest.skipUnless(LIB, 'set N19_LIB to the built libtau6loop.so')
class PyRandom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib = ctypes.CDLL(LIB)
        for name, t in (('tau6loop_rng_randrange', ctypes.c_uint64), ('tau6loop_rng_tau_stream', ctypes.c_uint64)):
            getattr(cls.lib, name).restype = ctypes.c_int64
        cls.lib.tau6loop_rng_shuffle.restype = ctypes.c_int64

    def randrange(self, seed, a, b, n):
        sb = seed.encode()
        out = (ctypes.c_uint64 * n)()
        k = self.lib.tau6loop_rng_randrange(sb, ctypes.c_size_t(len(sb)), ctypes.c_uint64(a), ctypes.c_uint64(b),
                                            ctypes.c_size_t(n), out)
        self.assertEqual(k, n)
        return list(out)

    def test_randrange_widths(self):
        for seed in seeds():
            for a, b in ((1, R), (1, 1 << 19), (0, 1 << 19), (2, R - 1), (0, 2), (5, 6), (0, (1 << 32) - 1), (7, (1 << 31) + 12345)):
                py = random.Random(seed)
                self.assertEqual(self.randrange(seed, a, b, 50), [py.randrange(a, b) for _ in range(50)],
                                 (seed, a, b))

    def test_tau_stream(self):
        for seed in seeds():
            rounds = 400
            sb = seed.encode()
            out = (ctypes.c_uint64 * (21 * rounds))()
            self.lib.tau6loop_rng_tau_stream(sb, ctypes.c_size_t(len(sb)), ctypes.c_uint64(R),
                                             ctypes.c_size_t(rounds), out)
            py = random.Random(seed)
            shifts = list(range(19))
            want = []
            for _ in range(rounds):
                want += [py.randrange(1, R), py.randrange(1, R)]
                py.shuffle(shifts)
                want += shifts
            self.assertEqual(list(out), want, seed)

    def test_shuffle_lengths(self):
        for seed in seeds()[:20]:
            for n in (1, 2, 3, 19, 64):
                sb = seed.encode()
                out = (ctypes.c_uint32 * (n * 5))()
                self.lib.tau6loop_rng_shuffle(sb, ctypes.c_size_t(len(sb)), ctypes.c_size_t(n), ctypes.c_size_t(5),
                                              out)
                py = random.Random(seed)
                v = list(range(n))
                want = []
                for _ in range(5):
                    py.shuffle(v)
                    want += v
                self.assertEqual(list(out), want, (seed, n))


if __name__ == '__main__':
    unittest.main()

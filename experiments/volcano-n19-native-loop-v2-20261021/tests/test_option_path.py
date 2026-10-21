"""The option path of the Sage scripts under an emulated `sage FILE.sage` (no Sage needed).

    python3 -m unittest -v tests/test_option_path.py

v1 (volcano-n19-native-loop-20261021) lost every option of arm_n2x.sage and
diagnosis/profile_n.sage on the runner (run 39526183111) while its local dry run passed,
because the dry run's stand-in `sage` (smoke/fake_sage.py) parsed the options itself and never
executed the .sage files. These tests execute the real files the way `sage` does
(tests/sage_emulation.py: preparse_file layout, Integer literals, a __main__ namespace shared
with every `load`), so they fail on v1 and pass on v2:

* arm_n2x.sage --options-only and profile_n.sage --mode load keep every option through the
  v3 load and echo them;
* the N2X commands run_schedule.py builds for every scheduled N2X run parse;
* a missing option exits with its name instead of a TypeError;
* the namespace audit (tests/namespace_audit.py) finds no clobbered or shadowed global;
* on v1's sources (when ../volcano-n19-native-loop-20261021 is present, or N19_V1_DIR names
  it) the emulation reproduces run 39526183111's tracebacks: TypeError in abspath at
  arm_n2x.sage.py line 107 (called from line 159) and profile_n.sage.py line 264 (from 313).

The pinned-image counterpart, with the real `sage`, is option_check.py in the smoke job.
"""
import json
import os
import sys
import tempfile
import traceback
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, EXP)
import namespace_audit as na  # noqa: E402
import sage_emulation as se  # noqa: E402

V1 = os.environ.get('N19_V1_DIR') or os.path.join(os.path.dirname(EXP), 'volcano-n19-native-loop-20261021')
LIB, V3LIB = '/rd/lib/libtau6loop.so', '/rd/lib/libtau6native.so'


def n2x_args(out, extra=()):
    return ['--arm', 'N2X', '--serial', '9', '--lib', LIB, '--v3lib', V3LIB, '--out', out, '--point', 'v3p00',
            '--scalar', '43903', '--rng-seed', 'n19-native-tau6-v3:00'] + list(extra)


def profile_args(out, mode='load'):
    return ['--mode', mode, '--point', 'v3p00', '--scalar', '43903', '--rng-seed', 'n19-native-tau6-v3:00',
            '--lib', V3LIB, '--out', out]


def last_frames(exc):
    return [(os.path.basename(f.filename), f.lineno) for f in traceback.extract_tb(exc.__traceback__)]


class OptionPath(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, 'out.json')

    def tearDown(self):
        self.tmp.cleanup()

    def test_arm_n2x_options_survive_the_v3_load(self):
        args = n2x_args(self.out, ['--options-only'])
        r = se.run_sage_file(os.path.join(EXP, 'arm_n2x.sage'), args)
        self.assertIsNone(r.exc, repr(r.exc))
        rec = json.load(open(self.out))
        self.assertEqual(rec['argv'][1:], args)
        for k, v in rec['options'].items():
            self.assertEqual(v, args[args.index(k) + 1], k)
        self.assertTrue(rec['v3_definitions_loaded'])
        self.assertEqual(r.stand_ins, [], 'the option path touched a Sage stand-in')

    def test_profile_n_load_mode_keeps_its_options(self):
        args = profile_args(self.out)
        r = se.run_sage_file(os.path.join(EXP, 'diagnosis', 'profile_n.sage'), args)
        self.assertIsNone(r.exc, repr(r.exc))
        rec = json.load(open(self.out))
        self.assertEqual(rec['argv'][1:], args)
        self.assertEqual((rec['mode'], rec['point'], rec['scalar']), ('load', 'v3p00', 43903))

    def test_scheduled_n2x_commands_parse(self):
        import run_schedule as rs

        class A:
            lib, v3lib, bin = LIB, V3LIB, '/rd/lib/tau6dlp'
        sched = json.load(open(os.path.join(EXP, 'schedule.json')))
        n2x = [(part, r) for part, p in sched['parts'].items() for seg in p['segments'] for r in seg['runs']
               if r['arm'] == 'N2X']
        self.assertEqual(len(n2x), 2 + 24)
        for part, run in n2x[:3] + n2x[-1:]:
            cmd = rs.command('sage', run, part, A, self.out, '/rd')
            self.assertTrue(cmd[1].endswith('arm_n2x.sage'))
            r = se.run_sage_file(cmd[1], cmd[2:] + ['--options-only'])
            self.assertIsNone(r.exc, '%s serial %s: %r' % (part, run['serial'], r.exc))
            rec = json.load(open(self.out))
            self.assertEqual(rec['options']['--point'], run['point'])
            self.assertEqual(rec['options']['--scalar'], str(run['scalar']))
            self.assertEqual(rec['options']['--rng-seed'], run['rng_seed'])
            self.assertEqual(rec['options']['--serial'], str(run['serial']))

    def test_missing_option_names_itself(self):
        args = [a for a in n2x_args(self.out, ['--options-only'])]
        i = args.index('--lib')
        del args[i:i + 2]
        r = se.run_sage_file(os.path.join(EXP, 'arm_n2x.sage'), args)
        self.assertIsInstance(r.exc, SystemExit)
        self.assertIn('missing option(s) --lib', str(r.exc))

    def test_namespace_audit_is_clean(self):
        for script in (os.path.join(EXP, 'arm_n2x.sage'), os.path.join(EXP, 'diagnosis', 'profile_n.sage')):
            res = na.audit(script)
            self.assertEqual((res['clobbered'], res['shadowed']), ([], []), script)

    @unittest.skipUnless(os.path.isfile(os.path.join(V1, 'arm_n2x.sage')), 'v1 sources not present')
    def test_v1_failure_is_reproduced(self):
        r = se.run_sage_file(os.path.join(V1, 'arm_n2x.sage'), n2x_args(self.out))
        self.assertIsInstance(r.exc, TypeError)
        self.assertIn('expected str, bytes or os.PathLike object, not NoneType', str(r.exc))
        self.assertEqual(last_frames(r.exc)[-3:-1], [('arm_n2x.sage.py', 159), ('arm_n2x.sage.py', 107)])
        self.assertEqual(r.namespace['_argv'], [os.path.join(os.path.dirname(V1),
                                                             'volcano-n19-native-tau6-v3-20261020', 'arm.sage')])
        r = se.run_sage_file(os.path.join(V1, 'diagnosis', 'profile_n.sage'), profile_args(self.out, 'timers'))
        self.assertIsInstance(r.exc, TypeError)
        self.assertEqual(last_frames(r.exc)[-3:-1], [('profile_n.sage.py', 313), ('profile_n.sage.py', 264)])
        for script in (os.path.join(V1, 'arm_n2x.sage'), os.path.join(V1, 'diagnosis', 'profile_n.sage')):
            self.assertEqual(na.audit(script)['clobbered'], ['_argv'], script)


if __name__ == '__main__':
    unittest.main()

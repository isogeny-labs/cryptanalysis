# Untimed Sage reproduction of v2's crash, run by the sage-smoke job of
# .github/workflows/n19-native-tau6-v3.yml in the pinned image. No interval here
# is a measurement.
#
#   sage diagnosis/digest_repro.sage --lib SO --out FILE
#
# 1. The exact failing calls: v2's own arm.sage (unchanged, from main) for the
#    rows p00-N and p00-B of run 39376405326, with that run's arguments
#    (v2 schedule.json) and this job's library (lib.rs is byte-identical to v2's).
#    Each must exit 1 with v2's traceback: relation_digests -> h(rows) ->
#    TypeError: Object of type Integer is not JSON serializable.
# 2. The mechanism: Sage's preparser on v2's line, and the types it produces in a
#    .sage file (this one): 0 is a Sage Integer, {}.get(c, 0) + int and % int stay
#    Integer, json.dumps raises on it.
# 3. The fix: relation_digest.relation_digests (plain Python) on relations whose
#    entries are Sage Integers gives the same digests as on Python ints, and
#    relation_digest.plain converts Sage Integer, RealNumber and RealDoubleElement and
#    rejects a finite-field element and a rational instead of str()-ing them.
import json
import os
import subprocess
import sys

MYDIR = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
V2 = os.path.join(os.path.dirname(MYDIR), 'volcano-n19-native-tau6-v2-20261019')
sys.path.insert(0, MYDIR)
import relation_digest as rd
from sage.repl.preparse import preparse

a = sys.argv[1:]
lib = os.path.abspath(a[a.index('--lib') + 1])
out_path = a[a.index('--out') + 1]
out = {'kind': 'untimed Sage diagnostic (digest crash of v2 run 39376405326)', 'sage_version': version()}

# 1. exact failing calls
sched = json.load(open(os.path.join(V2, 'schedule.json')))
v2rows = {r['row']: r for s in sched['segments'] for r in s['rows']}
calls = []
for name in ('p00-N', 'p00-B'):
    r = v2rows[name]
    tmp = os.path.join(os.path.dirname(os.path.abspath(out_path)), 'v2-%s.json' % name)
    cmd = ['sage', os.path.join(V2, 'arm.sage'), '--arm', r['arm'], '--lib', lib, '--out', tmp,
           '--point', r['point'], '--scalar', str(r['scalar']), '--rng-seed', r['rng_seed']]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err = p.stderr.decode('utf-8', 'replace')
    lines = [l for l in err.splitlines() if l.strip()]
    calls.append({'row': name, 'command': cmd[1:], 'exit': p.returncode, 'stderr_tail': lines[-14:],
                  'row_file_written': os.path.exists(tmp),
                  'through_relation_digests': 'in relation_digests' in err,
                  'at_rows_digest': "'rows_sha256': h(rows)" in err,
                  'last_line': lines[-1] if lines else None})
out['v2_exact_calls'] = calls
out['v2_reproduced'] = all(c['exit'] == 1 and not c['row_file_written'] and c['through_relation_digests'] and
                           c['at_rows_digest'] and
                           c['last_line'] == 'TypeError: Object of type Integer is not JSON serializable'
                           for c in calls)

# 2. mechanism
line = 'row[col] = (row.get(col, 0) + sg * pow(int(lam), int(e), int(p))) % int(p)'
v = ({}.get(int(3), 0) + int(1) * pow(int(5), int(2), int(7))) % int(7)   # as v2: only the literal 0 is preparsed
try:
    json.dumps([[int(3), v]])
    dump_err = None
except TypeError as e:
    dump_err = 'TypeError: %s' % e
out['mechanism'] = {'v2_line': line, 'preparsed': preparse(line),
                    'type_of_literal_0_in_a_sage_file': type(0).__name__,
                    'type_of_get_default_plus_int_mod_int': type(v).__name__,
                    'json_dumps_of_it': dump_err}
out['mechanism_ok'] = 'Integer(0)' in out['mechanism']['preparsed'] and type(v).__name__ == 'Integer' and \
    dump_err == 'TypeError: Object of type Integer is not JSON serializable'

# 3. fix
rels_sage = [[(15, 1, 3), (2, -1, 7)], [(4, -1, 0), (4, 1, 18)], [(9, 1, 11), (0, 1, 5)]]   # literals: Sage Integers
rels_int = [[tuple(int(x) for x in t) for t in r] for r in rels_sage]
d_int = rd.relation_digests(rels_int, int(41811), int(130873))
d_sage = rd.relation_digests(rels_sage, Integer(41811), Integer(130873))
probes = {}
for label, obj in (('Integer', Integer(7)), ('RealNumber', RR(0.5)), ('RealDoubleElement', RDF(0.25)),
                   ('python_bool', True), ('GF2_19_element', GF(2 ** 19, 'z').gen()), ('Rational', QQ(1) / 2)):
    try:
        probes[label] = {'converted': rd.plain({'v': obj})['v'], 'type': type(obj).__name__}
    except TypeError as e:
        probes[label] = {'rejected': str(e), 'type': type(obj).__name__}
out['fix'] = {'digests_int': d_int, 'digests_sage_Integer': d_sage, 'equal': d_int == d_sage, 'plain': probes}
# Gate: equal digests and exact conversion of Integer and RealNumber. The finite-field and
# rational probes are recorded (both should be rejected) but do not gate.
out['fix_ok'] = d_int == d_sage and type(probes['Integer'].get('converted')) is int and \
    probes['Integer'].get('converted') == 7 and probes['RealNumber'].get('converted') == 0.5
out['ok'] = out['v2_reproduced'] and out['mechanism_ok'] and out['fix_ok']
open(out_path, 'w').write(rd.dumps(out, indent=1, sort_keys=True) + '\n')
print(rd.dumps({k: out[k] for k in ('v2_reproduced', 'mechanism_ok', 'fix_ok', 'ok')}))
print(rd.dumps(out['mechanism']))
if not out['ok']:
    raise SystemExit(5)

"""Check the archived experiment, independent replay, and pinned Lean receipt."""
from pathlib import Path
import hashlib, json, re, subprocess, sys

H=Path(__file__).resolve().parent
seal=(H/'SEAL.sha256').read_text().splitlines()
for line in seal:
    digest,name=line.split('  ',1)
    assert hashlib.sha256((H/name).read_bytes()).hexdigest()==digest,name

result=json.loads((H/'run-result.json').read_text())
assert result['status']=='complete'
assert result['counts']=={'public_hits':17,'query_distinct_x':511,'query_equal_x':1,
 'query_failure':0,'query_pass':512,'rational_hits':0,'relation_mismatches':0,'vector_attempts':6656}
assert (H/'run.stderr').read_bytes()==b''

replay=subprocess.run([sys.executable,str(H/'audit.py')],capture_output=True,text=True,check=True)
assert replay.stderr==''
assert json.loads(replay.stdout)['status']=='PASS'
assert json.loads((H/'audit.json').read_text())['status']=='PASS'
assert (H/'audit.stderr').read_bytes()==b''
assert (H/'audit.stdout').read_text()==replay.stdout

source=(H/'formal/TwoImagePrecommit.lean').read_text()
assert not re.search(r'\b(sorry|admit|axiom|native_decide)\b',source)
build=(H/'formal/build-output.txt').read_text()
assert 'Build completed successfully (9040 jobs).' in build
expected=['first_point_equation','second_point_equation','interpA_eq_of_two_equations',
          'interpB_eq_of_two_equations','same_x_opposite','relation_transfer']
for name in expected:
    match=re.search(r"'XedniTwoImagePrecommit\."+name+r"' depends on axioms: \[([^]]*)\]",build)
    assert match,name
    assert set(match.group(1).split(', ')) <= {'propext','Classical.choice','Quot.sound'}
assert 'sorryAx' not in build and 'error:' not in build
print(json.dumps({'status':'PASS','sealed_files':len(seal),'public_tests':6656,
                  'query_curves':512,'rational_relations':0,'checked_theorems':len(expected)},sort_keys=True))

"""Generate finite Lean coverage and frozen-target miss certificates."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
POST=json.loads((ROOT/'post-run.json').read_text())


def local(name,key):
    raw=(ROOT/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==POST[key]
    return json.loads(raw)


def main():
    logs=local('class-logs.json','class_logs_sha256')['q_logs']
    fixture=local('fixture.json','fixture_sha256')
    audit=json.loads((ROOT/'sumset-audit.json').read_text())
    q=2531; target=fixture['scalar']
    assert audit['status']=='PASS' and len(logs)==40 and target==audit['target_scalar']
    lines=['module','','public import Init','','namespace FiniteCoverage',
           'set_option maxRecDepth 65536','set_option maxHeartbeats 0',
           'public def logs : List Nat := ['+', '.join(map(str,logs))+']',
           f'public def targetScalar : Nat := {target}',
           'public theorem log_count : logs.length = 40 := by decide',
           'public theorem logs_distinct : logs.eraseDups.length = 40 := by decide',
           'public theorem logs_nonzero : logs.all (· != 0) = true := by decide',
           'public theorem negation_closed :',
           '    logs.all (fun x => logs.contains ((2531 - x) % 2531)) = true := by decide',
           'public def unorderedSums : List Nat :=',
           '  (List.range 40).flatMap (fun i =>',
           '    ((List.range 40).filter (fun j => decide (i <= j))).map',
           '      (fun j => ((logs.getD i 0) + (logs.getD j 0)) % 2531))',
           'public theorem unordered_pattern_count : unorderedSums.length = 820 := by decide',
           'public theorem distinct_coverage : unorderedSums.eraseDups.length = 689 := by decide',
           'public theorem frozen_target_absent : unorderedSums.contains targetScalar = false := by decide',
           '#print axioms log_count','#print axioms logs_distinct',
           '#print axioms logs_nonzero','#print axioms negation_closed',
           '#print axioms unordered_pattern_count','#print axioms distinct_coverage',
           '#print axioms frozen_target_absent','end FiniteCoverage','']
    (HERE/'FiniteCoverage.lean').write_text('\n'.join(lines))
    cert={'schema':'hecke-d79-p63317-coverage-lean-cert-v1',
          'q':q,'logs':logs,'target_scalar':target,
          'unordered_patterns':820,'distinct_covered':689,
          'class_logs_sha256':POST['class_logs_sha256'],
          'fixture_sha256':POST['fixture_sha256']}
    (HERE/'certificate.json').write_text(json.dumps(cert,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'target_scalar':target,'patterns':820,'covered':689}))


if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""Retain initial logs/binaries and explicitly reconstructed pre-correction source."""
import hashlib,io,json,shutil,tarfile
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[1]
out=P/'local-validation-initial'; out.mkdir(exist_ok=False)
names=['suite/src/cryptanalysis/ic_boundary.rs','suite/src/cryptanalysis/ic_framework/batch_mitm.rs','suite/examples/ic_affine_pipeline_probe.rs']
data={name:(ROOT/name).read_bytes() for name in names}
name=names[1]; text=data[name].decode()
addition='''        let mut staged_params = Params::default();
        staged_params.set("vector_prepare", "5");
        let mut staged = BinaryBatchMitmOracle::default();
        staged
            .prepare(&ctx, &empty, &staged_params, &mut GroupOps::default())
            .unwrap();
        assert_eq!(staged.table.as_ref().unwrap().entries, 0);
'''
assert text.count(addition)==1 and text.count('("vector_prepare", "6"),')==1
text=text.replace(addition,'').replace('("vector_prepare", "6"),','("vector_prepare", "5"),')
data[name]=text.encode()
with tarfile.open(out/'source-reconstructed.tar.gz','w:gz') as archive:
    for name,raw in data.items():
        item=tarfile.TarInfo(name); item.size=len(raw); archive.addfile(item,io.BytesIO(raw))
for name in ['local-counterfactual.log','local-framework.log']: shutil.copy2(P/name,out/name)
old_test=ROOT/'suite/target/debug/deps/cryptanalysis_suite-41506936d1e77cdf'
shutil.copy2(old_test,out/'test-binary')
prior_probe=ROOT/'suite/target/debug/examples/ic_affine_pipeline_probe'
prior_pin=json.loads((ROOT/'experiments/ic-static-witness-map-20261117/fresh-generation.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(prior_probe)==prior_pin['local_probe_sha256_observed_now']
shutil.copy2(prior_probe,out/'prior-static-identity-probe')
(out/'disposition.json').write_text(json.dumps(dict(status='local_correctness_test_expectation_failed',observed='3counterfactual tests pass; framework28pass1fail because the old invalid-range case expects strategy5 rejection.',correction='Strategy5 was prospectively admitted. Test rejection changes to6, and positive5 validation is added.',source_capture='Retrospective reconstruction from those exact two test edits. The attempted pre-correction snapshot command failed because the shell could not create an internal-volume here-document tempfile; original logs and test binary are retained, not overwritten. No contemporaneous source-hash receipt is asserted.',source_sha256={name:hashlib.sha256(raw).hexdigest() for name,raw in data.items()},initial_test_binary_sha256=sha(out/'test-binary'),prior_static_identity_probe_sha256=sha(out/'prior-static-identity-probe'),native_performance_data=False),indent=2)+'\n')
print('Initial logs and binaries retained; source reconstruction explicitly labeled')

from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
sources=['suite/examples/ic_affine_pipeline_probe.rs','suite/Cargo.toml','suite/Cargo.lock','suite/build.rs',
 'suite/src/cryptanalysis/s3_affine_projection.rs','suite/src/cryptanalysis/ic_framework/affine.rs',
 'suite/src/cryptanalysis/ic_framework/batch_mitm.rs','suite/src/cryptanalysis/ic_framework/mod.rs','suite/src/cryptanalysis/ic_framework/plugins.rs',
 'suite/src/cryptanalysis/ic_framework/u32_reciprocal.rs','suite/src/cryptanalysis/ic_framework/linalg.rs','suite/src/cryptanalysis/ic_boundary.rs','suite/src/cryptanalysis/ic_boundary/batched_walk.rs','suite/src/cryptanalysis/ic_framework/stages.rs',
 'suite/src/cryptanalysis/koblitz_fast.rs','suite/src/cryptanalysis/semaev_decomp.rs']
def hashes():
 old=json.loads((Path(__file__).resolve().parent/'baseline-source-hashes.json').read_text())
 overlay='suite/src/cryptanalysis/ic_boundary/batched_walk.rs'
 old[overlay]=hashlib.sha256((ROOT/overlay).read_bytes()).hexdigest()
 return old

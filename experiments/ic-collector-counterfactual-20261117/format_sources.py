#!/usr/bin/env python3
"""Format only the three owned source buffers, without child-module writes."""
import os,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[1]
for name in ['suite/src/cryptanalysis/ic_boundary.rs','suite/src/cryptanalysis/ic_framework/batch_mitm.rs','suite/examples/ic_affine_pipeline_probe.rs']:
    path=ROOT/name
    r=subprocess.run(['rustfmt','--edition','2021','--emit','stdout'],input=path.read_bytes(),capture_output=True,check=True,cwd=ROOT)
    tmp=path.with_name(path.name+'.counterfactual-format'); assert not tmp.exists()
    tmp.write_bytes(r.stdout); os.replace(tmp,path)
print('Formatted three owned source buffers')

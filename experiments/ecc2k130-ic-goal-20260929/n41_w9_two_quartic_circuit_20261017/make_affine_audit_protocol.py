"""Freeze independent Sage rank audit inputs."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
base=json.loads((here/"affine_protocol.json").read_text())
paths=[here/name for name in ("affine_audit_sage.py","affine_protocol.json",
                              "affine_result.json","sage_runtime_info.json")]
paths += [Path(base[key]) for key in ("support","states","support_audit")]
assert not (here/"affine_audit_protocol.json").exists()
out={"status":"FROZEN_BEFORE_SAGE_AFFINE_AUDIT",
     "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths},
     **{key:base[key] for key in ("support","states")}}
(here/"affine_audit_protocol.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")

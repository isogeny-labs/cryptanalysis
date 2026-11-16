"""Check original snapshot byte identity without executing an experiment."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def main():
    manifest=json.loads((ROOT/'SNAPSHOT_SHA256.json').read_text())
    snapshot=(ROOT/'snapshot').resolve()
    for name,entry in manifest['files'].items():
        path=(snapshot/name).resolve()
        if not path.is_relative_to(snapshot):raise ValueError(f'Escaping path: {name}')
        data=path.read_bytes()
        if len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:
            raise ValueError(f'Snapshot byte mismatch: {name}')
    print(f"Snapshot byte inventory matches: {len(manifest['files'])} files")


if __name__=='__main__':main()

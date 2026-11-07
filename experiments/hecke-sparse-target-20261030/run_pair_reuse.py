"""Retain all four prespecified pair-reuse attempts, including failures."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-root',type=Path,required=True);args=parser.parse_args()
    args.out_root.mkdir(parents=True,exist_ok=False)
    subprocess.run(['bash','scripts/checkpoint.sh','gate'],cwd=ROOT,check=True)
    failed=False
    for cell in ('f6-small-01','f6-medium-01','f6-large-01','f30-01'):
        directory=args.out_root/cell
        command=[sys.executable,str(HERE/'pair_reuse.py'),'--cell',cell,'--out',str(directory/'receipt.json')]
        start=time.monotonic()
        try:
            p=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=600)
            code,stdout,stderr=p.returncode,p.stdout,p.stderr
        except subprocess.TimeoutExpired as e:
            def text(value):return value.decode() if isinstance(value,bytes) else (value or '')
            code,stdout,stderr=124,text(e.stdout),text(e.stderr)+'\nTIMEOUT\n'
        directory.mkdir(parents=True,exist_ok=True)
        (directory/'stdout.txt').write_text(stdout)
        (directory/'stderr.txt').write_text(stderr)
        (directory/'launch.json').write_text(json.dumps(dict(command=command,cap_seconds=600,
                    exit_code=code,wall_seconds_diagnostic=time.monotonic()-start),indent=2)+'\n')
        print(stdout+stderr,flush=True)
        failed=failed or code!=0
    raise SystemExit(1 if failed else 0)


if __name__=='__main__':main()

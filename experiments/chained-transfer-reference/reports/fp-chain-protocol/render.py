from pathlib import Path
import subprocess
p=Path(__file__).resolve().parent
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
f=p/'flow.svg';f.write_text('\n'.join(x.rstrip() for x in f.read_text().splitlines())+'\n')

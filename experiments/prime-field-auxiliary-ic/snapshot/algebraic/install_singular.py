"""Optional unprivileged Singular installation on Debian 13.

Normally use your system package manager to install Singular, or set
SINGULAR_BIN to an existing executable. This helper extracts Debian packages
into algebraic/vendor/root and makes no system installation.
"""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent/'vendor'
packages=['singular-ui','singular-data','singular-modules','libsingular4m4n1',
          'libflint19','libntl44','libgf2x3','libcdd0t64']


def main():
    apt=Path('/usr/bin/apt-get')
    if not apt.exists():raise SystemExit('Install Singular for your platform and set SINGULAR_BIN.')
    state=ROOT/'apt/lists';cache=ROOT/'apt/cache'
    (state/'partial').mkdir(parents=True,exist_ok=True)
    (cache/'archives/partial').mkdir(parents=True,exist_ok=True)
    base=[str(apt),'-o',f'Dir::State::lists={state}','-o',f'Dir::Cache={cache}',
          '-o','Debug::NoLocking=true']
    subprocess.run(base+['update'],check=True)
    subprocess.run(base+['download']+packages,cwd=ROOT,check=True)
    for deb in ROOT.glob('*.deb'):
        subprocess.run(['dpkg-deb','-x',str(deb),str(ROOT/'root')],check=True)
    print('Local Singular extracted. solver.py supplies its library paths.')


if __name__=='__main__':main()

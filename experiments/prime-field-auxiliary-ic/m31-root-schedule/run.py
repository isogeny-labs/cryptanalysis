"""Build the native checked-root panel and emit CSV for one integer seed."""
from pathlib import Path
import subprocess
import sys
import tempfile

here = Path(__file__).resolve().parent
source = (here.parent / "m31-native-root" / "bench.cpp").read_text()
prefix, marker, _ = source.partition("int main()")
assert marker
with tempfile.TemporaryDirectory() as tmp:
    exe = Path(tmp) / "panel"
    subprocess.run(["clang++", "-O3", "-std=c++17", "-mcpu=native", "-Wall",
                    "-Wextra", "-Werror", "-I", here, here / "root.cpp",
                    "-x", "c++", "-", "-o", exe],
                   input=prefix + (here / "panel.inc").read_text(), text=True, check=True)
    subprocess.run([exe, str(int(sys.argv[1]))], check=True)

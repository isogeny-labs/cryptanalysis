"""Compare the ordered map and the selected representatives to Python."""
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from census import representatives, P

groups = representatives()
selected = [x for key, x in groups.items()
            if key < (inverse := pow(key, -1, P)) and inverse in groups]
for arg in sys.argv[1:]:
    helper = str(Path(arg).resolve())
    output = subprocess.check_output([helper, "--representatives"]).splitlines()
    rows = [tuple(map(int, line.split())) for line in output]
    if rows != list(groups.items()):
        raise ValueError(f"ordered map mismatch in {helper}")
    pairs = list(map(int, subprocess.check_output([helper]).splitlines()))
    if pairs != selected:
        raise ValueError(f"pair mismatch in {helper}")
    print(f"{helper}: {len(rows)} ordered entries and {len(pairs)} matching pairs")

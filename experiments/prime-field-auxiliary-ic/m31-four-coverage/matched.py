"""Reproduce the three sample bases from the published two-point comparison."""
import subprocess
import sys
from matched_bases import sample_basis, smooth_basis

arms=[smooth_basis()]
# Primary endpoint: simple five-letter classes modulo global sign.
# Fixed comparison: smooth versus 256 successive draws from the published pool.
panel = sys.argv[2:3] == ["five-panel"]
for seed in range(256 if panel else 3):
    arms.append(sample_basis(seed))
if panel:
    assert sys.argv[2:] in (["five-panel"], ["five-panel", "reverse"])
    print("arm,simple_five_classes")
    for label,arm in enumerate(arms):
        ordered=arm[::-1] if sys.argv[3:] else arm
        count=subprocess.check_output([sys.argv[1],"simple-five"],
            input="".join(f"{x}\n" for x in ordered),text=True)
        print(f"{label},{int(count)}",flush=True)
    sys.exit()
reverse=sys.argv[2:]==["reverse"]
assert reverse or len(sys.argv)==2
words=[str(x) for arm in arms for x in (reversed(arm) if reverse else arm)]
subprocess.run([sys.argv[1],"matched"],input="\n".join(words),text=True,check=True)

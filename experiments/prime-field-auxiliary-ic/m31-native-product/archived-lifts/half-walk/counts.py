"""Count inversions executed by each public chain implementation outside timing."""
import csv
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
src = "experiments/prime-field-auxiliary-ic/snapshot/prepare.py"
old = subprocess.check_output(["git","show",f"61655fc9f:{src}"],cwd=here)
new = (here.parents[2]/"snapshot/prepare.py").read_bytes()
writer = csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("depth","method","inversions","add_calls"))
for depth in (1,5,8,10,12):
    for arm,source in (("walk",old),("half",new)):
        ns = {"__name__":"public_chain","__file__":src}
        exec(compile(source,src,"exec"),ns)
        counts = [0,0]
        add = ns["Curve"].add
        def count_add(curve,left,right):
            counts[1] += 1
            return add(curve,left,right)
        def count_pow(base,n,p):
            counts[0] += n == -1
            return pow(base,n,p)
        ns["Curve"].add = count_add
        ns["pow"] = count_pow
        ns["chain"](2**31-1,depth,enumerate_all=True)
        writer.writerow((depth,arm,*counts))

"""Generate the Boolean threshold model of the Rust network_sort schedule."""
import re
from pathlib import Path

directory = Path(__file__).resolve().parent
source = (directory / "packed-lift.rs").read_text()
body = source.split("fn network_sort(", 1)[1].split("{", 1)[1].split("}", 1)[0]
lines = [
    "import Std.Tactic.BVDecide",
    "namespace M31Network",
    "abbrev Lanes := BitVec 64",
    "def network (input : Lanes) : Lanes :=",
    "  let x := input",
]
for call in body.strip().splitlines():
    match = re.fullmatch(r"stage::<(\d+),\s*(\d+)>\(keys\);", call.strip())
    if not match:
        raise ValueError(f"Unrecognized comparator stage: {call}")
    block, stride = map(int, match.groups())
    if not 0 < stride < block <= 64 or any(v & (v - 1) for v in (stride, block)):
        raise ValueError(f"Invalid bitonic stage: {call}")
    ascending = descending = 0
    for chunk in range(0, 64, 2 * stride):
        for lane in range(chunk, chunk + stride):
            if lane & block:
                descending |= 1 << lane
            else:
                ascending |= 1 << lane
    lines.extend([
        f"  let lower := x &&& (x >>> {stride})",
        f"  let upper := x ||| (x >>> {stride})",
        f"  let x := (lower &&& {ascending}) ||| (upper &&& {descending}) ||| "
        f"(((upper &&& {ascending}) ||| (lower &&& {descending})) <<< {stride})",
    ])
lines.extend([
    "  x",
    "set_option maxRecDepth 8192 in",
    "theorem ordered (input : Lanes) :",
    "    ((network input <<< 1) &&& ~~~(network input)) = 0 := by",
    "  unfold network",
    "  bv_decide (config := {timeout := 120})",
    "end M31Network",
])
(directory / "NetworkBits.lean").write_text("\n".join(lines) + "\n")

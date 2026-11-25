"""Check affine and projective outcomes on the frozen M31 auxiliary chain."""
import json
import random
import subprocess

SNAPSHOT = "f9c7b49e7:experiments/prime-field-auxiliary-ic/snapshot/"

def evaluate(x, maps, c, p, *, projective):
    n, d = x, 1
    for i, m in enumerate(maps):
        u = (n - m["r"] * d) % p
        if u == 0:
            return "pole", i
        if projective:
            ud = u * d % p
            n, d = (u*u + m["A"]*ud + m["B"]*(d*d % p)) % p, ud
        else:
            n = (u + m["A"] + m["B"] * pow(u, -1, p)) % p
    return ("root" if (n - c*d) % p == 0 else "nonroot"), len(maps)

def main():
    def read(name):
        return subprocess.check_output(["git", "show", SNAPSHOT + name], text=True)

    archived = {"__file__": "prepare.py", "__name__": "archived"}
    exec(compile(read("prepare.py"), "prepare.py", "exec"), archived)
    chain = json.loads(read("auxiliary_31.json"))
    p, maps, c = chain["p"], chain["maps"], chain["terminal_c"]
    curve = archived["Curve"](p, a4=1)
    start = tuple(chain["auxiliary_generator"])
    generator = tuple(chain["kernel_generator"])
    def check(x):
        reference = evaluate(x, maps, c, p, projective=False)
        actual = evaluate(x, maps, c, p, projective=True)
        if actual != reference:
            raise ValueError((x, reference, actual))
        return actual

    point = start
    roots = set()
    for _ in range(chain["kernel_order"]):
        assert check(point[0]) == ("root", len(maps))
        roots.add(point[0])
        point = curve.add(point, generator)
    assert point == start and len(roots) == chain["kernel_order"]
    for i in range(len(maps)):
        point = curve.mul(chain["kernel_order"] >> (i+1), generator)
        assert check(point[0]) == ("pole", i)
    rng = random.Random(310028)
    nonroots = set()
    while len(nonroots) < 4096:
        x = rng.randrange(p)
        if check(x)[0] == "nonroot":
            nonroots.add(x)
    print(f"{len(roots)} roots, {len(maps)} distinct pole stages, {len(nonroots)} nonroots")

if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("Replay requires Python assertions.")
    main()

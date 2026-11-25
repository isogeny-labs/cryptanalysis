import json, subprocess, time, math
from sympy import isprime, nextprime

# L15: hold log(largest prime factor of p-1) fixed while varying p.
# p = m*q + 1 with q a fixed 28-bit prime and m near 2^(b-28).
QBITS = 28
q = int(nextprime(2 ** (QBITS - 1)))
rows = []
for bits in (40, 44, 48, 52):
    target_m = 1 << (bits - QBITS)
    m = target_m if target_m % 2 == 0 else target_m + 1
    while True:
        p = m * q + 1
        if p.bit_length() == bits and isprime(p):
            break
        m += 2
    g = 3
    x = 123456789
    h = pow(g, x, p)
    t0 = time.time()
    try:
        out = subprocess.run(["./build/ca", "ic", "--p", str(p), "--g", str(g),
                              "--h", str(h), "--verbose"],
                             capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        rows.append(dict(bits=bits, p=p, q=q, timeout=True))
        print(json.dumps(rows[-1]), flush=True)
        continue
    wall = time.time() - t0
    js = None
    used_ic = False
    for line in (out.stdout + out.stderr).splitlines():
        if "mod " in line and "active" in line:
            used_ic = True
        s = line.strip()
        if s.startswith("{"):
            js = json.loads(s)
    rec = dict(bits=bits, p=p, q=q, q_bits=q.bit_length(), mq=m,
               wall=round(wall, 3), ic_path=used_ic,
               **{k: (js or {}).get(k) for k in
                  ("status", "factor_base", "unknowns", "relations",
                   "sieve_seconds", "linalg_seconds", "total_seconds",
                   "lanczos_iterations")})
    rows.append(rec)
    print(json.dumps(rec), flush=True)

json.dump(rows, open("/Volumes/SSD990/llm/tmp/opencode/ic_l15.json", "w"), indent=1)
ok = [r for r in rows if r.get("total_seconds")]
if len(ok) >= 2:
    xs = [math.log(r["p"]) for r in ok]
    ys = [math.log(r["total_seconds"]) for r in ok]
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    a = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    print(f"fitted total ~ p^{a:.3f} at fixed q_bits={QBITS} over {n} points")

import json, subprocess, time, math
from sympy import isprime, nextprime

# L16: fix p at 56 bits, vary q_bits = log2(largest prime factor of p-1).
BITS = 56
ROWS = []
for qbits in (20, 24, 28, 32, 36):
    q = int(nextprime(2 ** (qbits - 1)))
    target_m = 1 << max(2, BITS - qbits)
    m = target_m if target_m % 2 == 0 else target_m + 1
    found = None
    for _ in range(4000):
        p = m * q + 1
        if p.bit_length() == BITS and isprime(p):
            found = p
            break
        m += 2
    if found is None:
        print(json.dumps({"q_bits": qbits, "error": "no prime"}), flush=True)
        continue
    p = found
    g, x = 3, 123456789
    h = pow(g, x, p)
    t0 = time.time()
    try:
        out = subprocess.run(["/Volumes/SSD990/cryptanalysis/build/ca", "ic",
                              "--p", str(p), "--g", str(g), "--h", str(h), "--verbose"],
                             capture_output=True, text=True, timeout=1200)
    except subprocess.TimeoutExpired:
        rec = dict(q_bits=qbits, q=q, p=p, timeout=True, wall=round(time.time() - t0, 1))
        ROWS.append(rec); print(json.dumps(rec), flush=True)
        continue
    wall = time.time() - t0
    js = None
    for line in (out.stdout + out.stderr).splitlines():
        s = line.strip()
        if s.startswith("{"):
            js = json.loads(s)
    rec = dict(q_bits=qbits, q=q, p=p, m=m, wall=round(wall, 3),
               **{k: (js or {}).get(k) for k in
                  ("status", "factor_base", "relations", "sieve_seconds",
                   "linalg_seconds", "total_seconds", "lanczos_iterations")})
    ROWS.append(rec); print(json.dumps(rec), flush=True)

json.dump(ROWS, open("/Volumes/SSD990/llm/tmp/opencode/ic_l16.json", "w"), indent=1)
ok = [r for r in ROWS if r.get("total_seconds")]
if len(ok) >= 2:
    xs = [math.log(r["q"]) for r in ok]
    ys = [math.log(r["total_seconds"]) for r in ok]
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    a = sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / sum((x-mx)**2 for x in xs)
    print(f"fitted total ~ q^{a:.3f} at fixed p_bits={BITS} over {n} points")
    # also fit linalg alone
    ls = [math.log(max(r["linalg_seconds"], 1e-9)) for r in ok]
    my2 = sum(ls)/n
    a2 = sum((x-mx)*(y-my2) for x, y in zip(xs, ls)) / sum((x-mx)**2 for x in xs)
    print(f"fitted linalg ~ q^{a2:.3f}")

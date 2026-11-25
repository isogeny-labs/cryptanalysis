import json, subprocess, time, statistics
from sympy import isprime, nextprime

# L26: bracket the 36 -> 47 bit threshold at fixed p = 56 bits.
# 5 repeats per cell; each run capped at 300 s.
BITS = 56
REPEATS = 5
ROWS = []
for qbits in (36, 40, 44, 46):
    q = int(nextprime(2 ** (qbits - 1)))
    target_m = 1 << max(2, BITS - qbits)
    m = target_m if target_m % 2 == 0 else target_m + 1
    p = None
    for _ in range(20000):
        cand = m * q + 1
        if cand.bit_length() == BITS and isprime(cand):
            p = cand; break
        m += 2
    if p is None:
        print(json.dumps({"q_bits": qbits, "error": "no prime"}), flush=True)
        continue
    g, x = 3, 123456789
    h = pow(g, x, p)
    times, lin, iters, tos = [], [], [], 0
    for rep in range(REPEATS):
        t0 = time.time()
        try:
            out = subprocess.run(["/Volumes/SSD990/cryptanalysis/build/ca", "ic",
                                  "--p", str(p), "--g", str(g), "--h", str(h), "--verbose"],
                                 capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            tos += 1
            times.append(300.0)
            continue
        wall = time.time() - t0
        js = None
        for line in (out.stdout + out.stderr).splitlines():
            s = line.strip()
            if s.startswith("{"):
                js = json.loads(s)
        times.append(wall)
        if js:
            lin.append(js.get("linalg_seconds"))
            iters.append(js.get("lanczos_iterations"))
    rec = dict(q_bits=qbits, q=q, p=p, m=m, repeats=REPEATS, timeouts=tos,
               median_wall=round(statistics.median(times), 3),
               min_wall=round(min(times), 3), max_wall=round(max(times), 3),
               median_linalg=round(statistics.median(lin), 3) if lin else None,
               iters=iters)
    ROWS.append(rec)
    print(json.dumps(rec), flush=True)

json.dump(ROWS, open("/Volumes/SSD990/llm/tmp/opencode/ic_l26.json", "w"), indent=1)

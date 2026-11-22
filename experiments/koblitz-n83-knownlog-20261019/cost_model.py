#!/usr/bin/env python3
"""Choose the known-log arm's orbit count K before any timing (`analysis/cost_model.json`).

A known-log base has no rank stage and no linear algebra, so its end-to-end
cold cost is generation + setup + one-target online:

    C(K) = gen(K) + base_load(K) + basis + index(K) + selftest(K) + verify(K) + fixed + online(K)

* online(K) = P(K) * ns_probe, with the archived probe law
  P(K) = r / (166 * 83 * K^2) (2,400 rank attempts of run 39214027289 average
  0.9785 of it at K = 600) and ns_probe the cP online cost per probe of that
  run (222.2 ns);
* index(K) and selftest(K) scale with the 83 K^2 logical states, base_load
  and verify (K scalar multiplications) with K; their K = 600 values are
  the run's cP means (`inputs/power_prior.json`);
* gen(K) is the generator's own clock (local, `smoke/`), linear in K.

Model A is the pure scaling above. Model B (sensitivity) also lets the
per-state index cost and the per-probe cost fall with the table size, with
the exponents of the local K220 / K600 smoke (`smoke/smoke_local.json`).
Both models are minimised over integer K; the frozen K_opt is the even
multiple of 10 nearest model A's minimum. Prediction, not a measurement.
"""

import json
import math
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "inputs" / "power_prior.json"
SMOKE = HERE / "smoke" / "smoke_local.json"
OUT = HERE / "analysis" / "cost_model.json"
R = 8569786107849059


def law(k):
    return R / (166 * 83 * k * k)


def constants():
    prior = json.loads(PRIOR.read_text())
    cold = prior["cold_cP"]
    mean = {key: statistics.mean(c[key] for c in cold) for key in
            ("base_load_ms", "basis_ms", "index_ms", "log_load_and_verify_ms", "scan_selftest_ms",
             "setup_complete_ms", "cold_ms", "online_ms", "probes")}
    attempts = [p for block in prior["rank_kP"] for p in block["attempt_probes"]]
    rho = prior["rho_rT"]
    ms_per_step = sum(r["online_ms"] for r in rho) / sum(r["steps"] for r in rho)
    smoke = json.loads(SMOKE.read_text())
    gen = {int(k): v["gen_ms_median"] for k, v in smoke["generator"].items()}
    (k1, g1), (k2, g2) = sorted(gen.items())
    local = smoke["producer_q0"]
    lo, hi = local["220"], local["600"]
    alpha = math.log((lo["index_ms"] / hi["index_ms"]) / (220 / 600) ** 2) / math.log(220 / 600)
    beta = math.log((lo["online_ms"] / lo["probes"]) / (hi["online_ms"] / hi["probes"])) / math.log(220 / 600)
    return {
        "K0": 600,
        "base_load_ms": mean["base_load_ms"], "basis_ms": mean["basis_ms"], "index_ms": mean["index_ms"],
        "scan_selftest_ms": mean["scan_selftest_ms"], "verify_ms": mean["log_load_and_verify_ms"],
        "fixed_ms": mean["setup_complete_ms"] - (mean["base_load_ms"] + mean["basis_ms"] + mean["index_ms"] +
                                                 mean["log_load_and_verify_ms"] + mean["scan_selftest_ms"]),
        "ns_per_probe_online": mean["online_ms"] * 1e6 / mean["probes"],
        "probe_law_ratio_rank_attempts": statistics.mean(attempts) / law(600),
        "rank_attempts": len(attempts),
        "gen_ms_slope": (g2 - g1) / (k2 - k1), "gen_ms_intercept": g1 - (g2 - g1) / (k2 - k1) * k1,
        "local_index_state_exponent": alpha, "local_probe_cost_exponent": beta,
        "rho_ms_per_step": ms_per_step, "rho_mean_cold_ms": statistics.mean(r["cold_ms"] for r in rho),
        "sqrt_r": math.sqrt(R),
    }


def cost(k, c, model):
    x = k / c["K0"]
    a = c["local_index_state_exponent"] if model == "B" else 0.0
    b = c["local_probe_cost_exponent"] if model == "B" else 0.0
    parts = {
        "gen": c["gen_ms_intercept"] + c["gen_ms_slope"] * k,
        "base_load": c["base_load_ms"] * x,
        "basis": c["basis_ms"],
        "index": c["index_ms"] * x ** (2 + a),
        "selftest": c["scan_selftest_ms"] * x ** 2,
        "verify": c["verify_ms"] * x,
        "fixed": c["fixed_ms"],
        "online": law(k) * c["ns_per_probe_online"] * x ** b / 1e6,
    }
    return sum(parts.values()), parts


def main():
    c = constants()
    unit = c["rho_ms_per_step"] * c["sqrt_r"]
    out = {"schema": 1, "constants": c, "probe_law": "P(K) = r / (166 * 83 * K^2)", "models": {}}
    for model in ("A", "B"):
        grid = {k: cost(k, c, model)[0] for k in range(100, 901)}
        k_star = min(grid, key=grid.get)
        out["models"][model] = {"K_star": k_star, "cost_ms_at_K_star": grid[k_star],
                                "curve_ms": {str(k): round(grid[k], 3) for k in range(100, 901, 10)}}
    k_a = out["models"]["A"]["K_star"]
    k_opt = int(round(k_a / 20.0)) * 20
    out["K_opt"] = k_opt
    out["K_opt_rule"] = "the even multiple of 10 nearest model A's integer minimum (multiples of 20)"
    for model in ("A", "B"):
        m = out["models"][model]
        total, parts = cost(k_opt, c, model)
        m["cost_ms_at_K_opt"] = total
        m["parts_ms_at_K_opt"] = parts
        m["K_opt_over_min"] = total / m["cost_ms_at_K_star"]
        m["predicted_S_e2e_at_K_opt"] = total / unit
        m["predicted_gap_to_rT_at_K_opt"] = total / c["rho_mean_cold_ms"]
        t600, p600 = cost(600, c, model)
        m["cost_ms_at_K600"] = t600
        m["parts_ms_at_K600"] = p600
        m["predicted_gap_to_rT_at_K600"] = t600 / c["rho_mean_cold_ms"]
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"K_opt": k_opt, "A": {k: out["models"]["A"][k] for k in ("K_star", "cost_ms_at_K_star",
                                                                              "cost_ms_at_K_opt", "cost_ms_at_K600",
                                                                              "predicted_gap_to_rT_at_K_opt")},
                      "B": {k: out["models"]["B"][k] for k in ("K_star", "cost_ms_at_K_star", "cost_ms_at_K_opt",
                                                              "K_opt_over_min", "predicted_gap_to_rT_at_K_opt")}},
                     indent=1))


if __name__ == "__main__":
    main()

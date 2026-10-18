#!/usr/bin/env python3
"""Frozen, CPU-only Boolean correctness controls. Not a performance benchmark.

All generated files stay beside this adapter. Existing source is read only.
Dinur's parity component is explicitly separated from full search.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import platform
import random
import resource
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PDP = REPO / "experiments/pdp-scaling"
sys.path.insert(0, str(PDP))
import sumpoly
import boolean_f5b
from descend import descend, verify_solution, Instance
from gf2n import GF2n, Curve, Point
from boolean_basis import certify_boolean_basis

boolean_f5b.native_interreduce = None  # Python reference; no hidden JIT/native path.
sumpoly.CACHE = HERE / "sources/sumpoly_cache.pkl"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def write_new(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def poly_eval(terms, assignment):
    return sum(mask & assignment == mask for mask in terms) & 1


def truth_roots(equations, nvars):
    # Independent bitset truth tables, not solver-supplied roots.
    size = 1 << nvars
    all_bits = (1 << size) - 1
    variables = []
    for j in range(nvars):
        step = 1 << j
        word = ((1 << step) - 1) << step
        width = 2 * step
        while width < size:
            word |= word << width
            width *= 2
        variables.append(word)
    monomials = [all_bits]
    for mask in range(1, size):
        bit = mask & -mask
        monomials.append(monomials[mask ^ bit] & variables[bit.bit_length() - 1])
    nonroots = 0
    for polynomial in equations:
        evaluated = 0
        for mask in polynomial:
            evaluated ^= monomials[mask]
        nonroots |= evaluated
    roots = all_bits ^ nonroots
    return roots, monomials


def order_layout(nvars, blocks, name):
    natural = list(range(nvars))
    reversed_vars = list(reversed(natural))
    interleaved = [block[j] for j in range(max(map(len, blocks)))
                   for block in blocks if j < len(block)]
    first = [v for block in blocks[:max(1, len(blocks)//2)] for v in block]
    second = [v for v in natural if v not in first]
    def subkey(mask, variables):
        bits = sum(((mask >> v) & 1) << i for i, v in enumerate(variables))
        return (bits.bit_count(), -bits)
    weights = [1] * nvars
    for j, block in enumerate(blocks):
        for v in block:
            weights[v] = 1 + j
    if name == "grevlex-natural":
        key = lambda mask: subkey(mask, natural)
    elif name == "grevlex-reversed-permutation":
        key = lambda mask: subkey(mask, reversed_vars)
    elif name == "grevlex-interleaved-permutation":
        key = lambda mask: subkey(mask, interleaved)
    elif name == "block-eliminate-first-half":
        key = lambda mask: (subkey(mask, first), subkey(mask, second))
    elif name == "block-eliminate-second-half":
        key = lambda mask: (subkey(mask, second), subkey(mask, first))
    elif name == "weighted-grevlex":
        key = lambda mask: (sum(weights[v] for v in natural if mask >> v & 1), -mask)
    else:
        raise ValueError(name)
    layout = sorted(range(1 << nvars), key=key)
    return layout, {"name":name,"blocks":blocks,"weights":weights,
                    "layout_sha256":digest(layout),"first_elimination_block":first,
                    "second_elimination_block":second}


class OrderedF5(boolean_f5b.BooleanF5B):
    def __init__(self, nvars, blocks, name, **kwargs):
        super().__init__(nvars, **kwargs)
        layout, self.order_record = order_layout(nvars, blocks, name)
        self._mask_by_rank = tuple(layout)
        ranks = [0] * (1 << nvars)
        for j, mask in enumerate(layout):
            ranks[mask] = j
        self._rank_by_mask = tuple(ranks)
        self.constant_one = 1 << ranks[0]
        self.max_observed_degree = 0
        self.materialized_product_rows = 0
        self.materialized_product_nnz = 0
        self.observed_monomials = set()

    def track(self, polynomial):
        terms = list(self.terms(polynomial))
        self.max_observed_degree = max(self.max_observed_degree,
                                      max(map(int.bit_count, terms), default=0))
        self.observed_monomials.update(terms)
        return polynomial

    def from_terms(self, terms):
        return self.track(super().from_terms(terms))

    def multiply_monomial(self, polynomial, monomial):
        product = super().multiply_monomial(polynomial, monomial)
        self.materialized_product_rows += 1
        self.materialized_product_nnz += product.bit_count()
        return self.track(product)

    def add(self, left, right):
        return self.track(left ^ right)


def certify_order(equations, basis, engine):
    roots, monomials = truth_roots(equations, engine.nvars)
    root_count = roots.bit_count()
    basis_roots, _ = truth_roots(basis, engine.nvars)
    leading = [engine.leading(engine.from_terms(g)) for g in basis]
    forbidden = 0
    for lm in leading:
        forbidden |= monomials[lm]
    standard = ((1 << (1 << engine.nvars)) - 1) ^ forbidden
    minimal = all(not any(i != j and other & lm == other
                          for j, other in enumerate(leading))
                  for i, lm in enumerate(leading))
    tails_standard = all(all(mask == lm or (standard >> mask) & 1 for mask in g)
                         for g, lm in zip(basis, leading))
    packed = [engine.from_terms(g) for g in basis]
    rows = engine.reduction_table(packed)
    source_remainders_zero = all(not engine.normal_form(engine.from_terms(g), packed, rows)
                                 for g in equations)
    all_pairs_zero = engine.is_groebner(packed, rows)
    return {"verified": roots == basis_roots and standard.bit_count() == root_count
            and minimal and tails_standard and source_remainders_zero and all_pairs_zero,
            "exact_root_equality":roots == basis_roots,"root_count":root_count,
            "standard_monomials":standard.bit_count(),"reduced":minimal and tails_standard,
            "source_generators_reduce_to_zero":source_remainders_zero,
            "ordinary_and_boolean_field_pairs_zero":all_pairs_zero,
            "roots_sha256":hashlib.sha256(roots.to_bytes((1 << engine.nvars)//8 + 1,"little")).hexdigest()}


def f5_worker(pipe, case, order, protocol):
    resource.setrlimit(resource.RLIMIT_AS, (protocol["memory_limit_bytes"],)*2)
    try:
        engine = OrderedF5(case["nvars"], case["blocks"], order,
                           timeout=protocol["solver_timeout_seconds"],
                           max_pairs=protocol["solver_critical_pair_budget"])
        generators = [engine.from_terms(g) for g in case["equations"] if g]
        basis_packed = engine.basis(generators)
        basis = [sorted(engine.terms(p)) for p in basis_packed]
        solve_stats = dict(engine.stats)
        observed = {"max_materialized_degree":engine.max_observed_degree,
                    "product_rows_requested":engine.materialized_product_rows,
                    "product_nnz_requested":engine.materialized_product_nnz,
                    "observed_columns":len(engine.observed_monomials),
                    "allocated_column_universe":1 << case["nvars"]}
        certificate = certify_order(case["equations"], basis, engine)
        pipe.send({"status":"complete" if certificate["verified"] else "verification-failed",
                   "basis":basis,"stats":solve_stats,"observed":observed,
                   "certificate":certificate,"order":engine.order_record,
                   "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    except BaseException as error:
        pipe.send({"status":"timeout" if isinstance(error,TimeoutError) else "error",
                   "error":repr(error),"traceback":traceback.format_exc()})
    finally:
        pipe.close()


def bounded_f5(case, order, protocol):
    parent, child = mp.Pipe(False)
    process = mp.Process(target=f5_worker,args=(child,case,order,protocol))
    process.start()
    child.close()
    if not parent.poll(protocol["solver_timeout_seconds"] + 10):
        process.terminate()
        process.join()
        return {"status":"timeout","error":"supervisor deadline"}
    try:
        result = parent.recv()
    except EOFError:
        result = {"status":"error","error":"worker exited without result","exitcode":process.exitcode}
    process.join(5)
    if process.is_alive():
        process.terminate()
        process.join()
    parent.close()
    return result


def export_direct(n, m, ell, law, seed, polynomials):
    rng = random.Random(seed)
    field, equations = GF2n(n), []
    curve = Curve(field,1)
    usable = [curve.lift_x(x) for x in range(1 << ell)]
    usable = [p for p in usable if p is not None]
    points = None
    if law.startswith("planted"):
        for _ in range(10000):
            points = rng.sample(usable,m) if len(usable) >= m else rng.choices(usable,k=m)
            points = [curve.neg(p) if rng.getrandbits(1) else p for p in points]
            target = curve.sum(points)
            if not target.inf:
                break
        else:
            raise RuntimeError("bounded planted-target construction exhausted")
    else:
        target = curve.random_point(rng)
    anf = descend(polynomials,field,curve,m,ell,target.x)
    for bit in range(n):
        equations.append(sorted(mask for mask, coeff in anf.items() if coeff >> bit & 1))
    return {"kind":"direct-Semaev","n":n,"m":m,"ell":ell,"nvars":m*ell,
            "field_modulus":field.mod,"curve":{"a2":0,"b":1},"subgroup":None,
            "subgroup_note":"full curve fixture, not an odd-prime subgroup IC measurement",
            "xR":target.x,"target":{"x":target.x,"y":target.y},
            "target_law":law,"seed":seed,"usable_factor_base_x":sorted(p.x for p in usable),
            "planted_points":None if points is None else [{"x":p.x,"y":p.y} for p in points],
            "planted_distinct_x":None if points is None else len({p.x for p in points}) == m,
            "equations":equations,"blocks":[list(range(i*ell,(i+1)*ell)) for i in range(m)],
            "input_max_degree":max(map(int.bit_count,anf),default=0)}


def export_chain(law, seed):
    # The tiny degree-four fixture has repeated factor-base points. It is a
    # correctness control only, not evidence on realistic m=4 decomposition.
    n, ell, m = 3, 1, 4
    field, curve = GF2n(n), Curve(GF2n(n),1)
    points = [curve.lift_x(x) for x in [1,1,1,0]]
    target = curve.sum(points) if law.startswith("planted") else curve.random_point(random.Random(seed))
    nv = m*ell + (m-2)*n
    def value(variable):
        if variable == "R":
            return {0:target.x}
        start, width = variable
        return {1 << (start+j):1 << j for j in range(width)}
    def multiply(left,right):
        out={}
        for a,ac in left.items():
            for b,bc in right.items():
                out[a|b]=out.get(a|b,0)^field.mul(ac,bc)
        return {a:c for a,c in out.items() if c}
    def square(poly):
        return {a:field.sqr(c) for a,c in poly.items()}
    def s3(a,b,c):
        a,b,c=value(a),value(b),value(c)
        out={0:1}
        for term in [multiply(square(a),square(b)),multiply(square(a),square(c)),
                     multiply(square(b),square(c)),multiply(multiply(a,b),c)]:
            for mask,coeff in term.items():
                out[mask]=out.get(mask,0)^coeff
        return [sorted(mask for mask,coeff in out.items() if coeff >> k & 1) for k in range(n)]
    xs=[(i,1) for i in range(4)]
    u1,u2=(4,3),(7,3)
    equations=s3(xs[0],xs[1],u1)+s3(u1,xs[2],u2)+s3(u2,xs[3],"R")
    return {"kind":"chained-S3","n":n,"m":m,"ell":ell,"nvars":nv,
            "field_modulus":field.mod,"curve":{"a2":0,"b":1},"subgroup":None,
            "xR":target.x,"target":{"x":target.x,"y":target.y},
            "target_law":law,"seed":seed,"degenerate_repeated_points":True,
            "equations":equations,"blocks":[[0],[1],[2],[3],[4,5,6],[7,8,9]],
            "input_max_degree":max((mask.bit_count() for g in equations for mask in g),default=0)}


def group_roots(case, roots):
    field=GF2n(case["n"],case["field_modulus"])
    curve=Curve(field,1)
    target=Point(case["target"]["x"],case["target"]["y"])
    unique_x=set()
    for assignment in range(1 << case["nvars"]):
        if roots >> assignment & 1:
            unique_x.add(tuple((assignment >> (i*case["ell"])) & ((1 << case["ell"])-1)
                               for i in range(case["m"])))
    valid=0
    for xs in unique_x:
        points=[curve.lift_x(x) for x in xs]
        if any(p is None for p in points):
            continue
        for signs in range(1 << case["m"]):
            total=curve.sum([curve.neg(p) if signs >> j & 1 else p for j,p in enumerate(points)])
            if not total.inf and total.x == target.x:
                valid += 1
                break
    return {"algebraic_root_count":roots.bit_count(),"distinct_factor_x_tuples":len(unique_x),
            "group_verified_factor_x_tuples":valid,
            "note":"Algebraic roots may fail point lifting or correspond to degenerate summation-polynomial components."}


def ideal_rows(equations, nv, degree, layout):
    rank={mask:i for i,mask in enumerate(layout)}
    for g in equations:
        for multiplier in [0]+[1 << j for j in range(nv)]:
            product=set()
            for monomial in g:
                product.symmetric_difference_update([monomial | multiplier])
            assert max(map(int.bit_count,product),default=0) <= degree
            yield sum(1 << rank[mask] for mask in product)


def eliminate(rows, trace=None):
    pivots={}
    learned=[]
    xors=0
    comparisons=0
    for i,original in enumerate(rows):
        row=original
        actions=[]
        if trace is not None:
            expected=trace[i]
            for pivot in expected[0]:
                comparisons += 1
                if not row or row.bit_length()-1 != pivot or pivot not in pivots:
                    return None,{"xor_rows":xors,"comparisons":comparisons,"divergence_row":i},None
                row ^= pivots[pivot]
                xors += 1
            comparisons += 1
            if (row.bit_length()-1 if row else None) != expected[1]:
                return None,{"xor_rows":xors,"comparisons":comparisons,"divergence_row":i},None
            if row:
                pivots[row.bit_length()-1]=row
        else:
            while row:
                pivot=row.bit_length()-1
                comparisons += 1
                if pivot not in pivots:
                    pivots[pivot]=row
                    break
                row ^= pivots[pivot]
                actions.append(pivot)
                xors += 1
            learned.append([actions,row.bit_length()-1 if row else None])
    # Canonical reduced row space (same column order) independent of row trace.
    canonical_rows=dict(pivots)
    for pivot in sorted(canonical_rows):
        for high in sorted(canonical_rows):
            if high > pivot and canonical_rows[high] >> pivot & 1:
                canonical_rows[high] ^= canonical_rows[pivot]
                xors += 1
    return [canonical_rows[j] for j in sorted(canonical_rows)],{
        "rank":len(pivots),"xor_rows":xors,"comparisons":comparisons,
        "zero_rows":len(rows)-len(pivots),"divergence_row":None},learned


def downset(n, n1, w):
    low=n-n1
    return [y | (z << low) for z in range(1 << n1)
            for y in range(1 << low) if y.bit_count() <= w]


def transform(values, domain, nv, stats):
    domain_set=set(domain)
    for bit in range(nv):
        b=1 << bit
        for mask in domain:
            if mask & b:
                assert mask ^ b in domain_set
                values[mask] ^= values[mask ^ b]
                stats["mobius_xors"] += 1
    return values


def dinur_mult_parity(equations, nv, n1, w, degree, rng, stats):
    """Dinur 2020 Algorithm 2, keeping N,d fixed across recursion.

    Dense arrays store downsets for simplicity; operations only visit the
    declared downset. No asymptotic memory improvement is claimed.
    """
    stats["recursive_calls"] += 1
    n2=math.floor(n1-nv/5)
    w=min(w,nv-n1)
    ys=[x for x in range(1 << (nv-n1)) if x.bit_count() <= w]
    if n2 <= 0:
        stats["base_calls"] += 1
        domain=downset(nv,n1,w)
        satisfied={x:1 for x in domain}
        for polynomial in equations:
            values={x:int(x in polynomial) for x in domain}
            transform(values,domain,nv,stats)
            for x in domain:
                satisfied[x] &= 1 ^ values[x]
                stats["base_and_operations"] += 1
        return {y:sum(satisfied[y | (z << (nv-n1))] for z in range(1 << n1)) & 1
                for y in ys}
    ell=n2+2
    repeats=48*nv+1
    eval_domain=downset(nv-n2,n1-n2,w)
    score={x:0 for x in eval_domain}
    for _ in range(repeats):
        mixed=[]
        for _ in range(ell):
            combination=set()
            for polynomial in equations:
                stats["random_coefficient_bits"] += 1
                if rng.getrandbits(1):
                    combination.symmetric_difference_update(polynomial)
                    stats["anf_term_xors"] += len(polynomial)
            mixed.append(combination)
        bound=min(degree*ell-n2,nv-n2)
        evaluations=dinur_mult_parity(mixed,nv,n2,bound,degree,rng,stats)
        coefficients=transform(dict(evaluations),list(evaluations),nv-n2,stats)
        values={x:coefficients.get(x,0) for x in eval_domain}
        # Evaluation downset includes all submasks of each requested point.
        transform(values,eval_domain,nv-n2,stats)
        for x,value in values.items():
            score[x] += value
            stats["scoreboard_additions"] += 1
    out={}
    for y in ys:
        parity=0
        for u in range(1 << (n1-n2)):
            parity ^= score[y | (u << (nv-n1))] > repeats//2
            stats["majority_reads"] += 1
        out[y]=int(parity)
    return out


def run_dinur(case):
    nv=case["nvars"]
    stats=Counter()
    n1=nv//2
    result=dinur_mult_parity([set(g) for g in case["equations"]],nv,n1,nv-n1,
                            case["input_max_degree"],random.Random(case["seed"]),stats)
    expected={y:sum(all(poly_eval(g,y | (z << (nv-n1))) == 0 for g in case["equations"])
                    for z in range(1 << n1)) & 1 for y in range(1 << (nv-n1))}
    return {"status":"verified" if result == expected else "verification-failed",
            "component":"Dinur Algorithm 2 multiple parity counting, not full search",
            "nvars":nv,"input_degree":case["input_max_degree"],"n1":n1,
            "lambda":"1/5","kappa":"1/2","repetitions":48*nv+1,
            "stats":dict(stats),"full_partial_parity_vector":result,
            "exhaustive_partial_parity_vector":expected,
            "total_parity":sum(result.values()) & 1,
            "search_reduction_calls_included":False,"solver_exponent_c":None}


def run(out):
    protocol=json.loads((HERE/"protocol.json").read_text())
    out.mkdir(parents=True,exist_ok=False)
    source_paths=[Path(__file__), HERE/"protocol.json"]+[PDP/p for p in [
        "boolean_f5b.py","boolean_f5b_native.cpp","boolean_basis.py","macaulay_cache.py",
        "descend.py","sumpoly.py","gf2n.py","boolean_native.py"]]
    provenance={"argv":sys.argv,"protocol_sha256":hashlib.sha256((HERE/"protocol.json").read_bytes()).hexdigest(),
                "sources":{str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
                "python":sys.version,"platform":platform.platform(),"maximum_workers":1,
                "gpu":{"devices":[],"F4_F2_ECHELON":os.environ.get("F4_F2_ECHELON")},
                "timing_tier":"unisolated CPU correctness control; seconds are diagnostic only",
                "conductor":"unavailable: executable not installed"}
    if provenance["gpu"]["F4_F2_ECHELON"] != "host":
        raise ValueError("explicit F4_F2_ECHELON=host required")
    write_new(out/"provenance.json",provenance)
    polynomials=sumpoly.load(5)
    cases=[]
    for j,(n,m,ell) in enumerate(protocol["direct_cells"]):
        for k,law in enumerate(protocol["direct_target_laws"]):
            case=export_direct(n,m,ell,law,protocol["seed"]+j*10+k,polynomials)
            case["case_id"]=f"direct-n{n}-m{m}-ell{ell}-{k}"
            cases.append(case)
    for j,law in enumerate(protocol["chained_cell"]["target_laws"]):
        case=export_chain(law,protocol["seed"]+j)
        case["case_id"]=f"chain-n3-m4-ell1-{j}"
        cases.append(case)
    for case in cases:
        case["input_sha256"]=digest(case)
        roots,_=truth_roots(case["equations"],case["nvars"])
        case["independent_group_root_check"]=group_roots(case,roots)
    write_new(out/"inputs.json",cases)
    print(f"exported {len(cases)} exact inputs",flush=True)
    native=out/"boolean-f5-native"
    command=["g++","-O3","-std=c++17",str(PDP/"boolean_f5b_native.cpp"),"-o",str(native)]
    build=subprocess.run(command,capture_output=True,text=True,timeout=60)
    write_new(out/"native-build.json",{"argv":command,"returncode":build.returncode,
                                     "stdout":build.stdout,"stderr":build.stderr})
    f5_results=[]
    for case in cases:
        for order in protocol["orders"]:
            result=bounded_f5(case,order,protocol)
            result.update({"case_id":case["case_id"],"input_sha256":case["input_sha256"],"engine":"python-Boolean-F5B","order_name":order})
            f5_results.append(result)
            print(case["case_id"],order,result["status"],flush=True)
        if build.returncode == 0:
            equations=[g for g in case["equations"] if g]
            data=f"{case['nvars']} {len(equations)} 100000 -1\n"+"".join(
                f"{len(g)} {' '.join(map(str,g))}\n" for g in equations)
            try:
                process=subprocess.run([str(native)],input=data,capture_output=True,text=True,
                                       timeout=protocol["solver_timeout_seconds"])
                raw={"case_id":case["case_id"],"engine":"native-Boolean-F5B",
                     "input_sha256":case["input_sha256"],"returncode":process.returncode,
                     "stdout":process.stdout,"stderr":process.stderr}
                lines=process.stdout.splitlines()
                if process.returncode == 0 and lines and lines[0].startswith("OK "):
                    basis=[list(map(int,line.split()))[1:] for line in lines[1:]]
                    cert=certify_boolean_basis(case["nvars"],equations,basis)
                    raw.update({"status":"complete" if cert["verified"] else "verification-failed",
                                "certificate":cert,"basis":basis,
                                "counter_limit":"native stdout exposes insertions/reductions, not criterion or zero-reduction counts"})
                else:
                    raw["status"]="error"
            except subprocess.TimeoutExpired as error:
                raw={"case_id":case["case_id"],"engine":"native-Boolean-F5B","status":"timeout",
                     "partial_stdout":(error.stdout or b"").decode() if isinstance(error.stdout,bytes) else error.stdout}
            f5_results.append(raw)
            print(case["case_id"],"native",raw["status"],flush=True)
        write_new(out/f"f5-{case['case_id']}.json",f5_results[-7:])
    write_new(out/"f5-results.json",f5_results)
    chains=[c for c in cases if c["kind"] == "chained-S3"]
    layout,_=order_layout(chains[0]["nvars"],chains[0]["blocks"],"grevlex-natural")
    training_rows=list(ideal_rows(chains[0]["equations"],10,4,layout))
    _,learning_stats,trace=eliminate(training_rows)
    tested_rows=list(ideal_rows(chains[1]["equations"],10,4,layout))
    baseline,baseline_stats,_=eliminate(tested_rows)
    replay,replay_stats,_=eliminate(tested_rows,trace)
    fallback_stats=None
    if replay is None:
        replay,fallback_stats,_=eliminate(tested_rows)
    replay_result={"cell":"m4 n3 ell1 chained S3","degree":4,"rows":len(training_rows),
                   "columns":sum(mask.bit_count() <= 4 for mask in layout),
                   "training_case":chains[0]["case_id"],"test_case":chains[1]["case_id"],
                   "learning":learning_stats,"baseline":baseline_stats,"replay_attempt":replay_stats,
                   "fallback":fallback_stats,"exact_row_space_equal":replay == baseline,
                   "row_space_sha256":digest(baseline),"trace_sha256":digest(trace),
                   "charged_total_xor_rows_learning_plus_one_target":learning_stats["xor_rows"]+replay_stats["xor_rows"]+(fallback_stats or {}).get("xor_rows",0),
                   "interpretation":"checked fixed-row pivot replay; not a completed Joux-Vitse F4 symbolic-learning implementation"}
    write_new(out/"degree4-trace.json",replay_result)
    write_new(out/"degree4-trace-actions.json",trace)
    dinur=[]
    for case in cases:
        if case["kind"] == "direct-Semaev":
            print("Dinur parity",case["case_id"],flush=True)
            result=run_dinur(case)
            result["case_id"]=case["case_id"]
            write_new(out/f"dinur-{case['case_id']}.json",result)
            dinur.append(result)
    write_new(out/"dinur-results.json",dinur)
    statuses=Counter(r["status"] for r in f5_results)
    summary={"f5_status_counts":dict(statuses),"f5_trials":len(f5_results),
             "dinur_parity_trials":len(dinur),"dinur_all_verified":all(r["status"] == "verified" for r in dinur),
             "trace_row_space_verified":replay_result["exact_row_space_equal"],
             "gpu_full_IC_performance":"not attempted: no configured GPU host",
             "full_Dinur_Lokshtanov_solver_exponent":"not measured"}
    write_new(out/"summary.json",summary)
    print(json.dumps(summary),flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    run(args.out)

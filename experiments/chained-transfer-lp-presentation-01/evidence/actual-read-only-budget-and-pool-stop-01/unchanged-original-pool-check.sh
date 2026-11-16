#!/usr/bin/env bash
# isolab_pool_check.sh: will a CPU/memory request fit on an Iso Lab NodePool now? Read-only.
#
# The 2026-11-10 blind spot (docs/session-logs/2026-11-10.md, 00:15Z): the launch card's pool check
# (research/pkm_falldegree_unblock_20261107/cards/no_active_jobs.sh) read only the study's own Jobs by
# name, so another lab Job holding 2 CPU on the only cpu-spot node went unseen and a 12-CPU job pended
# 38 min. This check counts EVERY pod on the pool's nodes and every pending pod that selects the pool,
# whatever its namespace or owner, and names the ones in the way.
#
#   scripts/isolab_pool_check.sh --cpu 12 --memory 56Gi [--pool cpu-spot] [--namespace isolab]
#                                [--exclude-job NAME]... [--save bundle.json] [--json]
#   scripts/isolab_pool_check.sh --from-json bundle.json --cpu 12 --memory 56Gi [--json]
#
# Live mode runs only these read-only calls (RBAC: list pods cluster-wide, list nodes, get the
# karpenter.sh NodePool, get resourcequotas in the namespace); it never creates, patches or deletes:
#   kubectl get nodepool.karpenter.sh <pool> -o json
#   kubectl get nodes -l isolab.dev/pool=<pool> -o json
#   kubectl get pods -A --field-selector=status.phase!=Succeeded,status.phase!=Failed -o json
#   kubectl get resourcequota -n <namespace> -o json
# --save writes those four answers as one bundle {nodepool, nodes, pods, quotas}; --from-json reads
# such a bundle (or the same keys hand-written, as in tools/test_isolab_pool_check.py) instead of
# the cluster, so a launch receipt can carry the exact input the verdict was computed from.
#
# The request fits when it fits the free allocatable of an existing pool node (allocatable minus
# every bound pod's requests, DaemonSet pods included), or, failing that, a new node of at least
# request + per-node DaemonSet requests + reserved (capacity - allocatable) stays within the
# NodePool limits after the pool's current node capacity and the requests of pods already pending
# for the pool (a lower bound: Karpenter picks the instance size); and in both cases it fits what is
# left of the namespace ResourceQuota. Requests are per pod: sum of containers, or the largest
# init container if larger, plus pod overhead.
#
# Exit: 0 fits; 10 does not fit (the blocking pods are printed by name); 2 usage; 3 the cluster or
# the bundle could not be read.
set -uo pipefail

pool=cpu-spot namespace=isolab cpu= memory= from= save= json=0
exclude=()
usage() { sed -n '10,12p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cpu) cpu=${2:-}; shift 2 ;;
    --memory) memory=${2:-}; shift 2 ;;
    --pool) pool=${2:-}; shift 2 ;;
    --namespace) namespace=${2:-}; shift 2 ;;
    --exclude-job) exclude+=("${2:-}"); shift 2 ;;
    --from-json) from=${2:-}; shift 2 ;;
    --save) save=${2:-}; shift 2 ;;
    --json) json=1; shift ;;
    -h|--help) usage ;;
    *) echo "isolab_pool_check: unknown argument $1" >&2; usage ;;
  esac
done
[[ -n "$cpu" && -n "$memory" ]] || usage

if [[ -z "$from" ]]; then
  command -v kubectl >/dev/null || { echo "isolab_pool_check: kubectl not found (use --from-json)" >&2; exit 3; }
  tmp=$(mktemp -d) || exit 3
  trap 'rm -rf "$tmp"' EXIT
  kubectl get nodepool.karpenter.sh "$pool" -o json > "$tmp/nodepool.json" || { echo "isolab_pool_check: cannot read NodePool $pool" >&2; exit 3; }
  kubectl get nodes -l "isolab.dev/pool=$pool" -o json > "$tmp/nodes.json" || { echo "isolab_pool_check: cannot list nodes" >&2; exit 3; }
  kubectl get pods -A --field-selector=status.phase!=Succeeded,status.phase!=Failed -o json > "$tmp/pods.json" \
    || { echo "isolab_pool_check: cannot list pods in all namespaces" >&2; exit 3; }
  kubectl get resourcequota -n "$namespace" -o json > "$tmp/quotas.json" || echo '{"items":[]}' > "$tmp/quotas.json"
  from="$tmp/bundle.json"
  python3 - "$tmp" "$from" <<'PY' || exit 3
import json, sys
d = sys.argv[1]
bundle = {k: json.load(open(f"{d}/{k}.json")) for k in ("nodepool", "nodes", "pods", "quotas")}
json.dump(bundle, open(sys.argv[2], "w"), indent=1, sort_keys=True)
PY
  [[ -n "$save" ]] && cp "$from" "$save"
fi

exec python3 - "$from" "$pool" "$namespace" "$cpu" "$memory" "$json" "${exclude[@]}" <<'PY'
import json
import re
import sys

src, pool, namespace, cpu_req, mem_req, as_json, *exclude = sys.argv[1:]
UNITS = {"Ki": 2**10, "Mi": 2**20, "Gi": 2**30, "Ti": 2**40, "Pi": 2**50,
         "k": 10**3, "K": 10**3, "M": 10**6, "G": 10**9, "T": 10**12, "P": 10**15, "m": 1e-3, "": 1}


def qty(text) -> float:
    """A Kubernetes quantity: cpu in cores ("180m" = 0.18), memory in bytes ("56Gi")."""
    if text is None or text == "":
        return 0.0
    m = re.fullmatch(r"([0-9.]+(?:[eE][-+]?[0-9]+)?)(Ki|Mi|Gi|Ti|Pi|k|K|M|G|T|P|m)?", str(text).strip())
    if not m:
        raise ValueError(f"not a quantity: {text!r}")
    return float(m.group(1)) * UNITS[m.group(2) or ""]


def gib(b: float) -> str:
    return f"{b / 2**30:.2f}Gi"


try:
    bundle = json.load(open(src))
    nodepool, nodes, pods = bundle["nodepool"], bundle["nodes"]["items"], bundle["pods"]["items"]
    quotas = (bundle.get("quotas") or {}).get("items", [])
    want = {"cpu": qty(cpu_req), "memory": qty(mem_req)}
except (OSError, ValueError, KeyError, TypeError) as exc:
    print(f"isolab_pool_check: cannot read {src}: {exc}", file=sys.stderr)
    sys.exit(3)


def pod_requests(pod) -> dict:
    spec = pod.get("spec", {})
    total = {"cpu": 0.0, "memory": 0.0}
    for c in spec.get("containers", []):
        for r in total:
            total[r] += qty((c.get("resources", {}).get("requests") or {}).get(r))
    for c in spec.get("initContainers", []):
        for r in total:
            total[r] = max(total[r], qty((c.get("resources", {}).get("requests") or {}).get(r)))
    for r in total:
        total[r] += qty((spec.get("overhead") or {}).get(r))
    return total


def owner(pod) -> tuple[str, str]:
    meta = pod.get("metadata", {})
    labels = meta.get("labels") or {}
    job = labels.get("batch.kubernetes.io/job-name") or labels.get("job-name")
    if job:
        return "Job", job
    refs = meta.get("ownerReferences") or [{}]
    return refs[0].get("kind") or "Pod", refs[0].get("name") or meta.get("name", "?")


pool_nodes = {}
for n in nodes:
    labels = n.get("metadata", {}).get("labels") or {}
    if labels.get("isolab.dev/pool") == pool or labels.get("karpenter.sh/nodepool") == pool:
        st = n.get("status", {})
        pool_nodes[n["metadata"]["name"]] = {
            "allocatable": {r: qty((st.get("allocatable") or {}).get(r)) for r in want},
            "capacity": {r: qty((st.get("capacity") or {}).get(r)) for r in want},
            "used": {r: 0.0 for r in want}, "daemonset": {r: 0.0 for r in want}}

bound, pending = [], []
for p in pods:
    phase = (p.get("status") or {}).get("phase")
    if phase in ("Succeeded", "Failed"):
        continue
    kind, name = owner(p)
    if kind == "Job" and name in exclude:
        continue
    spec = p.get("spec", {})
    req = pod_requests(p)
    row = {"namespace": p["metadata"].get("namespace", ""), "pod": p["metadata"]["name"], "owner_kind": kind,
           "owner": name, "cpu": req["cpu"], "memory": req["memory"], "phase": phase,
           "node": spec.get("nodeName"), "created": p["metadata"].get("creationTimestamp")}
    if spec.get("nodeName") in pool_nodes:
        node = pool_nodes[spec["nodeName"]]
        for r in want:
            node["used"][r] += req[r]
            if kind == "DaemonSet":
                node["daemonset"][r] += req[r]
        bound.append(row)
    elif not spec.get("nodeName"):
        sel = spec.get("nodeSelector") or {}
        if sel.get("isolab.dev/pool") == pool or sel.get("karpenter.sh/nodepool") == pool:
            pending.append(row)

report = {"pool": pool, "namespace": namespace, "request": want, "nodes": [], "fits": False, "reasons": []}
fits_node = None
for name, node in sorted(pool_nodes.items()):
    free = {r: node["allocatable"][r] - node["used"][r] for r in want}
    ok = all(free[r] >= want[r] for r in want)
    report["nodes"].append({"node": name, "allocatable": node["allocatable"], "used": node["used"],
                            "free": free, "fits": ok})
    if ok and fits_node is None:
        fits_node = name

limits = {r: qty(((nodepool.get("spec") or {}).get("limits") or {}).get(r)) or float("inf") for r in want}
in_use = {r: qty(((nodepool.get("status") or {}).get("resources") or {}).get(r)) for r in want}
for r in want:   # status.resources may be absent (older Karpenter): sum the pool nodes' capacity
    in_use[r] = in_use[r] or sum(n["capacity"][r] for n in pool_nodes.values())
ds = {r: max((n["daemonset"][r] for n in pool_nodes.values()), default=0.0) for r in want}
reserved = {r: max((n["capacity"][r] - n["allocatable"][r] for n in pool_nodes.values()), default=0.0) for r in want}
queued = {r: sum(p[r] for p in pending) for r in want}
need_new = {r: want[r] + ds[r] + reserved[r] for r in want}
headroom = {r: limits[r] - in_use[r] - queued[r] for r in want}
new_node_ok = all(headroom[r] >= need_new[r] for r in want)
report["new_node"] = {"limits": limits, "pool_capacity_in_use": in_use, "pending_for_pool": queued,
                      "needs_at_least": need_new, "headroom": headroom, "fits": new_node_ok}

quota_ok = True
report["quotas"] = []
for q in quotas:
    hard, used = (q.get("status") or {}).get("hard") or q.get("spec", {}).get("hard") or {}, \
        (q.get("status") or {}).get("used") or {}
    for r in want:
        key = f"requests.{r}"
        if key in hard:
            left = qty(hard[key]) - qty(used.get(key))
            ok = left >= want[r]
            quota_ok &= ok
            report["quotas"].append({"quota": q["metadata"]["name"], "resource": key, "hard": qty(hard[key]),
                                     "used": qty(used.get(key)), "left": left, "fits": ok})

report["fits"] = (fits_node is not None or new_node_ok) and quota_ok
report["fits_on"] = fits_node or ("new node" if new_node_ok else None)
blocking = sorted([p for p in bound if p["owner_kind"] != "DaemonSet"] + pending,
                  key=lambda p: (-p["cpu"], -p["memory"], p["pod"]))
report["blocking"] = [] if report["fits"] else blocking

if as_json == "1":
    print(json.dumps(report, indent=2, sort_keys=True, default=lambda x: None))
else:
    print(f"pool {pool}: request {want['cpu']:g} CPU, {gib(want['memory'])}; {len(pool_nodes)} node(s), "
          f"{len(bound)} bound pod(s), {len(pending)} pending for the pool")
    for n in report["nodes"]:
        print(f"  node {n['node']}: allocatable {n['allocatable']['cpu']:g} CPU {gib(n['allocatable']['memory'])}, "
              f"requested {n['used']['cpu']:g} CPU {gib(n['used']['memory'])}, free {n['free']['cpu']:g} CPU "
              f"{gib(n['free']['memory'])} -> {'fits' if n['fits'] else 'does not fit'}")
    nn = report["new_node"]
    print(f"  new node: NodePool limits {nn['limits']['cpu']:g} CPU {gib(nn['limits']['memory'])}, in use "
          f"{nn['pool_capacity_in_use']['cpu']:g} CPU {gib(nn['pool_capacity_in_use']['memory'])}, pending "
          f"{nn['pending_for_pool']['cpu']:g} CPU; needs >= {nn['needs_at_least']['cpu']:g} CPU "
          f"{gib(nn['needs_at_least']['memory'])} -> {'fits' if nn['fits'] else 'does not fit'}")
    for q in report["quotas"]:
        unit = (lambda v: f"{v:g}") if q["resource"].endswith("cpu") else gib
        print(f"  quota {namespace}/{q['quota']} {q['resource']}: hard {unit(q['hard'])}, used {unit(q['used'])}, "
              f"left {unit(q['left'])} -> {'fits' if q['fits'] else 'does not fit'}")
    if report["fits"]:
        print(f"FITS on {report['fits_on']}")
    else:
        print("DOES NOT FIT; in the way (every non-DaemonSet pod on the pool or pending for it):")
        for p in blocking:
            where = f"on {p['node']}" if p["node"] else "pending"
            print(f"  {p['owner_kind']} {p['namespace']}/{p['owner']} (pod {p['pod']}): {p['cpu']:g} CPU "
                  f"{gib(p['memory'])}, {p['phase']} {where}, created {p['created']}")
sys.exit(0 if report["fits"] else 10)
PY

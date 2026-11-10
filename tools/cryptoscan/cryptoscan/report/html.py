"""Single-file HTML report: ``render(result) -> str``.

Self-contained (inline CSS, inline SVG charts, a little vanilla JS, no external
resources).  Every table is rendered as static HTML on the server so the page
reads with JavaScript disabled or in an email preview; JS only adds filtering,
column sorting and row expansion.  Long per-finding text (description,
remediation, references, raw spelling) and per-asset use lists are *not* in the
static HTML: they live once in a JSON blob (string-interned, so repeated text is
stored once) that the JS reads when a row is expanded.  The static "Top issues"
table carries one remediation per rule for the no-JS reader.

All data is escaped with ``html.escape``; the JSON blob escapes ``< > &``.
"""

from __future__ import annotations

import html as _h
import json
from typing import Any, Dict, List

from ..model import ScanResult, Severity
from ..names import security_strength
from .summary import CERT_BUCKETS, SEV_ORDER, TIMELINE_KEYS, asset_worst, host_of, quantum_status, sev_sort_key, summarize

SEV_NUM = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def e(x: Any) -> str:
    return _h.escape("" if x is None else str(x), quote=True)


CSS = """
:root{--bg:#fff;--fg:#111827;--muted:#4b5563;--card:#f9fafb;--border:#d1d5db;--link:#1d4ed8;
--sev-critical:#b91c1c;--sev-high:#c2410c;--sev-medium:#a16207;--sev-low:#2563eb;--sev-info:#6b7280;--ok:#15803d;
--fill-critical:#b91c1c;--fill-high:#ea580c;--fill-medium:#ca8a04;--fill-low:#2563eb;--fill-info:#6b7280;--fill-ok:#16a34a}
@media (prefers-color-scheme:dark){:root{--bg:#0b1220;--fg:#e5e7eb;--muted:#9ca3af;--card:#111a2e;--border:#334155;--link:#93c5fd;
--sev-critical:#f87171;--sev-high:#fb923c;--sev-medium:#facc15;--sev-low:#60a5fa;--sev-info:#9ca3af;--ok:#4ade80;
--fill-critical:#ef4444;--fill-high:#f97316;--fill-medium:#eab308;--fill-low:#3b82f6;--fill-info:#9ca3af;--fill-ok:#22c55e}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
main{max-width:1200px;margin:0 auto;padding:16px}
h1{font-size:1.6rem;margin:.2em 0}h2{font-size:1.2rem;margin:1.8em 0 .5em;border-bottom:1px solid var(--border);padding-bottom:.2em}
.muted{color:var(--muted)}.hdr{display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between}
.grade{display:flex;flex-direction:column;align-items:center;min-width:96px;padding:8px 14px;border:3px solid;border-radius:12px;font-weight:700}
.grade b{font-size:2.4rem;line-height:1}.grade span{font-size:.8rem}
.gA,.gB{color:var(--ok)}.gC{color:var(--sev-medium)}.gD{color:var(--sev-high)}.gF{color:var(--sev-critical)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin:14px 0}
.tile{background:var(--card);border:1px solid var(--border);border-left:6px solid;border-radius:8px;padding:8px 12px}
.tile b{display:block;font-size:1.7rem;line-height:1.1}.tile span{font-size:.8rem;text-transform:uppercase;letter-spacing:.04em}
.s4{color:var(--sev-critical)}.s3{color:var(--sev-high)}.s2{color:var(--sev-medium)}.s1{color:var(--sev-low)}.s0{color:var(--sev-info)}
.tile.s4,.tile.s3,.tile.s2,.tile.s1,.tile.s0{color:var(--fg)}
.tile.s4{border-left-color:var(--fill-critical)}.tile.s3{border-left-color:var(--fill-high)}.tile.s2{border-left-color:var(--fill-medium)}
.tile.s1{border-left-color:var(--fill-low)}.tile.s0{border-left-color:var(--fill-info)}
.pill{display:inline-block;padding:0 7px;border:1px solid currentColor;border-radius:99px;font-size:.75rem;font-weight:600;text-transform:uppercase;white-space:nowrap}
.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:12px;overflow:hidden}
.card h3{margin:0 0 8px;font-size:1rem}svg{max-width:100%;height:auto}svg text{fill:var(--fg);font:12px system-ui,sans-serif}
.f4{fill:var(--fill-critical)}.f3{fill:var(--fill-high)}.f2{fill:var(--fill-medium)}.f1{fill:var(--fill-low)}.f0{fill:var(--fill-info)}.fok{fill:var(--fill-ok)}
.k4{stroke:var(--fill-critical)}.k3{stroke:var(--fill-high)}.k0{stroke:var(--fill-info)}.kok{stroke:var(--fill-ok)}
.legend{display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:8px;font-size:.85rem}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px}
.sw.f4{background:var(--fill-critical)}.sw.f3{background:var(--fill-high)}.sw.f2{background:var(--fill-medium)}.sw.f1{background:var(--fill-low)}.sw.f0{background:var(--fill-info)}.sw.fok{background:var(--fill-ok)}
.tw{overflow-x:auto;border:1px solid var(--border);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{padding:5px 8px;border-bottom:1px solid var(--border);text-align:left;vertical-align:top}
th{background:var(--card);position:sticky;top:0;white-space:nowrap}
td.w{max-width:340px;overflow-wrap:anywhere}td.n,th.n{text-align:right}
.js th[data-k]{cursor:pointer}.js th[data-k]:after{content:" \\2195";color:var(--muted)}
th[data-dir=asc]:after{content:" \\2191"!important}th[data-dir=desc]:after{content:" \\2193"!important}
.js tr.m{cursor:pointer}tr.m:hover{background:var(--card)}tr.open{background:var(--card)}
tr.detail td{background:var(--card)}tr.detail dl{margin:0;display:grid;grid-template-columns:max-content 1fr;gap:3px 12px}
tr.detail dt{font-weight:600;color:var(--muted)}tr.detail dd{margin:0;overflow-wrap:anywhere}tr.detail ul{margin:0;padding-left:18px}
[hidden]{display:none!important}
.ctl{display:none;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0}.js .ctl{display:flex}
.ctl input,.ctl select{padding:5px 8px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--fg);font:inherit}
.ctl input{min-width:220px;flex:1}
.sevbtn{padding:3px 10px;border:1px solid var(--border);border-radius:99px;background:var(--bg);font:inherit;font-size:.82rem;cursor:pointer}
.sevbtn.s4,.sevbtn.s3,.sevbtn.s2,.sevbtn.s1,.sevbtn.s0{font-weight:600}.sevbtn[aria-pressed=false]{opacity:.45;text-decoration:line-through}
footer{margin:2em 0 1em;color:var(--muted);font-size:.85rem}code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.85em}
@media (max-width:600px){main{padding:10px}td.w{max-width:200px}}
@media print{.ctl{display:none!important}}
"""

JS = r"""
(function(){'use strict';
var D;try{D=JSON.parse(document.getElementById('cs-data').textContent)}catch(x){return}
document.documentElement.className+=' js';
function $(s,r){return (r||document).querySelector(s)}
function $$(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))}
function el(t,c,x){var n=document.createElement(t);if(c)n.className=c;if(x!=null)n.textContent=x;return n}
function S(i){return D.s[i]}
function kv(dl,k,v){if(v===''||v==null)return;dl.appendChild(el('dt',null,k));dl.appendChild(el('dd',null,v))}
function toggle(tr,cols,fill){var nx=tr.nextElementSibling;
 if(nx&&nx.className==='detail'){nx.parentNode.removeChild(nx);tr.classList.remove('open');tr.setAttribute('aria-expanded','false');return}
 var d=el('tr','detail'),td=el('td');td.colSpan=cols;fill(td,+tr.getAttribute('data-i'));d.appendChild(td);
 tr.parentNode.insertBefore(d,tr.nextSibling);tr.classList.add('open');tr.setAttribute('aria-expanded','true')}
function fillF(td,i){var f=D.f[i],dl=el('dl');kv(dl,'Description',S(f[0]));kv(dl,'Remediation',S(f[1]));
 if(f[2].length){var ul=el('ul');f[2].forEach(function(r){ul.appendChild(el('li',null,S(r)))});dl.appendChild(el('dt',null,'References'));var dd=el('dd');dd.appendChild(ul);dl.appendChild(dd)}
 kv(dl,'As spelled by source',S(f[3]));kv(dl,'Context',S(f[4]));
 if(f[5])kv(dl,'Quantum','Shor-vulnerable public-key material');if(f[6])kv(dl,'Deprecation year',String(f[6]));td.appendChild(dl)}
function fillA(td,i){var us=D.a[i];if(!us.length){td.appendChild(el('span','muted','No cryptographic uses recorded.'));return}
 var t=el('table'),h=el('tr');['Primitive','Use','Context','As spelled','Strength (bits)','Quantum'].forEach(function(x){h.appendChild(el('th',null,x))});t.appendChild(h);
 us.forEach(function(u){var r=el('tr');[S(u[1]),S(u[0]),S(u[2]),S(u[3]),u[4]==null?'':String(u[4]),S(u[5])].forEach(function(x){r.appendChild(el('td',null,x))});t.appendChild(r)});td.appendChild(t)}
function initTable(tbl,fill){if(!tbl)return;var cols=tbl.tHead.rows[0].cells.length,tb=tbl.tBodies[0];
 $$('tr.m',tb).forEach(function(r,i){r._o=i;r.setAttribute('aria-expanded','false')});
 tbl.addEventListener('click',function(ev){var th=ev.target.closest('th');
  if(th&&th.getAttribute('data-k')!==null){sort(tbl,th);return}
  if(ev.target.closest('a'))return;var tr=ev.target.closest('tr.m');if(tr)toggle(tr,cols,fill)});
 tbl.addEventListener('keydown',function(ev){if(ev.key==='Enter'||ev.key===' '){var tr=ev.target.closest&&ev.target.closest('tr.m');if(tr&&ev.target===tr){ev.preventDefault();toggle(tr,cols,fill)}}})}
function sort(tbl,th){var idx=th.cellIndex,num=th.getAttribute('data-t')==='n',asc=th.getAttribute('data-dir')!=='asc',tb=tbl.tBodies[0];
 $$('th',tbl).forEach(function(h){h.removeAttribute('data-dir');h.removeAttribute('aria-sort')});
 th.setAttribute('data-dir',asc?'asc':'desc');th.setAttribute('aria-sort',asc?'ascending':'descending');
 $$('tr.detail',tb).forEach(function(d){d.parentNode.removeChild(d)});
 var rs=$$('tr.m',tb);rs.forEach(function(r){r.classList.remove('open');r.setAttribute('aria-expanded','false')});
 function v(r){var c=r.cells[idx],x=c.getAttribute('data-v');if(x===null)x=c.textContent;return num?(parseFloat(x)||0):x.toLowerCase()}
 rs.sort(function(a,b){var x=v(a),y=v(b);return (x<y?-1:x>y?1:0)*(asc?1:-1)||a._o-b._o});
 rs.forEach(function(r){tb.appendChild(r)});if(tbl.id==='ft')apply()}
var ft=$('#ft'),st={q:'',col:'',sev:{}};
$$('.sevbtn').forEach(function(b){st.sev[b.getAttribute('data-s')]=true;
 b.addEventListener('click',function(){var k=b.getAttribute('data-s');st.sev[k]=!st.sev[k];b.setAttribute('aria-pressed',st.sev[k]?'true':'false');apply()})});
function apply(){if(!ft)return;var q=st.q.toLowerCase(),n=0,rs=$$('tbody tr.m',ft);
 rs.forEach(function(r){var ok=st.sev[r.getAttribute('data-s')]&&(!st.col||r.getAttribute('data-c')===st.col);
  if(ok&&q){if(r._t===undefined)r._t=r.textContent.toLowerCase();ok=r._t.indexOf(q)>=0}
  r.hidden=!ok;var nx=r.nextElementSibling;if(nx&&nx.className==='detail')nx.hidden=!ok;if(ok)n++});
 var c=$('#fcount');if(c)c.textContent=n+' of '+rs.length+' findings'}
var q=$('#fq'),cs=$('#fcol');
if(q)q.addEventListener('input',function(){st.q=q.value;apply()});
if(cs)cs.addEventListener('change',function(){st.col=cs.value;apply()});
initTable(ft,fillF);initTable($('#at'),fillA);initTable($('#inv'),function(){});apply();
})();
"""


class _Strings:
    def __init__(self) -> None:
        self.items: List[str] = []
        self.idx: Dict[str, int] = {}

    def __call__(self, s: Any) -> int:
        s = "" if s is None else str(s)
        i = self.idx.get(s)
        if i is None:
            i = self.idx[s] = len(self.items)
            self.items.append(s)
        return i


def _pill(sev: str) -> str:
    return f'<span class="pill s{SEV_NUM.get(sev, 0)}">{e(sev)}</span>'


def _stacked_bar(counts: Dict[str, int]) -> str:
    total = sum(counts.values())
    if not total:
        return '<p class="muted">No findings.</p>'
    W, x, parts = 600.0, 0.0, []
    for s in SEV_ORDER:
        n = counts[s]
        if not n:
            continue
        w = W * n / total
        parts.append(f'<rect class="f{SEV_NUM[s]}" x="{x:.1f}" y="0" width="{w:.1f}" height="30"><title>{s}: {n}</title></rect>')
        if w > 22:
            parts.append(f'<text x="{x + w / 2:.1f}" y="20" text-anchor="middle" style="fill:#fff;font-weight:700">{n}</text>')
        x += w
    legend = "".join(f'<span><i class="sw f{SEV_NUM[s]}"></i>{s} {counts[s]}</span>' for s in SEV_ORDER if counts[s])
    return (f'<svg viewBox="0 0 600 30" role="img" aria-label="Findings by severity">{"".join(parts)}</svg>'
            f'<div class="legend">{legend}</div>')


def _rules_chart(rules: List[Dict[str, Any]]) -> str:
    rules = rules[:10]
    if not rules:
        return '<p class="muted">No findings.</p>'
    mx = max(r["count"] for r in rules)
    rows = []
    for i, r in enumerate(rules):
        y = i * 24
        w = max(2.0, 330.0 * r["count"] / mx)
        label = r["rule_id"] if len(r["rule_id"]) <= 28 else r["rule_id"][:27] + "\u2026"
        rows.append(f'<text x="200" y="{y + 15}" text-anchor="end">{e(label)}</text>'
                    f'<rect class="f{SEV_NUM[r["severity"]]}" x="208" y="{y + 3}" width="{w:.1f}" height="16" rx="2">'
                    f'<title>{e(r["rule_id"])}: {r["count"]} ({e(r["severity"])})</title></rect>'
                    f'<text x="{208 + w + 5:.1f}" y="{y + 15}">{r["count"]}</text>')
    return f'<svg viewBox="0 0 640 {len(rules) * 24 + 4}" role="img" aria-label="Top rules">{"".join(rows)}</svg>'


def _donut(pq: Dict[str, Any]) -> str:
    total = pq["total_assets"]
    if not total:
        return '<p class="muted">No assets.</p>'
    segs = [("Quantum-vulnerable only", pq["vulnerable_only_assets"], "k3", "f3"),
            ("Hybrid / PQ available", pq["hybrid_assets"], "kok", "fok"),
            ("No vulnerable public key", pq["no_public_key_assets"], "k0", "f0")]
    out, off = [], 25.0
    for name, n, k, _ in segs:
        if not n:
            continue
        p = 100.0 * n / total
        out.append(f'<circle class="{k}" r="15.9155" cx="21" cy="21" fill="none" stroke-width="6" '
                   f'stroke-dasharray="{p:.2f} {100 - p:.2f}" stroke-dashoffset="{off:.2f}"><title>{name}: {n}</title></circle>')
        off -= p
    legend = "".join(f'<span><i class="sw {f}"></i>{n} {e(name)}</span>' for name, n, _, f in segs)
    return (f'<svg viewBox="0 0 42 42" width="170" height="170" role="img" aria-label="Post-quantum readiness">'
            f'<circle r="15.9155" cx="21" cy="21" fill="none" stroke="var(--border)" stroke-width="6"/>{"".join(out)}'
            f'<text x="21" y="21.5" text-anchor="middle" style="font-size:6px;font-weight:700">{pq["exposure_pct"]:.0f}%</text>'
            f'<text x="21" y="27" text-anchor="middle" style="font-size:3px">exposed</text></svg>'
            f'<div class="legend">{legend}</div>')


def _cert_timeline(counts: Dict[str, int]) -> str:
    if not sum(counts.values()):
        return '<p class="muted">No certificates with validity data.</p>'
    cls = {"expired": "f4", "<30d": "f3", "<90d": "f2", "<365d": "f1", "later": "f0"}
    mx = max(counts.values())
    parts = []
    for i, b in enumerate(CERT_BUCKETS):
        n = counts[b]
        h = 70.0 * n / mx if n else 0
        x = 10 + i * 76
        parts.append(f'<rect class="{cls[b]}" x="{x}" y="{80 - h:.1f}" width="60" height="{h:.1f}"><title>{e(b)}: {n}</title></rect>'
                     f'<text x="{x + 30}" y="{76 - h:.1f}" text-anchor="middle">{n}</text>'
                     f'<text x="{x + 30}" y="98" text-anchor="middle">{e(b)}</text>')
    return f'<svg viewBox="0 0 400 104" role="img" aria-label="Certificate expiry timeline">{"".join(parts)}</svg>'


def _th(label: str, key: str, num: bool = False) -> str:
    extra = ' data-t="n" class="n"' if num else ""
    return f'<th data-k="{key}"{extra}>{e(label)}</th>'


def render(result: ScanResult) -> str:
    s = summarize(result)
    meta = result.meta
    counts = s["severity_counts"]
    strs = _Strings()
    findings = sorted(result.findings, key=sev_sort_key)
    worst = asset_worst(result)

    # ---- findings table (static rows) + JSON details ----
    fdata: List[List[Any]] = []
    frows: List[str] = []
    for i, f in enumerate(findings):
        u = f.use
        fdata.append([strs(f.description), strs(f.remediation), [strs(r) for r in f.references],
                      strs(u.raw if u and u.raw else ""), strs(u.context if u and u.context else ""),
                      1 if f.quantum_vulnerable else 0, f.deprecation_year or 0])
        n = int(f.severity)
        frows.append(
            f'<tr class="m" tabindex="0" data-i="{i}" data-s="{n}" data-c="{e(f.collector)}">'
            f'<td data-v="{n}"><span class="pill s{n}">{f.severity.label}</span></td><td><code>{e(f.rule_id)}</code></td>'
            f'<td class="w">{e(f.title)}</td><td class="w">{e(f.asset_name)}</td><td>{e(host_of(result, f.host))}</td>'
            f'<td class="w">{e(f.location)}</td></tr>')

    # ---- assets ----
    assets = sorted(result.assets, key=lambda a: (-int(worst.get(a.asset_id, Severity.INFO)) if a.asset_id in worst else 1,
                                                  a.kind.value, a.name, a.asset_id))
    adata: List[List[Any]] = []
    arows: List[str] = []
    for i, a in enumerate(assets):
        adata.append([[strs(u.describe()), strs(u.primitive.value), strs(u.context or ""), strs(u.raw or ""),
                       security_strength(u), strs(quantum_status(u))] for u in a.uses])
        w = worst.get(a.asset_id)
        wl = w.label if w is not None else "none"
        wn = int(w) if w is not None else -1
        wcell = _pill(wl) if w is not None else '<span class="muted">none</span>'
        arows.append(
            f'<tr class="m" tabindex="0" data-i="{i}"><td>{e(a.kind.value)}</td><td class="w">{e(a.name)}</td>'
            f'<td>{e(host_of(result, a.host))}</td><td class="w">{e(a.location)}</td><td class="n" data-v="{len(a.uses)}">{len(a.uses)}</td>'
            f'<td data-v="{wn}">{wcell}</td></tr>')

    data = json.dumps({"s": strs.items, "f": fdata, "a": adata}, separators=(",", ":"))
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

    collectors = sorted({f.collector for f in findings})
    sev_buttons = "".join(
        f'<button type="button" class="sevbtn s{SEV_NUM[k]}" data-s="{SEV_NUM[k]}" aria-pressed="true">{k} ({counts[k]})</button>'
        for k in SEV_ORDER)
    tiles = "".join(f'<div class="tile s{SEV_NUM[k]}"><b>{counts[k]}</b><span>{k}</span></div>' for k in SEV_ORDER)
    pq = s["pqc"]
    title = f"cryptoscan report: {meta.hostname or 'unknown host'}"

    P: List[str] = []
    P.append('<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">'
             '<meta name="viewport" content="width=device-width,initial-scale=1">'
             '<meta name="color-scheme" content="light dark">'
             f'<title>{e(title)}</title><style>{CSS}</style></head><body><main>')
    P.append(f'<div class="hdr"><div><h1>{e(title)}</h1><div class="muted">Profile <b>{e(meta.profile)}</b> &middot; '
             f'{s["total_assets"]} assets &middot; {s["total_findings"]} findings &middot; worst: <b>{e(s["worst"])}</b> &middot; '
             f'{e((meta.finished or meta.started or "")[:19])}</div></div>'
             f'<div class="grade g{s["grade"]}" title="Triage score, 100 minus capped severity penalties"><b>{s["grade"]}</b>'
             f'<span>score {s["score"]}/100</span></div></div>')
    P.append(f'<div class="tiles">{tiles}</div>')
    P.append('<div class="charts">'
             f'<div class="card"><h3>Findings by severity</h3>{_stacked_bar(counts)}</div>'
             f'<div class="card"><h3>Top 10 rules</h3>{_rules_chart(s["top_rules"])}</div>'
             f'<div class="card"><h3>Post-quantum readiness (assets)</h3>{_donut(pq)}</div>'
             f'<div class="card"><h3>Certificate expiry</h3>{_cert_timeline(s["cert_expiry"])}</div></div>')

    # top issues (static, carries remediation for no-JS readers)
    P.append('<h2>Top issues</h2><div class="tw"><table><thead><tr><th>Rule</th><th>Title</th><th>Severity</th>'
             '<th class="n">Count</th><th class="n">Assets</th><th>Remediation</th></tr></thead><tbody>')
    for r in s["top_rules"][:50]:
        P.append(f'<tr><td><code>{e(r["rule_id"])}</code></td><td class="w">{e(r["title"])}</td><td>{_pill(r["severity"])}</td>'
                 f'<td class="n">{r["count"]}</td><td class="n">{r["assets"]}</td><td class="w">{e(r["remediation"])}</td></tr>')
    P.append('</tbody></table></div>')
    if len(s["top_rules"]) > 50:
        P.append(f'<p class="muted">{len(s["top_rules"]) - 50} more rules not listed.</p>')

    # findings
    P.append('<h2>Findings</h2>')
    P.append('<div class="ctl"><input id="fq" type="search" placeholder="Filter findings (rule, asset, host, text)" aria-label="Filter findings">'
             f'{sev_buttons}<select id="fcol" aria-label="Collector"><option value="">all collectors</option>'
             + "".join(f'<option value="{e(c)}">{e(c)}</option>' for c in collectors)
             + '</select><span id="fcount" class="muted"></span></div>')
    P.append('<div class="tw"><table id="ft"><thead><tr>' + _th("Severity", "sev", True).replace(' class="n"', "")
             + _th("Rule", "rule") + _th("Title", "title") + _th("Asset", "asset") + _th("Host", "host") + _th("Location", "loc")
             + '</tr></thead><tbody>' + "".join(frows) + '</tbody></table></div>')
    if not frows:
        P.append('<p class="muted">No findings.</p>')
    P.append('<p class="muted">Click a row to see the description, remediation, references and the raw spelling (needs JavaScript).</p>')

    # assets
    P.append('<h2>Asset inventory</h2><div class="tw"><table id="at"><thead><tr>' + _th("Kind", "kind") + _th("Name", "name")
             + _th("Host", "host") + _th("Location", "loc") + _th("Uses", "uses", True) + _th("Worst finding", "worst", True).replace(' class="n"', "")
             + '</tr></thead><tbody>' + "".join(arows) + '</tbody></table></div>')

    # algorithm inventory
    P.append('<h2>Algorithm inventory</h2><div class="tw"><table id="inv"><thead><tr>' + _th("Algorithm", "alg") + _th("Primitive", "prim")
             + _th("Strength (bits)", "str", True) + _th("Quantum", "q") + _th("Assets", "assets", True) + _th("Uses", "uses", True)
             + '</tr></thead><tbody>')
    for r in s["inventory"]:
        st = "" if r["strength"] is None else r["strength"]
        P.append(f'<tr><td class="w">{e(r["algorithm"])}</td><td>{e(r["primitive"])}</td><td class="n" data-v="{st if st != "" else -1}">{st}</td>'
                 f'<td title="{e(r["quantum_note"])}">{e(r["quantum"])}</td><td class="n">{r["assets"]}</td><td class="n">{r["count"]}</td></tr>')
    P.append('</tbody></table></div>')

    # PQC timeline
    P.append('<h2>Post-quantum timeline</h2><div class="tw"><table><thead><tr><th>Bucket</th><th class="n">Findings</th><th class="n">Assets</th></tr></thead><tbody>')
    for k in TIMELINE_KEYS:
        v = s["timeline"][k]
        P.append(f'<tr><td>{e(v["label"])}</td><td class="n">{v["findings"]}</td><td class="n">{v["assets"]}</td></tr>')
    P.append(f'</tbody></table></div><p class="muted">{pq["vulnerable_assets"]} of {pq["total_assets"]} assets use quantum-vulnerable '
             f'public-key cryptography; {pq["hybrid_assets"]} also offer a hybrid. Recorded traffic protected by these keys can be '
             'decrypted later once a quantum computer exists (harvest now, decrypt later).</p>')

    # certificates
    if s["certificates"]:
        P.append('<h2>Certificates</h2><div class="tw"><table><thead><tr><th>Subject</th><th>Issuer</th><th>Key</th><th>Signature</th>'
                 '<th>notAfter</th><th class="n">Days left</th></tr></thead><tbody>')
        for c in s["certificates"]:
            cls = {"expired": "s4", "<30d": "s3", "<90d": "s2"}.get(c["bucket"], "")
            P.append(f'<tr><td class="w">{e(c["subject"] or c["asset"])}</td><td class="w">{e(c["issuer"])}</td><td>{e(c["key"])}</td>'
                     f'<td>{e(c["signature"])}</td><td>{e(c["not_after"][:10])}</td><td class="n {cls}">{c["days_left"]}</td></tr>')
        P.append('</tbody></table></div>')

    # hosts
    P.append('<h2>Hosts</h2><div class="tw"><table><thead><tr><th>Host</th><th>Worst</th>'
             + "".join(f'<th class="n">{k}</th>' for k in SEV_ORDER) + '<th class="n">Assets</th></tr></thead><tbody>')
    for h in s["hosts"]:
        P.append(f'<tr><td>{e(h["host"])}</td><td>{_pill(h["worst"]) if h["worst"] != "none" else "none"}</td>'
                 + "".join(f'<td class="n">{h["counts"][k]}</td>' for k in SEV_ORDER) + f'<td class="n">{h["assets"]}</td></tr>')
    P.append('</tbody></table></div>')

    # coverage
    P.append('<h2>Collector coverage</h2><div class="tw"><table><thead><tr><th>Collector</th><th>Status</th><th>Reason</th>'
             '<th class="n">Assets</th><th class="n">Findings</th></tr></thead><tbody>')
    for c in s["coverage"]:
        P.append(f'<tr><td>{e(c["collector"])}</td><td>{e(c["status"])}</td><td class="w">{e(c["reason"])}</td>'
                 f'<td class="n">{c["assets"]}</td><td class="n">{c["findings"]}</td></tr>')
    P.append('</tbody></table></div>')

    P.append('<h2>Methodology</h2><p>Severities: <b>critical</b> broken or trivially attackable now; <b>high</b> formally disallowed or '
             'practically weak; <b>medium</b> below the selected profile or deprecated; <b>low</b> sunset and hygiene items; <b>info</b> '
             'inventory and transition notes. This is a configuration review, not a penetration test. Remote probes show what a server '
             'offers in a handshake, not what real clients negotiate. Score = 100 minus capped penalties (critical 25, high 10, medium 3, '
             'low 1 per finding; caps 75/40/20/10).</p>')
    P.append(f'<footer>cryptoscan {e(meta.version)} &middot; profile {e(meta.profile)} &middot; generated {e(meta.finished or meta.started or "n/a")}'
             f'<br>Command: <code>{e(" ".join(meta.command_line))}</code></footer>')
    P.append(f'</main><script type="application/json" id="cs-data">{data}</script><script>{JS}</script></body></html>')
    return "".join(P)

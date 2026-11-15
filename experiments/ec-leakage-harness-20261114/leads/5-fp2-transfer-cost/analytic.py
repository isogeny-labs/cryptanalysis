#!/usr/bin/env python3
"""ANALYTIC (not measured) crossover, NFS in F_{p^2} (Q=p^2) vs generic sqrt(r). [pcc:unverified]
L_Q[1/3,c]=exp(c (lnQ)^{1/3} (lnlnQ)^{2/3}), o(1) dropped.  Cost in log2 'cycles'.
Anchors: (a) A=80 at 1024 bits (common textbook figure); (b) record-style anchor, 795-bit prime-field DLP ~ 3100 core-years
~ 2^67.5 cycles (recalled from memory, unverified) -> formula-implied value at 1024 is printed.
Floor F: fixed NFS overhead (poly selection, sieving setup, linear algebra) in log2 cycles; cost=max(L-model, 2^F).
Generic side: sqrt(r) group ops, r ~ p ~ 2^n (supersingular t=0 curve, only way r|p+1 with r~p), times 2^G cycles/op (G=10)."""
import math, json
c=1.923
def lg(B):
    lnQ=B*math.log(2); return c*lnQ**(1/3)*math.log(lnQ)**(2/3)/math.log(2)
G=10
anch={'A80@1024':80-lg(1024),'rec795=67.5':67.5-lg(795)}
out={'formula_implied_log2_at_1024_under_record_anchor':round(lg(1024)+anch['rec795=67.5'],1),'runs':{}}
for an,off in anch.items():
  for F in (0,30,40):
    cross=None
    for n in range(16,600):
        ic=max(lg(2*n)+off,F); rho=n/2+G
        if cross is None and ic<rho: cross=n
    pts={n:dict(nfs_log2=round(max(lg(2*n)+off,F),1),rho_log2=n/2+G) for n in (40,64,80,100,128,160,192,256)}
    out['runs'][f'{an}|floor={F}']=dict(crossover_n=cross,field_bits=2*cross if cross else None,points=pts)
json.dump(out,open('analytic.json','w'),indent=1)
for k,v in out['runs'].items(): print(k,'crossover n =',v['crossover_n'],'field bits',v['field_bits'])
print('implied@1024',out['formula_implied_log2_at_1024_under_record_anchor'])
for n in (64,128,160,256): print(n,{k:(v['points'][n]['nfs_log2'],v['points'][n]['rho_log2']) for k,v in out['runs'].items()})

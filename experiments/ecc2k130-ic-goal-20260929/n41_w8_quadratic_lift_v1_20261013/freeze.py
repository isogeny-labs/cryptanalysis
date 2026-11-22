"""Freeze the width-16 degree-two lifted membership screen."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
table=PARENT/'n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv'
sources=[HERE/x for x in ('lift.cpp','lift','run.py')]
sources += [table,
    PARENT/'n41_w8_quadratic_partial_ideal_v3_20261013/joint_core.hpp',
    PARENT/'n41_w8_quadratic_partial_ideal_v3_20261013/result.json',
    PARENT/'n41_w8_ninepair_join_control_20261012/join9.cpp']
protocol={'status':'FROZEN','kind':'n41_w8_width16_quadratic_lift_screen',
          'curve_id':'EC1N41Ckb1h7d5e80d3c4d0','source_table':str(table),
          'witness_state_ids':[17678,155,6169,16990],
          'worker_count':1,'wall_cap_seconds':120,'rss_cap_bytes':4294967296,
          'sources':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in sources}}
with (HERE/'protocol.json').open('x') as out:
    json.dump(protocol,out,sort_keys=True,indent=2);out.write('\n')

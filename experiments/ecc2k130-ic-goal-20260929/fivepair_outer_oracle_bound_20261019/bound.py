"""Exact W29 fixed-outer coverage ceilings and N41 right-support calibration."""
import hashlib
import json
import math
from decimal import Decimal, getcontext
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"bound_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_W29_OUTER_COVERAGE_BOUND"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
read=lambda label:json.loads(Path(cfg["sources"][label]["path"]).read_text())
n41=read("n41_support")
audit=read("n41_sort_audit")
relation=read("n41_relation")
n41_curve=read("n41_group_audit")
sample=read("w29_sample")["sample"]
n131=read("n131_prior_bound")
native=json.loads(Path(cfg["sources"]["native_rate"]["path"]).read_text())
assert n41["status"]=="COMPLETE_N41_RIGHT_SUPPORT"
assert audit["status"]=="PASS_SORTED_N41_RIGHT_SUPPORT_AUDIT"
assert n41["row"]["distinct_sums"]==audit["row"]["distinct_sums"]==1258720
assert relation["hit"]["probes"]==396919
assert n41_curve["curve_id"]=="EC1N41Ckb1h7d5e80d3c4d0"
assert n131["curve_id"]=="EC1N131Ckb1heb5f1998f20b"
assert n131["status"]=="PASS_EXACT_N131_TARGET_ADVICE_BOUND"
assert sample["status"]=="COMPLETE_W29_SAMPLE"
assert sample["samples"]==65536 and sample["eligible_both"]==16677
assert native["status"]=="COMPLETE_SAMPLE" and native["sample_checked"]==1048576

r41=n41_curve["subgroup_order"]
raw41=n41_curve["cofactor"]*r41
m41=n41["row"]["distinct_sums"]
r131=int(n131["subgroup_order"])
code_capacity=1<<28
states_per_code=4
signed_max=states_per_code*code_capacity
pair_ceiling_max=signed_max*signed_max
projected_codes=sample["eligible_both"]*(code_capacity//sample["samples"])
signed_projected=states_per_code*projected_codes
pair_ceiling_projected=signed_projected*signed_projected


def ceiling(a,b):return (a+b-1)//b
def threshold(m,k):
    values=ceiling(r131,2*k*m)
    bits=(values-1).bit_length()
    return {"fixed_proposals_per_advice":k,"minimum_advice_values_for_half_bound":values,
            "minimum_advice_bits_for_half_bound":bits,
            "upper_at_preceding_bit_count_numerator":min(r131,(1<<(bits-1))*k*m) if bits else 0,
            "upper_at_threshold_bit_count_numerator":min(r131,(1<<bits)*k*m),
            "probability_denominator":r131}

getcontext().prec=50
z=1.96
n=sample["samples"];x=sample["eligible_both"];phat=x/n
center=(phat+z*z/(2*n))/(1+z*z/n)
half=z*math.sqrt(phat*(1-phat)/n+z*z/(4*n*n))/(1+z*z/n)
rate=Decimal(native["sample_seconds"])/Decimal(native["sample_checked"])
result={"status":"PASS_W29_FIXED_OUTER_COVERAGE_BOUND","candidate_id":None,
        "n41":{"curve_id":n41_curve["curve_id"],"raw_group_order":raw41,
               "distinct_right_pair_sums":m41,"compatible_pairs":n41["row"]["compatible_pairs"],
               "uniform_raw_single_residual_probability_numerator":m41,
               "uniform_raw_single_residual_probability_denominator":raw41,
               "archived_public_relation_probe":relation["hit"]["probes"]},
        "n131":{"curve_id":n131["curve_id"],"subgroup_order":r131,
                "raw_code_capacity":code_capacity,"signed_states_per_code_ceiling":states_per_code,
                "signed_state_ceiling":signed_max,"ordered_right_pair_sum_ceiling":pair_ceiling_max,
                "single_fixed_outer_probability_upper_numerator":pair_ceiling_max,
                "single_fixed_outer_probability_upper_denominator":r131,
                "advice_panels_max_source":[threshold(pair_ceiling_max,k) for k in cfg["proposal_budgets"]],
                "sample_projected_valid_codes":projected_codes,
                "sample_projected_signed_states":signed_projected,
                "sample_projected_ordered_pair_ceiling":pair_ceiling_projected,
                "advice_panels_sample_projection":[threshold(pair_ceiling_projected,k) for k in cfg["proposal_budgets"]],
                "sample_valid_rate":phat,
                "sample_valid_rate_wilson95":[center-half,center+half],
                "native_observed_seconds_per_raw_first_code":str(rate),
                "native_projected_seconds_per_valid_list_scan":str(rate*Decimal(projected_codes)),
                "native_projected_seconds_per_full_raw_scan":str(rate*Decimal(code_capacity))},
        "protocol_sha256":sha(HERE/"bound_protocol.json"),"script_sha256":sha(Path(__file__))}
(HERE/"bound_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({"status":result["status"],"n41_distinct":m41,
                  "n131_max_source_bits_20m":result["n131"]["advice_panels_max_source"][1]["minimum_advice_bits_for_half_bound"],
                  "n131_projected_bits_20m":result["n131"]["advice_panels_sample_projection"][1]["minimum_advice_bits_for_half_bound"]},sort_keys=True))

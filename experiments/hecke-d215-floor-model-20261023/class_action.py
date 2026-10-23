"""Compute the independent order-class action data for D=-215, f=6."""
import hashlib
import json
from pathlib import Path

from sage.all import BinaryQF, pari

HERE = Path(__file__).resolve().parent


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_STRUCTURE_AUDIT"
    d = -215
    discriminants = {str(f): d * f * f for f in (1, 2, 3, 6)}
    class_numbers = {f: int(pari.qfbclassno(delta)) for f, delta in discriminants.items()}
    norm2_f1 = BinaryQF(2, 1, 27)
    norm2_f3 = BinaryQF(2, 1, 242)
    norm3_f1 = BinaryQF(3, 1, 18)
    norm3_f2 = BinaryQF(3, 2, 72)
    forms = {"norm2_f1": norm2_f1, "norm2_f3": norm2_f3,
             "norm3_f1": norm3_f1, "norm3_f2": norm3_f2}
    assert {name: int(form.discriminant()) for name, form in forms.items()} == {
        "norm2_f1": -215, "norm2_f3": -1935, "norm3_f1": -215, "norm3_f2": -860}
    orders = {name: int(form.form_class().order()) for name, form in forms.items()}
    result = {"status": "VERIFIED_D215_CLASS_ACTION_DATA",
              "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
              "discriminants": discriminants, "class_numbers": class_numbers,
              "norm_form_orders": orders,
              "conditional_assumption": "The two rational X0(11) sheets each carry the norm-prime ideal-class action with the computed class order; this identification is checked by the saved graph, not proved here for all fields.",
              "degree2_c3_sheet_orbits_predicted": 2 * class_numbers["3"] // orders["norm2_f3"],
              "degree2_c3_orbit_length_predicted": orders["norm2_f3"],
              "degree3_c2_sheet_orbits_predicted": 2 * class_numbers["2"] // orders["norm3_f2"],
              "degree3_c2_orbit_length_predicted": orders["norm3_f2"],
              "script_sha256": hashlib.sha256((HERE / "class_action.py").read_bytes()).hexdigest(),
              "candidate_id": None, "timing_claim": None}
    (HERE / "class_action.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

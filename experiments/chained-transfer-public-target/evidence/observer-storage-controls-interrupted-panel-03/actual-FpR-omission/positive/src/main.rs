//! Probe the actual copied coefficient hook; original FpR supplies the algebra check.
pub use isogeny_algos::{bigint,field,fpm,poly};
#[path="fpr.rs"] mod copied_fpr;
use field::Field;
fn main() {
 let f=copied_fpr::FpR::from_modulus(223,&[220,0,0,1]);
 let original=isogeny_algos::arithmetic_audit_original_fpr::FpR::from_modulus(223,&[220,0,0,1]);
 let mut a=[0;16];a[..3].fill(1);
 let result=n4_arithmetic_taps::within("omission-probe",||f.mul(a,a));
 let reference=original.mul(a,a);
 assert_eq!(result,reference,"original algebra must agree before checking counts");
 let actual=n4_arithmetic_taps::count("omission-probe","FpR.coefficient",223,"mul");
 println!("N4_ARITHMETIC_HOOK_PROBE {}",serde_json::json!({"manifest_dir":env!("CARGO_MANIFEST_DIR"),"all_algebra_equal":true,"result":result,"original_result":reference,"observed_mul":actual,"expected_mul":11}));
 assert_eq!(actual,11,"analytic coefficient-count control must detect a missing hook");
}

//! The n = 19 tau6 index calculus (experiments/volcano-ic/tau.sage, arm tau6) end to
//! end in native code: protocol volcano-n19-native-loop-20261021, candidate N2.
//!
//! * `v3`: the per-shift solve of the current row (arm N of
//!   volcano-n19-native-tau6-v3-20261020), included from that experiment's
//!   source file by path, so it is the same source byte for byte, with its C
//!   ABI (`tau6_new`, `tau6_solve`, ...) and its tests.
//! * `pyrand`: CPython's MT19937 `random.Random(str)`, `randrange`, `shuffle`.
//! * `curve`: GF(2^19) and E: y^2 + xy = x^3 + 1.
//! * `dlp`: TauCurve, generator, tauEigen, tauDlp and the GF(r) left kernel.
//! * `ffi`: the C ABI the planted arm (Sage) and the pure-Python tests call.

#[path = "../../../volcano-n19-native-tau6-v3-20261020/native/src/lib.rs"]
pub mod v3;

pub mod curve;
pub mod dlp;
pub mod ffi;
pub mod json;
pub mod pyrand;
mod testvec;
pub mod util;

// Shared primitives for the N4 solver: operation counters, F_q, K = F_{q^3}, rng.
//
// Cost unit: F_q multiplications (`MUL`), with inversions (`INV`) priced by a measured
// time ratio, and additions only counted. Every arm (IC, rho) uses these same
// primitives, so the same counter measures both. A K-multiplication is charged 11 F_q
// multiplications (schoolbook 9 plus 2 for the reduction by x^3 = c), a K-Frobenius 2.
#![allow(dead_code)]

pub static mut MUL: u64 = 0;
pub static mut INV: u64 = 0;
pub static mut ADD: u64 = 0;
// native work in other rings / not priced in F_q multiplications
pub static mut LMUL: u64 = 0; // mod-ell multiplications (linear algebra)
pub static mut LADD: u64 = 0;
pub static mut HASH: u64 = 0; // hash-table inserts and lookups
pub static mut CMP: u64 = 0; // distinguished-point / partition checks

#[derive(Clone, Copy, Debug, Default)]
pub struct Cnt {
    pub mul: u64,
    pub inv: u64,
    pub add: u64,
    pub lmul: u64,
    pub ladd: u64,
    pub hash: u64,
    pub cmp: u64,
}
impl Cnt {
    pub fn since(&self, o: &Cnt) -> Cnt {
        Cnt {
            mul: self.mul - o.mul,
            inv: self.inv - o.inv,
            add: self.add - o.add,
            lmul: self.lmul - o.lmul,
            ladd: self.ladd - o.ladd,
            hash: self.hash - o.hash,
            cmp: self.cmp - o.cmp,
        }
    }
}
pub fn snap() -> Cnt {
    unsafe {
        Cnt { mul: MUL, inv: INV, add: ADD, lmul: LMUL, ladd: LADD, hash: HASH, cmp: CMP }
    }
}
#[inline(always)]
pub fn bump_mul(n: u64) {
    unsafe { MUL += n }
}
#[inline(always)]
pub fn bump_inv(n: u64) {
    unsafe { INV += n }
}
#[inline(always)]
pub fn bump_add(n: u64) {
    unsafe { ADD += n }
}
#[inline(always)]
pub fn bump_lmul(n: u64) {
    unsafe { LMUL += n }
}
#[inline(always)]
pub fn bump_ladd(n: u64) {
    unsafe { LADD += n }
}
#[inline(always)]
pub fn bump_hash(n: u64) {
    unsafe { HASH += n }
}
#[inline(always)]
pub fn bump_cmp(n: u64) {
    unsafe { CMP += n }
}


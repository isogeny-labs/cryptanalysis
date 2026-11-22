//! Adapter preserving the mirror's existing optional phase/group recorder.

use crate::Result;

pub(crate) fn phase(name: &'static str) -> Result<()> {
    crate::metrics::phase(name)
}

pub(crate) fn batch_group(doubling: bool) -> Result<()> {
    crate::metrics::group(doubling)
}

#[cfg(test)]
pub(crate) fn observe_group_calls<T>(
    meter: &mut crate::Meter,
    run: impl FnOnce(&mut crate::Meter) -> T,
) -> (T, u64) {
    let session = crate::metrics::Session::start().expect("isolated test metric session");
    let result = run(meter);
    let snapshot = session.finish().expect("test metric session finish");
    let groups = snapshot
        .phases
        .values()
        .map(|phase| phase.adds + phase.doubles)
        .sum();
    (result, groups)
}

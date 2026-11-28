// Rejected development implementation for pair_index.rs, retained for replay.
// This replaced KeyHasher and the Lookup type at the top of that file.
// Construction used `lookup: Lookup::new(size)?`; flush_build changed
// `self.lookup.get(&p.x()).copied()` to `self.lookup.get(p.x())`; find changed
// `*self.lookup.get(&p.x())?` to `self.lookup.get(p.x())?`. The existing insert
// call did not change. The HashMap and std::hash imports were removed.
struct Lookup {
    slots: Vec<Option<(u64, usize)>>,
    mask: usize,
}
impl Lookup {
    fn new(max_entries: usize) -> Result<Self> {
        let capacity = max_entries
            .checked_add(1)
            .and_then(usize::checked_next_power_of_two)
            .ok_or(Error::ResourceLimit("pair lookup size overflow"))?;
        Ok(Self {
            slots: vec![None; capacity],
            mask: capacity - 1,
        })
    }
    fn slot(&self, x: u64) -> usize {
        ((x.wrapping_mul(0x9e3779b97f4a7c15) >> 32) as usize) & self.mask
    }
    fn get(&self, x: u64) -> Option<usize> {
        let mut slot = self.slot(x);
        loop {
            match self.slots[slot] {
                None => return None,
                Some((key, index)) if key == x => return Some(index),
                Some(_) => slot = (slot + 1) & self.mask,
            }
        }
    }
    fn insert(&mut self, x: u64, index: usize) {
        let mut slot = self.slot(x);
        loop {
            match self.slots[slot] {
                None => {
                    self.slots[slot] = Some((x, index));
                    return;
                }
                Some((key, _)) if key == x => {
                    self.slots[slot] = Some((x, index));
                    return;
                }
                Some(_) => slot = (slot + 1) & self.mask,
            }
        }
    }
}

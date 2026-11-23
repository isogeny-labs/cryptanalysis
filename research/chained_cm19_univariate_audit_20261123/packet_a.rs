use crate::{need, AResult};

pub const SHAPES: [([u8; 4], usize, usize, usize); 13] = [
    (*b"E4XS", 117_649, 0, 14_707),
    (*b"E4PT", 16, 9, 144),
    (*b"E4AD", 256, 1, 256),
    (*b"E4FR", 16, 3, 48),
    (*b"E4WP", 256, 1, 256),
    (*b"FIBR", 15, 166, 2490),
    (*b"J4MP", 4096, 7, 28_672),
    (*b"KERN", 64, 2, 128),
    (*b"K4WP", 4096, 1, 4096),
    (*b"E11P", 11, 9, 99),
    (*b"E11A", 121, 1, 121),
    (*b"J11M", 1331, 6, 7986),
    (*b"ELDL", 11, 6, 66),
];

pub struct Reader<'a> {
    pub bytes: &'a [u8],
    offset: usize,
}
impl<'a> Reader<'a> {
    pub fn new(bytes: &'a [u8]) -> Self {
        Self { bytes, offset: 0 }
    }
    pub fn take(&mut self, n: usize) -> AResult<&'a [u8]> {
        let end = self.offset.checked_add(n).ok_or("packet offset overflow")?;
        let result = self.bytes.get(self.offset..end).ok_or("incomplete packet bytes")?;
        self.offset = end;
        Ok(result)
    }
    pub fn u8(&mut self) -> AResult<u8> {
        Ok(self.take(1)?[0])
    }
    pub fn u16(&mut self) -> AResult<usize> {
        let bytes: [u8; 2] = self.take(2)?.try_into().map_err(|_| "u16 width")?;
        Ok(usize::from(u16::from_le_bytes(bytes)))
    }
    pub fn u32(&mut self) -> AResult<u32> {
        let bytes: [u8; 4] = self.take(4)?.try_into().map_err(|_| "u32 width")?;
        Ok(u32::from_le_bytes(bytes))
    }
    pub fn end(&self) -> AResult<()> {
        need(self.offset == self.bytes.len(), "unconsumed packet payload")
    }
}

pub struct Section<'a> {
    pub tag: [u8; 4],
    pub start: usize,
    pub bytes: &'a [u8],
}
pub struct Packet<'a> {
    pub sections: Vec<Section<'a>>,
}
impl<'a> Packet<'a> {
    pub fn parse(bytes: &'a [u8]) -> AResult<Self> {
        need(bytes.len() == 59_325, "full original packet length")?;
        let mut input = Reader::new(bytes);
        need(input.take(8)? == b"CTJ4A001", "packet magic")?;
        need(input.u32()? == 1 && input.u32()? == 117_649, "packet version/field")?;
        for expected in [16, 11, 4096, 64, 1331, 15] {
            need(input.u32()? == expected, "packet planned cohort")?;
        }
        let mut sections = Vec::new();
        for (tag, count, width, length) in SHAPES {
            need(input.take(4)? == tag, "packet section order/tag")?;
            need(input.u32()? as usize == count, "packet section count")?;
            need(input.u32()? as usize == width, "packet record width")?;
            need(input.u32()? as usize == length, "packet payload length")?;
            let start = input.offset;
            sections.push(Section { tag, start, bytes: input.take(length)? });
        }
        need(input.take(8)? == b"COMPLETE", "packet completion footer")?;
        input.end()?;
        Ok(Self { sections })
    }
    pub fn section(&self, tag: &[u8; 4]) -> &Section<'a> {
        self.sections.iter().find(|s| &s.tag == tag).expect("all fixed sections parsed")
    }
}

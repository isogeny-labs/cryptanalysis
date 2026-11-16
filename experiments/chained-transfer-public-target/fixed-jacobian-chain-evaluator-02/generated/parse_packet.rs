fn parse_packet(
    field: &str,
    model: &str,
    key: &[u32; 19],
    wanted_field: &str,
    wanted_model: &str,
) -> Result<PicClass> {
    if field != wanted_field || model != wanted_model || key.iter().any(|&x| x >= 223) {
        return Err("foreign or noncanonical class".into());
    }
    match key[0] {
        0 => {
            if key[4..].iter().any(|&x| x != 0) {
                return Err("exceptional trailing data".into());
            }
            Ok(PicClass::Exc([key[1], key[2], key[3]]))
        }
        1 => Ok(PicClass::Typ(std::array::from_fn(|i| {
            std::array::from_fn(|j| key[1 + 6 * i + j])
        }))),
        _ => Err("unknown class tag".into()),
    }
}


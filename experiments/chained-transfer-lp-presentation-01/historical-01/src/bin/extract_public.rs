use chained_transfer_lp_historical_01::public_view::{
    encode, extract_feedback_control, extract_original,
};
use std::{
    error::Error,
    fs::{self, OpenOptions},
    io::Write,
};

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args().collect();
    let (view, destination) = match args.as_slice() {
        [_, mode, original, destination] if mode == "--primary" => (extract_original(&fs::read(original)?)?, destination),
        [_, mode, original, control, destination] if mode == "--feedback-control" => (extract_feedback_control(&fs::read(original)?, &fs::read(control)?)?, destination),
        _ => return Err("usage: extract_public --primary ORIGINAL OUT | --feedback-control ORIGINAL CONTROL OUT".into()),
    };
    let encoded = encode(&view)?;
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(destination)?;
    file.write_all(&encoded)?;
    file.sync_all()?;
    Ok(())
}

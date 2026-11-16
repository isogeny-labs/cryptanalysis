use chained_transfer_lp_historical_01::{controls, stream};
use std::{
    error::Error,
    fs::{self, File, OpenOptions},
    io::{BufReader, BufWriter, Write},
};

fn output(path: &str) -> Result<BufWriter<File>, Box<dyn Error>> {
    Ok(BufWriter::new(
        OpenOptions::new().write(true).create_new(true).open(path)?,
    ))
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args().collect();
    match args.as_slice() {
        [_, mode, kind, certificate, destination] if mode == "tamper-certificate" => {
            let mut out = output(destination)?;
            controls::certificate(&mut BufReader::new(File::open(certificate)?), &mut out, kind.as_str().try_into()?)?;
            out.flush()?;
            out.get_ref().sync_all()?;
        }
        [_, mode, kind, public, destination] if mode == "tamper-public" => {
            let original = fs::read(public)?;
            let bytes = match kind.as_str() {
                "raw-graph" => controls::raw_graph(&original)?,
                "oracle" => controls::oracle(&original)?,
                _ => return Err("unknown public control".into()),
            };
            let mut out = output(destination)?;
            out.write_all(&bytes)?;
            out.flush()?;
            out.get_ref().sync_all()?;
        }
        [_, mode, original, destination] if mode == "feedback-copy" => {
            let bytes = controls::feedback_copy(&fs::read(original)?)?;
            let mut out = output(destination)?;
            out.write_all(&bytes)?;
            out.flush()?;
            out.get_ref().sync_all()?;
        }
        [_, mode, first, second] if mode == "compare-feedback" => {
            controls::equal_scientific_bodies(&mut BufReader::new(File::open(first)?), &mut BufReader::new(File::open(second)?))?;
        }
        [_, mode, public, destination] if mode == "produce" => {
            let mut out = output(destination)?;
            stream::produce_public(&fs::read(public)?, &mut out)?;
            out.flush()?;
            out.get_ref().sync_all()?;
        }
        [_, mode, original, public, certificate, destination] if mode == "replay-primary" => {
            let mut out = output(destination)?;
            stream::verify_primary(&fs::read(original)?, &fs::read(public)?,
                &mut BufReader::new(File::open(certificate)?), &mut out)?;
            out.flush()?;
            out.get_ref().sync_all()?;
        }
        [_, mode, original, control, public, certificate, destination] if mode == "replay-feedback" => {
            let mut out = output(destination)?;
            stream::verify_feedback(&fs::read(original)?, &fs::read(control)?, &fs::read(public)?,
                &mut BufReader::new(File::open(certificate)?), &mut out)?;
            out.flush()?;
            out.get_ref().sync_all()?;
        }
        _ => return Err("usage: historical_certificates produce PUBLIC OUT | replay-primary ORIGINAL PUBLIC CERT OUT | replay-feedback ORIGINAL CONTROL PUBLIC CERT OUT | tamper-certificate KIND CERT OUT | tamper-public KIND PUBLIC OUT | feedback-copy ORIGINAL OUT | compare-feedback FIRST SECOND".into()),
    }
    Ok(())
}

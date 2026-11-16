//! Data-only build prerequisite for the unchanged original checker tests.
//! Restore the authentic compile-time fixture from the immutable Root revision;
//! never regenerate a certificate or replace existing different bytes.
#[allow(dead_code)]
#[path = "../../../../crypto/src/hash/sha256.rs"]
mod original_sha256;

use std::{error::Error, fs, path::PathBuf, process::Command};

const ROOT_SOURCE: &str = "2d46258afc20188b8593b3a0693183d1282e0aaf";
const FIXTURE: &str = "docs/identity-certificates/schoenhage-10mult.json";
const EXPECTED_SHA256: &str = "84a61d6ccc237b724695e8f1416e9ad48f24c899ae316512bf0b952e46edb293";

fn main() -> Result<(), Box<dyn Error>> {
    let manifest =
        PathBuf::from(std::env::var_os("CARGO_MANIFEST_DIR").ok_or("manifest directory missing")?);
    let root = manifest.join("../../../../crypto").canonicalize()?;
    let destination = root.join(FIXTURE);
    let bytes = if destination.exists() {
        if destination.is_symlink() {
            return Err("original fixture must be a regular file".into());
        }
        fs::read(&destination)?
    } else {
        let output = Command::new("git")
            .arg("-C")
            .arg(&root)
            .arg("show")
            .arg(format!("{ROOT_SOURCE}:{FIXTURE}"))
            .output()?;
        if !output.status.success() {
            return Err(format!(
                "immutable original fixture unavailable: {}",
                String::from_utf8_lossy(&output.stderr)
            )
            .into());
        }
        output.stdout
    };
    let digest: String = original_sha256::sha256(&bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect();
    if digest != EXPECTED_SHA256 {
        return Err(
            "existing/original fixture differs from its frozen SHA256; no overwrite".into(),
        );
    }
    if !destination.exists() {
        fs::create_dir_all(destination.parent().ok_or("fixture parent missing")?)?;
        fs::write(&destination, &bytes)?;
        eprintln!("restored complete immutable original identity fixture {ROOT_SOURCE}:{FIXTURE}");
    }
    println!("cargo:rerun-if-changed={}", destination.display());
    println!("cargo:rerun-if-changed=build.rs");
    Ok(())
}

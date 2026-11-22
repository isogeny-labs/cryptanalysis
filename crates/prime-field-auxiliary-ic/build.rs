use std::{env, process::Command};

fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-env-changed=RUSTC");
    let rustc = env::var_os("RUSTC").unwrap_or_else(|| "rustc".into());
    let Ok(output) = Command::new(rustc).arg("--version").output() else {
        return;
    };
    let text = String::from_utf8_lossy(&output.stdout);
    let version = text.split_whitespace().nth(1).unwrap_or("");
    let mut parts = version.split('.');
    let major = parts.next().and_then(|s| s.parse::<u32>().ok());
    let minor = parts.next().and_then(|s| s.parse::<u32>().ok());
    if major == Some(1) && minor.is_some_and(|v| v >= 80) {
        println!("cargo:rustc-check-cfg=cfg(auxiliary_ic_avx512)");
    }
    if major == Some(1) && minor.is_some_and(|v| v >= 89) {
        println!("cargo:rustc-cfg=auxiliary_ic_avx512");
    }
}

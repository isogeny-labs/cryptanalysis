//! End-to-end tests of `ca-ic fbkit` (list, explain, sweep, resume, rank,
//! export, S3 round trip against the `fake_aws.sh` stub, exit codes).

use serde_json::Value;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicUsize, Ordering};

static NEXT: AtomicUsize = AtomicUsize::new(0);

fn scratch(tag: &str) -> PathBuf {
    let p = std::env::temp_dir().join(format!(
        "ic-fbkit-test-{}-{}-{tag}",
        std::process::id(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    let _ = std::fs::remove_dir_all(&p);
    p
}

fn stub() -> String {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/fixtures/fake_aws.sh")
        .to_string_lossy()
        .into_owned()
}

/// Run `ca-ic <args> --json` with a clean S3 environment plus `envs`.
fn command(args: &[&str], envs: &[(&str, &str)]) -> (bool, Value) {
    let mut c = Command::new(env!("CARGO_BIN_EXE_ca-ic"));
    c.args(args)
        .arg("--json")
        .env_remove("FBKIT_S3_URI")
        .env_remove("IC_ARCHIVE_S3_URI")
        .env_remove("FBKIT_AWS_BIN");
    for (k, v) in envs {
        c.env(k, v);
    }
    let output = c.output().unwrap();
    let value = serde_json::from_slice(&output.stdout)
        .unwrap_or_else(|_| panic!("not JSON: {:?} {:?}", output.stdout, output.stderr));
    (output.status.success(), value)
}

fn sweep_args<'a>(dir: &'a str, m: &'a str, dims: &'a str) -> Vec<&'a str> {
    vec![
        "fbkit",
        "sweep",
        "--koblitz-degree",
        "11",
        "--curve-a",
        "1",
        "--families",
        "coordinate,geometric",
        "--dims",
        dims,
        "--m",
        m,
        "--metrics",
        "construction,yield,f4,sat",
        "--targets",
        "4",
        "--budget-seconds",
        "5",
        "--jobs",
        "4",
        "--dir",
        dir,
    ]
}

/// `^PS1N\d+C[a-z0-9]+fb\d+PDP\d+[a-z0-9]+h[0-9a-f]{12}$` without a regex crate.
fn is_ps1_label(s: &str) -> bool {
    let digits = |s: &str| -> (usize, usize) {
        let n = s.bytes().take_while(u8::is_ascii_digit).count();
        (n, n)
    };
    let Some(rest) = s.strip_prefix("PS1N") else {
        return false;
    };
    let (n, _) = digits(rest);
    let Some(rest) = rest[n..].strip_prefix('C').filter(|_| n > 0) else {
        return false;
    };
    let Some((head, hash)) = rest.rsplit_once('h') else {
        return false;
    };
    if hash.len() != 12
        || !hash
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    {
        return false;
    }
    // head = <tag>fb<digits>PDP<digits><solver>; the tag and solver are [a-z0-9]+
    let Some(fb) = head.find("fb") else {
        return false;
    };
    let after_fb = &head[fb + 2..];
    let (n1, _) = digits(after_fb);
    let Some(after) = after_fb[n1..].strip_prefix("PDP").filter(|_| n1 > 0) else {
        return false;
    };
    let (n2, _) = digits(after);
    fb > 0
        && n2 > 0
        && after.len() > n2
        && after[n2..]
            .bytes()
            .all(|b| b.is_ascii_digit() || b.is_ascii_lowercase())
        && head[..fb]
            .bytes()
            .all(|b| b.is_ascii_digit() || b.is_ascii_lowercase())
}

#[test]
fn list_and_explain() {
    let (ok, v) = command(&["fbkit", "list"], &[]);
    assert!(ok);
    assert_eq!(v["operation"], "fbkit-list");
    let fams = v["families"].as_array().unwrap();
    assert!(fams.len() >= 40, "{} families", fams.len());
    for f in fams {
        assert!(
            f["prior_verdict"].as_str().is_some_and(|s| !s.is_empty()),
            "{f}"
        );
    }
    assert!(v["what_this_is_not"]
        .as_str()
        .unwrap()
        .contains("not an IC1 result"));
    let (ok, v) = command(&["fbkit", "explain", "geometric"], &[]);
    assert!(ok);
    assert_eq!(v["operation"], "fbkit-explain");
    assert_eq!(v["family"]["name"], "geometric");
    assert!(v["markdown"].as_str().unwrap().contains("Citations"));
    let (ok, v) = command(&["fbkit", "explain", "no-such-family"], &[]);
    assert!(!ok);
    assert_eq!(v["status"], "error");
}

#[test]
fn sweep_resume_rank_export_and_s3_round_trip() {
    let dir = scratch("run");
    let d = dir.to_str().unwrap();
    let (ok, v) = command(&sweep_args(d, "2,3", "3-4"), &[]);
    assert!(ok, "{v}");
    assert_eq!(v["operation"], "fbkit-sweep");
    assert_eq!(v["status"], "complete", "{v}");
    assert_eq!(v["counts"]["total"], 8);
    assert_eq!(v["counts"]["run"], 8);
    assert_eq!(v["cells"].as_array().unwrap().len(), 8);
    for key in [
        "cell_id",
        "family",
        "l",
        "m",
        "status",
        "fb_points",
        "effective_columns",
        "coverage",
        "expected_trials",
        "solving_degree_mean",
        "sat_clauses",
        "conflicts_mean",
        "expected_pdp_ops",
    ] {
        assert!(v["cells"][0].get(key).is_some(), "row lacks {key}");
    }
    assert_eq!(std::fs::read_dir(dir.join("cells")).unwrap().count(), 8);
    for f in [
        "ranking.json",
        "report.md",
        "report.json",
        "inventory.json",
        "manifest.json",
        "curve.json",
    ] {
        assert!(dir.join(f).is_file(), "{f} missing");
    }
    assert!(std::fs::read_dir(dir.join("points")).unwrap().count() >= 1);
    let curve_id = v["curve_id"].as_str().unwrap().to_string();
    let sweep_id = v["sweep_id"].as_str().unwrap().to_string();
    assert!(curve_id.starts_with("EC1N11Ckb1h"));

    // A non-empty directory is refused without --resume.
    let (ok, e) = command(&sweep_args(d, "2,3", "3-4"), &[]);
    assert!(!ok);
    assert_eq!(e["status"], "error");

    // --resume re-runs nothing.
    let mut args = sweep_args(d, "2,3", "3-4");
    args.push("--resume");
    let (ok, r) = command(&args, &[]);
    assert!(ok, "{r}");
    assert_eq!(r["counts"]["run"], 0, "{r}");
    assert_eq!(r["counts"]["skipped"], 8);
    assert!(r["elapsed_seconds"].as_f64().unwrap() < v["elapsed_seconds"].as_f64().unwrap());
    // A different manifest cannot resume into this directory.
    let mut other = sweep_args(d, "2", "3-4");
    other.push("--resume");
    let (ok, e) = command(&other, &[]);
    assert!(!ok, "{e}");
    assert!(e["message"].as_str().unwrap().contains("holds sweep"));

    // rank
    let (ok, r) = command(
        &["fbkit", "rank", "--dir", d, "--objective", "solving-degree"],
        &[],
    );
    assert!(ok, "{r}");
    assert_eq!(r["operation"], "fbkit-rank");
    assert_eq!(r["ranking"]["objective"], "solving-degree");
    let (ok, e) = command(&["fbkit", "rank", "--dir", d, "--objective", "bogus"], &[]);
    assert!(!ok, "{e}");

    // export
    let first = v["cells"][0]["cell_id"].as_str().unwrap();
    let (ok, x) = command(&["fbkit", "export", "--dir", d, "--cell", first], &[]);
    assert!(ok, "{x}");
    assert_eq!(x["schema"], "ic-factor-base-archive/1");
    assert_eq!(x["archive"]["schema"], "ic-factor-base-archive/1");
    let label = x["ps1_label"].as_str().unwrap();
    assert!(is_ps1_label(label), "{label}");
    assert!(x["candidate_id"].is_null());
    assert_eq!(x["archive"]["curve"]["curve_id"], curve_id.as_str());
    // Export refuses to overwrite an existing archive file.
    let arch = scratch("arch.json");
    let a = arch.to_str().unwrap();
    let (ok, _) = command(
        &[
            "fbkit",
            "export",
            "--dir",
            d,
            "--cell",
            first,
            "--archive-out",
            a,
        ],
        &[],
    );
    assert!(ok);
    assert!(arch.is_file());
    let (ok, e) = command(
        &[
            "fbkit",
            "export",
            "--dir",
            d,
            "--cell",
            first,
            "--archive-out",
            a,
        ],
        &[],
    );
    assert!(!ok, "{e}");
    let _ = std::fs::remove_file(&arch);

    // Upload and download round trip against the stub bucket.
    let bucket = scratch("bucket");
    std::fs::create_dir_all(&bucket).unwrap();
    let envs = [
        ("FBKIT_AWS_BIN", stub()),
        ("FAKE_AWS_ROOT", bucket.to_string_lossy().into_owned()),
    ];
    let envs: Vec<(&str, &str)> = envs.iter().map(|(k, v)| (*k, v.as_str())).collect();
    let (ok, dry) = command(
        &[
            "fbkit",
            "upload",
            "--dir",
            d,
            "--s3",
            "s3://fake/prefix",
            "--dry-run",
        ],
        &envs,
    );
    assert!(ok, "{dry}");
    assert_eq!(dry["upload_status"], "dry_run");
    let (ok, up) = command(
        &["fbkit", "upload", "--dir", d, "--s3", "s3://fake/prefix"],
        &envs,
    );
    assert!(ok, "{up}");
    assert_eq!(up["status"], "complete");
    assert!(up["receipt"].as_str().is_some());
    let uri = format!("s3://fake/prefix/fbkit/{curve_id}/{sweep_id}");
    assert_eq!(up["destination"], uri.as_str());
    let dir2 = scratch("down");
    let d2 = dir2.to_str().unwrap();
    let (ok, dl) = command(&["fbkit", "download", "--s3", &uri, "--dir", d2], &envs);
    assert!(ok, "{dl}");
    assert_eq!(dl["status"], "complete");
    assert_eq!(
        std::fs::read(dir.join("inventory.json")).unwrap(),
        std::fs::read(dir2.join("inventory.json")).unwrap()
    );
    let (ok, vo) = command(&["fbkit", "download", "--dir", d2, "--verify-only"], &[]);
    assert!(ok, "{vo}");
    // Tampering is caught by --verify-only.
    let victim = std::fs::read_dir(dir2.join("cells"))
        .unwrap()
        .next()
        .unwrap()
        .unwrap()
        .path();
    std::fs::write(&victim, b"{}").unwrap();
    let (ok, bad) = command(&["fbkit", "download", "--dir", d2, "--verify-only"], &[]);
    assert!(!ok, "{bad}");
    for p in [dir, dir2, bucket] {
        let _ = std::fs::remove_dir_all(p);
    }
}

#[test]
fn upload_without_destination_skips_or_fails_on_require() {
    let dir = scratch("skip");
    let d = dir.to_str().unwrap();
    let (ok, v) = command(
        &[
            "fbkit",
            "build",
            "--koblitz-degree",
            "7",
            "--curve-a",
            "1",
            "--family",
            "coordinate:l=3",
            "--m",
            "2",
            "--dir",
            d,
        ],
        &[],
    );
    assert!(ok, "{v}");
    assert_eq!(v["operation"], "fbkit-build");
    let (ok, s) = command(&["fbkit", "upload", "--dir", d], &[]);
    assert!(ok, "{s}");
    assert_eq!(s["status"], "skipped");
    let (ok, r) = command(&["fbkit", "upload", "--dir", d, "--require"], &[]);
    assert!(!ok, "{r}");
    assert_eq!(r["status"], "error");
    let (ok, bad) = command(&["fbkit", "upload", "--dir", d, "--s3", "not-a-uri"], &[]);
    assert!(!ok, "{bad}");
    let _ = std::fs::remove_dir_all(dir);
}

#[test]
fn m_beyond_the_variable_cap_measures_construction_and_yield_only() {
    let dir = scratch("m8");
    let d = dir.to_str().unwrap();
    let (ok, v) = command(
        &[
            "fbkit",
            "sweep",
            "--koblitz-degree",
            "7",
            "--curve-a",
            "1",
            "--families",
            "coordinate",
            "--dims",
            "3",
            "--m",
            "2,8",
            "--metrics",
            "construction,yield,f4,sat",
            "--targets",
            "4",
            "--budget-seconds",
            "5",
            "--jobs",
            "2",
            "--dir",
            d,
        ],
        &[],
    );
    assert!(ok, "{v}");
    assert_eq!(v["counts"]["total"], 2);
    let cells = std::fs::read_dir(dir.join("cells")).unwrap();
    let mut saw = false;
    for c in cells {
        let c: Value = serde_json::from_slice(&std::fs::read(c.unwrap().path()).unwrap()).unwrap();
        if c["m"] == 8 {
            saw = true;
            assert!(c["metrics"]["construction"]["fb_points"].as_u64().is_some());
            assert!(c["metrics"]["yield"]["coverage"].is_number());
            for g in ["f4", "sat"] {
                let why = c["metrics"][g]["reason"].as_str().unwrap();
                assert!(
                    why.contains("n_vars") && why.contains("not_applicable"),
                    "{why}"
                );
                assert_eq!(c["metrics"][g]["measured"], false);
            }
        }
    }
    assert!(saw, "no m = 8 cell");
    let _ = std::fs::remove_dir_all(dir);
}

#[test]
fn curve_selectors_are_validated_and_out_never_overwrites() {
    let (ok, e) = command(&["fbkit", "build", "--family", "coordinate:l=3"], &[]);
    assert!(!ok);
    assert!(e["message"].as_str().unwrap().contains("curve selector"));
    let (ok, e) = command(
        &[
            "fbkit",
            "build",
            "--koblitz-degree",
            "7",
            "--curve-a",
            "1",
            "--bits",
            "16",
            "--family",
            "coordinate:l=3",
        ],
        &[],
    );
    assert!(!ok);
    assert!(e["message"].as_str().unwrap().contains("conflicting"));
    // A named profile past the supported degree is skipped, not a panic.
    let (ok, s) = command(
        &[
            "fbkit",
            "build",
            "--curve",
            "ecc2k-130",
            "--family",
            "coordinate:l=3",
        ],
        &[],
    );
    assert!(ok, "{s}");
    assert_eq!(s["status"], "skipped");
    // --out refuses an existing file.
    let out = scratch("out.json");
    std::fs::write(&out, b"keep").unwrap();
    let status = Command::new(env!("CARGO_BIN_EXE_ca-ic"))
        .args(["fbkit", "list", "--json", "--out"])
        .arg(&out)
        .status()
        .unwrap();
    assert!(!status.success());
    assert_eq!(std::fs::read(&out).unwrap(), b"keep");
    let _ = std::fs::remove_file(out);
}

//! Import the mathematical records and straight-line programs, not web prose.
//! Network retrieval uses curl; parsing, hashing and generation are native Rust.
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::{
    env, fs,
    path::{Path, PathBuf},
    process::Command,
};

const BASE: &str = "https://www.hyperelliptic.org/EFD/g12o/";

fn links(s: &str) -> BTreeSet<String> {
    s.split("href=\"")
        .skip(1)
        .filter_map(|x| x.split('"').next())
        .map(str::to_owned)
        .collect()
}

fn fetch(cache: &Path, path: &str) -> Result<String, String> {
    if path.contains("..") || path.starts_with('/') || path.contains(':') {
        return Err(format!("unsafe source path: {path}"));
    }
    let dest = cache.join(path);
    if let Ok(s) = fs::read_to_string(&dest) {
        return Ok(s);
    }
    let url = format!("{BASE}{path}");
    let result = Command::new("curl")
        .args([
            "--fail",
            "--silent",
            "--show-error",
            "--location",
            "--max-time",
            "45",
            "--retry",
            "2",
            &url,
        ])
        .output()
        .map_err(|e| e.to_string())?;
    if !result.status.success() {
        return Err(format!(
            "fetch {url}: {}",
            String::from_utf8_lossy(&result.stderr)
        ));
    }
    let s = String::from_utf8(result.stdout).map_err(|e| e.to_string())?;
    fs::create_dir_all(dest.parent().unwrap()).map_err(|e| e.to_string())?;
    fs::write(dest, &s).map_err(|e| e.to_string())?;
    Ok(s)
}

fn source(path: &str, text: String) -> Value {
    json!({"url":format!("{BASE}{path}"), "sha256":format!("{:x}",Sha256::digest(text.as_bytes())), "text":text})
}

fn values(s: &str, prefix: &str) -> Vec<String> {
    s.lines()
        .filter_map(|l| l.strip_prefix(prefix).map(str::to_owned))
        .collect()
}

fn run() -> Result<(), String> {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        return Err("usage: efd-import CACHE_DIRECTORY OUTPUT_JSON".into());
    }
    let cache = PathBuf::from(&args[1]);
    let index = fetch(&cache, "index.html")?;
    let pages: Vec<_> = links(&index)
        .into_iter()
        .filter(|p| p.starts_with("auto-") && p.ends_with(".html") && p.matches('-').count() >= 2)
        .collect();
    if pages.len() != 19 {
        return Err(format!(
            "expected 19 representations, found {}",
            pages.len()
        ));
    }
    let mut representations = Vec::new();
    let mut paths = BTreeSet::new();
    let mut models = BTreeSet::new();
    for page in pages {
        let html = fetch(&cache, &page)?;
        let ls = links(&html);
        let var_path = ls
            .iter()
            .find(|s| s.starts_with("data/") && s.ends_with("/variables"))
            .ok_or_else(|| format!("no variables for {page}"))?;
        let text = fetch(&cache, var_path)?;
        let id = var_path
            .trim_start_matches("data/")
            .trim_end_matches("/variables");
        models.insert(id.split('/').next().unwrap().to_owned());
        paths.extend(
            ls.iter()
                .filter(|s| s.starts_with("auto-code/") && s.ends_with(".op3"))
                .cloned(),
        );
        representations.push(json!({"id":id,"page_url":format!("{BASE}{page}"),
            "variables":values(&text,"variable "),"relations":values(&text,"satisfying "),
            "assumptions":values(&text,"assume "),"source":source(var_path,text)}));
    }
    let mut model_records = Vec::new();
    for model in models {
        let page = format!("auto-{model}.html");
        let html = fetch(&cache, &page)?;
        let ls = links(&html);
        let path = ls
            .iter()
            .find(|s| s.starts_with("data/") && s.ends_with("/coordinates"))
            .ok_or_else(|| format!("no model coordinates for {model}"))?;
        let text = fetch(&cache, path)?;
        model_records.push(json!({"id":model,"source":source(path,text)}));
    }
    let paths: Vec<_> = paths.into_iter().collect();
    let results = std::thread::scope(|scope| {
        let handles:Vec<_>=paths.chunks(paths.len().div_ceil(4)).map(|chunk|{
            let cache=&cache;
            scope.spawn(move|| -> Result<Vec<Value>,String> {
                let mut formulas=Vec::new();
                for op_path in chunk {
                    let id=op_path.trim_start_matches("auto-code/").trim_end_matches(".op3");
                    let data_path=format!("data/{id}");
                    let record=fetch(cache,&data_path)?;
                    let program=fetch(cache,op_path)?;
                    let parts:Vec<_>=id.split('/').collect();
                    if parts.len()!=4 { return Err(format!("invalid formula id {id}")); }
                    formulas.push(json!({"id":id,"representation":format!("{}/{}",parts[0],parts[1]),
                        "operation":parts[2],"name":parts[3],"assumptions":values(&record,"assume "),
                        "record":source(&data_path,record),"program":source(op_path,program),
                        "upstream_verification_url":format!("{BASE}auto-sage/{id}.sage")}));
                }
                Ok(formulas)
            })
        }).collect();
        handles
            .into_iter()
            .map(|h| h.join().map_err(|_| "import worker panicked".to_owned())?)
            .collect::<Result<Vec<_>, String>>()
    })?;
    let mut formulas: Vec<_> = results.into_iter().flatten().collect();
    formulas.sort_by(|a, b| a["id"].as_str().cmp(&b["id"].as_str()));
    if formulas.len() != 135 {
        return Err(format!("expected 135 formulas, found {}", formulas.len()));
    }
    let date = Command::new("date")
        .args(["-u", "+%F"])
        .output()
        .map_err(|e| e.to_string())?;
    if !date.status.success() {
        return Err("could not record retrieval date".into());
    }
    let retrieved = String::from_utf8(date.stdout).map_err(|e| e.to_string())?;
    let out = json!({"schema":"efd-binary-catalogue/v1","source_url":format!("{BASE}index.html"),
        "retrieved":retrieved.trim(),"characteristic":2,"models":model_records,
        "representations":representations,"formulas":formulas});
    let dest = PathBuf::from(&args[2]);
    fs::create_dir_all(dest.parent().unwrap()).map_err(|e| e.to_string())?;
    fs::write(
        &dest,
        format!("{}\n", serde_json::to_string_pretty(&out).unwrap()),
    )
    .map_err(|e| e.to_string())?;
    eprintln!(
        "imported {} formulas in {} representations to {}",
        out["formulas"].as_array().unwrap().len(),
        out["representations"].as_array().unwrap().len(),
        dest.display()
    );
    Ok(())
}

fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}

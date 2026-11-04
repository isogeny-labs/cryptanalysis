//! File/stdin consumer of structured prime-field counting and prefix witnesses.
fn main() {
    if let Err(error) = hashed_ecdl_tensor::structured_runner::command_line() {
        eprintln!("tensor-structured: {error}");
        std::process::exit(1);
    }
}

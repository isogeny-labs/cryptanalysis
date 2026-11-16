fn show(name: &str) {
    println!("HARNESS_THREAD {} {:?}", name, std::thread::current().id());
}
#[test]
fn a() { show("a"); }
#[test]
fn b() { show("b"); }
#[test]
fn c() { show("c"); }
#[test]
fn d() { show("d"); }

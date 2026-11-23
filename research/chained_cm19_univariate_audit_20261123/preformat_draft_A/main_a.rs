#[path="field_a.rs"] mod field;
#[path="packet_a.rs"] mod packet;
#[path="ec_a.rs"] mod ec;
#[path="cm_a.rs"] mod cm;
#[path="geometry_a.rs"] mod geometry;
#[path="verify_a.rs"] mod verify;

type AResult<T> = Result<T,&'static str>;
fn need(condition:bool,message:&'static str) -> AResult<()> {
    if condition {Ok(())} else {Err(message)}
}

fn run() -> Result<(),String> {
    let args:Vec<_>=std::env::args().collect();
    if args.len()!=2 {return Err("usage: qualifier ORIGINAL_PACKET".to_owned());}
    let original=std::fs::read(&args[1]).map_err(|e|format!("input: {e}"))?;
    println!("CT_CM19_UNIVARIATE_AUDIT_A\toriginal_bytes={}\tnew_source_first_call\tno_search_replay",original.len());
    verify::verify(&original).map_err(str::to_owned)?;
    let packet=packet::Packet::parse(&original).map_err(str::to_owned)?;
    let controls=[
        ("actual_scan_bit",packet.section(b"E4XS").start),
        ("actual_Weil_4_6",packet.section(b"E4WP").start+4*16+6),
        ("actual_J4_S_target",packet.section(b"J4MP").start+7),
        ("actual_f0_X_coefficient",packet.section(b"FIBR").start+7),
        ("actual_section_count",44),
        ("actual_completion_footer",original.len()-1),
    ];
    for (name,offset) in controls {
        let mut changed=original.clone();changed[offset]^=1;
        let rejection=verify::verify(&changed).err().ok_or_else(||format!("changed certificate accepted: {name}"))?;
        println!("ACTUAL_PACKET_MUTATION\t{name}\toffset={offset}\trejected={rejection}");
        verify::verify(&original).map_err(|e|format!("pristine restore after {name}: {e}"))?;
        println!("PRISTINE_RESTORE\t{name}\tPASS");
    }
    println!("COMPLETE_SEPARATE_AUDIT\tall13_original_sections\tall_fixed_cohorts\tsix_semantic_format_controls\tPASS");
    Ok(())
}
fn main() {
    if let Err(error)=run() {eprintln!("AUDIT_FAILURE\t{error}");std::process::exit(1);}
}

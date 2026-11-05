use ecdlp_surfaces::{
    bigint::BigInt,
    cli::Args,
    frobenius::filter,
    json::{big, boolean, number, object, text, Json},
    Result,
};

const HELP: &str = "frobenius_filter [--q 101] [--trace -7] [--coeffs 14,251,1414,10201]\n\
  [--output file.json]\n\
Integers (q, trace, coeffs) are arbitrary precision: decimal, or 2^k, e.g. --q 2^83.\n\
Input surface polynomial: T^4+c1*T^3+c2*T^2+c3*T+c4 (coeffs=c1,c2,c3,c4).\n\
Source polynomial: T^2-trace*T+q. Defaults describe E x E for the example curve.\n\
Passing is a necessary-condition filter; it does not construct a transfer map.";

fn run() -> Result<()> {
    let args = Args::parse(&["q", "trace", "coeffs", "output"])?;
    if args.help {
        println!("{HELP}");
        return Ok(());
    }
    let pieces = args
        .get("coeffs")
        .unwrap_or("14,251,1414,10201")
        .split(',')
        .map(|piece| BigInt::parse(piece).map_err(|_| "Invalid polynomial coefficient.".to_owned()))
        .collect::<Result<Vec<_>>>()?;
    let coefficients: [BigInt; 4] = pieces
        .try_into()
        .map_err(|_| "Supply exactly four coefficients c1,c2,c3,c4.")?;
    let integer = |key: &str, default: &str| BigInt::parse(args.get(key).unwrap_or(default));
    let result = filter(integer("q", "101")?, integer("trace", "-7")?, coefficients)?;
    let mut surface_coefficients = vec![number(1)];
    surface_coefficients.extend(result.coefficients.iter().map(big));
    let report = object([
        ("field_size", big(&result.q)),
        ("source_polynomial_coefficients", Json::Array(vec![number(1), big(&result.source_trace.neg()), big(&result.q)])),
        ("surface_polynomial_coefficients", Json::Array(surface_coefficients)),
        ("quotient_coefficients", Json::Array(result.quotient.iter().map(big).collect())),
        ("remainder_coefficients", Json::Array(result.remainder.iter().map(big).collect())),
        ("source_polynomial_divides", boolean(result.divides)),
        ("surface_reciprocal_conditions_pass", boolean(result.reciprocal)),
        ("quotient_elliptic_shape", boolean(result.quotient_elliptic_shape)),
        ("quotient_hasse_bound_pass", boolean(result.quotient_hasse_bound)),
        ("passes_necessary_conditions", boolean(result.passes_necessary_conditions())),
        ("subgroup_transfer_certified", boolean(false)),
        ("interpretation", text("This filters supplied Frobenius polynomials. It does not validate existence of a variety, construct a homomorphism, or certify subgroup preservation.")),
    ]);
    args.emit(&report)
}

fn main() {
    if let Err(error) = run() {
        eprintln!("error: {error}");
        std::process::exit(2);
    }
}

#!/usr/bin/env python3
"""Add a Q-independent OpenSSL warmup and charge Q setup to the target."""

from hashlib import sha256
from pathlib import Path
import sys

EXPECTED = '531e7f21fbcd6171cbf25898f29bf37c41b8b441d8f5a0eaaa8b70ba6268ae9f'


def replace_once(source: str, before: str, after: str) -> str:
    assert source.count(before) == 1, before
    return source.replace(before, after, 1)


def main(root: Path) -> None:
    path = root / 'src/bin/rho_restart_hybrid.rs'
    assert sha256(path.read_bytes()).hexdigest() == EXPECTED
    source = path.read_text()
    source = replace_once(source,
        '    unsafe fn new(q_hex: &str) -> Self {',
        '    unsafe fn new_unset() -> Self {')
    source = replace_once(source,
        '        state.set_affine(q, q_hex);\n        state\n    }',
        '        state\n    }\n\n'
        '    unsafe fn new(q_hex: &str) -> Self {\n'
        '        let mut state = Self::new_unset();\n'
        '        state.set_affine(state.q, q_hex);\n'
        '        state\n    }')
    source = replace_once(source,
        '    unsafe fn baseline(&mut self, a: *const c_void, b: *const c_void) -> String {',
        '    unsafe fn warm_generator(&mut self) -> String {\n'
        '        let one = [1u8];\n'
        '        let scalar = BN_bin2bn(one.as_ptr(), 1, ptr::null_mut());\n'
        '        assert!(!scalar.is_null());\n'
        '        assert_eq!(EC_POINT_mul(self.group, self.result, scalar,\n'
        '            ptr::null(), ptr::null(), self.ctx), 1);\n'
        '        let point = self.point_hex();\n'
        '        BN_free(scalar);\n'
        '        point\n'
        '    }\n\n'
        '    unsafe fn baseline(&mut self, a: *const c_void, b: *const c_void) -> String {')
    source = replace_once(source,
        '    assert!(mode == "openssl" || mode == "openssl_nowarm" || mode == "hybrid");',
        '    assert!(mode == "openssl" || mode == "openssl_nowarm" ||\n'
        '            mode == "openssl_globalwarm" || mode == "hybrid");')
    source = replace_once(source,
        '    let mut crypto = unsafe { Openssl::new(q_hex) };\n'
        '    let openssl_warmup_ms = if mode == "openssl_nowarm" { 0.0 } else {\n'
        '        let warm_start = Instant::now();\n'
        '        let warm = unsafe { crypto.baseline(cases[0].a_bn, cases[0].b_bn) };\n'
        '        assert_eq!(warm, cases[0].expected);\n'
        '        warm_start.elapsed().as_secs_f64() * 1000.0\n'
        '    };',
        '    let mut crypto = unsafe {\n'
        '        if mode == "openssl_globalwarm" { Openssl::new_unset() }\n'
        '        else { Openssl::new(q_hex) }\n'
        '    };\n'
        '    let openssl_warmup_ms = if mode == "openssl_nowarm" { 0.0 } else {\n'
        '        let warm_start = Instant::now();\n'
        '        let warm = unsafe {\n'
        '            if mode == "openssl_globalwarm" { crypto.warm_generator() }\n'
        '            else { crypto.baseline(cases[0].a_bn, cases[0].b_bn) }\n'
        '        };\n'
        '        if mode == "openssl_globalwarm" {\n'
        '            assert_eq!(warm, format!("{}:{}",\n'
        '                super::GENERATOR_X_HEX, super::GENERATOR_Y_HEX));\n'
        '        } else { assert_eq!(warm, cases[0].expected); }\n'
        '        warm_start.elapsed().as_secs_f64() * 1000.0\n'
        '    };')
    source = replace_once(source,
        '    let start = Instant::now();\n'
        '    let answers = cases.iter().map(|case| unsafe {',
        '    let target_start = Instant::now();\n'
        '    if mode == "openssl_globalwarm" {\n'
        '        unsafe { crypto.set_affine(crypto.q, q_hex); }\n'
        '    }\n'
        '    let target_preparation_ms = target_start.elapsed().as_secs_f64() * 1000.0;\n'
        '    let start = Instant::now();\n'
        '    let answers = cases.iter().map(|case| unsafe {')
    source = replace_once(source,
        '    let online_ms = start.elapsed().as_secs_f64() * 1000.0;',
        '    let restart_eval_ms = start.elapsed().as_secs_f64() * 1000.0;\n'
        '    let online_ms = target_preparation_ms + restart_eval_ms;')
    source = replace_once(source,
        '              openssl_warmup_ms={openssl_warmup_ms:.6} \\\n'
        '              table_preparation_ms={table_preparation_ms:.6} \\\n',
        '              openssl_warmup_ms={openssl_warmup_ms:.6} \\\n'
        '              target_preparation_ms={target_preparation_ms:.6} \\\n'
        '              restart_eval_ms={restart_eval_ms:.6} \\\n'
        '              table_preparation_ms={table_preparation_ms:.6} \\\n')
    path.write_text(source)


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(Path(sys.argv[1]))

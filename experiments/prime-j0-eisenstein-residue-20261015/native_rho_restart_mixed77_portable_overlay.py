#!/usr/bin/env python3
"""Build the mixed-77 source without unrelated compile-time atlas files.

The parent snapshot embeds twelve atlases through machine-local absolute
paths. This overlay leaves their consumers intact but loads each atlas only
if its corresponding optional mode is used. The joint rho-restart modes do
not access those atlases. Missing optional bytes fail at use, never silently
substitute empty data. Archived test-only modules after the release code are
removed from this benchmark source because they embed local machine paths.
"""
from pathlib import Path
import re
import sys

from native_rho_restart_mixed77_overlay import main as add_mixed77

ATLAS_NAMES = (
    'RADIX640_FULL_ATLAS', 'RADIX640_FINAL_ATLAS',
    'TAU384_MATCHING_ATLAS', 'FRONTIER7_FULL_ATLAS',
    'FRONTIER7_FINAL_ATLAS', 'FRONTIER8_FULL_ATLAS',
    'FRONTIER9_FINAL_ATLAS', 'FRONTIER9_FULL_ATLAS',
    'FRONTIER6_FULL_ATLAS', 'FRONTIER6_FINAL_ATLAS',
    'TAU_BUCKET_ATLAS', 'TAU_PAIR_ATLAS',
)

LOADER = '''
// Optional atlas modes read their own validated bytes at first use. The
// rho-restart joint modes neither read these files nor require the variable.
fn load_optional_atlas(name: &str) -> Vec<u8> {
    let directory = std::env::var_os("EISENSTEIN_ATLAS_DIR")
        .expect("EISENSTEIN_ATLAS_DIR is required for optional atlas modes");
    let path = std::path::PathBuf::from(directory).join(name);
    std::fs::read(&path).unwrap_or_else(|error|
        panic!("cannot read optional atlas {}: {}", path.display(), error))
}
'''


def main(root: Path) -> None:
    add_mixed77(root)  # verifies the archived parent hashes first
    windows = root / 'src/bin/eisenstein_fixed/unit_orbit_windows.rs'
    source = windows.read_text()
    use_line = 'use std::sync::LazyLock;\n'
    assert source.count(use_line) == 1
    source = source.replace(use_line, use_line + LOADER, 1)
    for name in ATLAS_NAMES:
        pattern = rf'const {name}: &\[u8\] = include_bytes!\(\s*"[^"]+"\s*\);'
        source, count = re.subn(pattern,
            f'static {name}: LazyLock<Vec<u8>> = '
            f'LazyLock::new(|| load_optional_atlas("{name.lower()}.bin"));',
            source)
        assert count == 1, (name, count)
        source = source.replace(f'from_bytes({name},',
                                f'from_bytes({name}.as_slice(),')
        source = source.replace(f'let bytes = {name};',
                                f'let bytes = {name}.as_slice();')
    test_marker = '\n#[cfg(test)]\nmod split_prime_tests {'
    assert source.count(test_marker) == 1
    source = source.split(test_marker, 1)[0] + '\n'
    assert 'include_bytes!' not in source
    assert '/private/tmp/' not in source and '/Volumes/' not in source
    windows.write_text(source)
    front = root / 'src/bin/eisenstein_fixed.rs'
    front_source = front.read_text()
    front_test_marker = '\n#[cfg(test)]\nmod eisenstein_tau_tests {'
    assert front_source.count(front_test_marker) == 1
    front_source = front_source.split(front_test_marker, 1)[0] + '\n'
    assert '/private/tmp/' not in front_source and '/Volumes/' not in front_source
    front.write_text(front_source)


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(Path(sys.argv[1]))

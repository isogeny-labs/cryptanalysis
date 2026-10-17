#!/usr/bin/env python3
"""Add an opt-in 76-tripling arm to the frozen portable mixed77 source."""
from hashlib import sha256
from pathlib import Path
import shutil
import sys

FRONT_SHA256 = 'a4b2fd132833f4df88ecf9b963979c5e601325d14c66dc1966a0c25c71b8648a'
WINDOWS_SHA256 = '9966cdc32e364f636c1a5b59ca7461aebdc3dfee6102bc97fff2efa5e8df21c0'
JOINT_SHA256 = '4295ed7584abe7fcf916c27e86cd843197ea7b1572b0b4789aca9ef5b283a498'
HERE = Path(__file__).resolve().parent


def replace_once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after, 1)


def main(root: Path) -> None:
    front = root / 'src/bin/eisenstein_fixed.rs'
    windows = root / 'src/bin/eisenstein_fixed/unit_orbit_windows.rs'
    joint = root / 'src/bin/rho_restart_joint.rs'
    for path, expected in ((front, FRONT_SHA256), (windows, WINDOWS_SHA256),
                           (joint, JOINT_SHA256)):
        assert sha256(path.read_bytes()).hexdigest() == expected, path
    front.write_text(replace_once(front.read_text(),
        '    if args.len() == 3 && args[0] == "--pilot-rho-restart-joint-mixed77" {',
        '    if args.len() == 3 && args[0] == "--pilot-rho-restart-joint-mixed76" {\n'
        '        let count: usize = args[2].parse().expect("rho restart count");\n'
        '        rho_restart_joint::run_mixed76(&args[1], count);\n'
        '        return;\n'
        '    }\n'
        '    if args.len() == 3 && args[0] == "--pilot-rho-restart-joint-mixed77" {'))
    windows.write_text(replace_once(windows.read_text(),
        'include!("joint_mixed77.rs");',
        'include!("joint_mixed77.rs");\ninclude!("joint_mixed76.rs");'))
    source = joint.read_text()
    assert 'include!("rho_restart_joint_mixed76.rs");' not in source
    joint.write_text(source + '\ninclude!("rho_restart_joint_mixed76.rs");\n')
    for name, target in (('joint_mixed76.rs', root / 'src/bin/eisenstein_fixed/joint_mixed76.rs'),
                         ('rho_restart_joint_mixed76.rs', root / 'src/bin/rho_restart_joint_mixed76.rs')):
        assert not target.exists()
        shutil.copyfile(HERE / name, target)


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(Path(sys.argv[1]))

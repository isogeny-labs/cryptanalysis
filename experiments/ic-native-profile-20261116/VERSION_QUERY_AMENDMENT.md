# Version metadata correction before profile attempt002

[pcc:unverified] Attempt20261116-114025-772f/profile-001 stops after1.7s:
callgrind_annotate --version prints callgrind_annotate-3.22.0 but exits255.
The driver requires0 for that metadata query and aborts before capability
preflight or any target. All11outputs remain; zero instruction captures.

Correct the metadata query using dpkg-query --show for the installed valgrind
package, retain valgrind --version and SHA-256 of valgrind, callgrind_annotate
and objdump. Require query success; no nonzero arithmetic/profile command is
accepted. Add an explicit required --run-id argument so profile-002 writes a
new output path without touching profile-001. All other frozen source/input/
binary/calibration/target/method/ISA-admission/control/order/resource/stop and
interpretation rules in PROTOCOL.md remain. This fixes metadata collection;
it does not admit a failed capability check, choose a host based on ISA, or
extend a cap. Publish the correction before the new bounded allocation.

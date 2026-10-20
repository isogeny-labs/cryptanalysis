"""Behavioral checks use temporary state, fake vendors, and real local processes."""
import json
import os
from pathlib import Path
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "bootstrap.sh"


def eventually(predicate, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(.05)
    raise AssertionError("condition did not become true")


def live(pid):
    result = subprocess.run(["ps", "-p", str(pid), "-o", "stat="], capture_output=True, text=True)
    return result.returncode == 0 and not result.stdout.strip().startswith("Z")


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="workmesh tests ")
        self.base = Path(self.temp.name)
        self.root = self.base / "state root"
        self.env = dict(os.environ)
        self.env.update(WB_ROOT=str(self.root), PROFILE="minimal", SYSTEM_PACKAGES="off",
                        DOCKER_MODE="off", ISOLATION="off", TS_ENABLED="no", CAIRN_MODE="off",
                        CONDUCTOR_MODE="off", CLAUDE_RC="no", CODEX_RC="no", LOGIN="no",
                        SAGE_MODE="off", INSTALL_CLIS="no", INSTALL_CLOUD_TOOLS="no")
        for key in ("TS_SOCKET", "TS_AUTHKEY_FILE", "DATABASE_URL_FILE", "CONDUCTOR_TOKEN_FILE",
                    "OPENAI_API_KEY_FILE", "ANTHROPIC_API_KEY_FILE", "CURSOR_API_KEY_FILE"):
            self.env.pop(key, None)

    def tearDown(self):
        self.call("stop", check=False)
        self.temp.cleanup()

    def call(self, *args, check=True, input=None):
        result = subprocess.run(["bash", str(SCRIPT), *map(str, args)], cwd=self.base,
                                env=self.env, input=input, capture_output=True, text=True, timeout=50)
        if check and result.returncode:
            self.fail(f"exit {result.returncode}: {result.stdout}\n{result.stderr}")
        return result

    def library(self, code, check=True):
        text = f"script={shlex.quote(str(SCRIPT))}; . \"$script\"; " + code
        result = subprocess.run(["bash", "-c", text], cwd=self.base, env=self.env,
                                capture_output=True, text=True, timeout=40)
        if check and result.returncode:
            self.fail(f"library exit {result.returncode}: {result.stderr}")
        return result

    def vendor(self, name, code):
        path = self.root / "bin" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!" + sys.executable + "\n" + code)
        path.chmod(0o755)
        return path

    def test_dry_run_has_no_side_effects_or_secret_reads(self):
        self.env["TS_AUTHKEY"] = "SYNTHETIC-DO-NOT-PRINT"
        self.env["DATABASE_URL_FILE"] = str(self.base / "missing-secret")
        out = self.call("bootstrap", "--dry-run")
        self.assertFalse(self.root.exists())
        self.assertNotIn("SYNTHETIC-DO-NOT-PRINT", out.stdout + out.stderr)

    def test_vendor_cli_installation_is_opt_in_by_default(self):
        self.env.pop("INSTALL_CLIS", None)
        out = self.call("plan")
        self.assertIn("Coding CLIs: no;", out.stdout)

    def test_lean_installer_is_independent_of_vendor_cli_flag(self):
        fetch_log = self.base / "fetches.log"
        install_marker = self.base / "elan-args.log"
        self.env.update(FETCH_LOG=str(fetch_log), LEAN_INSTALL_MARKER=str(install_marker), TMPDIR=str(self.base),
                        INSTALL_CLIS="no", INSTALL_LEAN="yes")
        out = self.library("""
            have() { return 1; }
            fetch() {
              printf '%s\\n' "$1" >> "$FETCH_LOG"
              cat > "$2" <<'ELAN'
#!/usr/bin/env bash
printf '%s\\n' "$*" > "$LEAN_INSTALL_MARKER"
ELAN
              chmod +x "$2"
            }
            install_clis
            install_lean
        """)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(fetch_log.read_text().splitlines(), [
            "https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh"
        ])
        self.assertEqual(install_marker.read_text().strip(),
                         "-y --no-modify-path --default-toolchain leanprover/lean4:v4.35.0")

    def test_vendor_cli_flag_does_not_install_lean_without_lean_opt_in(self):
        fetch_log = self.base / "fetches.log"
        self.env.update(FETCH_LOG=str(fetch_log), TMPDIR=str(self.base), INSTALL_CLIS="yes", INSTALL_LEAN="no")
        out = self.library("""
            have() { return 0; }
            fetch() { printf '%s\\n' "$1" >> "$FETCH_LOG"; }
            install_clis
            install_lean
        """)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertFalse(fetch_log.exists(), "Lean installer must remain opt-in")

    def test_cli_overrides_config(self):
        config = self.base / "trusted config.sh"
        config.write_text("PROFILE=full\nCONDUCTOR_MODE=local\n")
        out = self.call("plan", "--config", config, "--profile", "minimal")
        self.assertIn("profile: minimal", out.stdout)

    def test_invalid_options_and_port_collision_fail_before_writes(self):
        self.assertNotEqual(self.call("--wat", check=False).returncode, 0)
        self.env["CAIRN_HTTP_PORT"] = "18081"
        self.assertNotEqual(self.call("plan", check=False).returncode, 0)
        self.assertFalse(self.root.exists())

    def test_foreground_preserves_arguments_and_exit_code(self):
        literal = '$(touch SHOULD_NOT_EXIST) `touch ALSO_NOT` ; * spaced value'
        result = self.call("run", "--", sys.executable, "-c",
                           "import sys; print(sys.argv[1]); sys.exit(37)", literal, check=False)
        self.assertEqual(result.returncode, 37, result.stderr)
        self.assertEqual(result.stdout.strip(), literal)
        self.assertFalse((self.base / "SHOULD_NOT_EXIST").exists())
        self.assertFalse((self.base / "ALSO_NOT").exists())

    def test_foreground_keeps_stdin(self):
        result = self.call("run", "--", sys.executable, "-c", "print(input())", input="hello stdin\n")
        self.assertEqual(result.stdout.strip(), "hello stdin")

    def test_term_reaches_child_and_grandchild(self):
        record = self.base / "descendants.json"
        child_code = ("import subprocess,os,json,time; "
                      "p=subprocess.Popen(['sleep','120']); "
                      f"open({str(record)!r},'w').write(json.dumps([os.getpid(),p.pid])); "
                      "p.wait()")
        proc = subprocess.Popen(["bash", str(SCRIPT), "run", "--", sys.executable, "-c", child_code],
                                cwd=self.base, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            eventually(record.exists)
            pids = json.loads(record.read_text())
            proc.send_signal(signal.SIGTERM)
            _, errors = proc.communicate(timeout=20)
            self.assertEqual(proc.returncode, 143, errors)
            eventually(lambda: not any(live(pid) for pid in pids))
        finally:
            if proc.poll() is None: proc.kill(); proc.wait()

    def test_service_is_reused_and_stops_its_group(self):
        mark = self.base / "launch-count"
        code = f"open({str(mark)!r},'a').write('start\\n'); import time; time.sleep(120)"
        launch = "ensure_dirs; start_service demo \"$WORK_DIR\" " + shlex.quote(sys.executable) + " -c " + shlex.quote(code)
        self.library(launch)
        record = self.root / "state/services/demo.json"
        row = json.loads(record.read_text())
        eventually(mark.exists)
        self.library(launch)
        self.assertEqual(json.loads(record.read_text())["pid"], row["pid"])
        self.assertEqual(mark.read_text().splitlines(), ["start"])
        self.call("stop")
        eventually(lambda: not live(row["pid"]))
        self.assertFalse(record.exists())

    def test_run_preserves_preexisting_services(self):
        self.library("ensure_dirs; start_service existing \"$WORK_DIR\" sleep 120")
        record = self.root / "state/services/existing.json"
        row = json.loads(record.read_text())
        self.call("run", "--", sys.executable, "-c", "pass")
        self.assertTrue(live(row["pid"]))

    def test_stale_pid_cannot_stop_an_unrelated_process(self):
        directory = self.root / "state/services"
        directory.mkdir(parents=True)
        (directory / "stale.json").write_text(json.dumps({"pid": os.getpid(), "start": "wrong",
                                                       "launcher": str(directory / "stale.sh")}))
        self.call("stop")
        self.assertTrue(live(os.getpid()))

    def test_checksum_failure_prevents_install(self):
        artifact = self.base / "artifact"
        artifact.write_bytes(b"incorrect download")
        result = self.library("verify " + shlex.quote(str(artifact)) + " " + "0" * 64, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum mismatch", result.stderr)

    def test_go_older_than_toolchain_selection_is_not_retained(self):
        self.env["GO_VERSION"] = "latest"
        self.vendor("go", "print('go version go1.20.14 linux/amd64')\n")
        out = self.library("fetch() { echo metadata-download-needed; return 91; }; install_go", check=False)
        self.assertEqual(out.returncode, 91)
        self.assertIn("metadata-download-needed", out.stdout)
        self.vendor("go", "print('go version go1.21.13 linux/amd64')\n")
        out = self.library("fetch() { echo unexpected-download; return 91; }; install_go")
        self.assertNotIn("unexpected-download", out.stdout)

    def test_existing_tailscale_login_is_reused(self):
        log = self.base / "ts-args.jsonl"
        self.vendor("tailscale", f"""import json, sys
with open({str(log)!r}, 'a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')
print(json.dumps({{'BackendState': 'Running'}}))
""")
        self.env["TS_ENABLED"] = "yes"
        self.call("up")
        rows = [json.loads(x) for x in log.read_text().splitlines()]
        self.assertEqual(rows, [["status", "--json"]])

    def test_token_file_is_consumed_without_secret_arguments(self):
        token = self.base / "token"
        token.write_text("SYNTHETIC-CONDUCTOR-TOKEN")
        log = self.base / "conductor.jsonl"
        self.vendor("conductor", f"""import json, os, sys
with open({str(log)!r}, 'a') as f:
 f.write(json.dumps({{'argv':sys.argv[1:], 'token_available': bool(os.environ.get('CONDUCTOR_TOKEN'))}})+'\\n')
""")
        self.env.update(CONDUCTOR_MODE="client", CONDUCTOR_ENDPOINT="https://leader.example.ts.net",
                        CONDUCTOR_TOKEN_FILE=str(token), CONDUCTOR_PROJECT="crypto")
        result = self.call("up")
        rows = [json.loads(x) for x in log.read_text().splitlines()]
        self.assertTrue(all(row["token_available"] for row in rows))
        self.assertEqual([row["argv"][1] for row in rows if row["argv"][0] == "integrate"],
                         ["claude", "codex", "cursor", "opencode"])
        self.assertNotIn(token.read_text(), log.read_text() + result.stdout + result.stderr)

    def test_remote_conductor_rejects_plain_http_before_authentication(self):
        log = self.base / "conductor.jsonl"
        self.vendor("conductor", f"open({str(log)!r},'a').write('called\\n')\\n")
        self.env.update(CONDUCTOR_MODE="client", CONDUCTOR_ENDPOINT="http://leader.example:18081",
                        CONDUCTOR_TOKEN="SYNTHETIC-CONDUCTOR-TOKEN")
        result = self.call("up", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("remote Conductor endpoints must use HTTPS", result.stderr)
        self.assertFalse(log.exists(), "credentials must not be sent before endpoint validation")

    def test_conductor_client_allows_loopback_http(self):
        log = self.base / "conductor.jsonl"
        self.vendor("conductor", f"""with open({str(log)!r}, 'a') as f:
 f.write('called\\n')
""")
        self.env.update(CONDUCTOR_MODE="client", CONDUCTOR_ENDPOINT="http://127.0.0.1:18081")
        self.call("up")
        self.assertIn("called", log.read_text())

    def test_loopback_http_userinfo_cannot_bypass_tls_guard(self):
        log = self.base / "conductor.jsonl"
        self.vendor("conductor", f"""with open({str(log)!r}, 'a') as f:
 f.write('called\\n')
""")
        self.env.update(CONDUCTOR_MODE="client", CONDUCTOR_ENDPOINT="http://localhost:18081@leader.example",
                        CONDUCTOR_TOKEN="SYNTHETIC-CONDUCTOR-TOKEN")
        result = self.call("up", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONDUCTOR_ENDPOINT must not contain credentials", result.stderr)
        self.assertFalse(log.exists(), "credentials must not be sent to a userinfo-parsed remote host")

    def test_gateway_keeps_secret_reference_and_scoped_proxy(self):
        token = self.base / "gateway token"
        token.write_text("SYNTHETIC-GATEWAY-TOKEN")
        self.vendor("conductor-mcp", "import json,os,sys; print(json.dumps({'secret_available':bool(os.environ.get('CONDUCTOR_TOKEN')),'proxy':os.environ.get('HTTPS_PROXY'),'args':sys.argv[1:]}))\n")
        self.env.update(CONDUCTOR_TOKEN_FILE=str(token), CONDUCTOR_HTTP_PROXY="tailnet",
                        CONDUCTOR_ENDPOINT="https://leader.example.ts.net")
        self.library("ensure_dirs; write_mcp_launcher; write_mcp_launcher")
        program = self.root / "bin/conductor-mcp"
        self.assertNotIn(token.read_text(), program.read_text())
        result = subprocess.run([str(program), "--project", "crypto"], capture_output=True, text=True, check=True)
        row = json.loads(result.stdout)
        self.assertTrue(row["secret_available"])
        self.assertEqual(row["proxy"], "http://127.0.0.1:1056")
        self.assertEqual(row["args"], ["--project", "crypto"])

    def test_current_config_is_not_overridden_by_old_env_file(self):
        log = self.base / "endpoint.jsonl"
        self.vendor("conductor", f"import os; open({str(log)!r},'a').write(os.environ.get('CONDUCTOR_ENDPOINT','')+'\\n')\n")
        self.env.update(CONDUCTOR_MODE="client", CONDUCTOR_ENDPOINT="https://first.example.ts.net")
        self.call("up")
        self.env["CONDUCTOR_ENDPOINT"] = "https://second.example.ts.net"
        self.call("up")
        self.assertEqual(log.read_text().splitlines()[-1], "https://second.example.ts.net")

    def test_userspace_tailscale_uses_key_file_and_reuses_socket(self):
        state = self.base / "ts-up"
        args_file = self.base / "ts-args.jsonl"
        daemon_args = self.base / "daemon.json"
        self.vendor("tailscaled", f"""import json, socket, sys, time
open({str(daemon_args)!r}, 'w').write(json.dumps(sys.argv[1:]))
path=next(a.split('=',1)[1] for a in sys.argv if a.startswith('--socket='))
s=socket.socket(socket.AF_UNIX); s.bind(path); s.listen()
while True: time.sleep(1)
""")
        self.vendor("tailscale", f"""import json, pathlib, sys
args=[a for a in sys.argv[1:] if not a.startswith('--socket=')]
with open({str(args_file)!r},'a') as f: f.write(json.dumps(args)+'\\n')
if args[0]=='up': pathlib.Path({str(state)!r}).touch()
else: print(json.dumps({{'BackendState':'Running' if pathlib.Path({str(state)!r}).exists() else 'NeedsLogin'}}))
""")
        self.env.update(TS_ENABLED="yes", TS_MODE="userspace", TS_AUTHKEY="SYNTHETIC-TS-KEY")
        self.call("up")
        first = args_file.read_text()
        self.call("up")
        rows = [json.loads(x) for x in args_file.read_text().splitlines()]
        ups = [row for row in rows if row[0] == "up"]
        self.assertEqual(len(ups), 1)
        reference = next(arg.split("file:", 1)[1] for arg in ups[0] if arg.startswith("--auth-key=file:"))
        self.assertFalse(Path(reference).exists())
        self.assertNotIn("SYNTHETIC-TS-KEY", first + daemon_args.read_text())
        self.assertIn("--tun=userspace-networking", json.loads(daemon_args.read_text()))
        self.assertIn("--accept-dns=false", ups[0])

    def test_kernel_tailscale_requests_magicdns(self):
        # Fake root and daemon capabilities: this checks the generated CLI flags,
        # while live kernel-interface validation remains a host-side check.
        state = self.base / "kernel-up"
        args_file = self.base / "kernel-args.json"
        self.vendor("id", "print('0')\n")
        self.vendor("tailscaled", """import socket,sys,time
path=next(a.split('=',1)[1] for a in sys.argv if a.startswith('--socket='))
s=socket.socket(socket.AF_UNIX); s.bind(path); s.listen()
while True: time.sleep(1)
""")
        self.vendor("tailscale", f"""import json,pathlib,sys
args=[a for a in sys.argv[1:] if not a.startswith('--socket=')]
if args[0]=='up':
 pathlib.Path({str(state)!r}).touch(); open({str(args_file)!r},'w').write(json.dumps(args))
else: print(json.dumps({{'BackendState':'Running' if pathlib.Path({str(state)!r}).exists() else 'NeedsLogin'}}))
""")
        self.env.update(TS_ENABLED="yes", TS_MODE="kernel")
        self.call("up")
        self.assertIn("--accept-dns=true", json.loads(args_file.read_text()))

    def test_cairn_starts_private_with_distinct_ports(self):
        args_file = self.base / "cairn.json"
        with socket.socket() as temp:
            temp.bind(("127.0.0.1", 0)); port = temp.getsockname()[1]
        self.vendor("cairn", f"""import http.server, json, os, sys
open({str(args_file)!r}, 'w').write(json.dumps({{'argv':sys.argv[1:], 'private':os.environ.get('CAIRN_NETWORK'), 'sandbox':os.environ.get('CAIRN_REQUIRE_SANDBOX')}}))
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b'{{}}')
 def log_message(self, *args): pass
http.server.HTTPServer(('127.0.0.1', {port}), Handler).serve_forever()
""")
        self.env.update(CAIRN_MODE="node", CAIRN_AGENT="no", CAIRN_HTTP_PORT=str(port), CAIRN_P2P_BIND="127.0.0.1")
        self.call("up")
        row = json.loads(args_file.read_text())
        self.assertEqual(row["private"], "private")
        self.assertEqual(row["sandbox"], "1")
        self.assertIn("--no-mcp", row["argv"])
        self.assertIn(f"127.0.0.1:{port}", row["argv"])
        self.assertNotIn("127.0.0.1:8080", row["argv"])


if __name__ == "__main__":
    unittest.main()

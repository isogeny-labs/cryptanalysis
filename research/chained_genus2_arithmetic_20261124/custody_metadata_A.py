"""File, Git-object, hash and JSON custody only; never launches scientific code."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

STUDY = Path(__file__).resolve().parent
ROOT = STUDY.parents[1]

def now():
    return datetime.now(timezone.utc).isoformat()

def write(path, value):
    if path.exists():
        raise RuntimeError("write-once record exists: " + str(path))
    path.write_text(json.dumps(value, indent=2) + "\n")

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return {"bytes": path.stat().st_size, "sha256": h.hexdigest(), "mode": path.stat().st_mode & 0o777}

def metadata_command(argv, out):
    p = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        n = len(list(out.glob("failed-metadata-command-*.json")))
        write(out / ("failed-metadata-command-" + str(n) + ".json"),
              {"argv": argv, "exit": p.returncode, "stdout_utf8": p.stdout.decode(errors="replace"), "stderr_utf8": p.stderr.decode(errors="replace")})
        raise RuntimeError("metadata command failed; complete diagnostic retained")
    return p.stdout

def snapshot(out, tools):
    lock = json.loads((STUDY / "SOURCE_LOCK_A.json").read_text())
    paths = list(lock["files"]) + [str((STUDY / "SOURCE_LOCK_A.json").relative_to(ROOT))]
    original = {p: digest(ROOT / p) for p in paths}
    copied = {p: digest(out / "source" / p) for p in paths if (out / "source" / p).is_file()}
    return {"recorded": now(), "original": original, "copied": copied,
            "tools": {p: digest(Path(p)) for p in tools},
            "qualifier": digest(out / "qualifier") if (out / "qualifier").exists() else None}

def main():
    action = sys.argv[1]
    if action == "init":
        source, out, temp = sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
        lock = json.loads((STUDY / "SOURCE_LOCK_A.json").read_text())
        tools = []
        for name in ["rustc", "clippy-driver", "rustfmt"]:
            tool = metadata_command(["rustup", "which", "--toolchain", "1.99.1", name], out).decode().strip()
            if digest(Path(tool))["sha256"] != lock["tool_binary_sha256"][name]:
                raise RuntimeError("compiler-tool hash mismatch: " + name)
            tools.append(tool)
        for path, expected in lock['runtime_file_sha256'].items():
            if digest(Path(path))['sha256'] != expected:
                raise RuntimeError('runtime hash mismatch: ' + path)
            tools.append(path)
        write(out / "CONTEXT.json", {"recorded": now(), "source_commit": source, "repo": str(ROOT), "study": str(STUDY), "out": str(out), "compiler_temp": str(temp), "tools": tools,
                                      "ambient_boundary": "Exact tool binaries and explicitly named installed runtime files are hash-bound; other host OS/dynamic libraries remain ambient, not a hermetic execution proof.", "worker_environment": {k: os.environ[k] for k in ["RAYON_NUM_THREADS", "CARGO_BUILD_JOBS", "CHECKPOINT_SKIP"]}, "proof_environment": {k: os.environ.get(k) for k in ["LEAN_NUM_THREADS", "LEAN_STACK_SIZE_KB", "LEAN_MAIN_USE_THREAD", "MIMALLOC_ARENA_RESERVE", "LEAN_SYSROOT", "LEAN_PATH", "LEAN_OPTS"]}})
        for p, expected in lock["files"].items():
            b = (ROOT / p).read_bytes()
            if len(b) != expected["bytes"] or hashlib.sha256(b).hexdigest() != expected["sha256"] or (ROOT / p).stat().st_mode & 0o777 != expected["mode"]:
                raise RuntimeError("original source lock mismatch: " + p)
            public = metadata_command(["git", "cat-file", "blob", source + ":" + p], out)
            if public != b:
                raise RuntimeError("published source mismatch: " + p)
            dest = out / "source" / p
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / p, dest)
        lock_path = STUDY / "SOURCE_LOCK_A.json"
        public_lock = metadata_command(["git", "cat-file", "blob", source + ":" + str(lock_path.relative_to(ROOT))], out)
        if public_lock != lock_path.read_bytes():
            raise RuntimeError("published source-lock mismatch")
        shutil.copy2(lock_path, out / "source" / lock_path.relative_to(ROOT))
        ram = os.statvfs("/dev/shm"); disk = os.statvfs(temp)
        if ram.f_bavail * ram.f_frsize < 256 * 1024 * 1024 or disk.f_bavail * disk.f_frsize < 64 * 1024 * 1024:
            raise RuntimeError("frozen available-space floor")
        write(out / "BUILD_MANIFEST.json", snapshot(out, tools))
    elif action == "phase":
        out, name, status = Path(sys.argv[2]), sys.argv[3], int(sys.argv[4])
        write(out / (name + ".phase.json"), {"recorded": now(), "name": name, "expected_exit": 0, "exit": status,
                                                   "complete_stdout": digest(out / (name + ".stdout")), "complete_stderr": digest(out / (name + ".stderr"))})
    elif action == "pre":
        out = Path(sys.argv[2]); context = json.loads((out / "CONTEXT.json").read_text())
        write(out / "PRE_CALL_MANIFEST.json", snapshot(out, context["tools"]))
    elif action == "finish":
        out, status = Path(sys.argv[2]), int(sys.argv[3])
        if not (out / "CONTEXT.json").exists():
            write(out / "POST_CALL_MANIFEST.json", {"recorded": now(), "outer_exit": status, "init_incomplete": True})
            return
        context = json.loads((out / "CONTEXT.json").read_text()); post = snapshot(out, context["tools"])
        post["outer_exit"] = status
        post["compiled_executable"] = digest(out / "native-built") if (out / "native-built").exists() else None
        failures = []
        if (out / "BUILD_MANIFEST.json").exists():
            build = json.loads((out / "BUILD_MANIFEST.json").read_text())
            for key in ["original", "copied", "tools"]:
                if post[key] != build[key]: failures.append(key)
        else: failures.append("missing build manifest")
        if (out / "PRE_CALL_MANIFEST.json").exists():
            pre = json.loads((out / "PRE_CALL_MANIFEST.json").read_text())
            if post["qualifier"] != pre["qualifier"]: failures.append("qualifier")
        elif status == 0: failures.append("missing pre-call manifest")
        post["guard_failures"] = failures
        post["full_raw_cache_is_temporary_until_store_or_CI_artifact"] = True
        write(out / "POST_CALL_MANIFEST.json", post)
        if status == 0 and failures: raise RuntimeError("post-call guards failed: " + repr(failures))
    else:
        raise RuntimeError("unknown metadata action")

if __name__ == "__main__":
    main()

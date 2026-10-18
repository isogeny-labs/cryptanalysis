#!/usr/bin/env python3
"""Read-only documented bounded SSE logs; redact credentials before retention."""
import json
import os
import re
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path

POD_ID = "uf7o6868cpoxi7"
DEST = Path(__file__).resolve().parent
api_key = os.environ.get("RUNPOD_API_KEY", "").strip()
if not api_key:
    raise SystemExit("RUNPOD_API_KEY binding missing")

def clean(value):
    value = str(value).replace(api_key, "[REDACTED]")
    if re.search(r"PUBLIC_KEY|PRIVATE KEY|Authorization:|Bearer |RUNPOD_API_KEY|ssh-ed25519 |ssh-rsa ", value, re.I):
        return "[REDACTED sensitive log line]"
    return value[:4000]

url = f"https://api.runpod.io/v2/pods/{POD_ID}/logs?tail=200"
request = urllib.request.Request(url, headers={
    "Authorization": "Bearer " + api_key,
    "Accept": "text/event-stream",
    "User-Agent": "ideas-gpu-readonly-log-diagnostic/1",
})
status = {"pod_id": POD_ID, "method": "GET", "documented_endpoint": url,
          "api_mutations": 0, "sanitized_log_events": 0}
deadline = time.monotonic() + 15
try:
    with urllib.request.urlopen(request, timeout=10) as response:
        status["http_status"] = response.status
        with (DEST / "provider-logs-v2.sanitized.jsonl").open("w") as output:
            for _ in range(600):
                if time.monotonic() >= deadline:
                    break
                line = response.readline(16000)
                if not line:
                    break
                if line.startswith(b"data:"):
                    try:
                        data = json.loads(line[5:])
                    except (ValueError, UnicodeDecodeError):
                        continue
                    if isinstance(data, dict):
                        row = {key: clean(data.get(key, "")) for key in ("source", "line", "ts")}
                        output.write(json.dumps(row) + "\n")
                        status["sanitized_log_events"] += 1
except urllib.error.HTTPError as error:
    status["http_status"] = error.code
    status["error"] = "documented_log_endpoint_rejected"
except (urllib.error.URLError, TimeoutError, socket.timeout) as error:
    status["error"] = clean(type(error).__name__)
(DEST / "provider-logs-v2.status.json").write_text(json.dumps(status, indent=2) + "\n")
print(json.dumps(status))

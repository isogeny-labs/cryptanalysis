#!/usr/bin/env python3
"""Prospective RunPod API-v2 GPU continuation. No provider action on import/plan.

Uses the unchanged public payload-v5 and fixed remote_http_gpu_v3.py workload.
One additional actual pod, then stop even if a guard or native gate fails.
Credentials are read only in explicit execute/watchdog/cleanup modes. Never
write or print them, the HTTP bearer, full provider responses, or inventories.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

STUDY = Path(__file__).resolve().parent
API = "https://api.runpod.io/v2"
FLAVORS = ("NVIDIA GeForce RTX 4090", "NVIDIA RTX A6000", "NVIDIA GeForce RTX 5090")
IMAGE = "runpod/base:1.0.2-ubuntu2404"
PAYLOAD_SHA256 = "e269ad82ff1ff7724d88ccd34adf3752f642f9895f2dd015889315245fbfcfd4"
PAYLOAD_BYTES = 1626771
MAX_PRICE = 1.50
MAX_SECONDS = 3600
WATCHDOG_CLEANUP_SECONDS = 3300
CONTROLLER_SECONDS = 3000
ARTIFACT_VERSION = "ideas-gpu-final/v1"
ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{3,100}\Z")
SHA_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_once(path, value):
    path=Path(path)
    data=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()
    fd,temporary=tempfile.mkstemp(prefix=".gpu-final-",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as output:
            output.write(data); output.flush(); os.fsync(output.fileno())
        os.link(temporary,path)  # Atomic publication, fails if destination exists.
    finally:
        os.unlink(temporary)


def cleanup_record(path,value):
    """Disk-full/log failures must never stop attempts to release paid compute."""
    try:
        write_once(path,value)
    except (OSError,ValueError):
        return False
    return True


def read_json(path):
    def pairs(items):
        output = {}
        for key, value in items:
            if key in output:
                raise ValueError("duplicate JSON key")
            output[key] = value
        return output
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs)


def numeric(value):
    return type(value) in (int,float) and math.isfinite(value)


class ProviderError(RuntimeError):
    def __init__(self, status, detail="provider refused request"):
        self.status = status
        self.detail = detail
        super().__init__(f"provider HTTP {status}: {detail}")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):
        return None  # Never forward provider credentials or a service bearer.


def authenticated_open(request,timeout):
    return urllib.request.build_opener(NoRedirect()).open(request,timeout=timeout)


class ApiClient:
    """No automatic POST retry, no secret-bearing request/response logging."""
    def __init__(self, key, hidden=()):
        if not isinstance(key,str) or not key.strip():
            raise ValueError("RUNPOD_API_KEY is required for explicit provider operation")
        self._key = key.strip()
        self._hidden = [self._key,*hidden]

    def safe_detail(self, detail):
        text = str(detail)
        for secret in self._hidden:
            if secret:
                text = text.replace(secret,"<redacted>")
        return text[:1200]

    def call(self, method, path, body=None, timeout=30):
        if not path.startswith("/") or ".." in path:
            raise ValueError("API path must stay under the pinned v2 endpoint")
        request = urllib.request.Request(API+path,method=method,
            data=None if body is None else json.dumps(body,allow_nan=False).encode(),
            headers={"Authorization":"Bearer "+self._key,"Content-Type":"application/json",
                     "User-Agent":"cryptanalysis-research/1.0"})
        try:
            with authenticated_open(request,timeout) as response:
                status=response.status
                raw=response.read()
        except urllib.error.HTTPError as error:
            # Keep only sanitized RFC7807 detail; never archive response env/body.
            try:
                problem=json.loads(error.read(16384))
                detail=problem.get("detail",problem.get("title","request refused"))
            except (ValueError,TypeError):
                detail="non-JSON provider error"
            raise ProviderError(error.code,self.safe_detail(detail)) from None
        if status == 204:
            return status,None
        return status,json.loads(raw)


def public_source(commit):
    if not re.fullmatch(r"[0-9a-f]{40}",commit):
        raise ValueError("source commit must be an exact public 40-hex revision")
    packet=STUDY/"remote-payload-v5.tar.gz"
    if packet.stat().st_size != PAYLOAD_BYTES or sha(packet) != PAYLOAD_SHA256:
        raise ValueError("local payload-v5 bytes changed")
    manifest=read_json(STUDY/"remote-payload-v5.json")
    if manifest["sha256"] != PAYLOAD_SHA256 or manifest["bytes"] != PAYLOAD_BYTES:
        raise ValueError("payload-v5 manifest changed")
    return "https://raw.githubusercontent.com/aburan28/cryptanalysis/"+commit+"/experiments/ideas_gpu_20261018/remote-payload-v5.tar.gz"


def prove_public_source(url):
    # Separate request: no API client, cookies, bearer or Authorization header.
    request=urllib.request.Request(url,headers={"User-Agent":"cryptanalysis-research/1.0"})
    with urllib.request.urlopen(request,timeout=30) as response:
        payload=response.read(PAYLOAD_BYTES+1)
    actual=hashlib.sha256(payload).hexdigest()
    if len(payload) != PAYLOAD_BYTES or actual != PAYLOAD_SHA256:
        raise ValueError("unauthenticated public payload byte/hash proof failed")
    return dict(url=url,sha256=actual,bytes=len(payload),authorization_header_supplied=False,
                checked_at=datetime.now(timezone.utc).isoformat())


def startup_script(url):
    return "\n".join(("set -eu","mkdir -p /root/cryptanalysis","cd /root/cryptanalysis",
        "curl --fail --location --retry 3 --output /tmp/ideas-payload.tar.gz "+shlex.quote(url),
        "printf '%s  %s\\n' "+shlex.quote(PAYLOAD_SHA256)+" /tmp/ideas-payload.tar.gz | sha256sum -c -",
        "tar -xzf /tmp/ideas-payload.tar.gz",
        "exec python3 experiments/ideas_gpu_20261018/remote_http_gpu_v3.py --out /root/cryptanalysis/experiments/ideas_gpu_20261018/remote/run-gpu-v3",""))


def create_body(flavor,name,url,bearer):
    if flavor not in FLAVORS or not re.fullmatch(r"ideas-20261018-gpu-final-[0-9a-f]{16}",name):
        raise ValueError("request outside exact GPU candidate/namespace")
    if not isinstance(bearer,str) or len(bearer)<32:
        raise ValueError("fresh HTTP bearer must have at least 32 characters")
    return dict(name=name,image=IMAGE,cloud="COMMUNITY",
        gpu=dict(id=flavor,count=1,minCudaVersion="13.0",minRamPerGpu=32,minVcpuCountPerGpu=16),disk=40,
        ports=["8888/http"],entrypoint=["/bin/bash","-c"],cmd=[startup_script(url)],
        env={"IDEAS_HTTP_BEARER":bearer},startJupyter=False,startSsh=False)


def safe_body(body):
    return {**body,"env":{"IDEAS_HTTP_BEARER":"<redacted>"}}


def selected_catalog(client):
    status,data=client.call("GET","/catalog/gpus?include=AVAILABILITY&product=POD&count=1&cloud=COMMUNITY&minCudaVersion=13.0")
    if status != 200 or not isinstance(data,dict) or not isinstance(data.get("gpus"),list):
        raise ValueError("invalid GPU catalog envelope")
    selected=[]
    for flavor in FLAVORS:
        matches=[row for row in data["gpus"] if row.get("id")==flavor]
        if len(matches)>1:
            raise ValueError("duplicate GPU type in catalog")
        if not matches:
            continue
        row=matches[0]; price=row.get("price",{}).get("community")
        # Quotes and availability are advisory. The actual allocated pod must
        # independently pass guard_pod before any result can be accepted.
        if (row.get("manufacturer")!="NVIDIA" or row.get("community") is not True
                or not numeric(price) or not 0 < price <= MAX_PRICE
                or type(row.get("maxCount",{}).get("community")) is not int
                or row["maxCount"]["community"]<1):
            continue
        selected.append(dict(id=flavor,quoted_USD_per_hour=price,
            availability=row.get("availability"),cudaVersions=row.get("cudaVersions")))
    if not selected:
        raise ValueError("no allowed GPU type satisfies the catalog price guard")
    return selected


def named_pods(client,name):
    cursor=None; seen=set(); found=[]
    while True:
        query="/pods?includeClusterPods=true&limit=1000"
        if cursor is not None:
            query+="&cursor="+urllib.parse.quote(cursor,safe="")
        status,data=client.call("GET",query)
        if status!=200 or not isinstance(data.get("pods"),list):
            raise ValueError("invalid paginated pod list")
        found.extend(p for p in data["pods"] if p.get("name")==name)
        page=data.get("pagination",{})
        if type(page.get("hasNextPage")) is not bool:
            raise ValueError("missing pagination completeness flag")
        if not page["hasNextPage"]:
            return found
        cursor=page.get("nextCursor")
        if not isinstance(cursor,str) or not cursor or cursor in seen:
            raise ValueError("invalid/repeating pagination cursor")
        seen.add(cursor)


def pod_id(pod):
    value=pod.get("id")
    if not isinstance(value,str) or not ID_PATTERN.fullmatch(value):
        raise ValueError("invalid exact pod ID")
    return value


def guard_pod(pod,name,flavor,expected_id):
    gpu=pod.get("gpu",{})
    cuda=pod.get("cudaVersion")
    if (pod_id(pod)!=expected_id or pod.get("name")!=name or pod.get("cloud")!="COMMUNITY"
            or pod.get("image")!=IMAGE or pod.get("cpu") is not None or pod.get("cluster") is not None
            or gpu.get("id")!=flavor or type(gpu.get("count")) is not int or gpu["count"]!=1
            or not numeric(gpu.get("vcpuCount")) or gpu["vcpuCount"]<16
            or not numeric(gpu.get("memory")) or gpu["memory"]<32
            or not numeric(pod.get("cost")) or not 0 < pod["cost"] <= MAX_PRICE
            or not isinstance(cuda,str) or not re.fullmatch(r"[0-9]+\.[0-9]+",cuda)
            or tuple(map(int,cuda.split(".")))<(13,0)
            or pod.get("status") not in ("PROVISIONING","STARTING","RUNNING")):
        raise ValueError("allocated pod identity/GPU/RAM/CUDA/price guard failed")
    return {k:pod[k] for k in ("id","name","status","gpu","cost","cloud","image","cudaVersion")}


def ownership(path):
    value=read_json(path)
    if (value.get("schema")!=ARTIFACT_VERSION or value.get("api_base")!=API
            or value.get("maximum_seconds")!=MAX_SECONDS or type(value.get("maximum_seconds")) is not int
            or not isinstance(value.get("name"),str) or not value["name"].startswith("ideas-20261018-gpu-final-")
            or not ID_PATTERN.fullmatch(str(value.get("id","")))
            or not numeric(value.get("started_unix")) or not numeric(value.get("expires_unix"))
            or value["expires_unix"]-value["started_unix"]!=MAX_SECONDS
            or value.get("delete_url")!=API+"/pods/"+value["id"]):
        raise ValueError("invalid exact-owned-ID watchdog receipt")
    return value


def cleanup(client,owner):
    identifier=owner["id"]
    try:
        status,_=client.call("DELETE","/pods/"+identifier)
        if status!=204:
            raise ValueError("DELETE did not return204")
    except ProviderError as error:
        if error.status!=404:
            raise
    for _ in range(6):
        try:
            client.call("GET","/pods/"+identifier)
        except ProviderError as error:
            if error.status==404:
                return dict(id=identifier,delete_requested=True,absence_verified=True,verified_unix=time.time())
            raise
        time.sleep(5)
    raise RuntimeError("exact pod ID still readable after deletion; absence unverified")


def start_watchdog(intent_path,output,bearer):
    # Separate process/session survives loss of the main controller. No key in argv.
    with (output/"watchdog.stdout").open("xb") as stdout,(output/"watchdog.stderr").open("xb") as stderr:
        environment=dict(os.environ,IDEAS_EXPECTED_POD_BEARER=bearer)
        child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),"watchdog","--intent",str(intent_path)],
            stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,start_new_session=True,close_fds=True,env=environment)
    write_once(output/"watchdog-process.json",dict(pid=child.pid,independent_session=True,maximum_seconds=MAX_SECONDS))
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        if child.poll() is not None:
            raise RuntimeError("watchdog exited before readiness; no POST permitted")
        ready=output/"watchdog-ready.json"
        if ready.is_file():
            expected=read_json(intent_path)
            acknowledged=read_json(ready)
            if acknowledged==dict(name=expected["name"],intent_sha256=sha(intent_path),maximum_seconds=MAX_SECONDS):
                return
            raise ValueError("watchdog readiness acknowledgement mismatch")
        time.sleep(.1)
    raise RuntimeError("watchdog readiness deadline; no POST permitted")


def cleanup_until_absent(client,owner,output):
    """Keep trying after transient API failures; never treat failure as deletion.

    The independent cleanup starts 300 seconds before the 3600-second target. Provider outages
    can defeat a billing deadline; retain that violation and keep deleting.
    """
    attempt=0
    while True:
        try:
            return cleanup(client,owner)
        except BaseException as error:
            if isinstance(error,(KeyboardInterrupt,SystemExit)):
                raise
            record=dict(id=owner["id"],error_type=type(error).__name__,attempt=attempt,
                deadline_exceeded=time.time()>owner["expires_unix"],absence_verified=False)
            cleanup_record(Path(output)/f"watchdog-delete-failure-{owner['id']}-{attempt:04d}.json",record)
            attempt+=1
            time.sleep(min(30,2**min(attempt,5)))


def watchdog(owner_path,client):
    owner_path=Path(owner_path).resolve(); owner=ownership(owner_path)
    confirmation=owner_path.parent/"cleanup-confirmation.json"
    remaining=max(0.0,min(float(WATCHDOG_CLEANUP_SECONDS),owner["started_unix"]+WATCHDOG_CLEANUP_SECONDS-time.time()))
    deadline=time.monotonic()+remaining
    while time.monotonic()<deadline:
        if confirmation.is_file():
            saved=read_json(confirmation)
            if saved.get("id")==owner["id"] and saved.get("absence_verified") is True:
                return
        time.sleep(min(5,max(0,deadline-time.monotonic())))
    result=cleanup_until_absent(client,owner,owner_path.parent)
    cleanup_record(owner_path.parent/"watchdog-cleanup.json",result)


def intent_watchdog(intent_path,client,bearer):
    intent_path=Path(intent_path).resolve(); intent=read_json(intent_path); output=intent_path.parent
    if (intent.get("schema")!=ARTIFACT_VERSION+"/intent" or intent.get("api_base")!=API
            or intent.get("maximum_seconds")!=MAX_SECONDS or type(intent.get("maximum_seconds")) is not int
            or not isinstance(intent.get("name"),str) or not re.fullmatch(r"ideas-20261018-gpu-final-[0-9a-f]{16}",intent["name"])
            or not numeric(intent.get("started_unix")) or not numeric(intent.get("expires_unix"))
            or intent["expires_unix"]-intent["started_unix"]!=MAX_SECONDS
            or not isinstance(bearer,str) or len(bearer)<32
            or hashlib.sha256(bearer.encode()).hexdigest()!=intent.get("http_bearer_sha256")):
        raise ValueError("invalid pre-POST intent/nonce binding")
    write_once(output/"watchdog-ready.json",dict(name=intent["name"],intent_sha256=sha(intent_path),maximum_seconds=MAX_SECONDS))
    remaining=max(0.0,min(float(WATCHDOG_CLEANUP_SECONDS),intent["started_unix"]+WATCHDOG_CLEANUP_SECONDS-time.time()))
    deadline=time.monotonic()+remaining
    while time.monotonic()<deadline:
        if (output/"cleanup-requested.json").is_file() or (output/"cleanup-confirmation.json").is_file():
            break
        time.sleep(min(5,max(0,deadline-time.monotonic())))
    attempt=0; cleaned=[]
    while True:
        try:
            owner_path=output/"ownership.json"
            owner=None
            if owner_path.is_file():
                try:
                    owner=ownership(owner_path)
                except (OSError,ValueError,KeyError,TypeError) as error:
                    cleanup_record(output/f"ownership-read-failure-{attempt:04d}.json",dict(error_type=type(error).__name__,
                        fallback="continue fresh-name AND nonce reconciliation"))
            if owner and (owner["name"]!=intent["name"] or owner["expires_unix"]!=intent["expires_unix"]):
                raise ValueError("intent and exact ownership mismatch")
            matches=named_pods(client,intent["name"])
            # Reconciliation never adopts a pod on name alone: the fresh bearer
            # must match the provider's env, unless its ID came from our201.
            candidates=[]
            for pod in matches:
                identifier=pod_id(pod)
                expected=owner and identifier==owner["id"]
                if not expected and pod.get("env",{}).get("IDEAS_HTTP_BEARER")!=bearer:
                    raise ValueError("exact-name resource lacks the request's fresh nonce")
                candidates.append({**intent,"id":identifier})
            if owner and not any(p["id"]==owner["id"] for p in candidates):
                candidates.append(owner)
            for candidate in candidates:
                result=cleanup_until_absent(client,candidate,output)
                cleaned.append(result)
            if owner is not None or candidates or time.time()>=intent["expires_unix"]:
                cleanup_record(output/"intent-watchdog-cleanup.json",dict(name=intent["name"],cleaned=cleaned,
                    complete_current_inventory=True,unobserved_creation_remains_uncertain=(owner is None and not candidates),
                    deadline_exceeded=time.time()>intent["expires_unix"]))
                return
            # An ambiguous request with no visible ID remains monitored until
            # the fixed expiry; an empty early list never proves no creation.
        except BaseException as error:
            if isinstance(error,(KeyboardInterrupt,SystemExit)):
                raise
            cleanup_record(output/f"intent-watchdog-failure-{attempt:04d}.json",dict(error_type=type(error).__name__,
                deadline_exceeded=time.time()>intent["expires_unix"],absence_verified=False))
            attempt+=1
        time.sleep(min(30,2**min(attempt+1,5)))


def evidence_request(base,path,bearer,timeout=30):
    return authenticated_open(urllib.request.Request(base+path,
        headers={"Authorization":"Bearer "+bearer,"User-Agent":"cryptanalysis-research/1.0"}),timeout)


def fetch_job(owner,bearer,output,deadline):
    base="https://"+owner["id"]+"-8888.proxy.runpod.net"
    poll=0
    while time.monotonic()<deadline:
        try:
            with evidence_request(base,"/status",bearer) as response:
                status=json.load(response)
            write_once(output/f"status-{poll:04d}.json",status); poll+=1
            if status.get("done") is True and status.get("archive_error"):
                raise RuntimeError("fixed adapter archive failed")
            if status.get("done") is True and status.get("archive_ready") is True:
                break
        except (urllib.error.URLError,TimeoutError,ValueError):
            pass
        time.sleep(min(10,max(0,deadline-time.monotonic())))
    else:
        raise RuntimeError("fixed3000s controller deadline exceeded")
    expected=status.get("archive_sha256"); size=status.get("archive_bytes")
    if not isinstance(expected,str) or not SHA_PATTERN.fullmatch(expected) or type(size) is not int or size<=0:
        raise ValueError("invalid authenticated archive metadata")
    if shutil.disk_usage(output).free<size+1024**3:
        raise RuntimeError("insufficient local evidence disk space")
    archive=output/"evidence.tar.gz"; total=0
    destination=output/"evidence"
    if archive.exists() or destination.exists():
        raise FileExistsError("refusing any pre-existing final archive/extraction")
    with evidence_request(base,"/evidence.tar.gz",bearer,180) as response,archive.open("xb") as stream:
        while block:=response.read(1024*1024):
            total+=len(block)
            if total>size:
                raise ValueError("evidence exceeds authenticated archive size")
            stream.write(block)
    if total!=size or sha(archive)!=expected:
        raise ValueError("retrieved archive size/hash mismatch")
    destination.mkdir()
    with tarfile.open(archive) as tar:
        seen=set()
        for member in tar.getmembers():
            if member.name in seen:
                raise ValueError("duplicate archive member")
            seen.add(member.name)
            if (not member.name.startswith("remote/run-gpu-v3/") or not (member.isfile() or member.isdir())
                    or ".." in Path(member.name).parts or Path(member.name).is_absolute()):
                raise ValueError("archive member outside exact fresh GPU evidence namespace")
        tar.extractall(destination,filter="data")
    run=destination/"remote/run-gpu-v3"
    manifest=run/"http-evidence-files.sha256"
    if not manifest.is_file():
        raise ValueError("missing scientific evidence file manifest")
    entries=[]
    for line in manifest.read_text().splitlines():
        expected_file,relative=line.split("  ",1)
        path=Path(relative)
        if (not SHA_PATTERN.fullmatch(expected_file) or path.is_absolute() or ".." in path.parts
                or relative in entries or not (run/path).is_file() or sha(run/path)!=expected_file):
            raise ValueError("scientific member digest/path validation failed")
        entries.append(relative)
    actual={p.relative_to(run).as_posix() for p in run.rglob("*") if p.is_file() and p!=manifest}
    if set(entries)!=actual:
        raise ValueError("scientific member manifest coverage mismatch")
    write_once(output/"evidence-verification.json",dict(archive_sha256=expected,archive_bytes=total,
        member_files_verified=len(entries),exact_member_coverage=True,fresh_extraction=True))
    return dict(results_fetched=True,evidence_sha256=expected,evidence_bytes=total,
        workflow_returncode=status.get("returncode"),scientific_started=(destination/"remote/run-gpu-v3/started.utc").is_file())


def execute(commit,output,client_factory=ApiClient):
    output=Path(output).resolve()
    if output != (STUDY/"resource-runs/gpu-final-01").resolve():
        raise ValueError("final continuation output must be the one fresh resource-runs/gpu-final-01 directory")
    output.mkdir(parents=True,exist_ok=False)
    url=public_source(commit)
    write_once(output/"public-source-proof.json",prove_public_source(url))
    bearer=secrets.token_urlsafe(48)
    # Read only here, after explicit execute and unauthenticated source proof.
    client=client_factory(os.environ.get("RUNPOD_API_KEY",""),hidden=(bearer,))
    catalog=selected_catalog(client); write_once(output/"selected-catalog.json",catalog)
    name="ideas-20261018-gpu-final-"+secrets.token_hex(8)
    if named_pods(client,name):
        raise RuntimeError("prospective unique name already exists; refuse adoption/replacement")
    before=time.time(); monotonic_start=time.monotonic()
    intent=dict(schema=ARTIFACT_VERSION+"/intent",api_base=API,name=name,started_unix=before,
        expires_unix=before+MAX_SECONDS,maximum_seconds=MAX_SECONDS,
        http_bearer_sha256=hashlib.sha256(bearer.encode()).hexdigest(),payload_sha256=PAYLOAD_SHA256)
    intent_path=output/"ownership-intent.json"; write_once(intent_path,intent)
    # This detached process is armed before any paid POST can be sent.
    start_watchdog(intent_path,output,bearer)
    outcome=dict(schema=ARTIFACT_VERSION,source_commit=commit,payload_sha256=PAYLOAD_SHA256,
        started_unix=time.time(),pod_id=None,results_fetched=False,deleted=False,absence_verified=False)
    owner=None
    try:
        for index,selection in enumerate(catalog):
            flavor=selection["id"]
            attempt=output/f"allocation-{index+1:02d}"; attempt.mkdir()
            body=create_body(flavor,name,url,bearer); write_once(attempt/"request-redacted.json",safe_body(body))
            response_candidate=None
            try:
                status,pod=client.call("POST","/pods",body,timeout=60)
                if (isinstance(pod,dict) and pod.get("name")==name
                        and pod.get("env",{}).get("IDEAS_HTTP_BEARER")==bearer
                        and isinstance(pod.get("id"),str) and ID_PATTERN.fullmatch(pod["id"])):
                    response_candidate=pod
                if status!=201:
                    raise ValueError("create did not return201")
                identifier=pod_id(pod)
            except BaseException as error:
                write_once(attempt/"refusal.json",dict(error_type=type(error).__name__,
                    status=error.status if isinstance(error,ProviderError) else None,
                    detail=error.detail if isinstance(error,ProviderError) else "creation response missing/ambiguous; no automatic retry"))
                found=[response_candidate] if response_candidate is not None else named_pods(client,name)
                if len(found)>1:
                    raise RuntimeError("multiple exact-name allocations; manual exact-ID cleanup required") from None
                if found:
                    pod=found[0]; identifier=pod_id(pod)
                    if pod.get("env",{}).get("IDEAS_HTTP_BEARER")!=bearer:
                        raise RuntimeError("ambiguous exact-name resource lacks the fresh request nonce")
                elif isinstance(error,ProviderError) and error.status in (400,403):
                    # Explicit refusal only. Availability is advisory; preserve both attempts.
                    continue
                else:
                    raise RuntimeError("creation uncertain/refused; no fallback after ambiguous POST") from None
                ambiguous=True
            else:
                ambiguous=False
            # Own only the exact ID returned by this POST or its unique-name reconciliation.
            owner=dict(schema=ARTIFACT_VERSION,id=identifier,name=name,api_base=API,started_unix=before,
                expires_unix=before+MAX_SECONDS,maximum_seconds=MAX_SECONDS,delete_url=API+"/pods/"+identifier,
                flavor=flavor,source_commit=commit,payload_sha256=PAYLOAD_SHA256,creation_response_ambiguous=ambiguous)
            owner_path=output/"ownership.json"; write_once(owner_path,owner); outcome["pod_id"]=identifier
            if ambiguous:
                raise RuntimeError("ambiguous allocation recovered by exact unique name; clean up, do not run a second create")
            summary=guard_pod(pod,name,flavor,identifier)
            write_once(attempt/"created-summary.json",summary)
            print(json.dumps(dict(owned=summary,ownership_file=str(owner_path),maximum_seconds=MAX_SECONDS)),flush=True)
            outcome.update(fetch_job(owner,bearer,output,monotonic_start+CONTROLLER_SECONDS))
            break
        if owner is None:
            raise RuntimeError("all eligible exact GPU type requests refused; no capacity conclusion beyond these requests")
    except BaseException as error:
        outcome["controller_error_type"]=type(error).__name__
        outcome["controller_error"]=client.safe_detail(error) if isinstance(error,ProviderError) else "controller stopped; see stage receipts"
        raise
    finally:
        cleanup_record(output/"cleanup-requested.json",dict(name=name,requested_unix=time.time(),exact_name_nonce_binding=True))
        if owner is not None:
            try:
                result=cleanup(client,owner)
                cleanup_record(output/"cleanup-confirmation.json",result)
                outcome.update(deleted=True,absence_verified=True)
            except BaseException as error:
                outcome["cleanup_error_type"]=type(error).__name__
                # The independent watchdog remains responsible at the fixed deadline.
        outcome["finished_unix"]=time.time()
        write_once(output/"resource-outcome.json",outcome)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest="mode",required=True)
    for mode in ("plan","execute"):
        sub=commands.add_parser(mode); sub.add_argument("--source-commit",required=True)
        if mode=="execute":
            sub.add_argument("--out",type=Path,required=True)
    sub=commands.add_parser("watchdog")
    selection=sub.add_mutually_exclusive_group(required=True)
    selection.add_argument("--ownership",type=Path); selection.add_argument("--intent",type=Path)
    sub=commands.add_parser("cleanup"); sub.add_argument("--ownership",type=Path,required=True)
    args=parser.parse_args()
    if args.mode=="plan":
        url=public_source(args.source_commit)
        print(json.dumps(dict(schema=ARTIFACT_VERSION,provider_actions=False,source_url=url,
            payload_sha256=PAYLOAD_SHA256,bodies=[safe_body(create_body(flavor,"ideas-20261018-gpu-final-0000000000000000",url,"<fresh-http-bearer-never-recorded>")) for flavor in FLAVORS],
            maximum_price_per_hour=MAX_PRICE,maximum_seconds=MAX_SECONDS,
            cleanup_begins_seconds=WATCHDOG_CLEANUP_SECONDS,controller_seconds=CONTROLLER_SECONDS,
            maximum_actual_pods=1,required_fresh_local_output="resource-runs/gpu-final-01",
            native_payload_unchanged=True),indent=2))
    elif args.mode=="execute":
        execute(args.source_commit,args.out)
    else:
        client=ApiClient(os.environ.get("RUNPOD_API_KEY",""))
        if args.mode=="watchdog" and args.intent:
            intent_watchdog(args.intent,client,os.environ.get("IDEAS_EXPECTED_POD_BEARER",""))
        elif args.mode=="watchdog":
            watchdog(args.ownership,client)
        else:
            print(json.dumps(cleanup(client,ownership(args.ownership))))


if __name__=="__main__":
    main()

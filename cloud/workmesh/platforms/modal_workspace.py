"""Example: modal run platforms/modal_workspace.py

Create a Modal secret named workmesh-runtime with TS_AUTHKEY,
CONDUCTOR_ENDPOINT, CONDUCTOR_TOKEN, CONDUCTOR_PROJECT, CAIRN_LEADER_HOST.
Add vendor credentials using their supported environment variables or mount
login state. Running this example creates a billed 24-hour Sandbox.
"""
from pathlib import Path
import modal

ROOT = Path(__file__).resolve().parents[1]
app = modal.App("workmesh")
image = (
    modal.Image.debian_slim(python_version="3.12")
    .add_local_file(str(ROOT / "bootstrap.sh"), "/opt/bootstrap.sh", copy=True)
    .add_local_file(str(ROOT / "platforms/hosted-config.sh"), "/opt/hosted-config.sh", copy=True)
    .run_commands(
        "WB_ROOT=/opt/workmesh PROFILE=research DOCKER_MODE=client "
        "CONDUCTOR_MODE=client CAIRN_MODE=worker ISOLATION=off "
        "bash /opt/bootstrap.sh install"
    )
)
secrets = modal.Secret.from_name("workmesh-runtime")


@app.local_entrypoint()
def main(name: str = "main"):
    # Use one active Sandbox per named volume. Different simultaneous workspaces
    # need different names so they have separate Cairn/Tailscale identities.
    state = modal.Volume.from_name(f"workmesh-state-{name}", create_if_missing=True)
    sandbox = modal.Sandbox.create(
        "bash", "/opt/bootstrap.sh", "run", "--root", "/opt/workmesh",
        "--config", "/opt/hosted-config.sh", "--", "sleep", "infinity",
        app=app, image=image, secrets=[secrets],
        volumes={"/opt/workmesh/state": state},
        timeout=24 * 60 * 60,
    )
    print(f"Sandbox: {sandbox.object_id}")
    print("Use Modal's Sandbox exec/shell interface to enter the workspace.")

#!/usr/bin/env python3
"""Provider-label amendment; original controller/source remains preserved."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import controller
original = controller.podtool.pod_body

def provider_supported_body(args, keys, extra_env=None):
    body = original(args, keys, extra_env)
    body["allowedCudaVersions"] = ["13.0"]
    return body

# controller.main wraps this function and sets 13.3. Replace the actual API
# request's provider label at the final boundary, retaining every other field.
api = controller.podtool.api
def supported_api(method,url,body=None,timeout=60):
    if method == "POST" and url == controller.podtool.REST + "/pods":
        body = dict(body)
        body["allowedCudaVersions"] = ["13.0"]
    return api(method,url,body,timeout)
controller.podtool.api = supported_api
if __name__ == "__main__":
    controller.main()

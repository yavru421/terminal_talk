
import os
import json
import requests

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise Exception("GITHUB_TOKEN environment variable not set!")
REPO = "yavru421/terminal_talk"
FILE_PATH = "directory.json"
API_URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def get_directory():
    r = requests.get(API_URL, headers=HEADERS)
    if r.status_code == 200:
        content = r.json()['content']
        import base64
        decoded = base64.b64decode(content).decode()
        return json.loads(decoded), r.json()['sha']
    elif r.status_code == 404:
        return {}, None
    else:
        raise Exception(f"Failed to fetch directory: {r.status_code} {r.text}")

def update_directory(directory, sha=None):
    data = json.dumps(directory, indent=2)
    import base64
    b64 = base64.b64encode(data.encode()).decode()
    payload = {
        "message": "Update directory",
        "content": b64,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(API_URL, headers=HEADERS, json=payload)
    if r.status_code in (200, 201):
        print("[INFO] Directory updated on GitHub.")
    else:
        raise Exception(f"Failed to update directory: {r.status_code} {r.text}")

def register_handle(handle, address):
    directory, sha = get_directory()
    directory[handle] = address
    update_directory(directory, sha)

def lookup_handle(handle):
    directory, _ = get_directory()
    return directory.get(handle)

if __name__ == "__main__":
    # Example usage
    my_handle = input("Enter your handle: ").strip()
    my_address = input("Enter your Tailscale IP or address: ").strip()
    register_handle(my_handle, my_address)
    print(f"[INFO] Registered {my_handle} -> {my_address}")
    peer = input("Enter peer handle to look up: ").strip()
    addr = lookup_handle(peer)
    if addr:
        print(f"[INFO] Peer {peer} address: {addr}")
    else:
        print(f"[WARN] Peer {peer} not found in directory.")

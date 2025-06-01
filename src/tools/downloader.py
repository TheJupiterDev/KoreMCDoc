# Downloads the vanilla-mcdocs

import os
import requests

# Constants
REPO = "SpyglassMC/vanilla-mcdoc"
BRANCH = "main"
API_URL = f"https://api.github.com/repos/{REPO}/contents/java"
DEST_FOLDER = "mcdoc"

os.makedirs(DEST_FOLDER, exist_ok=True)

def download_file(path, save_path):
    # Fix path to use forward slashes for URL
    url_path = path.replace(os.sep, "/")
    url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/java/{url_path}"
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download: {path} (status code {response.status_code})")

def fetch_and_download(api_url, rel_path=""):
    response = requests.get(api_url)
    if response.status_code != 200:
        print(f"Failed to fetch {api_url}")
        return

    items = response.json()
    for item in items:
        item_path = os.path.join(rel_path, item["name"])
        if item["type"] == "file" and item["name"].endswith(".mcdoc"):
            local_path = os.path.join(DEST_FOLDER, item_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            download_file(item_path, local_path)
        elif item["type"] == "dir":
            fetch_and_download(item["url"], item_path)

# Start
fetch_and_download(API_URL) # Downloads the vanilla-mcdoc

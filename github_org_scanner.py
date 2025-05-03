import os
import subprocess
import tempfile
import requests
import csv
from dotenv import load_dotenv  #for reading from .env file , used for local testing

# Load token from .env (for local testing)
load_dotenv()

GITHUB_TOKEN = os.getenv("MY_GITHUB_PAT")
USERNAME = "ruchi172a"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_repos(username):
    print(f"🔍 Fetching repositories for user: {username}")
    url = f"https://api.github.com/users/{username}/repos?per_page=100"
    repos = []
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        repos.extend(response.json())
        url = response.links.get("next", {}).get("url")
    return [repo["clone_url"] for repo in repos]

def check_requirements(repo_url, csv_writer):
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "clone", "--depth", "1", repo_url, tmpdir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        req_path = os.path.join(tmpdir, "requirements.txt")
        if not os.path.isfile(req_path):
            print(f"❌ No requirements.txt in {repo_url}")
            return

        print(f"📦 Checking: {repo_url}")
        subprocess.run(["pip", "install", "-r", req_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result = subprocess.run(["pip", "list", "--outdated", "--format=json"], capture_output=True, text=True)
        
        try:
            outdated = eval(result.stdout)
        except Exception:
            print(f"⚠️ Failed to parse output from {repo_url}")
            return

        for pkg in outdated:
            csv_writer.writerow({
                "Repository": repo_url.split("/")[-1].replace(".git", ""),
                "Package": pkg['name'],
                "Current Version": pkg['version'],
                "Latest Version": pkg['latest_version']
            })

def main():
    repos = get_repos(USERNAME)

    with open("dependency_report.csv", mode="w", newline="") as file:
        fieldnames = ["Repository", "Package", "Current Version", "Latest Version"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for repo_url in repos:
            check_requirements(repo_url, writer)

    print("✅ CSV report generated: dependency_report.csv")

if __name__ == "__main__":
    main()

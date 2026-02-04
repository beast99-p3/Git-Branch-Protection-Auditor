import os
import requests
import json
import csv
import time
from datetime import datetime

# Load .env file if it exists
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# --- CONFIGURATION ---
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME") or os.getenv("GITHUB_ORG")  # Reuse ORG variable
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
API_URL = "https://api.github.com"

# SOC 2 CONTROLS TO VALIDATE
REQUIRED_CONTROLS = {
    "pull_request_before_merging": "Change Mgmt: No direct commits to main",
    "required_approving_review_count": "Change Mgmt: Two-person rule (Peer Review)",
    "required_status_checks": "Quality: CI/CD Gates passed",
    "required_signatures": "Integrity: Signed Commits",
    "non_fast_forward": "Integrity: Linear History (Optional but recommended)"
}

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def get_all_repos(username):
    """Fetches all non-archived repositories for the user."""
    repos = []
    page = 1
    while True:
        url = f"{API_URL}/users/{username}/repos?per_page=100&page={page}&sort=full_name"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"Error fetching repos: {response.status_code} - {response.text}")
            break
            
        data = response.json()
        if not data:
            break
            
        for repo in data:
            if not repo['archived'] and not repo['disabled']:
                repos.append(repo)
        
        print(f"Fetched page {page} ({len(data)} repos)...")
        page += 1
        
    return repos

def get_effective_branch_rules(owner, repo, branch):
    """
    Hits the 'rules/branches' endpoint.
    This aggregates Classic Protection AND Repository Rulesets.
    """
    url = f"{API_URL}/repos/{owner}/{repo}/rules/branches/{branch}"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 404:
        return []  # No rules exist
    elif response.status_code != 200:
        print(f"Error checking rules for {repo}/{branch}: {response.status_code}")
        return []
        
    return response.json()

def audit_repo(repo):
    """Analyzes a single repository against SOC 2 controls."""
    results = {
        "repo_name": repo['name'],
        "default_branch": repo['default_branch'],
        "visibility": repo['visibility'],
        "audit_timestamp": datetime.now().isoformat()
    }

    # Fetch all active rules for the default branch
    rules = get_effective_branch_rules(repo['owner']['login'], repo['name'], repo['default_branch'])
    
    # Initialize all controls as Failed
    for control in REQUIRED_CONTROLS.keys():
        results[control] = False
        
    # Parse the rules to find compliance
    for rule in rules:
        rule_type = rule.get("type")
        
        if rule_type == "pull_request":
            results["pull_request_before_merging"] = True
            params = rule.get("parameters", {})
            if params.get("required_approving_review_count", 0) >= 1:
                results["required_approving_review_count"] = True
                
        if rule_type == "required_status_checks":
            results["required_status_checks"] = True
            
        if rule_type == "required_signatures":
            results["required_signatures"] = True
            
        if rule_type == "non_fast_forward":
            results["non_fast_forward"] = True

    # Calculate SOC 2 Pass/Fail Status
    results["SOC2_COMPLIANT"] = results["pull_request_before_merging"] and results["required_approving_review_count"]
    
    return results

def main():
    if not GITHUB_USERNAME or not GITHUB_TOKEN:
        print("Please set GITHUB_USERNAME (or GITHUB_ORG) and GITHUB_TOKEN environment variables.")
        return

    print(f"Starting SOC 2 Branch Protection Audit for User: {GITHUB_USERNAME}")
    repos = get_all_repos(GITHUB_USERNAME)
    print(f"Found {len(repos)} active repositories. Scanning rules...")

    audit_data = []
    
    for repo in repos:
        # Rate limit handling
        time.sleep(0.2) 
        try:
            print(f"  Auditing: {repo['name']}...")
            audit_data.append(audit_repo(repo))
        except Exception as e:
            print(f"Failed to audit {repo['name']}: {e}")

    # Export Report using native CSV module
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/github_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    if audit_data:
        # Define column order
        cols = ["repo_name", "SOC2_COMPLIANT", "default_branch"] + list(REQUIRED_CONTROLS.keys()) + ["visibility", "audit_timestamp"]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=cols)
            writer.writeheader()
            writer.writerows(audit_data)
    
    compliant_count = sum(1 for item in audit_data if item["SOC2_COMPLIANT"])
    
    print(f"\n{'='*60}")
    print(f"--- Audit Complete ---")
    print(f"{'='*60}")
    print(f"Scanned: {len(audit_data)} repositories")
    print(f"✅ Compliant: {compliant_count}")
    print(f"❌ Non-Compliant: {len(audit_data) - compliant_count}")
    print(f"\n📄 Report saved to: {filename}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

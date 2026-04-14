"""
GitHub Branch Protection Auditor
=================================

This tool helps ensure your GitHub repositories meet SOC 2 compliance standards
by automatically checking if proper branch protection rules are configured.

Why this matters:
- Prevents unauthorized code from reaching production
- Enforces peer review (the "two-person rule")
- Ensures automated tests pass before merging
- Creates an audit trail for compliance officers

Author: GitHub Copilot & User
Date: February 2026
"""

import os
import requests
import json
import csv
import time
from datetime import datetime
from auth_utils import (
    load_env_file,
    build_headers,
    get_github_token_and_mode,
    validate_token_scopes,
)

# ============================================================================
# STEP 1: Load Environment Variables from .env File
# ============================================================================
# We don't want to hardcode sensitive information like API tokens in the code.
# Instead, we read them from a .env file which is kept private (in .gitignore)

if load_env_file(".env"):
    print("📄 Loading configuration from .env file...")

# ============================================================================
# STEP 2: Configuration - Who and What to Audit
# ============================================================================

# Your GitHub organization name (e.g., "microsoft", "google")
GITHUB_ORG = os.getenv("GITHUB_ORG")

# OR your personal GitHub username (e.g., "beast99-p3")
# The script prioritizes GITHUB_ORG if both are set
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

# Base URL for GitHub's REST API (v3)
API_URL = "https://api.github.com"
HEADERS = {}

# ============================================================================
# STEP 3: Define SOC 2 Compliance Controls We're Checking
# ============================================================================
# These are the security controls that SOC 2 auditors look for.
# Each control maps to a specific GitHub branch protection setting.

REQUIRED_CONTROLS = {
    # Control 1: Pull Request Requirement
    # Ensures no one can push code directly to main/master without review
    "pull_request_before_merging": "Change Mgmt: No direct commits to main",
    
    # Control 2: Code Review Requirement (Most Critical!)
    # Enforces the "two-person rule" - someone else must approve your code
    "required_approving_review_count": "Change Mgmt: Two-person rule (Peer Review)",
    
    # Control 3: Automated Testing
    # CI/CD pipelines must pass (build, test, lint) before merging
    "required_status_checks": "Quality: CI/CD Gates passed",
    
    # Control 4: Cryptographic Verification
    # Commits must be signed with GPG keys to prevent impersonation
    "required_signatures": "Integrity: Signed Commits",
    
    # Control 5: Linear History (Best Practice)
    # Prevents messy merge commits, keeps history clean and traceable
    "non_fast_forward": "Integrity: Linear History (Optional but recommended)"
}

def get_all_repos_org(org):
    """
    Fetches all active repositories from a GitHub organization.
    
    Why pagination? GitHub limits API responses to 100 items per request.
    For large organizations with 500+ repos, we need to fetch multiple "pages".
    
    Args:
        org (str): The organization name (e.g., "microsoft")
    
    Returns:
        list: All active (non-archived, non-disabled) repositories
    """
    repos = []
    page = 1  # Start at page 1
    
    print(f"🔍 Scanning organization '{org}' for repositories...")
    
    while True:
        # Build the API URL with pagination parameters
        # per_page=100 means "give me up to 100 repos per request"
        url = f"{API_URL}/orgs/{org}/repos?per_page=100&page={page}&sort=full_name"
        
        # Make the HTTP GET request to GitHub
        response = requests.get(url, headers=HEADERS)
        
        # Check if the request was successful (200 = OK)
        if response.status_code != 200:
            print(f"❌ Error fetching repos: {response.status_code} - {response.text}")
            break
        
        # Convert JSON response to Python dictionary
        data = response.json()
        
        # If we get an empty list, we've fetched all pages
        if not data:
            break
        
        # Filter out archived and disabled repos (we only want active ones)
        for repo in data:
            if not repo['archived'] and not repo['disabled']:
                repos.append(repo)
        
        print(f"  📦 Fetched page {page} ({len(data)} repos)...")
        page += 1  # Move to next page
    
    return repos

def get_all_repos_user(username):
    """
    Fetches all active repositories from a personal GitHub account.
    
    This is similar to get_all_repos_org() but uses a different API endpoint
    because GitHub treats personal accounts and organizations differently.
    
    Args:
        username (str): GitHub username (e.g., "beast99-p3")
    
    Returns:
        list: All active personal repositories
    """
    repos = []
    page = 1
    
    print(f"👤 Scanning user '{username}' for repositories...")
    
    while True:
        # Different endpoint: /users/ instead of /orgs/
        url = f"{API_URL}/users/{username}/repos?per_page=100&page={page}&sort=full_name"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"❌ Error fetching repos: {response.status_code} - {response.text}")
            break
        
        data = response.json()
        if not data:
            break
        
        # Same filtering logic - skip archived and disabled repos
        for repo in data:
            if not repo['archived'] and not repo['disabled']:
                repos.append(repo)
        
        print(f"  📦 Fetched page {page} ({len(data)} repos)...")
        page += 1
    
    return repos

def get_effective_branch_rules(owner, repo, branch):
    """
    Fetches the ACTUAL branch protection rules for a specific branch.
    
    🎯 KEY INSIGHT FOR 2026:
    GitHub has two systems for branch protection:
    1. Classic Branch Protection (old way, per-repo)
    2. Repository Rulesets (new way, can be org-wide)
    
    This API endpoint is magical because it COMBINES both systems
    and returns the "effective" rules - what's ACTUALLY enforced.
    
    Args:
        owner (str): Repository owner (org name or username)
        repo (str): Repository name
        branch (str): Branch name (usually "main" or "master")
    
    Returns:
        list: Array of rule objects, or empty list if no protection
    """
    # The modern Rulesets API endpoint (introduced 2024)
    url = f"{API_URL}/repos/{owner}/{repo}/rules/branches/{branch}"
    response = requests.get(url, headers=HEADERS)
    
    # Handle different response codes:
    
    if response.status_code == 404:
        # 404 = Branch or rules not found
        # This means NO branch protection is configured
        return []
    
    elif response.status_code == 403:
        # 403 = Forbidden
        # Common on free GitHub plans - some features require paid plans
        # We treat this as "no protection" (non-compliant)
        return []
    
    elif response.status_code != 200:
        # Any other error (rate limit, auth failure, etc.)
        print(f"⚠️  Error checking rules for {repo}/{branch}: {response.status_code}")
        return []
    
    # Success! Return the array of protection rules
    return response.json()

def audit_repo(repo, owner):
    """
    The HEART of the auditor - analyzes one repository against all SOC 2 controls.
    
    Think of this as a security inspector checking a building:
    - Does it have locks? ✓/✗
    - Does it have an alarm system? ✓/✗
    - Does it have fire exits? ✓/✗
    
    We do the same for code repositories!
    
    Args:
        repo (dict): Repository metadata from GitHub API
        owner (str): Repository owner (for API calls)
    
    Returns:
        dict: Complete audit results with pass/fail for each control
    """
    
    # ========================================================================
    # Initialize the results dictionary with basic repo info
    # ========================================================================
    results = {
        "repo_name": repo['name'],
        "default_branch": repo['default_branch'],  # Usually "main" or "master"
        "visibility": repo['visibility'],          # public, private, or internal
        "audit_timestamp": datetime.now().isoformat()  # When we checked (for audit trail)
    }

    # ========================================================================
    # Fetch the actual protection rules from GitHub
    # ========================================================================
    rules = get_effective_branch_rules(owner, repo['name'], repo['default_branch'])
    
    # ========================================================================
    # Start with "guilty until proven innocent" - assume all controls FAIL
    # We'll flip these to True as we find matching rules
    # ========================================================================
    for control in REQUIRED_CONTROLS.keys():
        results[control] = False
    
    # ========================================================================
    # Parse the rules array and check what protections are actually enabled
    # ========================================================================
    # The rules array looks like:
    # [
    #   {"type": "pull_request", "parameters": {"required_approving_review_count": 2}},
    #   {"type": "required_status_checks", ...},
    #   ...
    # ]
    
    for rule in rules:
        rule_type = rule.get("type")  # What kind of protection is this?
        
        # ---- Check 1: Pull Request Requirement ----
        if rule_type == "pull_request":
            results["pull_request_before_merging"] = True
            
            # Dig deeper: how many reviewers are required?
            params = rule.get("parameters", {})
            review_count = params.get("required_approving_review_count", 0)
            
            if review_count >= 1:
                # At least one person must review! (The "two-person rule")
                results["required_approving_review_count"] = True
        
        # ---- Check 2: CI/CD Status Checks ----
        if rule_type == "required_status_checks":
            # Tests must pass before merging
            results["required_status_checks"] = True
        
        # ---- Check 3: Signed Commits ----
        if rule_type == "required_signatures":
            # Commits must be GPG-signed (prevents impersonation)
            results["required_signatures"] = True
        
        # ---- Check 4: Linear History ----
        if rule_type == "non_fast_forward":
            # Prevents messy merge commits
            results["non_fast_forward"] = True

    # ========================================================================
    # Calculate the OVERALL compliance verdict
    # ========================================================================
    # For SOC 2 Type 1/2, the MINIMUM requirement is:
    # 1. Pull requests must be required (no direct pushes)
    # 2. At least one code review must be required
    #
    # Everything else is "nice to have" but these two are CRITICAL
    results["SOC2_COMPLIANT"] = (
        results["pull_request_before_merging"] and 
        results["required_approving_review_count"]
    )
    
    return results

def main():
    """
    The main orchestrator - coordinates the entire audit process.
    
    Flow:
    1. Check credentials
    2. Decide: Organization or Personal account?
    3. Fetch all repositories
    4. Audit each one
    5. Generate CSV report
    6. Print summary
    """
    
    # ========================================================================
    # STEP 1: Verify we have the required credentials
    # ========================================================================
    try:
        github_token, auth_mode = get_github_token_and_mode()
    except RuntimeError as auth_error:
        print(f"❌ ERROR: {auth_error}")
        return
    
    global HEADERS
    HEADERS = build_headers(github_token)
    print(f"🔐 Authentication mode: {'GitHub App' if auth_mode == 'app' else 'Token'}")
    
    if auth_mode == "token":
        validate_token_scopes(github_token)

    # ========================================================================
    # STEP 2: Determine what we're auditing (Organization vs Personal)
    # ========================================================================
    target = None       # Who we're auditing (org name or username)
    audit_type = None   # "Organization" or "User"
    repos = []          # Will hold all repositories
    
    if GITHUB_ORG:
        # Organization audit takes priority if both are set
        target = GITHUB_ORG
        audit_type = "Organization"
        print(f"\n🏢 Starting SOC 2 Branch Protection Audit for Organization: {target}")
        print("=" * 60)
        repos = get_all_repos_org(target)
        
    elif GITHUB_USERNAME:
        # Personal account audit
        target = GITHUB_USERNAME
        audit_type = "User"
        print(f"\n👤 Starting SOC 2 Branch Protection Audit for User: {target}")
        print("=" * 60)
        repos = get_all_repos_user(target)
        
    else:
        # Neither is set - we can't proceed
        print("❌ ERROR: Please set either GITHUB_ORG or GITHUB_USERNAME in .env file")
        return
    
    print(f"\n✅ Found {len(repos)} active repositories. Starting analysis...\n")

    # ========================================================================
    # STEP 3: Audit each repository one by one
    # ========================================================================
    audit_data = []  # Will store results for all repos
    
    for repo in repos:
        # Rate limiting: Be nice to GitHub's API
        # Without this delay, we might hit rate limits (5000 requests/hour)
        time.sleep(0.2)  # 200ms delay between requests
        
        try:
            print(f"  🔍 Auditing: {repo['name']}...")
            
            # Get the owner (could be org or username)
            owner = repo.get('owner', {}).get('login', target)
            
            # Run the audit and store results
            audit_data.append(audit_repo(repo, owner))
            
        except Exception as e:
            # If something goes wrong with one repo, don't crash the entire audit
            print(f"  ❌ Failed to audit {repo['name']}: {e}")

    # ========================================================================
    # STEP 4: Generate the CSV report
    # ========================================================================
    # Make sure the reports folder exists
    os.makedirs("reports", exist_ok=True)
    
    # Create a descriptive filename with timestamp
    # Example: github_audit_report_organization_Test33best_20260203_204532.csv
    filename = (
        f"reports/github_audit_report_"
        f"{audit_type.lower()}_"
        f"{target}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    
    if audit_data:
        # Define the column order for the CSV
        # Most important columns first!
        cols = [
            "repo_name",           # What repo is this?
            "SOC2_COMPLIANT",      # The verdict! ✓ or ✗
            "default_branch",      # main? master?
        ] + list(REQUIRED_CONTROLS.keys()) + [  # All 5 individual controls
            "visibility",          # public/private/internal
            "audit_timestamp"      # When we checked
        ]
        
        # Write to CSV file
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=cols)
            writer.writeheader()        # Write column names
            writer.writerows(audit_data)  # Write all repo data
    
    # ========================================================================
    # STEP 5: Print a human-readable summary
    # ========================================================================
    # Count how many repos passed
    compliant_count = sum(1 for item in audit_data if item["SOC2_COMPLIANT"])
    
    print(f"\n{'='*60}")
    print(f"🎉 Audit Complete!")
    print(f"{'='*60}")
    print(f"📊 Target: {audit_type} '{target}'")
    print(f"📦 Scanned: {len(audit_data)} repositories")
    print(f"✅ Compliant: {compliant_count}")
    print(f"❌ Non-Compliant: {len(audit_data) - compliant_count}")
    print(f"\n📄 Report saved to: {filename}")
    print(f"{'='*60}\n")
    
    # Give users next steps
    if len(audit_data) - compliant_count > 0:
        print("💡 Next Steps:")
        print("   1. Open the CSV report in Excel or Google Sheets")
        print("   2. Filter SOC2_COMPLIANT = FALSE to see problematic repos")
        print("   3. Fix branch protection in GitHub repo settings")
        print(f"{'='*60}\n")

# ============================================================================
# ENTRY POINT: When you run "python github_auditor.py"
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔐 GitHub Branch Protection Auditor")
    print("    SOC 2 Compliance Scanner")
    print("="*60)
    main()

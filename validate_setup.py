"""
Setup Validator for GitHub Branch Protection Auditor
Run this before the main auditor to verify your configuration.
"""

import os
import sys
import requests

def validate_env():
    """Check if required environment variables are set."""
    print("🔍 Checking environment variables...")
    
    github_org = os.getenv("GITHUB_ORG")
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_org:
        print("  ❌ GITHUB_ORG not set")
        return False
    else:
        print(f"  ✅ GITHUB_ORG: {github_org}")
    
    if not github_token:
        print("  ❌ GITHUB_TOKEN not set")
        return False
    else:
        token_preview = github_token[:10] + "..." if len(github_token) > 10 else "***"
        print(f"  ✅ GITHUB_TOKEN: {token_preview}")
    
    return True

def validate_token_permissions():
    """Test if the GitHub token has correct permissions."""
    print("\n🔑 Validating GitHub token permissions...")
    
    github_token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Test token validity by fetching user info
    response = requests.get("https://api.github.com/user", headers=headers)
    
    if response.status_code != 200:
        print(f"  ❌ Token validation failed: {response.status_code}")
        if response.status_code == 401:
            print("     Token is invalid or expired. Generate a new token at:")
            print("     https://github.com/settings/tokens")
        return False
    
    user_data = response.json()
    print(f"  ✅ Token valid for user: {user_data.get('login')}")
    
    # Check token scopes
    scopes = response.headers.get('X-OAuth-Scopes', '').split(', ')
    print(f"  📋 Token scopes: {', '.join(scopes)}")
    
    required_scopes = {'repo', 'read:org'}
    has_required = any(s in scopes for s in required_scopes)
    
    if not has_required:
        print(f"  ⚠️  Warning: Token may need 'repo' and 'read:org' scopes")
        print(f"     Current scopes: {scopes}")
    
    return True

def validate_org_access():
    """Test if we can access the organization."""
    print("\n🏢 Validating organization access...")
    
    github_org = os.getenv("GITHUB_ORG")
    github_token = os.getenv("GITHUB_TOKEN")
    
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Try to fetch org info
    response = requests.get(f"https://api.github.com/orgs/{github_org}", headers=headers)
    
    if response.status_code == 404:
        print(f"  ❌ Organization '{github_org}' not found")
        print("     - Check if the org name is spelled correctly")
        print("     - Verify your token has access to this org")
        return False
    elif response.status_code != 200:
        print(f"  ❌ Failed to access org: {response.status_code}")
        return False
    
    org_data = response.json()
    print(f"  ✅ Organization found: {org_data.get('name', github_org)}")
    print(f"     Description: {org_data.get('description', 'No description')}")
    
    # Try to fetch repos
    print("\n📦 Checking repository access...")
    response = requests.get(
        f"https://api.github.com/orgs/{github_org}/repos?per_page=5",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"  ❌ Failed to fetch repos: {response.status_code}")
        return False
    
    repos = response.json()
    print(f"  ✅ Can access repositories ({len(repos)} fetched as sample)")
    
    if repos:
        print(f"     Sample repos:")
        for repo in repos[:3]:
            print(f"       - {repo['name']}")
    
    return True

def validate_dependencies():
    """Check if required Python packages are installed."""
    print("\n📚 Checking Python dependencies...")
    
    try:
        import requests
        print(f"  ✅ requests: {requests.__version__}")
    except ImportError:
        print("  ❌ requests not installed")
        return False
    
    try:
        import pandas
        print(f"  ✅ pandas: {pandas.__version__}")
    except ImportError:
        print("  ❌ pandas not installed")
        return False
    
    return True

def main():
    print("=" * 60)
    print("  GitHub Branch Protection Auditor - Setup Validator")
    print("=" * 60)
    print()
    
    # Load .env file if it exists
    if os.path.exists(".env"):
        print("📄 Loading .env file...")
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        print("  ✅ .env loaded\n")
    else:
        print("⚠️  No .env file found. Using system environment variables.\n")
    
    # Run validations
    checks = [
        ("Environment Variables", validate_env),
        ("Python Dependencies", validate_dependencies),
        ("GitHub Token", validate_token_permissions),
        ("Organization Access", validate_org_access),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"  ❌ {check_name} check failed: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("  ✅ All checks passed! You're ready to run the auditor.")
        print("=" * 60)
        print("\n🚀 Next step: Run the auditor with:")
        print("     python github_auditor.py")
        print("\n   Or use the batch file:")
        print("     run_auditor.bat")
        sys.exit(0)
    else:
        print("  ❌ Some checks failed. Please fix the issues above.")
        print("=" * 60)
        print("\n📖 For help, see QUICKSTART.md")
        sys.exit(1)

if __name__ == "__main__":
    main()

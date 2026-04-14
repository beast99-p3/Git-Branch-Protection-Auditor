"""
Setup Validator for GitHub Branch Protection Auditor
Run this before the main auditor to verify your configuration.
"""

import os
import sys
import requests
from auth_utils import load_env_file, get_secret, get_github_token_and_mode, build_headers

def validate_env():
    """Check if required environment variables are set."""
    print("🔍 Checking environment variables...")
    
    github_org = os.getenv("GITHUB_ORG")
    auth_mode = (os.getenv("GITHUB_AUTH_MODE") or "token").strip().lower()
    
    if not github_org:
        print("  ❌ GITHUB_ORG not set")
        return False
    else:
        print(f"  ✅ GITHUB_ORG: {github_org}")
    
    if auth_mode in ("token", "pat", ""):
        github_token = get_secret("GITHUB_TOKEN")
        if not github_token:
            print(
                "  ❌ GITHUB_TOKEN not set (or GITHUB_TOKEN_FILE / GITHUB_TOKEN_COMMAND missing)"
            )
            return False
        token_preview = github_token[:10] + "..." if len(github_token) > 10 else "***"
        print(f"  ✅ Token source resolved: {token_preview}")
    elif auth_mode in ("app", "github_app"):
        app_id = os.getenv("GITHUB_APP_ID")
        app_key = get_secret("GITHUB_APP_PRIVATE_KEY")
        if not app_id:
            print("  ❌ GITHUB_APP_ID not set for app auth mode")
            return False
        if not app_key:
            print(
                "  ❌ GITHUB_APP_PRIVATE_KEY not set "
                "(or GITHUB_APP_PRIVATE_KEY_FILE / GITHUB_APP_PRIVATE_KEY_COMMAND missing)"
            )
            return False
        print("  ✅ GitHub App configuration variables found")
    else:
        print("  ❌ GITHUB_AUTH_MODE must be 'token' or 'app'")
        return False
    
    return True

def validate_token_permissions():
    """Test if the GitHub token has correct permissions."""
    print("\n🔑 Validating GitHub token permissions...")
    
    try:
        github_token, mode = get_github_token_and_mode()
    except RuntimeError as err:
        print(f"  ❌ Failed to resolve authentication: {err}")
        return False
    headers = build_headers(github_token)
    
    # Test token validity by fetching user info
    response = requests.get("https://api.github.com/user", headers=headers)
    
    if response.status_code != 200:
        print(f"  ❌ Token validation failed: {response.status_code}")
        if response.status_code == 401:
            print("     Token is invalid or expired. Generate a new token at:")
            print("     https://github.com/settings/tokens")
        return False
    
    user_data = response.json()
    actor = user_data.get('login') or user_data.get('name') or "unknown"
    print(f"  ✅ Authentication valid for actor: {actor} ({mode})")
    
    # Check token scopes
    scopes = response.headers.get('X-OAuth-Scopes', '').split(', ')
    print(f"  📋 Token scopes: {', '.join(scopes)}")
    
    required_scopes = {'repo', 'read:org'}
    has_required = all(s in scopes for s in required_scopes) if scopes else False
    
    if not has_required:
        if mode == "token":
            print(f"  ⚠️  Warning: Token may need 'repo' and 'read:org' scopes")
            print(f"     Current scopes: {scopes}")
        else:
            print("  ℹ️  Scope headers are not always present for GitHub App tokens.")
    
    return True

def validate_org_access():
    """Test if we can access the organization."""
    print("\n🏢 Validating organization access...")
    
    github_org = os.getenv("GITHUB_ORG")
    github_token, _ = get_github_token_and_mode()
    headers = build_headers(github_token)
    
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
    if load_env_file(".env"):
        print("📄 Loading .env file...")
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

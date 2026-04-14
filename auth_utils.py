import os
import subprocess
import time

import jwt
import requests

API_URL = "https://api.github.com"
API_VERSION = "2022-11-28"


def load_env_file(path=".env"):
    """Load key=value pairs from a local .env file."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        return True
    return False


def _read_secret_file(secret_file):
    if not secret_file:
        return None
    if not os.path.exists(secret_file):
        return None
    with open(secret_file, "r", encoding="utf-8") as f:
        return f.read().strip()


def _read_secret_command(secret_command):
    if not secret_command:
        return None
    result = subprocess.run(
        secret_command,
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def get_secret(env_var_name):
    """
    Resolve secrets from:
    1) ENV var directly
    2) <VAR>_FILE (path to secret file)
    3) <VAR>_COMMAND (command that prints secret)
    """
    direct_value = os.getenv(env_var_name)
    if direct_value:
        return direct_value

    file_value = _read_secret_file(os.getenv(f"{env_var_name}_FILE"))
    if file_value:
        return file_value

    command_value = _read_secret_command(os.getenv(f"{env_var_name}_COMMAND"))
    if command_value:
        return command_value

    return None


def build_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
    }


def validate_token_scopes(token, required_scopes=None):
    """
    Validate PAT/fine-grained token and warn if expected classic scopes are missing.
    This is advisory and intentionally non-blocking.
    """
    if required_scopes is None:
        required_scopes = {"repo", "read:org"}

    response = requests.get(f"{API_URL}/user", headers=build_headers(token), timeout=20)
    if response.status_code != 200:
        print(f"⚠️  Could not validate token scopes (status {response.status_code}).")
        return

    scope_header = response.headers.get("X-OAuth-Scopes", "")
    scopes = {scope.strip() for scope in scope_header.split(",") if scope.strip()}
    missing_scopes = [scope for scope in required_scopes if scope not in scopes]

    if missing_scopes:
        print(
            f"⚠️  Token scope warning: missing recommended scopes: {', '.join(missing_scopes)}"
        )
        print("   The audit may still work for accessible repositories.")
    else:
        print("✅ Token scope check passed (repo, read:org).")


def _create_app_jwt(app_id, private_key):
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 9 * 60,
        "iss": app_id,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def _get_installation_id(app_jwt, target_org=None):
    headers = build_headers(app_jwt)
    response = requests.get(f"{API_URL}/app/installations", headers=headers, timeout=20)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to list app installations: {response.status_code} - {response.text}"
        )

    installations = response.json()
    if not installations:
        raise RuntimeError("No app installations found for this GitHub App.")

    if target_org:
        for installation in installations:
            account = installation.get("account", {})
            if account.get("login", "").lower() == target_org.lower():
                return installation["id"]

    return installations[0]["id"]


def get_github_token_and_mode():
    """
    Return (token, mode_string).
    Modes: 'token' (PAT/fine-grained) or 'app' (GitHub App installation token).
    """
    configured_mode = (os.getenv("GITHUB_AUTH_MODE") or "").strip().lower()

    if configured_mode in {"app", "github_app"}:
        use_app = True
    elif configured_mode in {"token", "pat", ""}:
        use_app = False
    else:
        raise RuntimeError("GITHUB_AUTH_MODE must be 'token' or 'app'.")

    if use_app:
        app_id = os.getenv("GITHUB_APP_ID")
        installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")
        private_key = get_secret("GITHUB_APP_PRIVATE_KEY")

        if not app_id or not private_key:
            raise RuntimeError(
                "GitHub App auth requires GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY "
                "(or GITHUB_APP_PRIVATE_KEY_FILE / GITHUB_APP_PRIVATE_KEY_COMMAND)."
            )

        app_jwt = _create_app_jwt(app_id, private_key)
        if not installation_id:
            installation_id = _get_installation_id(app_jwt, os.getenv("GITHUB_ORG"))

        token_response = requests.post(
            f"{API_URL}/app/installations/{installation_id}/access_tokens",
            headers=build_headers(app_jwt),
            timeout=20,
        )
        if token_response.status_code not in (200, 201):
            raise RuntimeError(
                "Failed to create installation token: "
                f"{token_response.status_code} - {token_response.text}"
            )

        token = token_response.json().get("token")
        if not token:
            raise RuntimeError("Installation token response did not include a token.")

        return token, "app"

    token = get_secret("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN is not set (or GITHUB_TOKEN_FILE / GITHUB_TOKEN_COMMAND)."
        )
    return token, "token"

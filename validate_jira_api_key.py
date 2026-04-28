#!/usr/bin/env python3
"""
Quick Jira API token validation script.

Usage:
  # Create a .env file in this folder:
  # JIRA_BASE_URL=https://your-domain.atlassian.net
  # JIRA_EMAIL=you@company.com
  # JIRA_API_TOKEN=your_token_here
  python3 validate_jira_api_key.py
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request


def load_dotenv(path: str = ".env") -> None:
    try:
        with open(path, "r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    os.environ.setdefault(key, value)
    except FileNotFoundError:
        pass


def main() -> int:
    load_dotenv()
    base_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    email = os.getenv("JIRA_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")

    missing = []
    if not base_url:
        missing.append("JIRA_BASE_URL")
    if not email:
        missing.append("JIRA_EMAIL")
    if not api_token:
        missing.append("JIRA_API_TOKEN")

    if missing:
        print("Missing required environment variables:")
        for item in missing:
            print(f"  - {item}")
        print("Add them to a local .env file, for example:")
        print("  JIRA_BASE_URL=https://your-domain.atlassian.net")
        print("  JIRA_EMAIL=you@company.com")
        print("  JIRA_API_TOKEN=your_token_here")
        return 1

    auth_raw = f"{email}:{api_token}".encode("utf-8")
    auth_header = base64.b64encode(auth_raw).decode("utf-8")

    url = f"{base_url}/rest/api/3/myself"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Basic {auth_header}",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print("Token check failed.")
        print(f"HTTP status: {exc.code}")
        if error_body:
            print(f"Jira response: {error_body}")
        print("This can mean the token is invalid, email is wrong, or API access is restricted.")
        return 2
    except Exception as exc:
        print(f"Network/request error: {exc}")
        return 1

    account_id = data.get("accountId", "n/a")
    display_name = data.get("displayName", "n/a")
    print("Token looks valid.")
    print("API endpoint: /rest/api/3/myself")
    print(f"Authenticated user: {display_name} (accountId: {account_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

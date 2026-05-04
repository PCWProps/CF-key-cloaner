from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"
DEFAULT_EXPIRY_DAYS = 365


class CfClonerError(Exception):
    """User-facing cf-cloner error."""


def run_command(args: list[str], *, input_text: str | None = None) -> str:
    try:
        result = subprocess.run(
            args,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or "command failed"
        raise CfClonerError(message) from exc


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise CfClonerError(
            f"Required command '{name}' was not found in PATH. "
            f"Install it before running cf-clone."
        )


def ensure_dependencies() -> None:
    for command in ("op", "fzf"):
        require_command(command)


def ensure_1password_signed_in() -> None:
    run_command(["op", "account", "get"])


def select_1password_item() -> tuple[str, str]:
    items_raw = run_command(
        ["op", "item", "list", "--categories", "API Credential", "--format", "json"]
    )
    items = json.loads(items_raw)
    if not items:
        raise CfClonerError("No 1Password API Credential items were found.")
    lines: list[str] = []
    id_to_title: dict[str, str] = {}
    for item in items:
        item_id = item.get("id")
        title = item.get("title", "Untitled")
        vault = item.get("vault", {}).get("name", "Unknown Vault")
        if not item_id:
            continue
        id_to_title[item_id] = title
        lines.append(f"{title} [{vault}] | {item_id}")
    selected = run_command(
        [
            "fzf",
            "--reverse",
            "--prompt",
            "Select source Cloudflare token: ",
            "--height",
            "40%",
        ],
        input_text="\n".join(lines),
    )
    if not selected:
        raise CfClonerError("Selection cancelled.")
    item_id = selected.rsplit("|", 1)[-1].strip()
    return item_id, id_to_title.get(item_id, "Unknown")


def get_credential_reference(item_id: str) -> str:
    item_raw = run_command(["op", "item", "get", item_id, "--format", "json"])
    item = json.loads(item_raw)
    fields = item.get("fields", [])
    for field in fields:
        label = str(field.get("label", "")).lower()
        purpose = str(field.get("purpose", "")).lower()
        if label in {"credential", "token", "api token", "api_token", "password"}:
            reference = field.get("reference")
            if reference:
                return reference
        if purpose == "password":
            reference = field.get("reference")
            if reference:
                return reference
    raise CfClonerError(
        "Could not find a credential/token/password field with a 1Password secret reference."
    )


def read_secret(reference: str) -> str:
    secret = run_command(["op", "read", reference])
    if not secret:
        raise CfClonerError("1Password returned an empty secret.")
    return secret


def cloudflare_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def cf_request(
    method: str,
    path: str,
    *,
    token: str,
    json_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{CLOUDFLARE_API_BASE}{path}"
    response = requests.request(
        method,
        url,
        headers=cloudflare_headers(token),
        json=json_payload,
        timeout=30,
    )
    try:
        data = response.json()
    except ValueError as exc:
        raise CfClonerError(f"Cloudflare returned non-JSON response: HTTP {response.status_code}") from exc
    if not data.get("success"):
        raise CfClonerError(
            "Cloudflare API request failed: "
            + json.dumps(data.get("errors", data), indent=2)
        )
    return data


def verify_source_token(token: str) -> str:
    data = cf_request("GET", "/user/tokens/verify", token=token)
    token_id = data.get("result", {}).get("id")
    if not token_id:
        raise CfClonerError("Cloudflare did not return a token id from verification.")
    return token_id


def fetch_source_policies(token: str, token_id: str) -> list[dict[str, Any]]:
    data = cf_request("GET", f"/user/tokens/{token_id}", token=token)
    policies = data.get("result", {}).get("policies")
    if not isinstance(policies, list):
        raise CfClonerError("Cloudflare did not return a valid policies array.")
    return policies


def create_cloned_token(
    *,
    source_token: str,
    new_name: str,
    policies: list[dict[str, Any]],
    expiry_days: int,
) -> tuple[str, str]:
    expires_on = (
        datetime.now(timezone.utc) + timedelta(days=expiry_days)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "name": new_name,
        "policies": policies,
        "expires_on": expires_on,
    }
    data = cf_request("POST", "/user/tokens", token=source_token, json_payload=payload)
    value = data.get("result", {}).get("value")
    if not value:
        raise CfClonerError("Cloudflare created the token but did not return a token value.")
    return value, expires_on


def save_token_to_1password(
    *,
    token_value: str,
    title: str,
    vault: str,
    source_reference: str,
    expires_on: str,
) -> None:
    notes = (
        "Created by cf-cloner.\n"
        f"Source reference: {source_reference}\n"
        f"Expires on: {expires_on}\n"
    )
    run_command(
        [
            "op",
            "item",
            "create",
            "--category",
            "API Credential",
            "--title",
            title,
            "--vault",
            vault,
            "credential=-",
            f"notesPlain={notes}",
        ],
        input_text=token_value,
    )


def prompt_required(label: str) -> str:
    value = input(label).strip()
    if not value:
        raise CfClonerError("A required value was empty.")
    return value


def clone_interactive(expiry_days: int) -> None:
    ensure_dependencies()
    ensure_1password_signed_in()
    print("☁️  cf-cloner")
    print("Select the source Cloudflare token from 1Password.")
    item_id, source_title = select_1password_item()
    source_reference = get_credential_reference(item_id)
    print(f"Selected source item: {source_title}")  # lgtm[py/clear-text-logging-sensitive-data]
    new_name = prompt_required("New Cloudflare token name: ")
    target_vault = prompt_required("Target 1Password vault: ")
    print("Reading source token from 1Password...")
    source_token = read_secret(source_reference)
    print("Verifying source token with Cloudflare...")
    source_token_id = verify_source_token(source_token)
    print("Fetching source token policies...")
    policies = fetch_source_policies(source_token, source_token_id)
    print(f"Creating cloned Cloudflare token with {len(policies)} policy block(s)...")
    new_token_value, expires_on = create_cloned_token(
        source_token=source_token,
        new_name=new_name,
        policies=policies,
        expiry_days=expiry_days,
    )
    print("Saving new token to 1Password...")
    save_token_to_1password(
        token_value=new_token_value,
        title=new_name,
        vault=target_vault,
        source_reference=source_reference,
        expires_on=expires_on,
    )
    print(f"✅ Success. Token '{new_name}' was created and saved to 1Password.")
    print(f"Expires on: {expires_on}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cf-clone",
        description="Clone Cloudflare API token scopes and save the new token to 1Password.",
    )
    parser.add_argument(
        "--expiry-days",
        type=int,
        default=DEFAULT_EXPIRY_DAYS,
        help="Number of days until the cloned token expires. Default: 365.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.expiry_days <= 0:
        print("❌ --expiry-days must be greater than 0.", file=sys.stderr)
        sys.exit(2)
    try:
        clone_interactive(expiry_days=args.expiry_days)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)
    except CfClonerError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

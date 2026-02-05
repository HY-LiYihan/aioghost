"""Interactive setup script to generate .env file for aioghost."""

from __future__ import annotations

import os
from pathlib import Path


def validate_api_key(api_key: str) -> bool:
    """Validate that the API key has the correct format (id:secret)."""
    if ":" not in api_key:
        return False
    parts = api_key.split(":")
    if len(parts) != 2:
        return False
    key_id, secret = parts
    # Key ID should be alphanumeric
    if not key_id.replace("_", "").isalnum():
        return False
    # Secret should be a hex string
    try:
        bytes.fromhex(secret)
        return True
    except ValueError:
        return False


def main() -> None:
    """Run interactive setup."""
    print("=" * 50)
    print("aioghost Setup Wizard")
    print("=" * 50)
    print()

    # Get Ghost API URL
    print("Step 1: Ghost Site URL")
    print("----------------------")
    print("Your Ghost site URL (e.g., https://your-site.ghost.io)")
    print("Must use HTTPS")
    print()

    while True:
        api_url = input("Ghost API URL: ").strip()
        if not api_url:
            print("✗ URL cannot be empty")
            continue
        if not api_url.startswith("https://"):
            print("✗ URL must use HTTPS")
            print("  Example: https://your-site.ghost.io")
            continue
        # Remove trailing slash
        api_url = api_url.rstrip("/")
        break

    print()

    # Get Admin API Key
    print("Step 2: Admin API Key")
    print("---------------------")
    print("Get your Admin API Key from:")
    print("  Ghost Admin → Settings → Integrations → Add custom integration")
    print()
    print("The key format should be: id:secret")
    print("  Example: 5f8a2b3c4d5e6f7g8h9i0j1k2:abc123def456...")
    print()

    while True:
        admin_api_key = input("Admin API Key: ").strip()
        if not admin_api_key:
            print("✗ API Key cannot be empty")
            continue

        if validate_api_key(admin_api_key):
            break
        else:
            print("✗ Invalid API Key format")
            print("  Expected format: id:secret (hex string for secret)")
            print("  Get it from: Ghost Admin → Settings → Integrations")

    print()

    # Show summary
    print("=" * 50)
    print("Configuration Summary")
    print("=" * 50)
    print(f"API URL:     {api_url}")
    print(f"API Key:     {admin_api_key[:20]}...{admin_api_key[-10:]}")
    print()

    confirm = input("Save this configuration? (y/n): ").strip().lower()
    if confirm != "y":
        print("Setup cancelled.")
        return

    # Write .env file
    env_path = Path(".env")
    content = f"""# Ghost Admin API Configuration
GHOST_API_URL={api_url}
GHOST_ADMIN_API_KEY={admin_api_key}
"""

    env_path.write_text(content, encoding="utf-8")
    print()
    print("✓ Configuration saved to .env")
    print()
    print("Next steps:")
    print("  1. Test your connection:")
    print("     python -m scripts.test_connection")
    print()
    print("  2. Create a test post:")
    print("     python -m scripts.test_post")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")

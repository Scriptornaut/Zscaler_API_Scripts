#!/usr/bin/env python

from dotenv import load_dotenv
import os
import sys
from zscaler.oneapi_client import LegacyZIAClient

# Load environment variables from .env file
load_dotenv()

# Configuration for Legacy ZIA Client
config = {
    "username": os.getenv("ZIA_USERNAME"),      # ZIA admin username
    "password": os.getenv("ZIA_PASSWORD"),      # ZIA admin password
    "api_key": os.getenv("ZIA_API_KEY"),        # ZIA API key
    "cloud": os.getenv("ZIA_CLOUD"),            # ZIA cloud environment
    "logging": {
        "enabled": bool(os.getenv("ZIA_LOG_ENABLED", "False").lower() == "true"),
        "verbose": bool(os.getenv("ZIA_LOG_VERBOSE", "False").lower() == "true"),
    },
}

# Check for missing environment variables
required_keys = ["username", "password", "api_key", "cloud"]
missing_vars = [key for key in required_keys if not config.get(key)]
if missing_vars:
    print(f"[ERROR] Missing required environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file and run the script again.")
    exit(1)

def fetch_custom_categories(client):
    """
    Fetches all custom URL categories defined in ZIA.

    Args:
        client (LegacyZIAClient): Authenticated ZIA SDK client.

    Returns:
        list: Custom URL categories with their IDs and names.
    """
    try:
        print("[INFO] Fetching URL categories...")
        url_categories, _, error = client.url_categories.list_categories()
        if error:
            print(f"[ERROR] Failed to fetch URL categories: {error}")
            exit(1)

        custom_categories = [
            {"id": category.id, "name": category.configured_name}
            for category in url_categories if category.id.startswith("CUSTOM_")
        ]
        print(f"[INFO] Found {len(custom_categories)} custom categories.")
        return custom_categories
    except Exception as e:
        print(f"[ERROR] Failed to fetch custom categories: {e}")
        exit(1)

def fetch_url_filtering_policies(client):
    """
    Fetches all URL filtering policies using client.url_filtering.list_rules()

    Args:
        client (LegacyZIAClient): Authenticated ZIA SDK client.

    Returns:
        list: List of policies with URL categories used.
    """
    try:
        print("[INFO] Fetching URL filtering policies...")
        filtering_policies, _, error = client.url_filtering.list_rules()
        if error:
            print(f"[ERROR] Failed to fetch URL filtering policies: {error}")
            exit(1)

        print(f"[INFO] Found {len(filtering_policies)} filtering policies.")
        return filtering_policies
    except Exception as e:
        print(f"[ERROR] Failed to fetch filtering policies: {e}")
        exit(1)

def map_categories_to_policies(custom_categories, filtering_policies):
    """
    Maps custom categories to the policies that use them.

    Args:
        custom_categories (list): Custom categories with their IDs and names.
        filtering_policies (list): List of URL filtering policies.

    Returns:
        list: Custom categories with detailed mapping to the policies they’re used in.
    """
    mapped_categories = []
    for category in custom_categories:
        category_id = category["id"]
        category_name = category["name"]

        # Find policies that reference this category ID
        linked_policies = []
        for policy in filtering_policies:
            policy_name = getattr(policy, "name", "Unnamed Policy")
            action = getattr(policy, "action", "No Action Defined")
            category_ids = getattr(policy, "url_categories", [])

            # Check if this category ID is referenced in the policy
            if category_id in category_ids:
                linked_policies.append({
                    "policy_name": policy_name,
                    "action": action
                })

        mapped_categories.append({
            "id": category_id,
            "name": category_name,
            "linked_policies": linked_policies
        })

    return mapped_categories

def main():
    try:
        # Authenticate using Legacy ZIA Client
        with LegacyZIAClient(config) as parent_client:
            print("[INFO] Authenticating to ZIA using Python SDK...")
            print("[INFO] Authentication successful!")

            # Assign client to `client.zia_legacy_client`
            client = parent_client.zia_legacy_client

            # Step 1: Fetch custom URL categories
            custom_categories = fetch_custom_categories(client)

            # Step 2: Fetch URL filtering policies
            filtering_policies = fetch_url_filtering_policies(client)

            # Step 3: Map categories to policies
            mapped_categories = map_categories_to_policies(custom_categories, filtering_policies)

            # Step 4: Display results
            print("\nCustom Categories Usage Analysis:\n", "-" * 50)
            for category in mapped_categories:
                print(f"- Category Name: {category['name']} | ID: {category['id']}")
                if category["linked_policies"]:
                    print("  Linked Policies:")
                    for policy in category["linked_policies"]:
                        print(f"    -> Policy Name: {policy['policy_name']} | Action: {policy['action']}")
                else:
                    print("  [INFO] This category is NOT used in any policies.")
            print("-" * 50)

    except Exception as e:
        print(f"[ERROR] An exception occurred during execution: {e}")
        exit(1)

if __name__ == "__main__":
    main()

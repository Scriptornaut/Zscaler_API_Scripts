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

def fetch_url_filtering_policies(client):
    """
    Fetches all URL filtering policies using client.url_filtering.list_rules()

    Args:
        client (LegacyZIAClient): Authenticated ZIA SDK client.

    Returns:
        list: List of URL filtering rules.
    """
    try:
        print("[INFO] Fetching URL filtering policies...")
        filtering_policies, _, error = client.url_filtering.list_rules()
        if error:
            print(f"[ERROR] Failed to fetch URL filtering policies: {error}")
            exit(1)

        print(f"[INFO] Found {len(filtering_policies)} URL filtering policies.")
        return filtering_policies # gets used in a later function
    except Exception as e:
        print(f"[ERROR] Failed to fetch URL filtering policies: {e}")
        exit(1)

def fetch_url_categories(client):
    """
    Fetches all URL categories using client.url_categories.list_categories().

    Args:
        client (LegacyZIAClient): Authenticated ZIA SDK client.

    Returns:
        dict: Dictionary mapping category IDs to names.
    """
    try:
        print("[INFO] Fetching URL categories...")
        url_categories, _, error = client.url_categories.list_categories()
        if error:
            print(f"[ERROR] Failed to fetch URL categories: {error}")
            exit(1)

        category_map = {category.id: category.configured_name for category in url_categories}
        print(f"[INFO] Found {len(category_map)} URL categories.")
        return category_map # gets used in next function
    except Exception as e:
        print(f"[ERROR] Failed to fetch URL categories: {e}")
        exit(1)

def identify_policies_using_custom_categories(filtering_policies, category_map):
    """
    Identifies policies that reference custom categories and maps IDs to names.

    Args:
        filtering_policies (list): List of URL filtering policies.
        category_map (dict): Dictionary mapping category IDs to names.

    Returns:
        list: Policies referencing custom categories, including ID-to-name mapping.
    """
    matching_policies = []
    for policy in filtering_policies:
        # Access attributes directly instead of using `.get()`
        policy_name = getattr(policy, "name", "Unnamed Policy")
        action = getattr(policy, "action", "No Action Defined")

        # Extract referenced categories from the 'url_categories' attribute
        category_ids = getattr(policy, "url_categories", [])

        # Check if category IDs match "CUSTOM_" and map to names
        custom_categories_in_policy = [
            {"id": cat_id, "name": category_map.get(cat_id, "Unknown")}
            for cat_id in category_ids if cat_id.startswith("CUSTOM_") #This came from POSTMAN Analysis work
        ]

        if custom_categories_in_policy:  # If custom categories are found in this policy
            matching_policies.append({
                "name": policy_name,
                "action": action,
                "custom_categories": custom_categories_in_policy
            })

    print(f"[INFO] Found {len(matching_policies)} policies referencing custom categories.")
    return matching_policies

def main():
    try:
        # Step 1: Authenticate using Legacy ZIA Client context manager
        with LegacyZIAClient(config) as parent_client:
            print("[INFO] Authenticating to ZIA using Python SDK...")
            print("[INFO] Authentication successful!")

            # Assign client to `client.zia_legacy_client`
            client = parent_client.zia_legacy_client

            # Fetch URL filtering policies and categories
            filtering_policies = fetch_url_filtering_policies(client)
            category_map = fetch_url_categories(client)

            # Identify policies referencing custom categories
            matched_policies = identify_policies_using_custom_categories(filtering_policies, category_map)

            # Display matched policies
            print("\nPolicies Referencing CUSTOM_ Categories:\n", "-" * 50)
            for policy in matched_policies:
                print(f"- Name: {policy['name']} | Action: {policy['action']}")
                for category in policy['custom_categories']:
                    print(f"    -> Category ID: {category['id']} | Name: {category['name']}")
            print("-" * 50)

    except Exception as e:
        print(f"[ERROR] An exception occurred during execution: {e}")
        exit(1)

if __name__ == "__main__":
    main()

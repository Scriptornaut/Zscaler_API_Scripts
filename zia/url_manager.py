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
        list: List of custom categories with their names and IDs.
    """
    try:
        print("[INFO] Fetching custom URL categories...")
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


def analyze_category_usage(custom_categories, filtering_policies):
    """
    Maps custom categories to the policies that use them and identifies unused categories.

    Args:
        custom_categories (list): List of custom categories (name and ID).
        filtering_policies (list): List of filtering policies (with URL categories used).

    Returns:
        dict: Contains mapped custom categories to referenced policies, along with unused categories.
    """
    used_category_ids = set()

    # Map policies to categories
    for policy in filtering_policies:
        category_ids = getattr(policy, "url_categories", [])
        for category_id in category_ids:
            if category_id.startswith("CUSTOM_"):
                used_category_ids.add(category_id)

    # Separate categories into used and unused
    used_categories = [
        {"id": cat["id"], "name": cat["name"], "linked_policies": []}
        for cat in custom_categories if cat["id"] in used_category_ids
    ]

    unused_categories = [
        {"id": cat["id"], "name": cat["name"]}
        for cat in custom_categories if cat["id"] not in used_category_ids
    ]

    # Map policies to their referenced categories
    for cat in used_categories:
        for policy in filtering_policies:
            category_ids = getattr(policy, "url_categories", [])
            if cat["id"] in category_ids:
                linked_policies = getattr(policy, "name", "Unnamed Policy")
                action = getattr(policy, "action", "No Action Defined")
                cat["linked_policies"].append({"policy_name": linked_policies, "action": action})

    return {"used_categories": used_categories, "unused_categories": unused_categories}


def bulk_update_urls(client, category_id, new_urls_file):
    """
    Updates a specific category’s URLs by merging the existing URLs and the new ones from a file.

    Args:
        client (LegacyZIAClient): Authenticated ZIA SDK client.
        category_id (str): ID of the category to update.
        new_urls_file (str): File containing the new URLs.

    Returns:
        None
    """
    try:
        # Fetch the category details
        category, _, error = client.url_categories.get_category(category_id)
        if error:
            print(f"[ERROR] Failed to fetch category '{category_id}': {error}")
            exit(1)

        existing_urls = set(category.urls)
        print(f"[INFO] Found {len(existing_urls)} existing URLs in '{category.configured_name}'.")

        # Read new URLs from file
        with open(new_urls_file, "r") as f:
            new_urls = {line.strip() for line in f if line.strip()}
        print(f"[INFO] Found {len(new_urls)} new URLs in '{new_urls_file}'.")

        # Merge URLs and update the category
        combined_urls = list(existing_urls | new_urls)
        updated_category, _, error = client.url_categories.update_url_category(
            category_id=category.id,
            configured_name=category.configured_name,
            super_category=category.super_category,
            urls=combined_urls
        )
        if error:
            print(f"[ERROR] Failed to update category '{category_id}': {error}")
            exit(1)
        activation_response, _, activation_error = client.activate.activate()
        if activation_error:
            print(f"[ERROR] Failed to activate changes: {activation_error}")
            exit(1)
        #    print(f"[INFO] Activation successful!\n{activation_response}")
        print(f"[INFO] Successfully updated '{updated_category.configured_name}' with {len(updated_category.urls)} total URLs.")
    except FileNotFoundError:
        print(f"[ERROR] The file '{new_urls_file}' was not found.", file=sys.stderr)
        exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to update URLs in category: {e}")
        exit(1)


def main():
    """
    Main driver function to work with ZIA URL-related endpoints.
    Provides a workflow for fetching categories, analyzing their usage, and optionally updating them.
    """
    try:
        with LegacyZIAClient(config) as parent_client:
            print("[INFO] Authenticating to ZIA using Python SDK...")
            print("[INFO] Authentication successful!")

            # Assign client to `client.zia_legacy_client`
            client = parent_client.zia_legacy_client

            # Step 1: Fetch custom URL categories
            custom_categories = fetch_custom_categories(client)

            # Step 2: Fetch URL filtering policies
            filtering_policies = fetch_url_filtering_policies(client)

            # Step 3: Analyze category usage
            analysis = analyze_category_usage(custom_categories, filtering_policies)

            # Display used categories with their policies
            print("\n[INFO] Custom Categories Used in Policies:\n", "-" * 50)
            for category in analysis["used_categories"]:
                print(f"- Category Name: {category['name']} | ID: {category['id']}")
                if category["linked_policies"]:
                    print("  Linked Policies:")
                    for policy in category["linked_policies"]:
                        print(f"    -> Policy Name: {policy['policy_name']} | Action: {policy['action']}")
                else:
                    print("  [INFO] This category is referenced but has no linked policies.")
            print("-" * 50)

            # Display unused categories
            print("\n[INFO] Custom Categories NOT Used in Policies:\n", "-" * 50)
            for category in analysis["unused_categories"]:
                print(f"- Category Name: {category['name']} | ID: {category['id']}")
            print("-" * 50)

            # Optional Step: Bulk upload URLs to a specific category
            update_choice = input("\nDo you want to update URLs in a category? (yes/no): ").strip().lower()
            if update_choice == "yes":
                category_id = input("Enter the Category ID to update (e.g., CUSTOM_01): ").strip()
                new_urls_file = input("Enter the file path for new URLs (e.g., urls.txt): ").strip()
                bulk_update_urls(client, category_id, new_urls_file)

    except Exception as e:
        print(f"[ERROR] An exception occurred during execution: {e}")
        exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python

from dotenv import load_dotenv
import os
from zscaler.oneapi_client import LegacyZIAClient

# Load environment variables from .env file
load_dotenv()

# Read configuration details from environment variables
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

# Validate environment variables
required_keys = ["username", "password", "api_key", "cloud"]
missing_vars = [key for key in required_keys if not config.get(key)]
if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file and run the script again.")
    exit(1)

# Function to fetch custom categories
def fetch_custom_url_categories(client):
    """
    Fetches all URL categories and filters for custom categories.

    Args:
        client (LegacyZIAClient): Authenticated ZIA client.

    Returns:
        list: List of custom categories with their details.
    """
    url_categories, _, error = client.zia_legacy_client.url_categories.list_categories()
    if error:
        print(f"Error fetching URL categories: {error}")
        exit(1)

    # Loop through categories and filter custom ones using attribute access
    custom_categories = []
    for category in url_categories:
        if category.custom_category:  # Access the 'custom_category' attribute directly
            custom_categories.append(category)

    return custom_categories

# Function to summarize categories
def summarize_custom_categories(custom_categories):
    """
    Summarizes the custom categories including the number of URLs in each.

    Args:
        custom_categories (list): List of custom URL categories.

    Returns:
        dict: Summary of total categories and total URLs across them.
    """
    total_urls = 0
    print(f"Total Custom Categories: {len(custom_categories)}\n")
    for category in custom_categories:
        name = getattr(category, "configured_name", "Unnamed Category")  # Use attribute access
        num_urls = getattr(category, "custom_urls_count", 0)  # Use attribute access
        total_urls += num_urls
        print(f"- {name}: {num_urls} URL(s)")
    print("-" * 50)
    return {"total_categories": len(custom_categories), "total_urls": total_urls}

# Main workflow
def main():
    try:
        # Step 1: Authenticate using the context manager
        with LegacyZIAClient(config) as client:
            print("Authenticating with the ZIA Python SDK API...")
            print("Authentication successful!")

            # Step 2: Fetch custom URL categories
            custom_categories = fetch_custom_url_categories(client)

            # Step 3: Summarize data
            summary = summarize_custom_categories(custom_categories)

            # Step 4: Display summary
            print(f"Summary:")
            print(f"Total Custom Categories: {summary['total_categories']}")
            print(f"Total URLs across all categories: {summary['total_urls']}")

    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()

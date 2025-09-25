#!/usr/bin/env python

from dotenv import load_dotenv
import os
import sys
import csv
from zscaler.oneapi_client import LegacyZIAClient

def main():
    """
    Main function to update a ZIA custom URL category with URLs and Ticket ID extracted from the first row of the CSV file.
    """
    # Load environment variables
    load_dotenv()

    # Environment configuration
    config = {
        "username": os.getenv("ZIA_USERNAME"),
        "password": os.getenv("ZIA_PASSWORD"),
        "api_key": os.getenv("ZIA_API_KEY"),
        "cloud": os.getenv("ZIA_CLOUD"),
    }
    
    if not all(config.values()):
        print("Error: Missing one or more required environment variables (ZIA_USERNAME, ZIA_PASSWORD, ZIA_API_KEY, ZIA_CLOUD).", file=sys.stderr)
        sys.exit(1)

    # Define category ID and CSV file paths
    category_id = os.getenv("ZIA_DEMO_CATEGORY", "CUSTOM_01")  # Target custom category for updates
    urls_file = "source_urls.csv"  # Input CSV containing URLs and Ticket ID
    ticket_id_field = "TicketID"  # Field name for Ticket ID in the CSV file

    try:
        # Step 1: Authenticate with ZIA SDK
        with LegacyZIAClient(config) as client:
            print("[INFO] Successfully authenticated with ZIA.")

            # --- Step 2: Fetch category details ---
            print(f"[INFO] Fetching details for category ID: {category_id}...")
            category, _, err = client.zia.url_categories.get_category(category_id)
            if err:
                print(f"[ERROR] Failed to fetch category '{category_id}': {err}", file=sys.stderr)
                sys.exit(1)

            # Get existing URLs
            existing_urls = set(category.urls)
            print(f"[INFO] Found {len(existing_urls)} existing URLs in category '{category.configured_name}'.")

            # --- Step 3: Read URLs and Ticket ID from the CSV file ---
            print(f"[INFO] Reading URLs and ticket ID from file: '{urls_file}'...")
            try:
                with open(urls_file, "r") as csvfile:
                    reader = csv.DictReader(csvfile)

                    # Extract Ticket ID from the first row
                    first_row = next(reader, None)
                    if first_row and ticket_id_field in first_row:
                        ticket_id = first_row[ticket_id_field].strip()
                    else:
                        ticket_id = "UNKNOWN_TICKET_ID"

                    # Extract URLs from all rows in the CSV file
                    urls_to_add = {row["URL"].strip() for row in reader if row.get("URL", "").strip()}
            except Exception as e:
                print(f"[ERROR] Failed to process CSV file '{urls_file}': {e}", file=sys.stderr)
                sys.exit(1)

            print(f"[INFO] Found {len(urls_to_add)} URLs in the CSV file.")
            print(f"[INFO] Extracted Ticket ID: {ticket_id}")

            # --- Step 4: Combine existing and new URLs ---
            print("[INFO] Combining new URLs with existing ones...")
            new_urls_to_add = urls_to_add - existing_urls  # Identify truly new URLs
            if not new_urls_to_add:
                print("[INFO] No new URLs to add. All URLs already exist in the category.")
                sys.exit(0)

            print(f"[INFO] Adding {len(new_urls_to_add)} new URLs to the category.")
            combined_urls = list(existing_urls | urls_to_add)  # Merge URLs

            # --- Step 5: Update URL category ---
            print("[INFO] Updating category with new URLs and updated description...")
            updated_description = f"{category.description} | Updated with Ticket ID: {ticket_id}"

            updated_category, _, err = client.zia.url_categories.update_url_category(
                category_id=category_id,
                configured_name=category.configured_name,  # Retain category name
                super_category=category.super_category,   # Retain super category
                description=updated_description,          # Include ticket ID in description
                urls=combined_urls                        # Send updated list of URLs
            )
            if err:
                print(f"[ERROR] Failed to update category '{category_id}': {err}", file=sys.stderr)
                sys.exit(1)

            print(f"[INFO] Successfully updated category '{updated_category.configured_name}'.")
            print(f"[INFO] Total URLs now in category: {len(updated_category.urls)}")

            # --- Step 6: Activate policy changes ---
            print("[INFO] Activating policy changes...")
            activation_response, _, activation_error = client.zia.activate.activate()
            if activation_error:
                print(f"[ERROR] Failed to activate changes: {activation_error}", file=sys.stderr)
                sys.exit(1)
            print("[INFO] Activation successful!")
            print(f"[INFO] Activation Response: {activation_response}")

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

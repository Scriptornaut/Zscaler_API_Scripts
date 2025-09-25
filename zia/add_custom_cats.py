import os
import sys
from dotenv import load_dotenv
from zscaler.oneapi_client import LegacyZIAClient

def main():
    """
    Main function to bulk-upload URLs to a ZIA custom category.
    """
    load_dotenv()

    config = {
        "username": os.getenv("ZIA_USERNAME"),
        "password": os.getenv("ZIA_PASSWORD"),
        "api_key": os.getenv("ZIA_API_KEY"),
        "cloud": os.getenv("ZIA_CLOUD"),
    }
    
    if not all(config.values()):
        print("Error: Missing one or more required environment variables (ZIA_USERNAME, ZIA_PASSWORD, ZIA_API_KEY, ZIA_CLOUD).", file=sys.stderr)
        sys.exit(1)

    # This line is important. There is no where in the web UI to see the category_id value. From my research
    # it only returns when pulling custom categories. You should be sure to document which category maps to which list.

    
    category_id = os.getenv("ZIA_DEMO_CATEGORY", "CUSTOM_01")
    urls_file = "sample_urls.txt"
    # I want to build a function that pulls the category ID from the tenant for all user defined categories and presents a table to the user.
    # The table should show a cat ID and the name of the URL list for example 1. [CUSTOM_02 | Malware_C2_URLs]. That table is then used as a
    # selection menu for the user which determines which list to update. 



    try:
        with LegacyZIAClient(config) as client:
            print("Successfully authenticated with ZIA.")

            # --- 1. Fetch the target category ---
            print(f"\nFetching details for category ID: {category_id}...")
            category, _, err = client.zia.url_categories.get_category(category_id)
            if err:
                print(f"Error: Failed to get category '{category_id}': {err}", file=sys.stderr)
                sys.exit(1)

            existing_urls = set(category.urls)
            print(f"Found {len(existing_urls)} URLs currently in '{category.configured_name}'.")

            # --- 2. Read new URLs from file ---
            print(f"Reading URLs to add from '{urls_file}'...")
            try:
                with open(urls_file, "r") as f:
                    urls_to_add = {line.strip() for line in f if line.strip()}
            except FileNotFoundError:
                print(f"Error: The file '{urls_file}' was not found.", file=sys.stderr)
                sys.exit(1)

            print(f"Found {len(urls_to_add)} unique URLs in the file.")
            
            # --- 3. Combine and Update URL List ---
            new_urls_to_add = urls_to_add - existing_urls
            if not new_urls_to_add:
                print("\nNo new URLs to add. All URLs from the file already exist in the category.")
                sys.exit(0)

            print(f"Adding {len(new_urls_to_add)} new, unique URLs to the category.")
            combined_urls = list(existing_urls.union(new_urls_to_add))

            # ======================================================================
            # THE FIX IS HERE:
            # We must pass back the mandatory fields from the original object.
            # ======================================================================
            updated_category, _, err = client.zia.url_categories.update_url_category(
                category_id=category_id,
                configured_name=category.configured_name, # Pass back the existing name
                super_category=category.super_category,   # Pass back the existing super_category
                urls=combined_urls                        # Send the new, combined list of URLs
            )
            # ======================================================================

            if err:
                print(f"Error: Failed to update category with new URLs: {err}", file=sys.stderr)
                sys.exit(1)
            print("[INFO] Activating policy changes...")
            activation_response, _, activation_error = client.zia.activate.activate()
            if activation_error:
                print(f"[ERROR] Failed to activate changes: {activation_error}")
                exit(1)
            print(f"[INFO] Activation successful!\n{activation_response}")
            
            print(f"\nSuccessfully updated category '{updated_category.configured_name}'.")
            print(f"Total URLs now in category: {len(updated_category.urls)}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

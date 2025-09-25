#!/usr/bin/env python3

import os
import sys
import code
from dotenv import load_dotenv
from zscaler.oneapi_client import LegacyZPAClient

def initialize_zpa_client(config):
    """
    Initializes the Legacy ZPA Client and returns the client.zpa object for interaction.
    """
    try:
        print("[INFO] Initializing Legacy ZPA Client...")
        # The parent_client manages the session lifecycle.
        parent_client = LegacyZPAClient(config)
        
        # Return the 'zpa' object, which contains the methods for API interaction
        # as seen in your example (client.zpa.segment_groups.add_group).
        # Authentication will be handled automatically on the first API call.
        print("[INFO] ZPA Client initialized successfully.")
        return parent_client.zpa
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize Legacy ZPA Client: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """
    Main function for loading configuration, initializing the client, and launching the interactive shell.
    """
    print("--- ZPA SDK Interactive Shell ---")
    load_dotenv()

    # Load environment variables into a configuration dictionary
    config = {
        "clientId": os.getenv("ZPA_CLIENT_ID"),
        "clientSecret": os.getenv("ZPA_CLIENT_SECRET"),
        "customerId": os.getenv("ZPA_CUSTOMER_ID"),
        "cloud": os.getenv("ZPA_CLOUD"),
        "microtenantId": os.getenv("ZPA_MICROTENANT_ID"), # Will be None if not set, which is fine
        "logging": {
            "enabled": bool(os.getenv("ZPA_LOG_ENABLED", "False").lower() == "true"),
            "verbose": bool(os.getenv("ZPA_LOG_VERBOSE", "False").lower() == "true"),
        },
    }

    # Check for missing required parameters
    required_keys = ["clientId", "clientSecret", "customerId", "cloud"]
    missing_vars = [key for key in required_keys if not config[key]]
    if missing_vars:
        print(f"[ERROR] Missing required ZPA environment variables: {', '.join(missing_vars)}")
        print("[INFO] Please ensure ZPA_CLIENT_ID, ZPA_CLIENT_SECRET, ZPA_CUSTOMER_ID, and ZPA_CLOUD are in your .env file.")
        sys.exit(1)

    print(f"[INFO] Using ZPA environment: {config['cloud']}")

    # Initialize the ZPA SDK client
    client = initialize_zpa_client(config)

    # Launch the interactive Python shell
    print("\n[INFO] Python shell initialized. Interact with the SDK via the 'client' object.")
    print("[TIP] Example commands:")
    print("  - List App Segments: segments = client.application_segment.list_segments()")
    print("  - List Server Groups: groups = client.server_groups.list_groups()")
    
    
    # Pass the client object into the local scope of the interactive shell
    code.interact(local={'client': client})

if __name__ == "__main__":
    main()

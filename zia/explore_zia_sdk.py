#!/usr/bin/env python

from dotenv import load_dotenv
import os
from zscaler.oneapi_client import LegacyZIAClient

# Load .env file explicitly
load_dotenv(dotenv_path="./.env")

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

# Check for missing required environment variables
required_keys = ["username", "password", "api_key", "cloud"]
missing_vars = [key for key in required_keys if not config.get(key)]
if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file and run the script again.")
    exit(1)

# Initialize the Legacy ZIA Client
try:
    with LegacyZIAClient(config) as client:
        print("Client successfully initialized!")
        print("You are now entering the Python CLI to interact with the SDK.")

        # Drop into the interactive Python REPL
        import code
        code.interact(local=locals())
except Exception as e:
    print(f"Error initializing LegacyZIAClient: {e}")

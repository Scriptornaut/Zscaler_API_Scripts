import os
import logging
import requests
from dotenv import load_dotenv

# --- Configuration ---
# Configure basic logging to see the script's actions
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("ZCC_TEST_SCRIPT")

# --- Core API Functions ---

def get_zcc_token(base_url, client_id, client_secret):
    """
    Authenticates to the ZCC API and returns a JWT token.
    Uses the same logic as your main script.
    """
    auth_url = f"{base_url}/papi/auth/v1/login"
    payload = {"apiKey": client_id, "secretKey": client_secret}
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    log.info(f"Requesting JWT token from: {auth_url}")
    try:
        response = requests.post(auth_url, headers=headers, json=payload)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        jwt_token = response.json().get("jwtToken")
        if not jwt_token:
            raise ValueError("Authentication successful, but no jwtToken in response.")
        log.info("✅ JWT Token retrieved successfully.")
        return jwt_token
    except requests.exceptions.RequestException as e:
        log.error(f"❌ API Request failed during authentication: {e}")
        return None
    except ValueError as e:
        log.error(f"❌ Authentication failed: {e}")
        return None

def test_removal_endpoint(base_url, token, endpoint_path, username):
    """
    Sends a POST request to a specified removal endpoint for a given username.
    This function is will print the raw API response.
    """
    removal_url = f"{base_url}{endpoint_path}"
    headers = {"Content-Type": "application/json", "auth-token": token}
    payload = {"userName": username}

    log.info(f"Sending POST to: {removal_url}")
    log.info(f"Payload: {payload}")

    try:
        response = requests.post(removal_url, headers=headers, json=payload)
        
        # We print the results regardless of status code for analysis
        print("-" * 50)
        print(f">>> Status Code: {response.status_code}")
        try:
            # Try to print JSON, but fall back to raw text if it fails
            print(f">>> Response JSON: {response.json()}")
        except requests.exceptions.JSONDecodeError:
            print(f">>> Response Text: {response.text}")
        print("-" * 50)

    except requests.exceptions.RequestException as e:
        log.error(f"❌ An error occurred during the API call: {e}")

# --- Main Interactive Execution Block ---

def main():
    """Main function to run the interactive test."""
    load_dotenv()
    log.info("--- Starting ZCC API Endpoint Tester ---")

    try:
        # Load credentials from .env file
        client_id = os.getenv("ZCC_CLIENT_ID")
        client_secret = os.getenv("ZCC_CLIENT_SECRET")
        override_url = os.getenv("ZCC_OVERRIDE_URL")
        if not all([client_id, client_secret, override_url]):
            raise ValueError("Missing required ZCC environment variables (ZCC_CLIENT_ID, ZCC_CLIENT_SECRET, ZCC_OVERRIDE_URL).")

        # Construct the base URL correctly
        if not override_url.startswith("https://"):
            base_url = f"https://{override_url.strip('/')}"
        else:
            base_url = override_url.strip('/')

        # Authenticate once at the beginning
        token = get_zcc_token(base_url, client_id, client_secret)
        if not token:
            log.error("Could not authenticate. Please check your credentials and API connectivity. Exiting.")
            return

        # Interactive loop for testing
        while True:
            print("\nSelect the endpoint to test:")
            print("  1. Soft Remove (/papi/public/v1/removeDevices)")
            print("  2. Force Remove (/papi/public/v1/forceRemoveDevices)")
            print("  3. Exit")
            
            choice = input("Enter your choice (1, 2, or 3): ").strip()

            if choice == '3':
                log.info("Exiting the script.")
                break
            
            if choice not in ['1', '2']:
                log.warning("Invalid choice. Please try again.")
                continue

            # Set the endpoint path based on user choice
            endpoint_path = "/papi/public/v1/removeDevices" if choice == '1' else "/papi/public/v1/forceRemoveDevices"
            
            # Prompt for the username to test
            username_to_test = input("Enter the username to test against this endpoint: ").strip()
            if not username_to_test:
                log.warning("Username cannot be empty.")
                continue

            # Call the test function
            test_removal_endpoint(base_url, token, endpoint_path, username_to_test)

    except Exception as e:
        log.error(f"❌ An unrecoverable error occurred: {e}", exc_info=False)


if __name__ == "__main__":
    main()

# ZCC Remove Devices by User

This Python script provides an interactive command-line interface to issue "Soft Remove" and "Force Remove" actions via Zscaler Client Connector (ZCC) API. It is designed for administrators to remove devices from ZCC registration by username.

The script authenticates to the API, then allows you enter a username for action. Note that this script will issue a removal for all the requested users' devices including mobile (iOS & Android). 

## Prerequisites

- Python 3.6+
- The `requests` and `python-dotenv` libraries.

## Setup & Configuration

1.  **Install Dependencies:**
    It is recommended to create a `requirements.txt` file with the following content:
    ```text
    requests
    python-dotenv
    ```
    Then, install the required libraries using pip:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Create an Environment File:**
    In the same directory as the script, create a file named `.env`. This file will store your API credentials securely. Add the following content to the file, replacing the placeholder values with your actual credentials:

    ```text
    # Zscaler Client Connector API Credentials
    ZCC_CLIENT_ID="your_client_id_here"
    ZCC_CLIENT_SECRET="your_client_secret_here"

    # ZCC Portal URL (e.g., mobileadmin.zscaler.net, mobileadmin.zscalertwo.net)
    ZCC_OVERRIDE_URL="your.mobileadmin.cloud.name"
    ```

## How to Use

1.  Open a terminal or command prompt in the project directory.
2.  Run the script using the following command:
    ```bash
    python zcc_device_remove_by_user.py
    ```
3.  The script will first attempt to authenticate using the credentials in your `.env` file.
4.  Once successful, an interactive menu will appear, allowing you to choose between **Soft Remove** and **Force Remove**.
5.  After selecting an option, you will be prompted to enter the username you wish to test.
6.  The script will execute the API call and print the **Status Code** and **Response JSON** directly to the console for your analysis.
7.  The menu will reappear, allowing you to test another user or endpoint immediately.

### Example Session

```bash
$ python zcc_device_remove_by_user.py
2025-11-07 15:30:01,123 [INFO] --- Starting ZCC API Endpoint Tester ---
2025-11-07 15:30:01,123 [INFO] Requesting JWT token from: https://mobileadmin.zscalertwo.net/papi/auth/v1/login
2025-11-07 15:30:02,456 [INFO] ✅ JWT Token retrieved successfully.

Select the endpoint to test:
  1. Soft Remove (/papi/public/v1/removeDevices)
  2. Force Remove (/papi/public/v1/forceRemoveDevices)
  3. Exit
Enter your choice (1, 2, or 3): 2

Enter the username to test against this endpoint: test.user@example.com
2025-11-07 15:30:15,789 [INFO] Sending POST to: https://mobileadmin.zscalertwo.net/papi/public/v1/forceRemoveDevices
2025-11-07 15:30:15,789 [INFO] Payload: {'userName': 'test.user@example.com'}
--------------------------------------------------
>>> Status Code: 200
>>> Response JSON: {'devicesRemoved': 3}
--------------------------------------------------

Select the endpoint to test:
  1. Soft Remove (/papi/public/v1/removeDevices)
  2. Force Remove (/papi/public/v1/forceRemoveDevices)
  3. Exit
Enter your choice (1, 2, or 3): 3
2025-11-07 15:30:20,001 [INFO] Exiting the script.
```

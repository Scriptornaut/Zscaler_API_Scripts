ZIA Scripts Directory
Overview
This directory contains a collection of unofficial scripts developed for interacting with the Zscaler Internet Access (ZIA) environment. The scripts leverage the Zscaler Python SDK, publicly available ZIA APIs, and Zscaler documentation. They are intended for development, testing, and automation purposes.

Disclaimer
These scripts are not official Zscaler products. They are provided as-is and built using public documentation, API Developer Guides, and the Zscaler Python SDK. Use them at your own discretion; Zscaler does not provide support for these scripts.

Scripts
1. Interactive ZIA Shell
Initializes an interactive Python CLI session with the ZIA SDK, enabling direct experimentation with SDK functionality.

Usage: Provides access to the SDK methods for exploring ZIA features.
Dependencies: python-dotenv, zscaler-sdk.
2. Custom URL Categories Analysis
Analyzes custom URL categories in the ZIA environment and identifies their usage across URL filtering policies.

Usage: Fetches category data, maps policies to their referenced categories, and highlights unused categories.
Dependencies: python-dotenv, zscaler-sdk.
3. Summarize Custom URL Categories
Summarizes custom categories, counting the number of URLs associated with each and reporting the total number across categories.

Usage: Useful for tracking category usage and maintaining large custom URL lists.
Dependencies: python-dotenv, zscaler-sdk.
4. Bulk-Upload URLs to Custom Categories
Uploads a batch of URLs to a specified ZIA custom category by merging new URLs with existing ones.

Usage: Automates adding large URL lists to a category and activates changes.
Dependencies: python-dotenv, zscaler-sdk.
5. Generate Sample URL List
Generates a list of realistic domain names for testing purposes. Saves output to a text file.

Usage: Ideal for creating test data for uploading to ZIA categories.
Dependencies: None.
6. Identify Policies Using Custom Categories
Cross-references custom categories (CUSTOM_) with URL filtering policies to identify policies using those categories. Provides a detailed mapping.

Usage: Helps to understand how custom categories are used across policies.
Dependencies: python-dotenv, zscaler-sdk.
7. Custom Categories Analysis and Bulk URL Updater
Combines category analysis with optional bulk URL updates. Separates categories into "used" and "unused," and allows interactive updates.

Usage: Provides an end-to-end workflow for category management.
Dependencies: python-dotenv, zscaler-sdk.
8. Bulk URL Update with Ticket ID Integration
Updates a custom category with URLs from a CSV file and integrates the Ticket ID into the category description for traceability.

Usage: Suitable for workflow tracking and batch URL updates.
Dependencies: python-dotenv, zscaler-sdk, csv.
Prerequisites
Python Version: Ensure you are running Python 3.7+.
Required Libraries: Install dependencies via pip:
bash
Copy code
pip install python-dotenv zscaler-sdk
Optional dependency for CSV-related scripts:
bash
Copy code
pip install csv
Configuration: All scripts use environment variables for authentication and configuration. Create a .env file in this directory with the following details:
env
Copy code
ZIA_USERNAME=<your_zscaler_admin_username>
ZIA_PASSWORD=<your_zscaler_admin_password>
ZIA_API_KEY=<your_zscaler_api_key>
ZIA_CLOUD=<your_zscaler_cloud_environment> # Example: 'zscloud.net'
Notes
These scripts are ideal for automating common ZIA management tasks, like URL category updates, reporting, and analysis.
Ensure proper permissions and access credentials when running these scripts.
For official Zscaler documentation and SDK guides, refer to:
Zscaler API Developer Guide
Zscaler Python SDK Docs

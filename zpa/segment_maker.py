import os
import csv
import sys
from collections import defaultdict
from dotenv import load_dotenv
from typing import List, Dict, Optional
from zscaler.oneapi_client import LegacyZPAClient

def str2bool(value: str) -> bool:
    """
    Converts a string value to a boolean.
    - This function checks if the input string represents a truthy value (e.g., "1", "true", "yes", "y").
    - Zscaler uses boolean flags (e.g., enabled/disabled), making this conversion helpful for validating CSV inputs.
    """
    return str(value).lower() in ("1", "true", "yes", "y")

def list_server_groups(client) -> Dict[str, str]:
    """
    Lists all server groups in ZPA and maps their names to IDs.
    - Server groups represent network resources that application segments connect to.
    - The function uses the Zscaler API client to fetch server group details.
      * Returns a dictionary where keys are server group names and values are their IDs for easy lookup.
    """
    groups, _, err = client.server_groups.list_groups()
    if err:
        print(f"[ERROR] Failed to fetch server groups: {err}")
        return {}

    return {group.name: group.id for group in groups}

def list_segment_groups(client) -> Dict[str, str]:
    """
    Lists all segment groups in ZPA and maps their names to IDs.
    - Segment groups are used to organize application segments logically.
    - This function retrieves segment group information using the ZPA API.
      * Returns a dictionary where keys are segment group names and values are their IDs.
    """
    groups, _, err = client.segment_groups.list_groups()
    if err:
        print(f"[ERROR] Failed to fetch segment groups: {err}")
        return {}

    return {group.name: group.id for group in groups}

def parse_ports(port_string: str) -> List[Dict]:
    """
    Converts a comma-separated port string into a list of port range dictionaries.
    - Example: Input `'8000,8001'` → Output `[{'from': '8000', 'to': '8000'}, {'from': '8001', 'to': '8001'}]`
    - This is used to define TCP/UDP port ranges for ZPA application segments.
    """
    ports = (port_string or "").strip().split(",")
    return [{"from": p.strip(), "to": p.strip()} for p in ports if p.strip()]

def parse_csv_row(row: Dict, server_groups: Dict[str, str], segment_groups: Dict[str, str]) -> Optional[Dict]:
    """
    Parses and validates a row from a CSV file to build a payload for ZPA app segment creation.
    - Validates required fields (NAME, SEGMENT_GROUP_ID, etc.) and checks if server group/segment group names exist in ZPA.
    - Returns a dictionary representing the app segment, or None if the row is invalid.
    - Example output: {"name": ..., "server_group_ids": [...], "domain_names": [...], ...}
    """
    name = row.get("NAME", "").strip()
    segment_group_name = row.get("SEGMENT_GROUP_ID", "").strip()
    server_group_names = [name.strip() for name in row.get("SERVER_GROUP_IDS", "").split(",") if name.strip()]
    domain_names = [domain.strip() for domain in row.get("DOMAINS", "").split(",") if domain.strip()]

    errors = []  # Keep track of validation errors
    if not name:
        errors.append("NAME is required.")
    if not segment_group_name or segment_group_name not in segment_groups:
        suggested = list(segment_groups.keys())[0] if segment_groups else "Unknown"
        errors.append(f"SEGMENT_GROUP_ID missing or invalid. Suggested: '{suggested}'")
    if not domain_names:
        errors.append("DOMAINS is required (e.g., IP addresses or FQDNs).")

    # Validate server group names and map them to IDs
    server_group_ids = []
    for sg_name in server_group_names:
        if sg_name not in server_groups:
            suggested = list(server_groups.keys())[0] if server_groups else "Unknown"
            errors.append(f"Server Group '{sg_name}' is invalid. Suggested: '{suggested}'")
        else:
            server_group_ids.append(server_groups[sg_name])
    
    if not server_group_ids:
        errors.append("SERVER_GROUP_IDS are all invalid or missing.")

    if errors:
        # If any validation fails, display errors and skip this row
        print(f"\n[ERROR] Row validation failed for app segment '{name or 'Unnamed'}':")
        for error in errors:
            print(f"  - {error}")
        return None

    # Construct the validated payload
    return {
        "name": name,
        "description": row.get("DESCRIPTION", "").strip(),
        "enabled": str2bool(row.get("ENABLED", "true")),
        "segment_group_id": segment_groups.get(segment_group_name),
        "server_group_ids": server_group_ids,
        "domain_names": domain_names,
        "tcp_port_range": parse_ports(row.get("TCP_PORTS", "")),
        "udp_port_range": parse_ports(row.get("UDP_PORTS", "")),
        "double_encrypt": str2bool(row.get("DOUBLE_ENCRYPT", "false")),
    }

def segment_exists(client, domain: str, ports: List[Dict]) -> bool:
    """
    Checks if an application segment already exists in ZPA based on domain and port configuration.
    - Prevents duplicate application segment creation if an identical configuration already exists.
    - Combines ZPA's list operation and payload comparison for this check.
    """
    segments, _, err = client.application_segment.list_segments()
    if err:
        print(f"[WARNING] Could not check for existing segments: {err}")
        return False  # Default to False if an API error occurs.

    # Compare each existing segment's domains and ports with the provided domain and ports
    for segment in segments:
        if domain in segment.domain_names and segment.tcp_port_range == ports:
            return True
    return False

def create_app_segments(client, rows: List[Dict], force_creation: bool):
    """
    Creates application segments in ZPA based on validated rows.
    - Verifies if the segment already exists before attempting creation (unless `force_creation` is enabled).
    - Uses ZPA API's `add_segment` method for app segment creation.
    """
    created_count = 0  # Count successfully created app segments
    for row in rows:
        domain = row.get("domain_names")[0]  # Use the first domain name in the row
        ports = row.get("tcp_port_range")

        if not force_creation and segment_exists(client, domain, ports):
            print(f"  ~ Skipping existing app segment for domain '{domain}' and ports '{ports}'")
            continue

        created_segment, _, err = client.application_segment.add_segment(**row)
        if err:
            print(f"  ! Failed to create app segment '{row.get('name')}': {err}")
        else:
            created_count += 1
            print(f"  ✓ Created app segment '{row.get('name')}'")
    return created_count

def main():
    """
    Main function to load configuration, validate CSV input, and create ZPA app segments.
    - Handles environment variable loading, CSV file parsing, and ZPA API initialization.
    - Provides error handling for missing configuration or invalid CSV rows.
    """
    print("--- ZPA Bulk App Segment Creation ---")

    load_dotenv()  # Load environment variables from .env file
    client_id = os.getenv("ZPA_CLIENT_ID")
    client_secret = os.getenv("ZPA_CLIENT_SECRET")
    customer_id = os.getenv("ZPA_CUSTOMER_ID")
    cloud = os.getenv("ZPA_CLOUD")

    if not all([client_id, client_secret, customer_id, cloud]):
        print("\n[ERROR] Missing required environment variables.", file=sys.stderr)
        sys.exit(1)

    config = {
        "client_id": client_id,
        "client_secret": client_secret,
        "customer_id": customer_id,
        "cloud": cloud,
    }

    # Initialize ZPA Client
    with LegacyZPAClient(config) as parent_client:
        legacy_client = parent_client.zpa_legacy_client
        server_groups = list_server_groups(legacy_client)
        segment_groups = list_segment_groups(legacy_client)

        if not server_groups:
            print("[ERROR] No server groups found. Unable to proceed.")
            sys.exit(1)
        if not segment_groups:
            print("[ERROR] No segment groups found. Unable to proceed.")
            sys.exit(1)

        print("[INFO] Fetched server and segment group details successfully.")

        # Parse arguments for CSV file input and force flag
        import argparse
        parser = argparse.ArgumentParser(description="Validate and create ZPA app segments via SDK")
        parser.add_argument("--csv", required=True, help="Path to CSV file with app segment details")
        parser.add_argument("--force", action="store_true", help="Force creation even if an app segment with the same domain and ports exists")
        args = parser.parse_args()

        try:
            with open(args.csv, newline="") as f:
                reader = csv.DictReader(f)
                rows = []
                for row in reader:
                    parsed_row = parse_csv_row(row, server_groups, segment_groups)
                    if parsed_row:
                        rows.append(parsed_row)
        except FileNotFoundError:
            print(f"\n[ERROR] CSV file '{args.csv}' not found.", file=sys.stderr)
            sys.exit(1)

        if not rows:
            print("\n[INFO] No valid rows found in the CSV. Exiting.")
            sys.exit(0)
            
        # Calculate the total number of applications (domain/IP + port combinations)
        application_count = 0
        for row in rows:
            num_domains = len(row.get("domain_names", []))
            num_ports = len(row.get("tcp_port_range", [])) + len(row.get("udp_port_range", []))
            if num_domains > 0 and num_ports > 0:
                application_count += num_domains * num_ports

        segment_count = len(rows)  # Valid rows to create app segments

        print(f"\n[INFO] Found {application_count} total applications defined across {segment_count} app segments to be created.")

        # Create app segments directly
        created_count = create_app_segments(legacy_client, rows, args.force)
        print(f"\n[INFO] Successfully created {created_count} app segments.")
        
if __name__ == "__main__":
    main()

import os
import csv
import sys
import argparse
from dotenv import load_dotenv
from typing import List, Dict, Set
from zscaler.oneapi_client import LegacyZPAClient

# --- Helper Functions ---

def get_id_to_name_map(client, resource_type: str) -> Dict[str, str]:
    """Fetches ZPA resources and returns a mapping of their ID to their Name."""
    print(f"[INFO] Fetching all {resource_type.replace('_', ' ')}...")
    try:
        if resource_type == 'server_groups':
            resources, _, err = client.server_groups.list_groups()
        elif resource_type == 'segment_groups':
            resources, _, err = client.segment_groups.list_groups()
        else:
            raise ValueError("Invalid resource_type specified.")
        if err:
            print(f"[ERROR] Failed to fetch {resource_type.replace('_', ' ')}: {err}", file=sys.stderr)
            return {}
        id_map = {res.id: res.name for res in resources}
        print(f"  > Found {len(id_map)} {resource_type.replace('_', ' ')}.")
        return id_map
    except Exception as e:
        print(f"[ERROR] An exception occurred while fetching {resource_type}: {e}", file=sys.stderr)
        return {}

def format_ports_to_string(port_ranges: List[Dict]) -> str:
    """Converts a list of port range dictionaries to a comma-separated string."""
    if not port_ranges:
        return ""
    formatted_ports = []
    for port_range in port_ranges:
        p_from, p_to = port_range.get('from'), port_range.get('to')
        formatted_ports.append(p_from if p_from == p_to else f"{p_from}-{p_to}")
    return ",".join(formatted_ports)

def get_segment_ids_by_type(client, app_type: str) -> Set[str]:
    """
    Uses the app_segment_by_type controller to fetch segment IDs for a specific type.
    
    Args:
        client: The ZPA legacy client instance.
        app_type (str): The type to query (e.g., "BROWSER_ACCESS").

    Returns:
        A set of segment IDs for the given type.
    """
    print(f"[INFO] Fetching IDs for '{app_type}' segments...")
    try:
        # Using the exact method you found!
        segments, _, err = client.app_segment_by_type.get_segments_by_type(application_type=app_type)
        
        if err:
            print(f"[ERROR] Failed to fetch '{app_type}' segments: {err}", file=sys.stderr)
            return set()
            
        segment_ids = {segment.id for segment in segments}
        print(f"  > Found {len(segment_ids)} '{app_type}' segments.")
        return segment_ids
    except Exception as e:
        print(f"[ERROR] An exception occurred while fetching '{app_type}' segments: {e}", file=sys.stderr)
        return set()

# --- Main Logic ---

def main():
    print("--- ZPA Bulk App Segment Export (v3 - Corrected) ---")
    
    parser = argparse.ArgumentParser(description="Export ZPA Application Segments to a CSV file.")
    parser.add_argument("--outfile", default="zpa_app_segments_export.csv", help="Path to the output CSV file.")
    args = parser.parse_args()

    load_dotenv()
    config = {
        "client_id": os.getenv("ZPA_CLIENT_ID"),
        "client_secret": os.getenv("ZPA_CLIENT_SECRET"),
        "customer_id": os.getenv("ZPA_CUSTOMER_ID"),
        "cloud": os.getenv("ZPA_CLOUD")
    }
    if not all(config.values()):
        print("\n[ERROR] Missing required environment variables.", file=sys.stderr)
        sys.exit(1)

    try:
        with LegacyZPAClient(config) as parent_client:
            legacy_client = parent_client.zpa_legacy_client
            print("[INFO] Successfully connected to ZPA tenant.")

            # --- Pre-fetch all required data ---
            server_group_map = get_id_to_name_map(legacy_client, 'server_groups')
            segment_group_map = get_id_to_name_map(legacy_client, 'segment_groups')
            if not server_group_map or not segment_group_map:
                print("[ERROR] Could not fetch Server or Segment Group mappings. Aborting.", file=sys.stderr)
                sys.exit(1)

            # Fetch specialized segment IDs using the correct method
            ba_segment_ids = get_segment_ids_by_type(legacy_client, "BROWSER_ACCESS")
            pra_segment_ids = get_segment_ids_by_type(legacy_client,"SECURE_REMOTE_ACCESS")
            inspection_segment_ids = get_segment_ids_by_type(legacy_client, "INSPECT")

            # Fetch the master list of all application segments
            print("[INFO] Fetching master list of all application segments...")
            all_segments, _, err = legacy_client.application_segment.list_segments()
            if err:
                print(f"[ERROR] Failed to fetch master application segment list: {err}", file=sys.stderr)
                sys.exit(1)
            print(f"  > Found {len(all_segments)} total segments to process.")

            # --- Process and enrich data for CSV ---
            csv_rows = []
            for segment in all_segments:
                server_group_names = [server_group_map.get(sg['id'], f"UNKNOWN_ID_{sg['id']}") for sg in segment.server_groups]
                
                row_data = {
                    "NAME": segment.name,
                    "DESCRIPTION": segment.description,
                    "ENABLED": str(segment.enabled).lower(),
                    "SEGMENT_GROUP_ID": segment_group_map.get(segment.segment_group_id, f"UNKNOWN_ID_{segment.segment_group_id}"),
                    "SERVER_GROUP_IDS": ",".join(server_group_names),
                    "DOMAINS": ",".join(segment.domain_names),
                    "TCP_PORTS": format_ports_to_string(segment.tcp_port_range),
                    "UDP_PORTS": format_ports_to_string(segment.udp_port_range),
                    "DOUBLE_ENCRYPT": str(segment.double_encrypt).lower(),
                    # Check if the segment ID is in our specialized sets
                    "IS_BROWSER_ACCESS": str(segment.id in ba_segment_ids).lower(),
                    "IS_PRA": str(segment.id in pra_segment_ids).lower(),
                    "IS_INSPECTION": str(segment.id in inspection_segment_ids).lower(),
                }
                csv_rows.append(row_data)

            if not csv_rows:
                print("[INFO] No application segments found to export.")
                sys.exit(0)
            
            # --- Write to CSV File ---
            print(f"\n[INFO] Writing {len(csv_rows)} records to '{args.outfile}'...")
            header = [
                "NAME", "DESCRIPTION", "ENABLED", "SEGMENT_GROUP_ID", 
                "SERVER_GROUP_IDS", "DOMAINS", "TCP_PORTS", "UDP_PORTS", 
                "DOUBLE_ENCRYPT", "IS_BROWSER_ACCESS", "IS_PRA", "IS_INSPECTION"
            ]
            
            with open(args.outfile, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=header)
                writer.writeheader()
                writer.writerows(csv_rows)
            print(f"\n[SUCCESS] Export complete. Data saved to '{args.outfile}'.")

    except Exception as e:
        print(f"\n[FATAL] An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

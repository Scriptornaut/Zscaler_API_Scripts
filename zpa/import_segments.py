import os
import csv
import sys
import argparse
from dotenv import load_dotenv
from typing import List, Dict, Optional
from zscaler.oneapi_client import LegacyZPAClient

# --- Helper functions (Unchanged) ---
def str2bool(value: str) -> bool:
    return str(value).lower() in ("1", "true", "yes", "y")

def list_server_groups(client) -> Dict[str, str]:
    groups, _, err = client.server_groups.list_groups()
    if err:
        print(f"[ERROR] Failed to fetch server groups: {err}", file=sys.stderr)
        return {}
    return {group.name: group.id for group in groups}

def list_segment_groups(client) -> Dict[str, str]:
    groups, _, err = client.segment_groups.list_groups()
    if err:
        print(f"[ERROR] Failed to fetch segment groups: {err}", file=sys.stderr)
        return {}
    return {group.name: group.id for group in groups}

def parse_ports(port_string: str) -> List[str]:
    ports = (port_string or "").strip().split(",")
    return [p.strip() for p in ports if p.strip()]

def parse_csv_row(row: Dict) -> Optional[Dict]:
    # This function just prepares the dictionary from the CSV row.
    # Validation of group names will happen later.
    if not all([row.get("NAME"), row.get("DOMAINS"), row.get("SERVER_GROUP_IDS")]):
        print(f"[WARNING] Skipping row with missing required fields (NAME, DOMAINS, SERVER_GROUP_IDS): {row}")
        return None
        
    return {
        "name": row.get("NAME", "").strip(),
        "description": row.get("DESCRIPTION", "").strip(),
        "enabled": str2bool(row.get("ENABLED", "true")),
        "segment_group_name": row.get("SEGMENT_GROUP_ID", "").strip(),
        "server_group_names": [name.strip() for name in row.get("SERVER_GROUP_IDS", "").split(",")],
        "domain_names": [d.strip() for d in row.get("DOMAINS", "").split(",")],
        "tcp_ports": parse_ports(row.get("TCP_PORTS", "")),
        "udp_ports": parse_ports(row.get("UDP_PORTS", "")),
        "double_encrypt": str2bool(row.get("DOUBLE_ENCRYPT", "false")),
        "is_browser_access": str2bool(row.get("IS_BROWSER_ACCESS", "false")),
        "is_pra": str2bool(row.get("IS_PRA", "false")),
        "is_inspection": str2bool(row.get("IS_INSPECTION", "false")),
    }

# --- REMOVED the broken segment_exists function ---

# --- REVISED 'create_and_configure_segments' ---
def create_and_configure_segments(client, rows: List[Dict], server_groups_map, segment_groups_map, force: bool, existing_segment_names: set):
    """
    Creates a parent App Segment, then adds BA/PRA child applications as needed.
    """
    created_count = 0
    configured_apps = 0

    for row in rows:
        name = row.get('name')
        # CORRECTED: Check against the pre-fetched set of names
        if not force and name in existing_segment_names:
            print(f"  ~ Skipping existing app segment: '{name}'")
            continue

        # --- Validation Step ---
        # Check if all required server/segment groups exist before proceeding
        server_group_names = row['server_group_names']
        segment_group_name = row['segment_group_name']
        missing_sgs = [sg for sg in server_group_names if sg not in server_groups_map]
        if missing_sgs:
            print(f"  ! SKIPPING '{name}': The following Server Groups were not found in the tenant: {', '.join(missing_sgs)}")
            continue
        if segment_group_name not in segment_groups_map:
            print(f"  ! SKIPPING '{name}': The Segment Group '{segment_group_name}' was not found in the tenant.")
            continue
        # --- End Validation ---

        # 1. Create the Parent Application Segment
        print(f"  > Creating parent App Segment: '{name}'")
        server_group_ids = [server_groups_map[sg_name] for sg_name in server_group_names]
        segment_group_id = segment_groups_map[segment_group_name]
        
        create_payload = {
            "name": name, "description": row['description'], "enabled": row['enabled'],
            "segment_group_id": segment_group_id, "server_group_ids": server_group_ids,
            "domain_names": row['domain_names'],
            "tcp_port_range": [{"from": p, "to": p} for p in row['tcp_ports']],
            "udp_port_range": [{"from": p, "to": p} for p in row['udp_ports']],
            "double_encrypt": row['double_encrypt'],
            "app_protection_enabled": row['is_inspection']
        }
        
        parent_segment, _, err = client.application_segment.add_segment(**create_payload)
        if err:
            print(f"  ! FAILED to create parent segment '{name}': {err}")
            continue
        created_count += 1
        print(f"  ✓ Created parent segment '{name}' (ID: {parent_segment.id})")

        # 2. Add Browser Access (BA) Child Applications
        if row['is_browser_access']:
            print("    ...Configuring Browser Access applications...")
            for domain in row['domain_names']:
                for port in row['tcp_ports']:
                    protocol = "HTTPS" if port in ["443", "8443"] else "HTTP"
                    ba_name = f"{domain}:{port}"
                    print(f"      - Adding BA app: '{ba_name}'")
                    _, ba_err = client.app_segments_ba.add_segment(segment_id=parent_segment.id, name=ba_name, domain=domain, application_port=port, application_protocol=protocol, enabled=True)
                    if ba_err: print(f"      ! FAILED to add BA app '{ba_name}': {ba_err}")
                    else: configured_apps += 1

        # 3. Add Privileged Remote Access (PRA) Child Applications
        if row['is_pra']:
            print("    ...Configuring Privileged Remote Access applications...")
            for domain in row['domain_names']:
                for port in row['tcp_ports']:
                    protocol = "SSH" if port == "22" else "RDP" if port == "3389" else None
                    if not protocol: continue
                    pra_name = f"{protocol}-{domain}:{port}"
                    print(f"      - Adding PRA app: '{pra_name}'")
                    _, pra_err = client.app_segments_pra.add_segment(segment_id=parent_segment.id, name=pra_name, domain=domain, application_port=port, application_protocol=protocol, enabled=True)
                    if pra_err: print(f"      ! FAILED to add PRA app '{pra_name}': {pra_err}")
                    else: configured_apps += 1

    return created_count, configured_apps

def main():
    print("--- ZPA Bulk App Segment Import (v6 - Corrected) ---")
    load_dotenv()
    config = {"client_id": os.getenv("ZPA_CLIENT_ID"), "client_secret": os.getenv("ZPA_CLIENT_SECRET"), "customer_id": os.getenv("ZPA_CUSTOMER_ID"), "cloud": os.getenv("ZPA_CLOUD")}
    if not all(config.values()):
        sys.exit("\n[ERROR] Missing required environment variables.")

    with LegacyZPAClient(config) as parent_client:
        legacy_client = parent_client.zpa_legacy_client
        server_groups = list_server_groups(legacy_client)
        segment_groups = list_segment_groups(legacy_client)
        if not server_groups or not segment_groups:
            sys.exit("[ERROR] No server or segment groups found.")
        print("[INFO] Fetched server and segment group details successfully.")

        # --- NEW: Pre-fetch existing segment names for efficiency ---
        print("[INFO] Fetching names of all existing application segments...")
        all_existing_segments, _, err = legacy_client.application_segment.list_segments() # Corrected call
        if err:
            print(f"[WARNING] Could not fetch existing segments: {err}. The --force flag will be required to avoid errors.")
            existing_segment_names = set()
        else:
            existing_segment_names = {segment.name for segment in all_existing_segments}
            print(f"  > Found {len(existing_segment_names)} existing segments.")

        parser = argparse.ArgumentParser(description="Create and configure ZPA app segments.")
        parser.add_argument("--csv", required=True, help="Path to CSV file.")
        parser.add_argument("--force", action="store_true", help="Force creation even if segment name exists.")
        args = parser.parse_args()

        try:
            with open(args.csv, newline="", encoding='utf-8') as f:
                reader = csv.DictReader(f)
                parsed_rows = [parsed for row in reader if (parsed := parse_csv_row(row))]
        except FileNotFoundError:
            sys.exit(f"\n[ERROR] CSV file '{args.csv}' not found.")

        if not parsed_rows:
            sys.exit("\n[INFO] No valid rows found in CSV.")
            
        print(f"\n[INFO] Found {len(parsed_rows)} valid app segments to process.")

        created, configured = create_and_configure_segments(legacy_client, parsed_rows, server_groups, segment_groups, args.force, existing_segment_names)
        print(f"\n[INFO] Process complete. Parent Segments Created: {created}, BA/PRA Apps Configured: {configured}.")

if __name__ == "__main__":
    main()

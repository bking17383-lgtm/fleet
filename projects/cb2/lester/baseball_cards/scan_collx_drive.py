#!/usr/bin/env python3
"""Scan Drive/Downloads for CollX CSV — Lester or Brian can run without reboot."""
from collx_data import auto_import_from_drive, discover_collx_csv_paths, ensure_inbox, status

if __name__ == "__main__":
    inbox = ensure_inbox()
    print(f"CollX inbox: {inbox}")
    found = discover_collx_csv_paths()
    if not found:
        print("NO CSV FOUND on Drive or Downloads.")
        print("Save Gmail CollX attachment to Google Drive → collx_inbox/")
        print("See MyDrive/COLLX_FROM_EMAIL.txt")
    else:
        print(f"Found {len(found)} candidate CSV(s):")
        for row in found:
            print(f"  score={row['score']}  {row['path']}")
    result = auto_import_from_drive()
    print("Import:", result.get("status"), result.get("message") or result.get("imported"))

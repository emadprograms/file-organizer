"""Rebuild all batches from vault documents and run v11 verification."""

import os
import sys
import io
import sqlite3
from pathlib import Path

# Force UTF-8 stdout and unbuffered output
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from src.migration.v11_migration import build_batch_from_vault, verify_v11_areas, verify_migration_integrity, get_pdf_page_count
from src.db.connection import get_db_connection
from src.db.repository import Repository

AREAS_ROOT = Path(r"D:\areas_v11")
DB_PATH = Path(r"D:\areas_v11\organizer.db")

def main():
    if not AREAS_ROOT.exists():
        print(f"ERROR: Areas root does not exist: {AREAS_ROOT}")
        sys.exit(1)
        
    if not DB_PATH.exists():
        print(f"ERROR: Database does not exist: {DB_PATH}")
        sys.exit(1)

    conn = get_db_connection(DB_PATH)
    repo = Repository(conn, autocommit=False)

    print("=" * 60)
    print("STEP 1: Delete stray imported batch PDFs in Safra D")
    print("=" * 60)
    safra_d_dir = AREAS_ROOT / "Safra D"
    deleted_stray_count = 0
    if safra_d_dir.exists():
        for hdir in sorted(safra_d_dir.iterdir()):
            if not hdir.is_dir():
                continue
            bdir = hdir / "batches"
            if bdir.exists():
                for f in list(bdir.glob("*.pdf")):
                    try:
                        f.unlink()
                        deleted_stray_count += 1
                    except Exception as e:
                        print(f"Could not delete {f}: {e}")
    print(f"Deleted {deleted_stray_count} stray batch PDFs from Safra D houses.\n")

    print("=" * 60)
    print("STEP 2: Build batch PDFs from vault documents and pages table")
    print("=" * 60)
    
    total_houses = 0
    built_count = 0
    failed_builds = []

    for area_dir in sorted(AREAS_ROOT.iterdir()):
        if not area_dir.is_dir() or area_dir.name.startswith("."):
            continue

        print(f"\nProcessing Area: {area_dir.name}")
        for house_dir in sorted(area_dir.iterdir()):
            if not house_dir.is_dir() or house_dir.name.startswith("."):
                continue

            total_houses += 1
            hid = house_dir.name.split(" - ")[0].strip()
            vault_dir = house_dir / "vault"
            batches_dir = house_dir / "batches"
            batches_dir.mkdir(parents=True, exist_ok=True)
            batch_pdf_path = batches_dir / f"batch_1_{hid}.pdf"

            # Query pages for this house
            rows = conn.execute(
                "SELECT page_number, vault_id FROM pages WHERE house_id = ? ORDER BY page_number",
                (hid,),
            ).fetchall()
            
            pages_data = [{"page_number": r[0], "vault_id": r[1]} for r in rows if r[1]]
            
            # If no rows or house 551 in Safra D, filter to vault files actually present in this folder
            if vault_dir.exists():
                present_vids = {f.name[4:-4] for f in vault_dir.glob("doc_*.pdf")}
                if pages_data:
                    # Keep pages that exist in this vault
                    folder_pages_data = [p for p in pages_data if p["vault_id"] in present_vids]
                    if not folder_pages_data:
                        folder_pages_data = [{"page_number": idx + 1, "vault_id": vid} for idx, vid in enumerate(sorted(present_vids))]
                else:
                    folder_pages_data = [{"page_number": idx + 1, "vault_id": vid} for idx, vid in enumerate(sorted(present_vids))]
            else:
                folder_pages_data = pages_data

            success = build_batch_from_vault(vault_dir, folder_pages_data, batch_pdf_path)
            
            if success and batch_pdf_path.exists():
                actual_pages = get_pdf_page_count(batch_pdf_path)
                built_count += 1
                
                # Update batches table in DB if batch exists
                b_row = conn.execute("SELECT id FROM batches WHERE house_id = ?", (hid,)).fetchone()
                if b_row:
                    conn.execute(
                        "UPDATE batches SET filename = ?, file_path = ?, page_count = ?, status = 'completed' WHERE id = ?",
                        (f"batch_1_{hid}.pdf", f"batches/batch_1_{hid}.pdf", actual_pages, b_row[0]),
                    )
                else:
                    conn.execute(
                        "INSERT INTO batches (house_id, filename, file_path, page_count, status) VALUES (?, ?, ?, ?, 'completed')",
                        (hid, f"batch_1_{hid}.pdf", f"batches/batch_1_{hid}.pdf", actual_pages),
                    )
            else:
                failed_builds.append((area_dir.name, hid))
                print(f"  [FAIL] Could not build batch for {area_dir.name}/{hid}", flush=True)

            if total_houses % 20 == 0:
                print(f"  ... Progress: {total_houses} houses processed ({built_count} built) ...", flush=True)

    conn.commit()
    print(f"\nBatch building completed: {built_count}/{total_houses} successfully created.")
    if failed_builds:
        print(f"Failed houses: {failed_builds}")

    print("\n" + "=" * 60)
    print("STEP 3: Run v11 verification across all files")
    print("=" * 60)
    verification_results = verify_v11_areas(AREAS_ROOT, DB_PATH, conn=conn)
    conn.close()

    print(f"Total Houses Checked: {verification_results['total_houses']}")
    print(f"Passed: {verification_results['passed']}")
    print(f"Failed: {verification_results['failed']}")

    if verification_results["failed"] > 0:
        print("\nFailures:")
        for fail in verification_results["failures"]:
            print(f"  [{fail['area']}] {fail['house_id']}: {fail['errors']}")
    else:
        print("\nALL HOUSES PASSED V11 VERIFICATION! 100% INTEGRITY ACHIEVED.")

if __name__ == "__main__":
    main()

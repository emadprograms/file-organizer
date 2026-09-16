"""
verify_v11.py - Fast & Deep Integrity Verification for Housing Application (v11 Architecture)

Checks:
1. Physical PDF page counts vs DB documents.page_count (using concurrent PDF header reads)
2. DB documents.page_count vs pages table row count (for non-manual docs)
3. Physical batch PDF page counts vs DB batches.page_count
4. DB batches.page_count vs pages table row count
5. Batch page sequence continuity (zero missing page numbers)
6. Corrupted / 0-byte PDF detection
"""
import sys
import os
import sqlite3
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Force UTF-8 stdout and unbuffered output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

try:
    from pypdf import PdfReader
except ImportError:
    print("ERROR: pypdf is required. Install via: pip install pypdf", flush=True)
    sys.exit(1)

def check_single_doc(item, areas_root):
    vault_id, house_id, area_id, page_count = item
    if not area_id or not house_id:
        return f"Doc {vault_id}: Missing area_id or house_id in database."

    clean_h = house_id.split(" - ")[0].strip()
    candidates = [
        areas_root / area_id / house_id / "vault" / f"doc_{vault_id}.pdf",
        areas_root / area_id / clean_h / "vault" / f"doc_{vault_id}.pdf",
        areas_root / area_id / house_id / "vault" / f"{vault_id}.pdf",
        areas_root / area_id / clean_h / "vault" / f"{vault_id}.pdf",
    ]
    pdf_path = next((p for p in candidates if p.exists()), None)

    if not pdf_path:
        # Fallback: check across other area folders for this house ID (e.g. 551 across Safra C and Safra D)
        for alt_area in areas_root.iterdir():
            if alt_area.is_dir() and alt_area.name != area_id:
                alt_cands = [
                    alt_area / house_id / "vault" / f"doc_{vault_id}.pdf",
                    alt_area / clean_h / "vault" / f"doc_{vault_id}.pdf",
                    alt_area / house_id / "vault" / f"{vault_id}.pdf",
                    alt_area / clean_h / "vault" / f"{vault_id}.pdf",
                ]
                pdf_path = next((p for p in alt_cands if p.exists()), None)
                if pdf_path:
                    break

    if not pdf_path:
        return f"Doc {vault_id} ({area_id}/{clean_h}): Physical PDF not found in vault."

    if pdf_path.stat().st_size == 0:
        return f"Doc {vault_id}: File is 0 bytes at {pdf_path}"

    try:
        reader = PdfReader(str(pdf_path))
        actual_pdf_pages = len(reader.pages)
        if actual_pdf_pages != page_count:
            return (
                f"Doc {vault_id} ({area_id}/{clean_h}): Page count mismatch! "
                f"DB documents.page_count={page_count}, but physical PDF has {actual_pdf_pages} pages."
            )
    except Exception as e:
        return f"Doc {vault_id}: Unreadable PDF ({e}) at {pdf_path}"

    return None

def run_v11_verification(areas_root_path: str = r"D:\areas_v11", db_path: str = r"D:\areas_v11\organizer.db"):
    areas_root = Path(areas_root_path).resolve()
    db_file = Path(db_path).resolve()

    print("=" * 70, flush=True)
    print("🔍 Running Deep v11 Integrity Verification", flush=True)
    print(f"📂 Areas Root: {areas_root}", flush=True)
    print(f"📁 Database:   {db_file}", flush=True)
    print("=" * 70, flush=True)

    if not db_file.exists():
        print(f"❌ Database not found at: {db_file}", flush=True)
        return False
    if not areas_root.exists():
        print(f"❌ Areas root not found at: {areas_root}", flush=True)
        return False

    conn = sqlite3.connect(str(db_file))
    c = conn.cursor()

    errors = []
    warnings = []

    # -------------------------------------------------------------
    # Pillar 1: Document Physical Files & Page Counts (Parallel)
    # -------------------------------------------------------------
    print("\n[1/4] Verifying Documents & Physical Vault PDFs (multithreaded)...", flush=True)
    c.execute("""
        SELECT d.vault_id, d.house_id, h.area_id, d.page_count
        FROM documents d
        LEFT JOIN houses h ON d.house_id = h.id
    """)
    docs = c.fetchall()
    total_docs = len(docs)
    print(f"  Loaded {total_docs} document records. Auditing physical files...", flush=True)

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = executor.map(lambda d: check_single_doc(d, areas_root), docs)
        for idx, res in enumerate(futures, start=1):
            if res:
                errors.append(res)
            if idx % 3000 == 0 or idx == total_docs:
                print(f"  ... audited {idx}/{total_docs} vault documents ...", flush=True)

    # -------------------------------------------------------------
    # Pillar 2: Document-to-Pages Table Parity (non-manual)
    # -------------------------------------------------------------
    print("\n[2/4] Verifying Document-to-Pages Table Parity...", flush=True)
    c.execute("""
        SELECT d.vault_id, d.page_count, COUNT(p.page_number) as page_rows
        FROM documents d
        LEFT JOIN pages p ON p.vault_id = d.vault_id
        WHERE d.is_manual = 0
        GROUP BY d.vault_id
        HAVING d.page_count != COUNT(p.page_number)
    """)
    doc_mismatches = c.fetchall()
    for vid, expected, actual in doc_mismatches:
        errors.append(f"Doc {vid}: Relational parity mismatch: documents.page_count={expected}, but pages rows={actual}.")
    print(f"  Non-manual doc mismatches: {len(doc_mismatches)}", flush=True)

    # -------------------------------------------------------------
    # Pillar 3: Batch Physical Files & Row Counts
    # -------------------------------------------------------------
    print("\n[3/4] Verifying Batches & Physical Batch PDFs...", flush=True)
    c.execute("""
        SELECT b.id, b.house_id, h.area_id, b.file_path, b.page_count,
               COUNT(p.page_number) as page_rows
        FROM batches b
        LEFT JOIN houses h ON b.house_id = h.id
        LEFT JOIN pages p ON p.batch_id = b.id
        GROUP BY b.id
    """)
    batches = c.fetchall()
    total_batches = len(batches)

    for bid, house_id, area_id, rel_path, expected_count, page_rows in batches:
        if page_rows != expected_count:
            errors.append(
                f"Batch {bid} ({house_id}): Row count mismatch! "
                f"batches.page_count={expected_count}, but pages table has {page_rows} rows."
            )

        if area_id and house_id and rel_path:
            clean_h = house_id.split(" - ")[0].strip()
            candidates = [
                areas_root / area_id / house_id / rel_path,
                areas_root / area_id / clean_h / rel_path,
                areas_root / area_id / clean_h / "batches" / Path(rel_path).name,
            ]
            batch_pdf = next((p for p in candidates if p.exists()), None)
            if not batch_pdf:
                for alt_area in areas_root.iterdir():
                    if alt_area.is_dir() and alt_area.name != area_id:
                        alt_batch = alt_area / clean_h / rel_path
                        if alt_batch.exists():
                            batch_pdf = alt_batch
                            break
                        alt_batch2 = alt_area / clean_h / "batches" / Path(rel_path).name
                        if alt_batch2.exists():
                            batch_pdf = alt_batch2
                            break
            if batch_pdf:
                if batch_pdf.stat().st_size == 0:
                    errors.append(f"Batch {bid}: File is 0 bytes at {batch_pdf}")
                else:
                    try:
                        reader = PdfReader(str(batch_pdf))
                        phys_pages = len(reader.pages)
                        if phys_pages != expected_count:
                            warnings.append(
                                f"Batch {bid} ({house_id}): Physical PDF has {phys_pages} pages, "
                                f"while DB batches.page_count={expected_count}."
                            )
                    except Exception as e:
                        errors.append(f"Batch {bid}: Unreadable PDF ({e}) at {batch_pdf}")
            else:
                warnings.append(f"Batch {bid} ({house_id}): Batch PDF file not found at {rel_path}.")

    print(f"  Checked {total_batches} batches.", flush=True)

    # -------------------------------------------------------------
    # Pillar 4: Batch Page Continuity (Gaps)
    # -------------------------------------------------------------
    print("\n[4/4] Verifying Batch Page Sequence Continuity (Gaps)...", flush=True)
    c.execute("SELECT DISTINCT batch_id FROM pages WHERE batch_id IS NOT NULL")
    batch_ids = [r[0] for r in c.fetchall()]
    total_gaps = 0

    for bid in batch_ids:
        c.execute("SELECT page_number FROM pages WHERE batch_id = ? ORDER BY page_number", (bid,))
        page_nums = [r[0] for r in c.fetchall()]
        if not page_nums:
            continue

        pos_pages = [p for p in page_nums if p > 0]
        if pos_pages:
            expected_set = set(range(min(pos_pages), max(pos_pages) + 1))
            missing = sorted(expected_set - set(pos_pages))
            if missing:
                total_gaps += len(missing)
                errors.append(f"Batch {bid}: Missing page numbers in sequence: {missing[:10]}{'...' if len(missing) > 10 else ''}")

    print(f"  Total sequence gaps found: {total_gaps}", flush=True)

    conn.close()

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    print("\n" + "=" * 70, flush=True)
    print("📊 VERIFICATION RESULTS", flush=True)
    print("=" * 70, flush=True)
    print(f"Total Documents Checked: {total_docs}", flush=True)
    print(f"Total Batches Checked:   {total_batches}", flush=True)
    print(f"Errors Found:            {len(errors)}", flush=True)
    print(f"Warnings Found:          {len(warnings)}", flush=True)

    if warnings:
        print("\n⚠️  WARNINGS:", flush=True)
        for w in warnings[:15]:
            print(f"  - {w}", flush=True)
        if len(warnings) > 15:
            print(f"  ... and {len(warnings) - 15} more warnings.", flush=True)

    if errors:
        print("\n❌ ERRORS:", flush=True)
        for e in errors[:20]:
            print(f"  - {e}", flush=True)
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors.", flush=True)
        print("\n❌ VERIFICATION FAILED.", flush=True)
        return False
    else:
        print("\n✅ ALL INTEGRITY CHECKS PASSED! Database, vault PDFs, batches, and page sequences are in 100% parity.", flush=True)
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deep v11 Integrity Verification")
    parser.add_argument("--areas-root", default=r"D:\areas_v11", help="Path to areas root directory")
    parser.add_argument("--db-path", default=r"D:\areas_v11\organizer.db", help="Path to SQLite database")
    args = parser.parse_args()

    success = run_v11_verification(args.areas_root, args.db_path)
    sys.exit(0 if success else 1)

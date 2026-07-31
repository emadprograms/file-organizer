"""
ai_stitch.py — Mechanical PDF stitching from AI-generated source files.

Zero LLM calls. Reads AI-generated JSON files from .source_files/ and:
  1. Slices the addition PDF into individual compressed document PDFs.
  2. Places them in the correct tenant/category folder structure.
  3. Prepends new pages to {house_id}_finalized.pdf with updated TOC.
  4. Merges new JSON entries into the master source files (shifting existing indices).

Usage:
    python scripts/ai_stitch.py <house_id> "<area>"
    python scripts/ai_stitch.py 504 "Safra D"
    python scripts/ai_stitch.py 502 "Safra D" --additions-dir "D:/custom/path"

Expects the AI to have already written:
    .source_files/{house_id}_addition_grouped.json

Optionally also reads:
    .source_files/{house_id}_addition_report.json  (per-page categorization)
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fitz  # PyMuPDF
import yaml

from src.pdf.compress import compress_pdf


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def resolve_tenant_folder(tenant_name: str, tenants: list[dict]) -> str:
    """Map a canonical tenant name → physical folder name with date range."""
    for t in tenants:
        if t["name"] == tenant_name:
            start_year = str(t.get("start_date", "????"))[:4]
            end = t.get("end_date", "present")
            end_display = "الآن" if end in ("present", None) else str(end)[:4]
            return f"{tenant_name} \u200e({start_year} - {end_display})\u200e"
    # Fallback: raw name
    return tenant_name


def sanitize_filename(name: str) -> str:
    """Remove characters that are illegal in Windows filenames."""
    for ch in r'<>:"/\|?*':
        name = name.replace(ch, "_")
    return name.strip()


def dedup_path(path: Path) -> Path:
    """If *path* already exists, append _2, _3, … until unique."""
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 2
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


# ---------------------------------------------------------------------------
# Core: generate individual PDFs per group
# ---------------------------------------------------------------------------

def generate_documents(
    groups: list[dict],
    addition_pdf: Path,
    house_dir: Path,
    tenants: list[dict],
    house_id: str,
    logger,
) -> tuple[list[dict], list[dict]]:
    """
    For each document group, extract pages from the addition PDF, compress,
    and save into the correct tenant/folder path.

    Returns (per_page_entries, generated_groups) where generated_groups is
    the input groups annotated with ``output_file`` for the manifest.
    """
    doc = fitz.open(str(addition_pdf))
    per_page: list[dict] = []
    annotated_groups: list[dict] = []

    for group in groups:
        start = group["start_page"]
        end = group["end_page"]
        tenant = group["primary_tenant"]
        folder = group["folder_path"]
        title = group.get("brief_arabic_title") or "بدون عنوان"
        dates = group.get("dates", [])
        date_str = dates[0] if dates else "unknown"

        # Resolve full tenant folder name
        tenant_folder = resolve_tenant_folder(tenant, tenants)

        # Build filename
        if title and title != "بدون عنوان":
            filename = sanitize_filename(f"{date_str} - {title}.pdf")
        else:
            filename = sanitize_filename(f"{date_str}.pdf")

        target_dir = house_dir / tenant_folder / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        abs_path = dedup_path(target_dir / filename)

        # Extract pages → tmp → compress → final
        tmp_slice = Path(tempfile.gettempdir()) / f"slice_{uuid.uuid4().hex}.pdf"
        try:
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start, to_page=end)
            new_doc.save(str(tmp_slice))
            new_doc.close()

            try:
                compress_pdf(str(tmp_slice), str(abs_path))
            except Exception:
                shutil.copy2(str(tmp_slice), str(abs_path))
        finally:
            if tmp_slice.exists():
                try:
                    os.remove(str(tmp_slice))
                except OSError:
                    pass

        rel_output = f"{house_dir.name}/{tenant_folder}/{folder}/{abs_path.name}"
        target_folder_rel = f"{tenant_folder}/{folder}"

        logger(f"  -> {abs_path.name}  (pages {start+1}-{end+1})")

        # Build per-page entries
        for pidx in range(start, end + 1):
            per_page.append({
                "page_index": pidx,
                "tenant": tenant,
                "date": date_str,
                "output_file": rel_output,
                "page_in_output": pidx - start + 1,
                "target_folder": target_folder_rel,
            })

        annotated = dict(group)
        annotated["output_file"] = rel_output
        annotated_groups.append(annotated)

    doc.close()
    per_page.sort(key=lambda x: x["page_index"])
    return per_page, annotated_groups


# ---------------------------------------------------------------------------
# Core: merge into master JSONs
# ---------------------------------------------------------------------------

def merge_master_jsons(
    source_dir: Path,
    house_id: str,
    new_report: list[dict] | None,
    new_grouped: list[dict],
    new_per_page: list[dict],
    page_shift: int,
):
    """Prepend new entries to master JSONs, shifting existing indices forward."""

    # --- report.json (per-page list) ---
    report_path = source_dir / f"{house_id}_report.json"
    if new_report and report_path.exists():
        existing = load_json(report_path)
        if isinstance(existing, dict):
            existing = [existing[k] for k in sorted(existing.keys(), key=int)]
        merged = new_report + existing
        save_json(report_path, merged)
    elif new_report:
        save_json(report_path, new_report)

    # --- 1_cleaned.json (per-page list) ---
    cleaned_path = source_dir / f"{house_id}_1_cleaned.json"
    if new_report and cleaned_path.exists():
        existing_cleaned = load_json(cleaned_path)
        if isinstance(existing_cleaned, dict):
            existing_cleaned = [existing_cleaned[k] for k in sorted(existing_cleaned.keys(), key=int)]
        
        # Shift original_index for existing
        for item in existing_cleaned:
            if "original_index" in item:
                item["original_index"] += page_shift
        
        # Build new cleaned entries from new_report + groups mapping
        new_cleaned = []
        for i, page_data in enumerate(new_report):
            cleaned_entry = dict(page_data)
            cleaned_entry["original_index"] = i
            # Find which group this page belongs to
            for g in new_grouped:
                if g["start_page"] <= i <= g["end_page"]:
                    cleaned_entry["canonical_tenant"] = g["primary_tenant"]
                    cleaned_entry["resolved_date"] = g["dates"][0] if g.get("dates") else "1900-01-01"
                    break
            new_cleaned.append(cleaned_entry)
            
        merged_cleaned = new_cleaned + existing_cleaned
        save_json(cleaned_path, merged_cleaned)

    # --- grouped.json ---
    grouped_path = source_dir / f"{house_id}_2_grouped.json"
    if grouped_path.exists():
        existing = load_json(grouped_path)
        for g in existing:
            g["start_page"] += page_shift
            g["end_page"] += page_shift
        merged = new_grouped + existing
        save_json(grouped_path, merged)
    else:
        save_json(grouped_path, new_grouped)

    # --- routed_and_finalized.json ---
    manifest_path = source_dir / f"{house_id}_3_routed_and_finalized.json"
    if manifest_path.exists():
        existing = load_json(manifest_path)

        # Shift existing per_page indices
        if "per_page" in existing:
            for p in existing["per_page"]:
                p["page_index"] += page_shift
            merged_per_page = new_per_page + existing["per_page"]
            existing["per_page"] = merged_per_page

        # Shift existing grouped indices
        if "grouped" in existing:
            for g in existing["grouped"]:
                if "start_page" in g:
                    g["start_page"] += page_shift
                    g["end_page"] += page_shift
                if "original_index" in g:
                    g["original_index"] += page_shift
            existing["grouped"] = new_grouped + existing["grouped"]
        else:
            existing["grouped"] = new_grouped

        # Update summary
        if "summary" in existing:
            existing["summary"]["total_input_pages"] += page_shift
            existing["summary"]["total_output_pages"] += page_shift
            existing["summary"]["output_file_count"] += len(new_grouped)

        save_json(manifest_path, existing)
    else:
        manifest = {
            "summary": {
                "house_id": house_id,
                "total_input_pages": page_shift,
                "total_output_pages": page_shift,
                "output_file_count": len(new_grouped),
                "unaccounted_pages": [],
            },
            "per_page": new_per_page,
        }
        save_json(manifest_path, manifest)


# ---------------------------------------------------------------------------
# Core: prepend to finalized PDF
# ---------------------------------------------------------------------------

def prepend_to_finalized(
    addition_pdf: Path,
    house_dir: Path,
    house_id: str,
    new_grouped: list[dict],
    logger,
):
    """Compress the addition PDF and prepend it to the finalized PDF."""

    finalized_path = house_dir / f"{house_id}_finalized.pdf"
    tmp_compressed = Path(tempfile.gettempdir()) / f"compressed_{uuid.uuid4().hex}.pdf"
    tmp_finalized = Path(tempfile.gettempdir()) / f"finalized_{uuid.uuid4().hex}.pdf"

    try:
        # 1. Compress the new pages
        compress_pdf(str(addition_pdf), str(tmp_compressed))

        # 2. Open existing finalized or create new
        if finalized_path.exists():
            full_pdf = fitz.open(str(finalized_path))
        else:
            full_pdf = fitz.open()

        # 3. Count pages before insertion (for TOC shifting reference)
        new_doc = fitz.open(str(tmp_compressed))
        page_shift = new_doc.page_count

        # 4. Insert new pages at position 0
        full_pdf.insert_pdf(new_doc, start_at=0)
        new_doc.close()

        # 5. Build TOC: prepend new entries, keep existing (auto-shifted by PyMuPDF)
        toc = full_pdf.get_toc()

        new_toc = []
        for group in new_grouped:
            title = group.get("brief_arabic_title") or group.get("folder_path") or "بدون عنوان"
            target_page = min(group["start_page"] + 1, full_pdf.page_count)
            new_toc.append([1, title, target_page])

        for item in toc:
            new_toc.append(item)

        full_pdf.set_toc(new_toc)

        # 6. Save
        full_pdf.save(str(tmp_finalized))
        full_pdf.close()

        shutil.move(str(tmp_finalized), str(finalized_path))
        size_mb = finalized_path.stat().st_size / (1024 * 1024)
        logger(f"Updated {finalized_path.name} ({size_mb:.1f} MB, {page_shift} new pages prepended)")

        return page_shift

    except Exception as e:
        logger(f"ERROR: Failed to rebuild finalized PDF: {e}")
        raise
    finally:
        for tmp in (tmp_compressed, tmp_finalized):
            if tmp.exists():
                try:
                    os.remove(str(tmp))
                except OSError:
                    pass


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Mechanical PDF stitching from AI-generated source files")
    parser.add_argument("house_id", help="House number, e.g. 504")
    parser.add_argument("area", help='Area name, e.g. "Safra D"')
    parser.add_argument("--additions-dir", help="Custom path to the additions directory")
    parser.add_argument("--no-finalize", action="store_true", help="Skip prepending to finalized PDF")
    args = parser.parse_args()

    house_id = args.house_id
    area = args.area

    def log(msg):
        print(msg, flush=True)

    log(f"AI Stitch: Processing house {house_id} in {area}")

    # Locate house directory
    areas_root = Path("D:/Areas")
    area_dir = areas_root / area
    house_dir = None
    for d in area_dir.iterdir():
        if d.is_dir() and d.name.startswith(f"{house_id} "):
            source_dir = d / ".source_files"
            if (source_dir / f"{house_id}_1_tenants.yaml").exists():
                house_dir = d
                break

    if not house_dir:
        log(f"ERROR: House directory not found for {house_id} in {area_dir}")
        sys.exit(1)

    source_dir = house_dir / ".source_files"

    # Read AI-generated grouped JSON
    addition_grouped_path = source_dir / f"{house_id}_addition_grouped.json"
    if not addition_grouped_path.exists():
        log(f"ERROR: AI-generated grouped file not found: {addition_grouped_path}")
        sys.exit(1)

    groups = load_json(addition_grouped_path)
    log(f"Loaded {len(groups)} document groups from AI analysis")

    # Read tenants YAML
    tenants_yaml_path = source_dir / f"{house_id}_1_tenants.yaml"
    if not tenants_yaml_path.exists():
        log(f"ERROR: Tenants YAML not found: {tenants_yaml_path}")
        sys.exit(1)

    with open(tenants_yaml_path, "r", encoding="utf-8") as f:
        tenants = yaml.safe_load(f)

    # Find addition PDF
    if args.additions_dir:
        addition_pdf = Path(args.additions_dir) / f"{house_id}.pdf"
    else:
        addition_pdf = Path(f"D:/{area} additions/{house_id}.pdf")

    if not addition_pdf.exists():
        log(f"ERROR: Addition PDF not found: {addition_pdf}")
        sys.exit(1)

    doc = fitz.open(str(addition_pdf))
    total_new_pages = doc.page_count
    doc.close()
    log(f"Addition PDF: {total_new_pages} pages")

    # Optionally read per-page report
    addition_report_path = source_dir / f"{house_id}_addition_report.json"
    new_report = None
    if addition_report_path.exists():
        new_report = load_json(addition_report_path)

    # Step 1: Generate individual document PDFs
    log("\n--- Generating individual document PDFs ---")
    per_page, annotated_groups = generate_documents(
        groups, addition_pdf, house_dir, tenants, house_id, log
    )
    log(f"Generated {len(annotated_groups)} document PDFs")

    # Step 2: Prepend to finalized PDF
    if not args.no_finalize:
        log("\n--- Prepending to finalized PDF ---")
        page_shift = prepend_to_finalized(
            addition_pdf, house_dir, house_id, groups, log
        )
    else:
        page_shift = total_new_pages
        log("Skipping finalized PDF update (--no-finalize)")

    # Step 3: Merge into master JSONs
    log("\n--- Merging into master source files ---")
    merge_master_jsons(
        source_dir, house_id, new_report, groups, per_page, page_shift
    )
    log("Master JSONs updated successfully")

    # Step 4: Clean up addition files (but keep the original addition PDF)
    log("\n--- Cleanup ---")
    for tmp_file in (addition_grouped_path, addition_report_path):
        if tmp_file.exists():
            archive_dir = source_dir / "addition_archives"
            archive_dir.mkdir(exist_ok=True)
            shutil.move(str(tmp_file), str(archive_dir / tmp_file.name))
            log(f"Archived {tmp_file.name}")

    log(f"\n✅ AI Stitch complete for house {house_id}!")
    log(f"   {len(annotated_groups)} documents placed in {house_dir.name}")
    if not args.no_finalize:
        log(f"   {total_new_pages} pages prepended to {house_id}_finalized.pdf")


if __name__ == "__main__":
    main()

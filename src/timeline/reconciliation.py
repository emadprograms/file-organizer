"""Reconciliation logic for file organizer."""
import logging
import json
from pathlib import Path

logger = logging.getLogger(f"file_organizer.{__name__}")

def run_reconciliation(summary: dict, per_page: list, total_input_pages: int, house_id: str, output_dir: Path, dry_run: bool = False):
    """Write reconciliation manifest and assert page counts."""
    unaccounted_pages = []
    accounted_page_indices = {p["page_index"] for p in per_page}
    for i in range(total_input_pages):
        if i not in accounted_page_indices:
            unaccounted_pages.append(i)
            
    manifest = {
        "summary": {
            "house_id": house_id,
            "total_input_pages": total_input_pages,
            "total_output_pages": summary.get("total_output_pages", len(per_page)),
            "output_file_count": summary.get("output_file_count", len({p["output_file"] for p in per_page})),
            "unaccounted_pages": unaccounted_pages
        },
        "per_page": per_page
    }
    
    if not dry_run:
        from src.utils.fs import atomic_write
        source_files_dir = output_dir / ".source_files"
        source_files_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = source_files_dir / f"{house_id}_3_routed_and_finalized.json"
        with atomic_write(str(manifest_path)) as tmp_path:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
    else:
        logger.info(f"  [DRY RUN] Would write manifest to {output_dir / '.source_files' / f'{house_id}_3_routed_and_finalized.json'}")
    
    from src.core.ui import vprint
    from rich.table import Table
    table = Table(title="Reconciliation Report")
    table.add_column("House ID")
    table.add_column("Total Input Pages")
    table.add_column("Total Output Pages")
    table.add_column("Output File Count")
    table.add_column("Unaccounted Pages")
    table.add_row(
        str(manifest["summary"]["house_id"]),
        str(manifest["summary"]["total_input_pages"]),
        str(manifest["summary"]["total_output_pages"]),
        str(manifest["summary"]["output_file_count"]),
        str(len(manifest["summary"]["unaccounted_pages"]))
    )
    vprint(table)
    
    if total_input_pages != manifest["summary"]["total_output_pages"]:
        raise RuntimeError("Reconciliation failed: total input pages != total output pages")

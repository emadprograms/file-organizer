"""Reconciliation logic for file organizer."""
import logging
import json
from pathlib import Path

logger = logging.getLogger(f"file_organizer.{__name__}")

from typing import Any

def run_reconciliation(
    summary: dict[str, Any], 
    per_page: list[dict[str, Any]], 
    total_input_pages: int, 
    house_id: str, 
    output_dir: Path, 
    dry_run: bool = False,
    prepend: bool = False
) -> None:
    """Write reconciliation manifest and assert page counts.

    Produces a JSON manifest and a terminal report to ensure no pages were 
    lost during processing.

    Args:
        summary (dict[str, Any]): High-level summary dictionary.
        per_page (list[dict[str, Any]]): Detailed mapping of pages.
        total_input_pages (int): The number of pages processed.
        house_id (str): The canonical house ID.
        output_dir (Path): The directory to save the output files.
        dry_run (bool): If True, skip writing files.
        prepend (bool): If True, prepends the new data to the manifest instead of appending.

    Raises:
        RuntimeError: If the input and output page counts do not match.
    """
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
        from src.core.state import State
        source_files_dir = output_dir / ".source_files"
        source_files_dir.mkdir(parents=True, exist_ok=True)
        state = State(house_id, source_files_dir)
        
        # Merge if exists (for append mode)
        if state.data.get("manifest"):
            try:
                existing = state.data["manifest"]
                if isinstance(existing, dict) and "per_page" in existing:
                    if prepend:
                        # Shift existing items by the number of new input pages
                        page_shift = manifest["summary"]["total_input_pages"]
                        for p in existing["per_page"]:
                            p["page_index"] += page_shift
                        
                        # Merge data: new items + shifted existing items
                        manifest["per_page"] = manifest["per_page"] + existing["per_page"]
                        manifest["summary"]["total_input_pages"] += existing["summary"]["total_input_pages"]
                        manifest["summary"]["total_output_pages"] += existing["summary"]["total_output_pages"]
                        manifest["summary"]["output_file_count"] += existing["summary"]["output_file_count"]
                    else:
                        # Update indices for new pages to append at the end
                        page_shift = existing["summary"].get("total_input_pages", 0)
                        for p in manifest["per_page"]:
                            p["page_index"] += page_shift
                        
                        # Merge data
                        existing["per_page"].extend(manifest["per_page"])
                        existing["summary"]["total_input_pages"] += manifest["summary"]["total_input_pages"]
                        existing["summary"]["total_output_pages"] += manifest["summary"]["total_output_pages"]
                        existing["summary"]["output_file_count"] += manifest["summary"]["output_file_count"]
                        
                        manifest = existing
            except Exception as e:
                logger.error(f"Failed to merge existing reconciliation manifest from state: {e}")
                
        state.data["manifest"] = manifest
        state.save()
    else:
        logger.info(f"  [DRY RUN] Would write manifest to {output_dir / '.source_files' / f'{house_id}_state.json'}")
    
    from src.presentation.ui import vprint
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
    
    if manifest["summary"]["total_input_pages"] != manifest["summary"]["total_output_pages"]:
        raise RuntimeError(f"Reconciliation failed: total input pages ({manifest['summary']['total_input_pages']}) != total output pages ({manifest['summary']['total_output_pages']})")

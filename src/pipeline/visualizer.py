import logging
from rich.table import Table
from rich.tree import Tree
from src.core.schemas import DocumentGroup
from src.presentation.ui import vprint

from typing import Any

logger = logging.getLogger(f"file_organizer.{__name__}")

class Visualizer:
    """Visualizer for rendering dry run output previews."""
    def __init__(self) -> None:
        """Initialize the Visualizer."""
        pass

    def print_summary(self, house_id: str, summary: dict[str, Any], per_page: list[dict[str, Any]], documents: list[DocumentGroup]) -> None:
        """Print a summary table and tree view of the dry run output.
        
        Args:
            house_id (str): The identifier of the house.
            summary (dict[str, Any]): Dictionary containing total output pages and file count.
            per_page (list[dict[str, Any]]): List of metadata describing the output files for each page.
            documents (list[DocumentGroup]): List of all processed document groups.
            
        Returns:
            None
        """
        vprint("\n[bold cyan]=== Dry Run Output Preview ===[/bold cyan]\n")
        
        # Table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric")
        table.add_column("Value")
        
        table.add_row("Total Output Pages", str(summary.get("total_output_pages", 0)))
        table.add_row("Total Output Files", str(summary.get("output_file_count", 0)))
        
        vprint(table)
        vprint()
        
        # Tree: House ID -> Tenant -> Category -> PDFs
        tree = Tree(f"🏠 [bold blue]{house_id}[/bold blue]")
        
        # Build tree structure from output_file relative paths
        structure = {}
        for p in per_page:
            # Normalize path separators
            path_parts = p["output_file"].replace("\\", "/").split("/")
            if len(path_parts) == 4:
                house_id, tenant, category, filename = path_parts
                if tenant not in structure:
                    structure[tenant] = {}
                if category not in structure[tenant]:
                    structure[tenant][category] = set()
                structure[tenant][category].add(filename)
                
        # Add to tree
        for tenant in sorted(structure.keys()):
            tenant_node = tree.add(f"👤 [bold green]{tenant}[/bold green]")
            for category in sorted(structure[tenant].keys()):
                cat_node = tenant_node.add(f"📁 [bold yellow]{category}[/bold yellow]")
                for filename in sorted(list(structure[tenant][category])):
                    cat_node.add(f"📄 {filename}")
                    
        vprint(tree)
        vprint()

from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from typing import Any
from src.core.schemas import DocumentGroup

class Visualizer:
    def __init__(self):
        self.console = Console()

    def print_summary(self, house_id: str, summary: dict, per_page: list, documents: list[DocumentGroup]):
        self.console.print("\n[bold cyan]=== Dry Run Output Preview ===[/bold cyan]\n")
        
        # Table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric")
        table.add_column("Value")
        
        table.add_row("Total Output Pages", str(summary.get("total_output_pages", 0)))
        table.add_row("Total Output Files", str(summary.get("output_file_count", 0)))
        
        self.console.print(table)
        self.console.print()
        
        # Tree: House ID -> Tenant -> Category -> PDFs
        tree = Tree(f"🏠 [bold blue]{house_id}[/bold blue]")
        
        # Build tree structure from output_file relative paths
        structure = {}
        for p in per_page:
            # Normalize path separators
            path_parts = p["output_file"].replace("\\", "/").split("/")
            if len(path_parts) == 3:
                tenant, category, filename = path_parts
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
                    
        self.console.print(tree)
        self.console.print()

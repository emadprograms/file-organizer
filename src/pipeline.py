from typing import List
from src.ingest import PdfIngestor
from src.llm import GemmaClient
from src.schemas import PageClassification, DocumentGroup, Category


class Pipeline:
    def __init__(self, api_keys: list[str] = None, delay_between_pages: float = 1.0):
        self.ingestor = PdfIngestor()
        self.client = GemmaClient(api_keys, delay_between_pages)

    def _is_same_person(self, name1: str, name2: str) -> bool:
        """Fuzzy match to handle OCR noise or name variations like 'ال'."""
        if name1 in ("UNKNOWN", "NONE", "") or name2 in ("UNKNOWN", "NONE", ""):
            return False
        # Remove spaces and common prefixes
        def normalize(n: str) -> str:
            return n.replace(" ", "").replace("ال", "").replace("أ", "ا").replace("إ", "ا").replace("ة", "ه")
        n1 = normalize(name1)
        n2 = normalize(name2)
        return n1 in n2 or n2 in n1 or name1 == name2

    def process_pdf(self, pdf_path: str) -> list[DocumentGroup]:
        """
        Two-pass architecture:
        Pass 1: Vision extraction (category, resident, date) per page.
        Pass 2: Python timeline logic to group consecutive pages by Category + Primary Tenant.
        """
        print(f"Starting Pass 1 (Vision Extraction) for {pdf_path}...")
        
        raw_pages = []
        for page_index, image_bytes in self.ingestor.extract_pages_as_images(pdf_path):
            result = self.client.classify_page(image_bytes=image_bytes)
            # Add page_index to the result temporarily for pass 2
            setattr(result, 'page_index', page_index)
            raw_pages.append(result)
            print(f" Extracted Page {page_index}: {result.category.value} | {result.resident} | {result.date}")

        print(f"Starting Pass 2 (Tenant Grouping) for {pdf_path}...")
        
        documents: list[DocumentGroup] = []
        current_primary_tenant = "UNKNOWN"

        for page in raw_pages:
            # 1. Determine the Primary Tenant for this page based on Timeline Rules
            if page.category == Category.AMAR_TAKHSEES:
                # Independent, does not change the house's current tenant timeline
                page_primary_tenant = page.resident
            elif page.category == Category.PERSONAL_DETAILS:
                # Inherits the timeline's active tenant (e.g. wife inherits husband's folder)
                page_primary_tenant = current_primary_tenant
            elif page.resident not in ("NONE", "UNKNOWN", ""):
                # Document has a valid name — evaluate if timeline changes
                if not self._is_same_person(current_primary_tenant, page.resident):
                    # Tenant has changed! Update the timeline.
                    current_primary_tenant = page.resident
                page_primary_tenant = current_primary_tenant
            else:
                # Document has NO name (e.g. pictures, generic notifications)
                page_primary_tenant = current_primary_tenant

            # 2. Grouping Logic
            # Merge with previous group IF same Category AND same Primary Tenant
            if (documents and 
                documents[-1].category == page.category and 
                documents[-1].primary_tenant == page_primary_tenant):
                
                documents[-1].end_page = page.page_index
                if page.date != "NONE":
                    documents[-1].dates.append(page.date)
            else:
                # Start a new group
                documents.append(DocumentGroup(
                    start_page=page.page_index,
                    end_page=page.page_index,
                    house_number=page.house_number,
                    primary_tenant=page_primary_tenant,
                    category=page.category,
                    dates=[page.date] if page.date != "NONE" else []
                ))

        print(f"Identified {len(documents)} document groups based on timeline logic.")
        return documents

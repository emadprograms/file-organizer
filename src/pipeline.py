from typing import List
from src.ingest import PdfIngestor
from src.llm import GemmaClient
from src.schemas import PageClassification, DocumentGroup, Category


class Pipeline:
    def __init__(self, api_keys: list[str] = None, delay_between_pages: float = 1.0):
        self.ingestor = PdfIngestor()
        self.client = GemmaClient(api_keys, delay_between_pages)



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
            raw_pages.append((page_index, result))
            print(f" Extracted Page {page_index}: {result.category.value} | {result.resident} | {result.date}")

        print(f"Starting Pass 1.5 (Entity Resolution) for {pdf_path}...")
        log_lines = []
        for page_index, page in raw_pages:
            log_lines.append(f"Page {page_index}: {page.category.value} | {page.resident} | {page.date}")
        raw_pages_log = "\n".join(log_lines)
        
        canonical_mapping = self.client.resolve_entities(raw_pages_log)

        print(f"Starting Pass 2 (Tenant Grouping) for {pdf_path}...")
        
        documents: list[DocumentGroup] = []
        current_primary_tenant = "UNKNOWN"

        for page_index, page in raw_pages:
            # 1. Determine the Primary Tenant for this page based on Timeline Rules
            mapped_resident = canonical_mapping.get(page.resident, page.resident)

            if page.category == Category.AMAR_TAKHSEES:
                # Independent, does not change the house's current tenant timeline
                page_primary_tenant = mapped_resident
            elif page.category == Category.PERSONAL_DETAILS:
                # Inherits the timeline's active tenant (e.g. wife inherits husband's folder)
                page_primary_tenant = current_primary_tenant
            elif mapped_resident not in ("NONE", "UNKNOWN", ""):
                # Document has a valid name — evaluate if timeline changes
                if current_primary_tenant != mapped_resident:
                    # Tenant has changed! Update the timeline.
                    current_primary_tenant = mapped_resident
                page_primary_tenant = current_primary_tenant
            else:
                # Document has NO name (e.g. pictures, generic notifications)
                page_primary_tenant = current_primary_tenant

            # 2. Grouping Logic
            # Merge with previous group IF same Category AND same Primary Tenant
            if (documents and 
                documents[-1].category == page.category and 
                documents[-1].primary_tenant == page_primary_tenant):
                
                documents[-1].end_page = page_index
                if page.date != "NONE":
                    documents[-1].dates.append(page.date)
            else:
                # Start a new group
                documents.append(DocumentGroup(
                    start_page=page_index,
                    end_page=page_index,
                    house_number=page.house_number,
                    primary_tenant=page_primary_tenant,
                    category=page.category,
                    dates=[page.date] if page.date != "NONE" else []
                ))

        print(f"Identified {len(documents)} document groups based on timeline logic.")
        return documents

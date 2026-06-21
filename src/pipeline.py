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
        Processes a PDF sequentially page-by-page using Gemma's multimodal vision.
        Groups continuation pages together and returns a list of DocumentGroups.
        """
        print(f"Starting processing for {pdf_path}...")

        current_group_start: int = 0
        current_classification: PageClassification = None
        previous_summary: str = ""
        documents: list[DocumentGroup] = []

        for page_index, image_bytes in self.ingestor.extract_pages_as_images(pdf_path):
            result = self.client.classify_page(
                image_bytes=image_bytes,
                previous_summary=previous_summary
            )

            if current_classification is None:
                # First page — start a new group
                current_group_start = page_index
                current_classification = result
            elif result.is_continuation:
                # Continuation of current group — just track the end page
                pass
            else:
                # New topic — emit the current group and start a new one
                documents.append(DocumentGroup(
                    start_page=current_group_start,
                    end_page=page_index - 1,
                    house_number=current_classification.house_number,
                    resident=current_classification.resident,
                    category=current_classification.category
                ))
                previous_summary = (
                    f"Pages {current_group_start}-{page_index - 1}: "
                    f"{current_classification.category.value} for house "
                    f"{current_classification.house_number}, "
                    f"resident {current_classification.resident}"
                )
                current_group_start = page_index
                current_classification = result

        # Emit the final group
        if current_classification is not None:
            # Find the last page index from the ingestor
            last_page = current_group_start
            for page_index, _ in []:  # already consumed
                last_page = page_index
            documents.append(DocumentGroup(
                start_page=current_group_start,
                end_page=page_index,  # page_index is the last value from the loop
                house_number=current_classification.house_number,
                resident=current_classification.resident,
                category=current_classification.category
            ))

        print(f"Identified {len(documents)} document groups.")
        return documents

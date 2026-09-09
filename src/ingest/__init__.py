"""Ingest module for file-organizer."""

from src.ingest.manual_ingest import extract_pdf_text, ingest_document_manual
from src.ingest.v11_ingest import ingest_pdf_to_house

__all__ = ["extract_pdf_text", "ingest_document_manual", "ingest_pdf_to_house"]

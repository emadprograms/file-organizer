import pytest
from pathlib import Path
from src.timeline.core import FileOrganizer
from src.core.schemas import DocumentGroup

def test_file_organizer_yaml_tenant_logic():
    organizer = FileOrganizer()
    
    yaml_data = [
        {
            "name": "Jane Doe",
            "start_date": "2020",
            "end_date": "present"
        },
        {
            "name": "John Smith",
            "start_date": "2015-01",
            "end_date": "2019-12"
        }
    ]
    
    docs = [
        DocumentGroup(
            category="contract",
            brief_arabic_title="Contract",
            start_page=0,
            end_page=0,
            primary_tenant="Jane Doe",
            dates=["2021-01"]
        ),
        DocumentGroup(
            category="contract",
            brief_arabic_title="Contract",
            start_page=1,
            end_page=1,
            primary_tenant="John Smith",
            dates=["2016"]
        )
    ]
    
    tenant_folder_names, latest_tenant = organizer.compute_tenant_folders(docs, yaml_data)
    
    assert latest_tenant == "Jane Doe"
    assert "Jane Doe" in tenant_folder_names
    assert "الآن" in tenant_folder_names["Jane Doe"]
    assert "John Smith" in tenant_folder_names
    assert "2019" in tenant_folder_names["John Smith"]

def test_file_organizer_unassigned_empty_tenant():
    organizer = FileOrganizer()
    
    docs = [
        DocumentGroup(
            category="contract",
            brief_arabic_title="Contract",
            start_page=0,
            end_page=0,
            primary_tenant="", # Should become "Unassigned"
            dates=["2021-01"]
        )
    ]
    
    tenant_folder_names, latest_tenant = organizer.compute_tenant_folders(docs, None)
    assert "Unassigned" in tenant_folder_names

def test_file_organizer_filename_collision(tmp_path):
    organizer = FileOrganizer()
    
    docs = [
        DocumentGroup(
            category="contract",
            brief_arabic_title="Contract",
            start_page=0,
            end_page=0,
            primary_tenant="Test Tenant",
            dates=["2021-01"]
        ),
        DocumentGroup(
            category="contract", # Identical doc, will cause filename collision
            brief_arabic_title="Contract",
            start_page=1,
            end_page=1,
            primary_tenant="Test Tenant",
            dates=["2021-01"]
        )
    ]
    
    # Needs a dummy source pdf
    dummy_pdf = tmp_path / "dummy.pdf"
    import fitz
    doc = fitz.open()
    doc.new_page()
    doc.new_page()
    doc.save(str(dummy_pdf))
    doc.close()
    
    tenant_folders = {"Test Tenant": "Test Tenant (2021-2021)"}
    
    per_page = organizer.process_documents(docs, str(dummy_pdf), "123", tmp_path, tenant_folders)
    
    assert len(per_page) == 2
    filenames = [p["output_file"] for p in per_page]
    # Check that collision was resolved (e.g., _2 added)
    assert any("_2" in f for f in filenames)

def test_ensure_target_directories_rename_failure(tmp_path, monkeypatch):
    organizer = FileOrganizer()
    
    target_dir = tmp_path / "original_dir"
    target_dir.mkdir()
    
    # Mock rename to raise an Exception
    def mock_rename(*args, **kwargs):
        raise OSError("Permission denied")
    
    monkeypatch.setattr(Path, "rename", mock_rename)
    
    house_dir = organizer.ensure_target_directories(target_dir, {"T": "Tenant"}, "House 123", tmp_path)
    
    # Rename failed, so it should have fallen back to creating house_dir
    assert house_dir.exists()

def test_file_organizer_organize(tmp_path):
    organizer = FileOrganizer()
    
    docs = [
        DocumentGroup(
            category="contract",
            brief_arabic_title="Contract",
            start_page=0,
            end_page=0,
            primary_tenant="Jane Doe",
            dates=["2021-01"]
        )
    ]
    
    # Create dummy pdf
    dummy_pdf = tmp_path / "dummy.pdf"
    import fitz
    doc = fitz.open()
    doc.new_page()
    doc.save(str(dummy_pdf))
    doc.close()
    
    per_page, full_house_id = organizer.organize(
        documents=docs,
        source_pdf=str(dummy_pdf),
        house_id="123",
        output_base_dir=tmp_path,
        yaml_data=[{"name": "Jane Doe", "start_date": "2020", "end_date": "present"}]
    )
    
    assert full_house_id == "123 - Jane Doe"
    assert len(per_page) == 1
    
    # Check that it returns empty list if no docs
    empty_res = organizer.organize([], str(dummy_pdf), "123", tmp_path)
    assert empty_res == []

def test_file_organizer_dry_run(tmp_path):
    organizer = FileOrganizer()
    
    docs = [
        DocumentGroup(
            category="contract",
            brief_arabic_title="Contract",
            start_page=0,
            end_page=0,
            primary_tenant="Jane Doe",
            dates=["2021-01"]
        )
    ]
    
    # Process dry run
    tenant_folders = {"Jane Doe": "Jane Doe (2021-2021)"}
    per_page = organizer.process_documents(docs, "dummy.pdf", "123", tmp_path, tenant_folders, dry_run=True)
    
    assert len(per_page) == 1

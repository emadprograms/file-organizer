import pytest
from pypdf import PdfWriter
def make_valid_pdf(path):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(path, "wb") as f:
        writer.write(f)

from pathlib import Path
from src.timeline.core import FileOrganizer

def test_pipeline_idempotency_cleans_old_artifacts(tmp_path: Path):
    """
    Ensure FileOrganizer.ensure_target_directories completely deletes old artifacts
    (vault directory, [Timeline View] shortcuts, and old tenant folders) when prepend_mode=False.
    """
    organizer = FileOrganizer()
    
    house_id = "568"
    full_house_id = "568 - محمد عمران"
    output_base_dir = tmp_path / "output"
    output_base_dir.mkdir()
    
    house_dir = output_base_dir / full_house_id
    house_dir.mkdir(parents=True)
    
    # Create old artifacts
    vault_dir = house_dir / ".source_files" / "vault"
    vault_dir.mkdir(parents=True)
    make_valid_pdf(vault_dir / "old_vault_file.pdf")
    
    timeline_dir = house_dir / "[Timeline View]"
    timeline_dir.mkdir(parents=True)
    make_valid_pdf(timeline_dir / "shortcut.lnk")
    
    old_tenant_dir = house_dir / "محمد (2000 - 2024) - old"
    old_tenant_dir.mkdir(parents=True)
    make_valid_pdf(old_tenant_dir / "old_file.pdf")
    
    # Create a non-tenant directory to ensure it is NOT deleted
    safe_dir = house_dir / "Should Not Delete"
    safe_dir.mkdir()
    
    # Run ensure_target_directories with prepend_mode=False
    tenant_folder_names = {"new_tenant": "أحمد (2025 - 2026)"}
    
    returned_house_dir = organizer.ensure_target_directories(
        target_dir=house_dir,  # target_dir is same as house_dir here to skip rename logic
        tenant_folder_names=tenant_folder_names,
        full_house_id=full_house_id,
        output_base_dir=output_base_dir,
        prepend_mode=False
    )
    
    # Assertions
    assert returned_house_dir == house_dir
    
    # 1. Vault dir should be deleted
    assert not vault_dir.exists()
    
    # 2. Timeline dir should be deleted
    assert not timeline_dir.exists()
    
    # 3. Old tenant folder should be deleted (matches "(*)" and " - ")
    assert not old_tenant_dir.exists()
    
    # 4. Safe dir should still exist
    assert safe_dir.exists()
    
    # 5. New tenant folder should be created
    new_tenant_dir = house_dir / "أحمد (2025 - 2026)"
    assert new_tenant_dir.exists()

def test_pipeline_idempotency_keeps_artifacts_in_prepend_mode(tmp_path: Path):
    """
    Ensure FileOrganizer.ensure_target_directories keeps old artifacts
    when prepend_mode=True.
    """
    organizer = FileOrganizer()
    
    full_house_id = "568 - محمد عمران"
    output_base_dir = tmp_path / "output"
    house_dir = output_base_dir / full_house_id
    
    # Create old artifacts
    vault_dir = house_dir / ".source_files" / "vault"
    vault_dir.mkdir(parents=True)
    
    timeline_dir = house_dir / "[Timeline View]"
    timeline_dir.mkdir(parents=True)
    
    old_tenant_dir = house_dir / "محمد (2000 - 2024) - old"
    old_tenant_dir.mkdir(parents=True)
    
    returned_house_dir = organizer.ensure_target_directories(
        target_dir=house_dir,
        tenant_folder_names={},
        full_house_id=full_house_id,
        output_base_dir=output_base_dir,
        prepend_mode=True
    )
    
    assert returned_house_dir == house_dir
    assert vault_dir.exists()
    assert timeline_dir.exists()
    assert old_tenant_dir.exists()

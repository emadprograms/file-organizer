import re

def update_reconcile():
    with open("src/reconcile/core.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Add report initialization at the top of the function
    if "report =" not in content:
        content = content.replace(
            "    routed_data = state.data.get(\"manifest\", {})",
            """    routed_data = state.data.get("manifest", {})
        
    report = {
        "ghost_adopted": 0,
        "raw_pdf_ingested": 0,
        "user_deleted": 0,
        "orphans_trashed": 0,
        "renamed_moved": 0,
        "duplicates_adopted": 0,
        "file_moves_planned": 0,
        "verification_status": "Unknown"
    }"""
        )

    # Increment report fields
    # 1. User Deleted
    content = content.replace("deleted_vault_ids.add(vault_id)", "deleted_vault_ids.add(vault_id)\n            report[\"user_deleted\"] += 1")

    # 2. Renamed/Moved
    content = content.replace("logger.info(f\"Detected manual move/rename", "report[\"renamed_moved\"] += 1\n                logger.info(f\"Detected manual move/rename")

    # 3. Duplicate Adopted
    content = content.replace("logger.info(f\"Adopting copied/ghost shortcut", "report[\"duplicates_adopted\"] += 1\n                logger.info(f\"Adopting copied/ghost shortcut")

    # 4. Ghost Adopted
    content = content.replace("logger.info(f\"Adopting completely new ghost", "report[\"ghost_adopted\"] += 1\n                    logger.info(f\"Adopting completely new ghost")

    # 5. Orphans Trashed
    content = content.replace("logger.info(f\"Trashing orphan vault PDF", "report[\"orphans_trashed\"] += 1\n                    logger.info(f\"Trashing orphan vault PDF")

    # 6. Raw PDF Ingested
    content = content.replace("logger.info(f\"Ingesting raw PDF:", "report[\"raw_pdf_ingested\"] += 1\n                logger.info(f\"Ingesting raw PDF:")

    # 7. File Moves Planned
    content = content.replace("logger.info(f\"Reconciliation required. {len(moves)} distinct file moves planned.\")", "report[\"file_moves_planned\"] = len(moves)\n        logger.info(f\"Reconciliation required. {len(moves)} distinct file moves planned.\")")

    # Final block: Auto-Verification and Report generation
    old_end = """        logger.info(f"Updated unified state JSON successfully in {source_dir}")
    
    return 0"""
    
    new_end = """        logger.info(f"Updated unified state JSON successfully in {source_dir}")
        
        # Save Report
        with open(source_dir / "reconcile_report.json", "w", encoding="utf-8") as rf:
            json.dump(report, rf, indent=2, ensure_ascii=False)
            
        logger.info("=== RECONCILIATION SUMMARY ===")
        logger.info(f"Raw PDFs Ingested:   {report['raw_pdf_ingested']}")
        logger.info(f"Ghosts Adopted:      {report['ghost_adopted']}")
        logger.info(f"Duplicates Adopted:  {report['duplicates_adopted']}")
        logger.info(f"Renamed/Moved:       {report['renamed_moved']}")
        logger.info(f"User Deletions:      {report['user_deleted']}")
        logger.info(f"Orphans Trashed:     {report['orphans_trashed']}")
        logger.info(f"Auto-Moves Planned:  {report['file_moves_planned']}")
        logger.info("==============================")
        
        # Auto-Verification (REQ-06)
        try:
            from src.reconcile.verify import run_verification
            # We need to pass args with the new_house_dir if it changed
            class VerifyArgs:
                target_dir = new_house_dir
            
            logger.info("Running auto-verification...")
            v_res = run_verification(VerifyArgs())
            report["verification_status"] = "Pass" if v_res == 0 else "Fail"
            
            if v_res != 0:
                logger.warning("Verification found issues after reconciliation.")
                
            # Re-save report with verification status
            with open(source_dir / "reconcile_report.json", "w", encoding="utf-8") as rf:
                json.dump(report, rf, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Auto-verification failed to run: {e}")
            report["verification_status"] = "Error"
    
    return 0"""
    
    if old_end in content:
        content = content.replace(old_end, new_end)
    else:
        print("End block not found!")
        
    with open("src/reconcile/core.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Done!")

if __name__ == "__main__":
    update_reconcile()

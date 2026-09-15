---
status: complete
quick_id: 260915-d4p
slug: isolate-active-tenant-compliance-and-refine-dividers
date: 2026-09-15
description: Isolate Active Tenant Compliance Document Counts (House 500 Fix) & Refine Card/Profile Dividers
commit: HEAD
---

# Quick Task Plan: Isolate Active Tenant Compliance Document Counts (House 500 Fix) & Refine Card/Profile Dividers

**Task ID**: 260915-d4p  
**Status**: Complete  
**Date**: 2026-09-15  

## Objectives
1. **House 500 Integrity Accuracy**:
   - Isolate compliance check strictly to the active residing tenant's documents.
   - Prevent past tenant documents in the house archive from inflating the active tenant's document count (e.g. Fawaz having 1 contract while archive had 3).
2. **House Card Layout**:
   - Revert footer pill placement to avoid crowding stay duration and doc counts.
   - Place warning strip in the tenants section separated by a dedicated subtle divider (.card-warning-divider).
3. **Tenant UI Layout**:
   - Open by default with compact padding and concise wording (no verbose paragraphs).
   - Place a divider (.tenant-section-divider) between compliance checklist and tenants list.
4. **Verification**:
   - Unit tests in RepositoryTests.cs and 	enant_file_integrity.test.js.
   - All tests passing and dist synced.

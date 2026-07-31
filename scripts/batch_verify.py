"""
Batch Verify — Deep content verification for processed houses.
Validates YAML, cleaned, grouped, routed JSONs against actual filesystem.
Performs six levels of verification:
  1. Structure  — folder names, .source_files, JSON/YAML existence
  2. Cleaned    — page index coverage, tenant assignments, categories, dates
  3. Grouped    — page ranges, overlaps, tenant matching, folder_path format
  4. Routed     — summary integrity, per_page coverage, output files on disk
  5. Filesystem — orphan files, rogue folders, tenant folder existence
  6. PDF        — finalized PDF page count cross-check

Usage:
    python scripts/batch_verify.py "Safra C" --houses 508,510,512
    python scripts/batch_verify.py "Safra C"                        # all houses
"""

import argparse
import json
import os
import sys
import re
from pathlib import Path
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# ---------------------------------------------------------------------------
# Optional imports
# ---------------------------------------------------------------------------
try:
    import yaml as _yaml
    def load_yaml(path):
        with open(path, 'r', encoding='utf-8') as f:
            return _yaml.safe_load(f)
except ImportError:
    _yaml = None
    def load_yaml(path):
        """Minimal YAML list-of-dicts parser (covers tenants YAML only)."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        tenants, cur = [], {}
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('- name:'):
                if cur:
                    tenants.append(cur)
                cur = {'name': stripped.split(':', 1)[1].strip().strip("'").strip('"')}
            elif stripped.startswith('start_date:'):
                cur['start_date'] = stripped.split(':', 1)[1].strip().strip("'").strip('"')
            elif stripped.startswith('end_date:'):
                cur['end_date'] = stripped.split(':', 1)[1].strip().strip("'").strip('"')
        if cur:
            tenants.append(cur)
        return tenants

try:
    from pypdf import PdfReader
    HAS_PDF_READER = True
except ImportError:
    try:
        from PyPDF2 import PdfReader
        HAS_PDF_READER = True
    except ImportError:
        HAS_PDF_READER = False


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def pdf_page_count(path):
    if not HAS_PDF_READER:
        return None
    try:
        return len(PdfReader(str(path)).pages)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Issue tracking
# ---------------------------------------------------------------------------
class Issue:
    ERROR = "ERROR"
    WARN  = "WARN"
    PASS  = "PASS"

    def __init__(self, level, check, message):
        self.level   = level
        self.check   = check
        self.message = message

    def __str__(self):
        icons = {self.ERROR: "FAIL", self.WARN: "WARN", self.PASS: "PASS"}
        return f"  [{icons[self.level]}] {self.check}: {self.message}"


# ---------------------------------------------------------------------------
# HouseVerifier
# ---------------------------------------------------------------------------
class HouseVerifier:
    DATE_RE   = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    FOLDER_RE = re.compile(r'^\d{2}_(?!Unknown)')

    def __init__(self, house_id, area_dir):
        self.house_id    = house_id
        self.area_dir    = area_dir
        self.issues      = []
        self.house_dir   = None
        self.source_dir  = None
        self.tenants     = None
        self.cleaned     = None
        self.grouped     = None
        self.routed      = None
        self.report_data = None
        self.total_pages = None
        self._output_files_on_record = set()

    # -- helpers --
    def _add(self, lvl, chk, msg):
        self.issues.append(Issue(lvl, chk, msg))
    def _ok(self, chk, msg):
        self._add(Issue.PASS, chk, msg)
    def _err(self, chk, msg):
        self._add(Issue.ERROR, chk, msg)
    def _warn(self, chk, msg):
        self._add(Issue.WARN, chk, msg)

    @property
    def errors(self):   return [i for i in self.issues if i.level == Issue.ERROR]
    @property
    def warnings(self): return [i for i in self.issues if i.level == Issue.WARN]
    @property
    def passes(self):   return [i for i in self.issues if i.level == Issue.PASS]

    # -- entry point --
    def verify(self):
        if not self._check_structure():
            return
        self._check_report()
        self._check_cleaned()
        self._check_grouped()
        self._check_routed()
        self._check_cross_cleaned_routed()
        self._check_filesystem()
        self._check_finalized_pdf()
        self._check_addition_files()

    # -----------------------------------------------------------------------
    # Level 1 — Structure
    # -----------------------------------------------------------------------
    def _check_structure(self):
        matching = [d for d in self.area_dir.iterdir()
                    if d.is_dir() and (d.name == self.house_id
                                       or d.name.startswith(f"{self.house_id} - "))]
        if not matching:
            self._err("Structure", f"No directory found for house {self.house_id}")
            return False

        if len(matching) > 1:
            self._err("Structure", f"Multiple directories (ghost folders!): "
                       f"{[d.name for d in matching]}")

        # Prefer the one with .source_files
        self.house_dir = None
        for d in matching:
            if (d / ".source_files").exists():
                self.house_dir = d
                break
        if not self.house_dir:
            self.house_dir = matching[0]

        self.source_dir = self.house_dir / ".source_files"
        if not self.source_dir.exists():
            self._err("Structure", ".source_files directory MISSING")
            return False
        self._ok("Structure", ".source_files directory exists")

        # Tenants YAML
        yaml_path = self.source_dir / f"{self.house_id}_1_tenants.yaml"
        if not yaml_path.exists():
            yaml_path = self.source_dir / f"{self.house_id}_tenants.yaml"
        if not yaml_path.exists():
            self._err("Structure", "Tenants YAML MISSING")
            return False

        self.tenants = load_yaml(yaml_path)
        if not self.tenants:
            self._err("Structure", "Tenants YAML is empty")
            return False
        self._ok("Structure", f"Tenants YAML: {len(self.tenants)} tenant(s)")

        # Folder name vs current tenant
        current = next((t['name'] for t in self.tenants
                        if t.get('end_date', '').lower() in ('present', 'الآن')),
                       self.tenants[-1]['name'])
        expected = f"{self.house_id} - {current}"
        if self.house_dir.name == expected:
            self._ok("Structure", "Folder name matches current tenant")
        else:
            self._warn("Structure",
                        f"Folder name '{self.house_dir.name}' ≠ expected '{expected}'")

        # JSON files
        self.cleaned = self._try_load("cleaned",
                        self.source_dir / f"{self.house_id}_1_cleaned.json")
        self.grouped = self._try_load("grouped",
                        self.source_dir / f"{self.house_id}_2_grouped.json")
        self.routed  = self._try_load("routed",
                        self.source_dir / f"{self.house_id}_3_routed_and_finalized.json")
        self.report_data = self._try_load("report",
                        self.source_dir / f"{self.house_id}_report.json")

        # Finalized PDF
        fp = self.house_dir / f"{self.house_id}_finalized.pdf"
        if fp.exists():
            self._ok("Structure",
                      f"Finalized PDF exists ({fp.stat().st_size / 1048576:.1f} MB)")
        else:
            self._err("Structure", "Finalized PDF MISSING")

        return True

    def _try_load(self, label, path):
        if path.exists():
            self._ok("Structure", f"{label} JSON exists")
            return load_json(path)
        else:
            self._err("Structure", f"{label} JSON MISSING ({path.name})")
            return None

    # -----------------------------------------------------------------------
    # Level 2a — Report JSON
    # -----------------------------------------------------------------------
    def _check_report(self):
        if not self.report_data:
            return
        # report_data may be a list of dicts or contain non-dict entries
        if not isinstance(self.report_data, list):
            self._warn("Report", "report JSON is not a list — skipping")
            return
        total = len(self.report_data)
        classified = sum(1 for p in self.report_data
                         if isinstance(p, dict) and p.get('status') == 'classified')
        if classified == total:
            self._ok("Report", f"All {total} pages have status='classified'")
        else:
            self._err("Report", f"{total - classified}/{total} pages NOT classified")

        # Cross-check count with cleaned
        if self.cleaned and len(self.cleaned) != total:
            self._err("Report", f"Report has {total} entries but cleaned has {len(self.cleaned)}")
        elif self.cleaned:
            self._ok("Report", f"Report count ({total}) matches cleaned count")

    # -----------------------------------------------------------------------
    # Level 2b — Cleaned JSON
    # -----------------------------------------------------------------------
    def _check_cleaned(self):
        if not self.cleaned:
            return
        pages = self.cleaned
        total = len(pages)
        self.total_pages = total

        # Index coverage
        indices  = [p.get('original_index') for p in pages]
        expected = set(range(total))
        actual   = set(indices)
        missing  = expected - actual
        dupes    = [i for i, c in Counter(indices).items() if c > 1]
        extra    = actual - expected

        if not missing and not dupes and not extra:
            self._ok("Cleaned", f"All {total} page indices 0–{total-1} present, no gaps/dupes")
        else:
            if missing:
                self._err("Cleaned", f"Missing indices: {sorted(missing)[:20]}"
                           f"{'…' if len(missing) > 20 else ''}")
            if dupes:
                self._err("Cleaned", f"Duplicate indices: {sorted(dupes)[:20]}")
            if extra:
                self._err("Cleaned", f"Out-of-range indices: {sorted(extra)[:20]}")

        # Tenant assignments
        names = {t['name'] for t in self.tenants}
        bad, null_ct = set(), 0
        for p in pages:
            ct = p.get('canonical_tenant')
            if ct is None:
                null_ct += 1
            elif ct not in names:
                bad.add(ct)
        if bad:
            self._err("Cleaned", f"Pages assigned to unknown tenants: {bad}")
        elif null_ct:
            self._warn("Cleaned", f"{null_ct} pages have null canonical_tenant")
        else:
            self._ok("Cleaned", "All pages assigned to valid YAML tenants")

        # Categories
        valid_cats = {'forms', 'id_cards', 'pictures', 'letters',
                      'utility_bills', 'contract', 'others'}
        inv, null_cat = set(), 0
        for p in pages:
            c = p.get('category')
            if c is None: null_cat += 1
            elif c not in valid_cats: inv.add(c)
        if inv:
            self._warn("Cleaned", f"Non-standard categories: {inv}")
        if null_cat:
            self._warn("Cleaned", f"{null_cat} pages have null category")
        if not inv and not null_cat:
            self._ok("Cleaned", "All pages have valid categories")

        # Dates
        bad_d = sum(1 for p in pages
                    if p.get('resolved_date') and not self.DATE_RE.match(p['resolved_date']))
        if bad_d:
            self._err("Cleaned", f"{bad_d} pages have malformed resolved_date")
        else:
            self._ok("Cleaned", "All resolved_date values are valid YYYY-MM-DD")

    # -----------------------------------------------------------------------
    # Level 3 — Grouped JSON
    # -----------------------------------------------------------------------
    def _check_grouped(self):
        if not self.grouped:
            return
        groups = self.grouped
        n = len(groups)
        if n == 0:
            self._err("Grouped", "Empty groups array")
            return

        all_pages, overlaps, bad_ranges = set(), [], []
        for i, g in enumerate(groups):
            sp, ep = g.get('start_page'), g.get('end_page')
            if sp is None or ep is None:
                self._err("Grouped", f"Group {i}: missing start_page/end_page")
                continue
            if sp > ep:
                bad_ranges.append(i)
                continue
            rng = set(range(sp, ep + 1))
            ov = all_pages & rng
            if ov:
                overlaps.append((i, sorted(ov)[:5]))
            all_pages |= rng

        if bad_ranges:
            self._err("Grouped", f"Groups with start > end: {bad_ranges}")
        else:
            self._ok("Grouped", "All groups have valid ranges (start ≤ end)")

        if overlaps:
            self._err("Grouped", f"Overlapping pages: {overlaps[:5]}")
        else:
            self._ok("Grouped", "No overlapping page assignments")

        # Coverage vs cleaned
        if self.total_pages:
            exp = set(range(self.total_pages))
            miss = exp - all_pages
            ext  = all_pages - exp
            if not miss and not ext:
                self._ok("Grouped", f"All {self.total_pages} pages covered by {n} groups")
            else:
                if miss:
                    self._err("Grouped", f"Pages missing from groups: {sorted(miss)[:20]}"
                               f"{'…' if len(miss) > 20 else ''}")
                if ext:
                    self._err("Grouped", f"Groups reference out-of-range pages: {sorted(ext)[:10]}")

        # Sort order
        sps = [g.get('start_page', 0) for g in groups]
        if sps == sorted(sps):
            self._ok("Grouped", "Groups sorted by start_page")
        else:
            self._warn("Grouped", "Groups NOT sorted by start_page")

        # Tenant match
        names = {t['name'] for t in self.tenants}
        bad = {g.get('primary_tenant') for g in groups} - names - {None}
        if bad:
            self._err("Grouped", f"Groups assigned to unknown tenants: {bad}")
        else:
            self._ok("Grouped", "All group tenants match YAML")

        # folder_path format
        null_fp = sum(1 for g in groups if g.get('folder_path') is None)
        bad_fp = {g.get('folder_path') for g in groups
                  if g.get('folder_path') is not None
                  and not self.FOLDER_RE.match(g.get('folder_path'))}
        if bad_fp:
            self._err("Grouped", f"Invalid folder_path format: {bad_fp}")
        elif null_fp:
            self._warn("Grouped", f"{null_fp} groups have null folder_path")
        else:
            self._ok("Grouped", "All folder_path values use ##_name format")

        # Dates
        bad_d = sum(1 for g in groups for d in g.get('dates', [])
                    if not self.DATE_RE.match(d))
        empty_d = sum(1 for g in groups if not g.get('dates'))
        if bad_d:
            self._err("Grouped", f"{bad_d} group-date entries have invalid format")
        else:
            self._ok("Grouped", "All group dates valid YYYY-MM-DD")
        if empty_d:
            self._warn("Grouped", f"{empty_d} groups have empty dates array")

    # -----------------------------------------------------------------------
    # Level 4 — Routed & Finalized JSON
    # -----------------------------------------------------------------------
    def _check_routed(self):
        if not self.routed:
            return
        summary  = self.routed.get('summary', {})
        per_page = self.routed.get('per_page', [])
        ti = summary.get('total_input_pages', 0)
        to = summary.get('total_output_pages', 0)
        ua = summary.get('unaccounted_pages', [])
        oc = summary.get('output_file_count', 0)

        if ti == to:
            self._ok("Routed", f"Input ({ti}) == Output ({to}) pages")
        else:
            self._err("Routed", f"Page mismatch: {ti} input vs {to} output")

        if not ua:
            self._ok("Routed", "No unaccounted pages")
        else:
            self._err("Routed", f"Unaccounted pages: {ua[:20]}")

        # Cross-check vs cleaned
        if self.total_pages:
            if ti == self.total_pages:
                self._ok("Routed", f"total_input_pages ({ti}) matches cleaned ({self.total_pages})")
            else:
                self._err("Routed", f"total_input_pages ({ti}) ≠ cleaned ({self.total_pages})")

        # per_page coverage
        idxs = [p.get('page_index') for p in per_page]
        exp  = set(range(ti))
        act  = set(idxs)
        miss = exp - act
        dups = [i for i, c in Counter(idxs).items() if c > 1]

        if not miss:
            self._ok("Routed", f"All {ti} page indices present in per_page")
        else:
            self._err("Routed", f"Missing per_page indices: {sorted([m for m in miss if m is not None])[:20]}")
        if not dups:
            self._ok("Routed", "No duplicate page indices in per_page")
        else:
            self._err("Routed", f"Duplicate per_page indices: {sorted([d for d in dups if d is not None])[:10]}")

        # Tenant match
        names = {t['name'] for t in self.tenants}
        bad = {p.get('tenant') for p in per_page} - names - {None}
        if bad:
            self._err("Routed", f"Pages routed to unknown tenants: {bad}")
        else:
            self._ok("Routed", "All routed tenants match YAML")

        # Output files on disk
        missing_files = []
        self._output_files_on_record = set()
        for p in per_page:
            of = p.get('output_file')
            if not of:
                continue
            # Normalize path separators
            of_norm = of.replace('/', os.sep).replace('\\', os.sep)
            self._output_files_on_record.add(of_norm)
            full = self.area_dir / of_norm
            if not full.exists():
                missing_files.append(of)

        checked = len(self._output_files_on_record)
        if not missing_files:
            self._ok("Routed", f"All {checked} referenced output files exist on disk")
        else:
            self._err("Routed", f"{len(missing_files)} output files MISSING from disk:")
            for mf in missing_files[:15]:
                self._err("Routed", f"  → {mf}")
            if len(missing_files) > 15:
                self._err("Routed", f"  … and {len(missing_files) - 15} more")

        # Unique output file count vs summary
        unique_files = {p.get('output_file') for p in per_page if p.get('output_file')}
        if len(unique_files) == oc:
            self._ok("Routed", f"Output file count ({oc}) matches summary")
        else:
            self._warn("Routed",
                        f"Unique output files ({len(unique_files)}) ≠ summary count ({oc})")

    # -----------------------------------------------------------------------
    # Level 4b — Cross-check cleaned ↔ routed
    # -----------------------------------------------------------------------
    def _check_cross_cleaned_routed(self):
        if not self.cleaned or not self.routed:
            return
        per_page = self.routed.get('per_page', [])
        routed_map = {p.get('page_index'): p for p in per_page}
        mismatches = 0
        for cp in self.cleaned:
            idx = cp.get('original_index')
            ct  = cp.get('canonical_tenant')
            rp  = routed_map.get(idx)
            if rp and ct and rp.get('tenant') != ct:
                mismatches += 1
        if mismatches:
            self._warn("Cross-check",
                        f"{mismatches} pages have different tenant in cleaned vs routed")
        else:
            self._ok("Cross-check",
                       "Cleaned canonical_tenant matches routed tenant for all pages")

    # -----------------------------------------------------------------------
    # Level 5 — Filesystem cross-check
    # -----------------------------------------------------------------------
    def _check_filesystem(self):
        if not self.tenants or not self.house_dir:
            return

        names = {t['name'] for t in self.tenants}

        # Tenant folders
        actual = [d for d in self.house_dir.iterdir()
                  if d.is_dir() and d.name != '.source_files' and not d.name.startswith('.')]
        rogue = []
        for d in actual:
            # Folder format: "TenantName ‎(StartYear - EndYear)‎"
            # Try splitting on LRM+( or plain (
            folder_tenant = d.name.split(' \u200e(')[0]
            if folder_tenant not in names:
                folder_tenant = d.name.split(' (')[0]
                if folder_tenant not in names:
                    rogue.append(d.name)

        if rogue:
            self._err("Filesystem", f"Rogue tenant folders (not in YAML): {rogue}")
        else:
            self._ok("Filesystem", f"All {len(actual)} tenant folder(s) match YAML")

        from src.core.utils import sanitize_filename
        # Every YAML tenant has a folder
        for t in self.tenants:
            # Construct expected folder name
            start_yr = str(t.get("start_date", "")).split("-")[0] if t.get("start_date") else "unknown"
            end_yr = str(t.get("end_date", "present"))
            if end_yr != "present":
                end_yr = end_yr.split("-")[0]
            else:
                end_yr = "الآن"
            
            safe_name = sanitize_filename(t['name'])
            expected_folder = f"{safe_name} \u200E({start_yr} - {end_yr})\u200E"
            
            found = any(d.name == expected_folder for d in actual)
            if found:
                self._ok("Filesystem", f"Folder exists and exact match for tenant: {t['name'][:30]}…")
            else:
                # Let's check if it exists but with wrong dates
                wrong_dates = next((d.name for d in actual if d.name.startswith(safe_name)), None)
                if wrong_dates:
                    self._err("Filesystem", f"Folder dates mismatch! Expected '{expected_folder}', found '{wrong_dates}'")
                else:
                    self._err("Filesystem", f"MISSING folder for tenant: {t['name']}")

        # Orphan PDFs
        if self._output_files_on_record:
            orphans = []
            for tf in actual:
                for root, _, files in os.walk(str(tf)):
                    for f in files:
                        if not f.endswith('.pdf') or f.startswith('._'):
                            continue
                        full = Path(root) / f
                        rel = str(full.relative_to(self.area_dir)).replace('/', os.sep)
                        if rel not in self._output_files_on_record:
                            orphans.append(
                                str(full.relative_to(self.area_dir)))

            if not orphans:
                self._ok("Filesystem", "No orphan PDF files (all match routed JSON)")
            else:
                self._warn("Filesystem",
                            f"{len(orphans)} PDF(s) on disk NOT in routed JSON:")
                for o in orphans[:15]:
                    self._warn("Filesystem", f"  → {o}")
                if len(orphans) > 15:
                    self._warn("Filesystem", f"  … and {len(orphans) - 15} more")

        # Category sub-folder structure (every folder under tenant should be ##_name)
        bad_cat_folders = []
        for tf in actual:
            for sub in tf.iterdir():
                if sub.is_dir() and not self.FOLDER_RE.match(sub.name):
                    bad_cat_folders.append(f"{tf.name}/{sub.name}")
        if bad_cat_folders:
            self._warn("Filesystem",
                        f"Non-standard category subfolders: {bad_cat_folders[:10]}")
        else:
            self._ok("Filesystem", "All category subfolders use ##_name format")

    # -----------------------------------------------------------------------
    # Level 6 — Finalized PDF page count
    # -----------------------------------------------------------------------
    def _check_finalized_pdf(self):
        fp = self.house_dir / f"{self.house_id}_finalized.pdf"
        if not fp.exists():
            return

        if not HAS_PDF_READER:
            self._warn("PDF", "pypdf/PyPDF2 not installed — cannot verify page count")
            return

        count = pdf_page_count(fp)
        if count is None:
            self._warn("PDF", "Could not read finalized PDF")
            return

        if self.total_pages:
            if count == self.total_pages:
                self._ok("PDF", f"Finalized PDF pages ({count}) == cleaned ({self.total_pages})")
            else:
                self._err("PDF",
                           f"Finalized PDF pages ({count}) ≠ cleaned ({self.total_pages})")

        if self.routed:
            rt = self.routed.get('summary', {}).get('total_input_pages', 0)
            if count == rt:
                self._ok("PDF", f"Finalized PDF pages ({count}) == routed summary ({rt})")
            else:
                self._err("PDF", f"Finalized PDF pages ({count}) ≠ routed summary ({rt})")

    # -----------------------------------------------------------------------
    # Addition files (if present)
    # -----------------------------------------------------------------------
    def _check_addition_files(self):
        if not self.source_dir:
            return
        add_grouped = self.source_dir / f"{self.house_id}_addition_grouped.json"
        add_report  = self.source_dir / f"{self.house_id}_addition_report.json"

        if not add_grouped.exists() and not add_report.exists():
            return  # No additions processed — that's fine

        self._ok("Addition", "Addition files detected — running addition checks")

        if add_grouped.exists():
            data = load_json(add_grouped)
            names = {t['name'] for t in self.tenants}
            bad_t = {g.get('primary_tenant') for g in data} - names - {None}
            if bad_t:
                self._err("Addition", f"Grouped tenants not in YAML: {bad_t}")
            else:
                self._ok("Addition", f"All {len(data)} addition groups have valid tenants")

            # Page coverage
            all_pg = set()
            for g in data:
                sp, ep = g.get('start_page', 0), g.get('end_page', 0)
                all_pg |= set(range(sp, ep + 1))
            self._ok("Addition", f"Addition groups cover pages: 0–{max(all_pg) if all_pg else 0}")
        else:
            self._warn("Addition", "addition_grouped.json MISSING")

        if add_report.exists():
            rdata = load_json(add_report)
            classified = sum(1 for p in rdata if p.get('status') == 'classified')
            self._ok("Addition", f"Addition report: {classified}/{len(rdata)} pages classified")
        else:
            self._warn("Addition", "addition_report.json MISSING")

    # -----------------------------------------------------------------------
    # Report
    # -----------------------------------------------------------------------
    def print_report(self):
        errs  = len(self.errors)
        warns = len(self.warnings)
        ok    = len(self.passes)
        icon  = "✅" if errs == 0 else "❌"
        label = self.house_dir.name if self.house_dir else self.house_id

        print(f"\n{icon} House {label}")
        print("─" * 60)
        for i in self.issues:
            print(str(i))
        status = "PASS" if errs == 0 else "FAIL"
        print(f"\n  Result: {status} ({ok} passed, {errs} errors, {warns} warnings)")
        return errs == 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Deep verification for batch-processed houses")
    parser.add_argument("area", help="Area name (e.g. 'Safra C')")
    parser.add_argument("--houses", type=str, default=None,
                        help="Comma-separated house IDs (e.g. 508,510,512)")
    parser.add_argument("--areas-root", type=Path, default=Path("D:/Areas"),
                        help="Root directory for areas")

    args = parser.parse_args()
    area_dir = args.areas_root / args.area
    if not area_dir.exists():
        print(f"ERROR: Area directory not found: {area_dir}")
        return 1

    if args.houses:
        house_ids = [h.strip() for h in args.houses.split(',')]
    else:
        seen = set()
        house_ids = []
        for d in sorted(area_dir.iterdir(), key=lambda x: x.name):
            if not d.is_dir() or d.name.startswith('.'):
                continue
            m = re.match(r'^(\d+)', d.name)
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                house_ids.append(m.group(1))
        house_ids.sort(key=int)

    total = len(house_ids)
    print(f"\n{'━' * 60}")
    print(f"  Deep Verification Report for {args.area}")
    print(f"  Houses to verify: {total}")
    print(f"{'━' * 60}")

    passed = failed = 0
    failed_ids = []
    for hid in house_ids:
        v = HouseVerifier(hid, area_dir)
        v.verify()
        if v.print_report():
            passed += 1
        else:
            failed += 1
            failed_ids.append(hid)

    print(f"\n{'━' * 60}")
    print(f"  Summary: {passed} passed, {failed} failed out of {total} houses")
    if failed_ids:
        print(f"  Failed: {', '.join(failed_ids)}")
    print(f"{'━' * 60}\n")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

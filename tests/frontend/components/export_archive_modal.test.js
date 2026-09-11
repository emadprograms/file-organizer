import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Export Archive Options Modal Component', () => {
  const mockProfile = {
    area_id: 'Safra C',
    house_id: '500',
    tenants: [
      {
        id: 1,
        name: 'محمد مبارك',
        is_active: false,
        duration_str_ar: '2020 – 2022',
        category_count: 2,
        document_count: 4
      },
      {
        id: 2,
        name: 'خالد العتيبي',
        is_active: true,
        duration_str_ar: '2022 (مستمر)',
        category_count: 3,
        document_count: 6
      }
    ],
    archive: {
      total_documents: 10,
      total_pages: 25,
      timespan_str_ar: '2020 – 2024',
      categories: [
        { category: '05 - عقود', document_count: 6 },
        { category: '06 - كهرباء وماء', document_count: 4 }
      ]
    }
  };

  beforeEach(() => {
    document.body.innerHTML = `
      <div id="document-list-panel">
        <div class="header">
          <button id="btn-export-house-archive" type="button" title="Export House Archive"></button>
          <button id="btn-manage-tenants" title="House Settings & Tenants"></button>
        </div>
      </div>
      <div id="document-list"></div>
      <div id="stats-badge"></div>

      <!-- House Archive Export Modal -->
      <div id="export-archive-modal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center hidden p-4" tabindex="-1" role="dialog" aria-labelledby="export-archive-modal-title" aria-modal="true">
        <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
          <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/70">
            <h3 class="text-base font-bold text-slate-900 tracking-tight" id="export-archive-modal-title">تصدير الأرشيف • Export Archive</h3>
            <button id="export-archive-modal-close" type="button" class="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer" aria-label="Close">X</button>
          </div>

          <div class="p-6 space-y-5">
            <div>
              <label class="block text-xs font-bold text-slate-800 mb-2">صيغة التصدير • Format</label>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3" id="export-format-options">
                <div id="export-opt-zip" class="export-format-card border-2 border-blue-500 bg-blue-50/50 rounded-xl p-3.5 cursor-pointer transition-all" data-format="zip">
                  <div class="w-2 h-2 rounded-full bg-blue-600" id="export-radio-zip"></div>
                  <div>
                    <div class="font-bold text-sm text-slate-900 leading-snug">ZIP</div>
                    <div class="text-xs font-medium text-slate-500 mt-0.5">مجلدات • Folders</div>
                  </div>
                </div>
                <div id="export-opt-pdf" class="export-format-card border-2 border-slate-200 bg-white rounded-xl p-3.5 cursor-pointer transition-all" data-format="pdf">
                  <div class="w-2 h-2 rounded-full bg-rose-600 hidden" id="export-radio-pdf"></div>
                  <div>
                    <div class="font-bold text-sm text-slate-900 leading-snug">PDF</div>
                    <div class="text-xs font-medium text-slate-500 mt-0.5">تسلسل زمني • Timeline</div>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <label for="export-archive-tenant-select" class="block text-xs font-bold text-slate-800 mb-2">المستأجر • Tenant</label>
              <select id="export-archive-tenant-select" class="w-full px-3.5 py-2.5 text-xs font-medium border border-slate-200 rounded-xl">
                <option value="">🏛️ كامل السجل • All Records</option>
              </select>
            </div>
          </div>

          <div class="px-6 py-3.5 border-t border-slate-100 bg-slate-50/70 flex justify-end items-center gap-2">
            <button id="btn-cancel-export-archive" type="button">Cancel</button>
            <button id="btn-confirm-export-archive" type="button">
              <span id="export-archive-spinner" class="hidden"></span>
              <span id="export-archive-btn-text">⬇️ Download</span>
            </button>
          </div>
        </div>
      </div>
    `;

    window.isStaticMode = false;
    window.showToast = vi.fn();
    window.currentArea = 'Safra C';
    window.currentHouse = '500';

    const scriptCode = fs.readFileSync(
      path.resolve(__dirname, '../../../src/api/static/js/house-profile.js'),
      'utf8'
    );
    eval(scriptCode);
  });

  afterEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  it('renders house profile without archive summary and opens modal on clicking header export button', () => {
    window.renderHouseProfile(mockProfile);

    // Verify digital archive summary is no longer in document-list
    const docList = document.getElementById('document-list');
    expect(docList.textContent).not.toContain('بيانات الأرشيف الرقمي للمنزل');

    // Verify header export button exists
    const exportBtn = document.getElementById('btn-export-house-archive');
    expect(exportBtn).not.toBeNull();

    const modal = document.getElementById('export-archive-modal');
    expect(modal.classList.contains('hidden')).toBe(true);

    exportBtn.click();
    expect(modal.classList.contains('hidden')).toBe(false);

    // Verify streamlined title
    const modalTitle = document.getElementById('export-archive-modal-title');
    expect(modalTitle.textContent).toBe('تصدير الأرشيف • Export Archive');

    // Verify tenant dropdown populated with streamlined default option
    const tenantSelect = document.getElementById('export-archive-tenant-select');
    expect(tenantSelect.options.length).toBe(3); // All tenants + 2 tenants
    expect(tenantSelect.options[0].value).toBe('');
    expect(tenantSelect.options[0].textContent).toContain('كامل السجل • All Records');
    expect(tenantSelect.options[1].value).toBe('1');
    expect(tenantSelect.options[1].textContent).toContain('محمد مبارك');
    expect(tenantSelect.options[2].value).toBe('2');
    expect(tenantSelect.options[2].textContent).toContain('خالد العتيبي');
  });

  it('switches export format between ZIP and PDF', () => {
    window.openExportArchiveModal(mockProfile);

    const optZip = document.getElementById('export-opt-zip');
    const optPdf = document.getElementById('export-opt-pdf');
    const radioZip = document.getElementById('export-radio-zip');
    const radioPdf = document.getElementById('export-radio-pdf');

    // Default is ZIP
    expect(optZip.classList.contains('border-blue-500')).toBe(true);
    expect(radioZip.classList.contains('hidden')).toBe(false);
    expect(radioPdf.classList.contains('hidden')).toBe(true);

    // Switch to PDF
    optPdf.click();
    expect(optPdf.classList.contains('border-rose-500')).toBe(true);
    expect(radioPdf.classList.contains('hidden')).toBe(false);
    expect(radioZip.classList.contains('hidden')).toBe(true);

    // Switch back to ZIP
    optZip.click();
    expect(optZip.classList.contains('border-blue-500')).toBe(true);
    expect(radioZip.classList.contains('hidden')).toBe(false);
    expect(radioPdf.classList.contains('hidden')).toBe(true);
  });

  it('allows tenant dropdown selection', () => {
    window.openExportArchiveModal(mockProfile);

    const tenantSelect = document.getElementById('export-archive-tenant-select');
    tenantSelect.value = '2';
    expect(tenantSelect.value).toBe('2');
  });

  it('triggers download and toast with selected format and tenant', () => {
    window.openExportArchiveModal(mockProfile);

    // Select PDF format
    const optPdf = document.getElementById('export-opt-pdf');
    optPdf.click();

    // Select tenant 2
    const tenantSelect = document.getElementById('export-archive-tenant-select');
    tenantSelect.value = '2';

    // Mock anchor click
    let clickedDownloadUrl = null;
    let clickedDownloadFilename = null;
    const originalAppendChild = document.body.appendChild;
    vi.spyOn(document.body, 'appendChild').mockImplementation((node) => {
      if (node.tagName === 'A') {
        clickedDownloadUrl = node.href;
        clickedDownloadFilename = node.download;
      }
      return originalAppendChild.call(document.body, node);
    });

    const confirmBtn = document.getElementById('btn-confirm-export-archive');
    confirmBtn.click();

    expect(window.showToast).toHaveBeenCalledWith(
      expect.stringContaining('ملف PDF المدمج'),
      'success'
    );
    expect(clickedDownloadUrl).toContain('/api/areas/Safra%20C/houses/500/export-pdf?tenant_id=2');
    expect(clickedDownloadFilename).toBe('archive_Safra_C_500_tenant_2.pdf');
  });

  it('closes modal on close button, cancel button, backdrop click, and Escape key', () => {
    window.openExportArchiveModal(mockProfile);
    const modal = document.getElementById('export-archive-modal');
    expect(modal.classList.contains('hidden')).toBe(false);

    // Close button
    const closeBtn = document.getElementById('export-archive-modal-close');
    closeBtn.click();
    expect(modal.classList.contains('hidden')).toBe(true);

    // Cancel button
    window.openExportArchiveModal(mockProfile);
    expect(modal.classList.contains('hidden')).toBe(false);
    const cancelBtn = document.getElementById('btn-cancel-export-archive');
    cancelBtn.click();
    expect(modal.classList.contains('hidden')).toBe(true);

    // Backdrop click
    window.openExportArchiveModal(mockProfile);
    expect(modal.classList.contains('hidden')).toBe(false);
    modal.click();
    expect(modal.classList.contains('hidden')).toBe(true);

    // Escape key
    window.openExportArchiveModal(mockProfile);
    expect(modal.classList.contains('hidden')).toBe(false);
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(modal.classList.contains('hidden')).toBe(true);
  });
});

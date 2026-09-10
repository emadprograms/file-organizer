import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('House Profile & Header Archive Export', () => {
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
      <div id="export-archive-modal" class="hidden"></div>
    `;

    window.isStaticMode = false;
    window.showToast = vi.fn();
    window.currentArea = 'Area A';
    window.currentHouse = 'House 100';

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

  it('renders house profile without bottom archive summary and opens modal via header export button', () => {
    const mockProfile = {
      area_id: 'Area A',
      house_id: 'House 100',
      tenants: [
        {
          name: 'Tenant A',
          is_active: true,
          duration_str_ar: '2024 (مستمر)',
          category_count: 2,
          document_count: 5
        }
      ],
      archive: {
        total_documents: 10,
        total_pages: 25,
        timespan_str_ar: '2020 – 2024',
        categories: [
          { category: 'عقود', document_count: 6 },
          { category: 'فواتير', document_count: 4 }
        ]
      }
    };

    window.renderHouseProfile(mockProfile);

    // Verify digital archive summary is no longer in document-list
    const docList = document.getElementById('document-list');
    expect(docList.textContent).not.toContain('بيانات الأرشيف الرقمي للمنزل');
    expect(docList.textContent).not.toContain('النطاق الزمني للوثائق');
    expect(docList.textContent).not.toContain('التصنيفات الرئيسية المتوفرة');

    // Verify tenant information is rendered
    expect(docList.textContent).toContain('سجل المستأجرين المتعاقبين');
    expect(docList.textContent).toContain('Tenant A');

    // Verify export button in header exists
    const exportBtn = document.getElementById('btn-export-house-archive');
    expect(exportBtn).not.toBeNull();

    // Verify clicking opens modal
    const modal = document.getElementById('export-archive-modal');
    expect(modal.classList.contains('hidden')).toBe(true);
    exportBtn.click();
    expect(modal.classList.contains('hidden')).toBe(false);
  });

  it('supports legacy btn-export-house-zip if present for backward compatibility', () => {
    const legacyBtn = document.createElement('button');
    legacyBtn.id = 'btn-export-house-zip';
    document.body.appendChild(legacyBtn);

    const mockProfile = {
      area_id: 'Area A',
      house_id: 'House 100',
      tenants: []
    };

    window.renderHouseProfile(mockProfile);

    const modal = document.getElementById('export-archive-modal');
    expect(modal.classList.contains('hidden')).toBe(true);
    legacyBtn.click();
    expect(modal.classList.contains('hidden')).toBe(false);
  });
});

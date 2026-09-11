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

  it('renders streamlined intuitive tenancy register cards without wordy boilerplate', () => {
    const mockProfile = {
      area_id: 'Area A',
      house_id: 'House 100',
      tenants: [
        {
          name: 'فواز خليل الطارش',
          is_active: true,
          duration_str_ar: 'بدء الإيجار 2020 (مستمر منذ 7 سنوات)',
          category_count: 10,
          document_count: 25
        },
        {
          name: 'عادل عبد الرحيم جاسم',
          is_active: false,
          duration_str_ar: 'فترة الإيجار: 2000 – 2002 (سنتان)',
          category_count: 7,
          document_count: 10
        }
      ],
      archive: {
        total_documents: 35,
        total_pages: 50,
        timespan_str_ar: '2000 – 2020',
        categories: []
      }
    };

    window.renderHouseProfile(mockProfile);

    const docList = document.getElementById('document-list');
    // Header should contain the section title and clean count badge (without writing 'مستأجر')
    expect(docList.textContent).toContain('سجل المستأجرين المتعاقبين');
    expect(docList.textContent).not.toContain('2 مستأجر');

    // Should NOT contain wordy boilerplate strings
    expect(docList.textContent).not.toContain('استعراض المجلدات');
    expect(docList.textContent).not.toContain('بدء الإيجار');
    expect(docList.textContent).not.toContain('فترة الإيجار:');
    expect(docList.textContent).not.toContain('المستأجر الحالي');
    expect(docList.textContent).not.toContain('مستأجر سابق');

    // Should contain intuitive badges and stripped clean duration
    expect(docList.textContent).toContain('حالي');
    expect(docList.textContent).toContain('سابق');
    expect(docList.textContent).toContain('2020 (مستمر منذ 7 سنوات)');
    expect(docList.textContent).toContain('2000 – 2002 (سنتان)');

    // Should contain document and category counts
    expect(docList.textContent).toContain('25');
    expect(docList.textContent).toContain('10');

    // Should have tenant cards with proper data attributes and blue styling for active tenant
    const cards = docList.querySelectorAll('.tenant-profile-card');
    expect(cards.length).toBe(2);
    expect(cards[0].dataset.tenantName).toBe('فواز خليل الطارش');
    expect(cards[0].className).toContain('border-blue-200');
    expect(cards[0].className).toContain('bg-blue-50/40');
    expect(cards[0].innerHTML).toContain('border-blue-300 bg-blue-100 text-blue-800');
    expect(cards[1].dataset.tenantName).toBe('عادل عبد الرحيم جاسم');
    expect(cards[1].className).toContain('border-slate-200');
  });
});


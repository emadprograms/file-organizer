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

    // Verify tenant information is rendered directly without redundant sub-header
    expect(docList.textContent).not.toContain('سجل المستأجرين المتعاقبين');
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
    // Redundant tenancy register sub-header bar and count badge should NOT be rendered
    expect(docList.textContent).not.toContain('سجل المستأجرين المتعاقبين');
    expect(document.querySelector('.tenants-count-badge')).toBeNull();

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

    // Should have tenant cards with proper data attributes and amber styling for 7-year active tenant
    const cards = docList.querySelectorAll('.tenant-profile-card');
    expect(cards.length).toBe(2);
    expect(cards[0].dataset.tenantName).toBe('فواز خليل الطارش');
    expect(cards[0].className).toContain('border-amber-200');
    expect(cards[0].className).toContain('bg-amber-50/40');
    expect(cards[0].innerHTML).toContain('border-amber-300 bg-amber-100 text-amber-800');
    expect(cards[1].dataset.tenantName).toBe('عادل عبد الرحيم جاسم');
    expect(cards[1].className).toContain('border-slate-200');
  });

  it('renders green for <5 years, yellow for 5-10 years, and red for >10 years in tenant selection', () => {
    const mockProfile = {
      area_id: 'Area A',
      house_id: 'House 100',
      tenants: [
        {
          name: 'مستأجر قصير',
          is_active: true,
          duration_str_ar: 'بدء الإيجار 2024 (مستمر منذ سنتين)',
          category_count: 1,
          document_count: 2
        },
        {
          name: 'مستأجر متوسط',
          is_active: true,
          duration_str_ar: 'بدء الإيجار 2018 (مستمر منذ 8 سنوات)',
          category_count: 3,
          document_count: 6
        },
        {
          name: 'مستأجر طويل',
          is_active: true,
          duration_str_ar: 'بدء الإيجار 2010 (مستمر منذ 16 سنة)',
          category_count: 5,
          document_count: 12
        }
      ],
      archive: { total_documents: 20, total_pages: 20, categories: [] }
    };

    window.renderHouseProfile(mockProfile);

    const cards = document.querySelectorAll('.tenant-profile-card');
    expect(cards.length).toBe(3);

    // 1. < 5 Years: Emerald Green
    expect(cards[0].className).toContain('border-emerald-200');
    expect(cards[0].className).toContain('bg-emerald-50/40');
    expect(cards[0].innerHTML).toContain('border-emerald-300 bg-emerald-100 text-emerald-800');
    expect(cards[0].innerHTML).toContain('bg-emerald-500');

    // 2. 5–10 Years: Amber Yellow
    expect(cards[1].className).toContain('border-amber-200');
    expect(cards[1].className).toContain('bg-amber-50/40');
    expect(cards[1].innerHTML).toContain('border-amber-300 bg-amber-100 text-amber-800');
    expect(cards[1].innerHTML).toContain('bg-amber-500');

    // 3. > 10 Years: Rose Red
    expect(cards[2].className).toContain('border-rose-200');
    expect(cards[2].className).toContain('bg-rose-50/40');
    expect(cards[2].innerHTML).toContain('border-rose-300 bg-rose-100 text-rose-800');
    expect(cards[2].innerHTML).toContain('bg-rose-500');
  });

  it('omits redundant tenancy register sub-header and count badge in tenant selection area (QCK-19)', () => {
    // 1. Multiple tenants (3 tenants)
    const mockProfile3 = {
      area_id: 'Area A',
      house_id: 'House 100',
      tenants: [
        { name: 'Tenant 1', is_active: true, duration_category: 'short', category_count: 3, document_count: 10 },
        { name: 'Tenant 2', is_active: false, duration_category: 'short', category_count: 2, document_count: 4 },
        { name: 'Tenant 3', is_active: false, duration_category: 'short', category_count: 1, document_count: 2 }
      ],
      archive: { total_documents: 16, total_pages: 20, categories: [] }
    };

    window.renderHouseProfile(mockProfile3);

    const docList = document.getElementById('document-list');
    // Header text and count badge should be absent
    expect(docList.textContent).not.toContain('سجل المستأجرين المتعاقبين');
    expect(document.querySelector('.tenants-count-badge')).toBeNull();

    // Tenant cards should be directly present and populated
    const cards = document.querySelectorAll('.tenant-profile-card');
    expect(cards.length).toBe(3);
    expect(cards[0].textContent).toContain('Tenant 1');
    expect(cards[1].textContent).toContain('Tenant 2');
    expect(cards[2].textContent).toContain('Tenant 3');

    // 2. Single tenant
    const mockProfile1 = {
      area_id: 'Area A',
      house_id: 'House 100',
      tenants: [
        { name: 'Tenant 1', is_active: true, duration_category: 'short', category_count: 1, document_count: 1 }
      ],
      archive: { total_documents: 1, total_pages: 1, categories: [] }
    };

    window.renderHouseProfile(mockProfile1);

    expect(docList.textContent).not.toContain('سجل المستأجرين المتعاقبين');
    expect(document.querySelector('.tenants-count-badge')).toBeNull();
    const singleCards = document.querySelectorAll('.tenant-profile-card');
    expect(singleCards.length).toBe(1);
    expect(singleCards[0].textContent).toContain('Tenant 1');
  });
});



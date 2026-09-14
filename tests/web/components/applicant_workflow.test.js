import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Applicant Integrated Workflows Suite (Phase 113)', () => {
  const htmlContent = fs.readFileSync(
    path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/index.html'),
    'utf8'
  );
  const houseProfileCode = fs.readFileSync(
    path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/house-profile.js'),
    'utf8'
  );
  const tenantManagerCode = fs.readFileSync(
    path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/tenant-manager.js'),
    'utf8'
  );
  const categoriesViewCode = fs.readFileSync(
    path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/categories-view.js'),
    'utf8'
  );
  const timelineViewCode = fs.readFileSync(
    path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/timeline-view.js'),
    'utf8'
  );
  const commandPaletteCode = fs.readFileSync(
    path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/command-palette.js'),
    'utf8'
  );

  beforeEach(() => {
    document.body.innerHTML = htmlContent;

    window.isStaticMode = false;
    window.showToast = vi.fn();
    global.showToast = window.showToast;
    window.currentArea = 'Safra C';
    window.currentHouse = '500';
    global.currentArea = 'Safra C';
    global.currentHouse = '500';
    global.currentTenant = null;
    global.currentTimeline = [];
    global.globalTreeData = [];
    global.currentCategories = [];

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => []
    });

    eval(houseProfileCode);
    eval(tenantManagerCode);
    eval(categoriesViewCode);
    eval(timelineViewCode);
    eval(commandPaletteCode);
  });

  afterEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  it('Test 1: House Profile renders segregated sections with distinctive applicant styling, 📋 متقدم (لم يسكن), application date, document count, and notes', () => {
    const mockProfile = {
      area_id: 'Safra C',
      house_id: '500',
      tenants: [
        {
          name: 'فهد المنصور',
          is_active: true,
          is_resident: 1,
          duration_str_ar: 'بدء الإيجار 2021 (مستمر)',
          category_count: 3,
          document_count: 12
        },
        {
          name: 'خالد عبد الله',
          is_active: false,
          is_resident: 0,
          start_date: '2024-03-15',
          notes: 'ألغي التخصيص لعدم المراجعة',
          category_count: 2,
          document_count: 4
        },
        {
          name: 'سالم جديد',
          is_active: false,
          is_resident: 0,
          start_date: null,
          category_count: 0,
          document_count: 0
        }
      ],
      archive: { total_documents: 16, total_pages: 20, categories: [] }
    };

    window.renderHouseProfile(mockProfile);

    const docList = document.getElementById('document-list');
    expect(docList).not.toBeNull();

    // Segregated sections
    const residentsSection = docList.querySelector('.residents-section');
    expect(residentsSection).not.toBeNull();
    expect(residentsSection.textContent).toContain('المستأجرون');
    expect(residentsSection.textContent).toContain('فهد المنصور');

    const applicantsSection = docList.querySelector('.applicants-section');
    expect(applicantsSection).not.toBeNull();
    expect(applicantsSection.textContent).toContain('المتقدمون');

    // Distinctive applicant styling
    const applicantCards = applicantsSection.querySelectorAll('.applicant-profile-card');
    expect(applicantCards.length).toBe(2);
    const applicantCard = applicantCards[0];
    expect(applicantCard.className).toContain('border-dashed');
    expect(applicantCard.className).toContain('border-purple-200');
    expect(applicantCard.className).toContain('bg-purple-50/20');

    // Badge: 📋 متقدم (لم يسكن)
    const badge = applicantCard.querySelector('.applicant-badge');
    expect(badge).not.toBeNull();
    expect(badge.textContent).toContain('📋 متقدم (لم يسكن)');

    // Application date / First document appearance
    expect(applicantCard.textContent).toContain('أول وثيقة: 2024-03-15');

    // Applicant with no documents renders waiting message
    expect(applicantCards[1].textContent).toContain('بانتظار أول وثيقة (تلقائي)');

    // Document count
    expect(applicantCard.textContent).toContain('4');

    // Notes badge should be removed
    const notesEl = applicantCard.querySelector('.applicant-notes');
    expect(notesEl).toBeNull();
  });

  it('Test 2: Applicant card click updates window.location.hash to #/area/.../house/.../tenant/{houseId}_{applicantName}', () => {
    const mockProfile = {
      area_id: 'Safra C',
      house_id: '500',
      tenants: [
        {
          name: 'سالم المقيم',
          is_active: true,
          is_resident: 1,
          duration_str_ar: 'بدء الإيجار 2020 (مستمر)',
          category_count: 2,
          document_count: 5
        },
        {
          name: 'خالد عبد الله',
          is_active: false,
          is_resident: 0,
          start_date: '2024-03-15',
          notes: 'ألغي التخصيص لعدم المراجعة',
          category_count: 1,
          document_count: 2
        }
      ],
      archive: { total_documents: 7, total_pages: 10, categories: [] }
    };

    window.renderHouseProfile(mockProfile);

    const applicantCard = document.querySelector('.applicant-profile-card');
    expect(applicantCard).not.toBeNull();

    window.location.hash = '';
    applicantCard.click();

    const expectedHash = `#/area/${encodeURIComponent('Safra C')}/house/500/tenant/${encodeURIComponent('500_خالد عبد الله')}`;
    expect(window.location.hash).toBe(expectedHash);
  });

  it('Test 3: House settings modal toggles between Resident and Applicant: selecting Applicant unchecks and disables Present, disables End Date, sets application date title, and saving sends is_resident: 0 and notes in POST payload', async () => {
    const manageBtn = document.getElementById('btn-manage-tenants');
    manageBtn.click();

    const modal = document.getElementById('tenant-modal');
    expect(modal.classList.contains('hidden')).toBe(false);

    const addBtn = document.getElementById('btn-add-tenant-row');
    addBtn.click();

    const row = document.querySelector('.tenant-row');
    const typeSelect = row.querySelector('.tenant-type-select');
    const presentCheck = row.querySelector('.tenant-present-check');
    const endInput = row.querySelector('.tenant-end-input');
    const startInput = row.querySelector('.tenant-start-input');
    const nameInput = row.querySelector('.tenant-name-input');
    expect(row.querySelector('.tenant-notes-input')).toBeNull();

    // Default is resident
    expect(typeSelect.value).toBe('resident');
    expect(presentCheck.checked).toBe(true);
    expect(endInput.disabled).toBe(true);

    // Switch to applicant
    typeSelect.value = 'applicant';
    typeSelect.dispatchEvent(new Event('change'));

    // Verify unchecks and disables present
    expect(presentCheck.checked).toBe(false);
    expect(presentCheck.disabled).toBe(true);
    expect(presentCheck.classList.contains('opacity-30')).toBe(true);

    // Verify disables end date
    expect(endInput.disabled).toBe(true);
    expect(endInput.value).toBe('');
    expect(endInput.title).toBe('N/A (لم يسكن)');

    // Verify application date title
    expect(startInput.title).toBe('Application / Order Date • تاريخ الطلب/التخصيص');

    // Fill applicant data
    nameInput.value = 'خالد عبد الله';
    startInput.value = '2024-03-15';

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'success', reallocated_count: 0, tenants_count: 1 })
    });

    const saveBtn = document.getElementById('tenant-modal-save');
    saveBtn.click();

    await new Promise(r => setTimeout(r, 20));

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/areas/Safra%20C/houses/500/tenants',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenants: [
            {
              id: null,
              name: 'خالد عبد الله',
              start_date: '2024-03-15',
              end_date: null,
              house_id: '500',
              is_resident: 0,
              notes: null
            }
          ],
          reallocate: true
        })
      })
    );
  });

  it('Test 4: Batch Move/Copy modal tenant options badge applicants with 📋 ${name} (متقدم - لم يسكن)', async () => {
    // 1. Check helper formatting function
    const label = window.formatBatchTenantLabel({ name: 'سارة خالد', is_resident: 0 });
    expect(label).toBe('📋 سارة خالد (متقدم - لم يسكن)');

    const residentLabel = window.formatBatchTenantLabel({ name: 'أحمد المقيم', is_resident: 1 });
    expect(residentLabel).toBe('أحمد المقيم (المستأجر الحالي)');
    expect(residentLabel).not.toContain('متقدم');

    // 2. Setup mock categories and selected document for move/copy
    global.currentCategories = [
      {
        tenant: 'سارة خالد',
        name: '05 - عقود',
        document_count: 1,
        documents: [
          { vault_id: 'doc001', brief_arabic_title: 'طلب تخصيص', is_manual: 0, tenant_id: 88 }
        ]
      }
    ];
    window.toggleDocSelection('doc001', true);

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [
        { id: 88, name: 'سارة خالد', start_date: '2024-01-01', is_resident: 0 },
        { id: 89, name: 'أحمد المقيم', start_date: '2020-01-01', is_resident: 1, is_active: true }
      ]
    });

    // Populate Move modal select
    await window.populateBatchTenantSelect('batch-move-tenant-select');
    const moveSelect = document.getElementById('batch-move-tenant-select');
    const applicantOptMove = Array.from(moveSelect.options).find(o => o.value === '88');
    expect(applicantOptMove).toBeDefined();
    expect(applicantOptMove.textContent).toBe('📋 سارة خالد (متقدم - لم يسكن)');

    const residentOptMove = Array.from(moveSelect.options).find(o => o.value === '89');
    expect(residentOptMove).toBeDefined();
    expect(residentOptMove.textContent).toBe('أحمد المقيم (المستأجر الحالي)');

    // Populate Copy modal select
    await window.populateBatchTenantSelect('batch-copy-tenant-select');
    const copySelect = document.getElementById('batch-copy-tenant-select');
    const applicantOptCopy = Array.from(copySelect.options).find(o => o.value === '88');
    expect(applicantOptCopy).toBeDefined();
    expect(applicantOptCopy.textContent).toBe('📋 سارة خالد (متقدم - لم يسكن)');
  });

  it('Test 5: Timeline document card displays purple applicant badge with clipboard bullet when document belongs to applicant (is_resident === 0)', () => {
    const mockTimeline = [
      {
        vault_id: 'vault_app_01',
        primary_tenant: 'Applicant Person',
        is_resident: 0,
        dates: ['2023-05-15'],
        brief_arabic_title: 'طلب تخصيص سكن',
        category: '05 - عقود',
        is_manual: 0,
        is_timeline_visible: 1
      },
      {
        vault_id: 'vault_res_02',
        primary_tenant: 'Resident Person',
        is_resident: 1,
        dates: ['2021-02-10'],
        brief_arabic_title: 'عقد إيجار المنزل',
        category: '05 - عقود',
        is_manual: 0,
        is_timeline_visible: 1
      }
    ];

    window.renderTimeline(mockTimeline);

    const docList = document.getElementById('document-list');
    const appCard = docList.querySelector('[data-vault-id="vault_app_01"]');
    expect(appCard).not.toBeNull();

    // Purple applicant badge
    const appBadge = appCard.querySelector('span[title="متقدم (لم يسكن)"]');
    expect(appBadge).not.toBeNull();
    expect(appBadge.className).toContain('bg-purple-50');
    expect(appBadge.className).toContain('text-purple-700');
    expect(appBadge.className).toContain('border-purple-200');
    expect(appBadge.textContent).toContain('Applicant Person');

    // Clipboard bullet (purple rounded-full indicator)
    const bullet = appBadge.querySelector('.bg-purple-500.rounded-full');
    expect(bullet).not.toBeNull();

    // Resident card should have standard slate badge
    const resCard = docList.querySelector('[data-vault-id="vault_res_02"]');
    expect(resCard).not.toBeNull();
    const resBadge = resCard.querySelector('span.bg-slate-100');
    expect(resBadge).not.toBeNull();
    expect(resBadge.textContent).toContain('Resident Person');
    expect(resCard.querySelector('span[title="متقدم (لم يسكن)"]')).toBeNull();
  });

  it('Test 6: Command palette renders applicant search result with purple styling, 📋 clipboard avatar, and applicant badge', () => {
    const results = [
      {
        id: '500_applicant_person',
        type: 'tenant',
        title: 'Applicant Person',
        subtitle: 'House 500 • Safra C',
        url: '/#/area/Safra C/house/500',
        is_resident: 0
      }
    ];

    window.renderSearchResults(results);

    const item = document.querySelector('.command-palette-result-item');
    expect(item).not.toBeNull();
    expect(item.className).toContain('hover:bg-purple-50/70');
    expect(item.className).toContain('hover:border-purple-300');

    // Clipboard avatar
    const avatar = item.querySelector('.w-7');
    expect(avatar).not.toBeNull();
    expect(avatar.textContent.trim()).toBe('📋');
    expect(avatar.className).toContain('text-purple-600');
    expect(avatar.className).toContain('bg-purple-50');

    // Applicant badge
    const badge = item.querySelector('span.text-\\[10px\\]');
    expect(badge).not.toBeNull();
    expect(badge.textContent).toBe('📋 متقدم (لم يسكن)');
    expect(badge.className).toContain('text-purple-700');
    expect(badge.className).toContain('bg-purple-50');
    expect(badge.className).toContain('border-purple-300');
  });
});

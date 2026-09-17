import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Area Grid House Card Component - Scrollbar for > 3 Tenancies', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="area-grid-panel" class="flex">
        <h2 id="grid-area-title">Safra C</h2>
        <div id="grid-area-stats"></div>
        <div id="grid-tenure-legend"></div>
        <div id="area-grid-container"></div>
      </div>
    `;

    delete global.globalTreeData;
    delete window.globalTreeData;
    global.currentArea = 'Safra C';
    global.currentHouse = null;
    global.currentTenant = null;
    global.window.location = { hash: '' };

    const scriptCode = fs.readFileSync(
      path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/area-grid.js'),
      'utf8'
    );
    eval(scriptCode);
  });

  afterEach(() => {
    delete global.globalTreeData;
    delete window.globalTreeData;
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  it('does NOT add scrollbar classes when a house card has 3 or fewer tenants', () => {
    const areaNode = {
      name: 'Safra C',
      children: [
        {
          id: '101',
          name: '101 - Three Tenants House',
          duration_category: 'short',
          total_documents: 5,
          children: [
            { type: 'tenant', name: 'Tenant 1', subtitle: '2020 - 2021' },
            { type: 'tenant', name: 'Tenant 2', subtitle: '2021 - 2022' },
            { type: 'tenant', name: 'Tenant 3', subtitle: '2022 - Present' }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    const card = document.querySelector('.house-card[data-house-id="101"]');
    expect(card).not.toBeNull();

    const tenantsSection = card.querySelector('.tenants-overview-section');
    expect(tenantsSection).not.toBeNull();
    expect(tenantsSection.classList.contains('overflow-y-auto')).toBe(false);
    expect(tenantsSection.classList.contains('max-h-[118px]')).toBe(false);
  });

  it('adds scrollbar classes (max-h-[118px] overflow-y-auto pr-1) when a house card has more than 3 tenants', () => {
    const areaNode = {
      name: 'Safra C',
      children: [
        {
          id: '102',
          name: '102 - Four Tenants House',
          duration_category: 'medium',
          total_documents: 12,
          children: [
            { type: 'tenant', name: 'Tenant 1', subtitle: '2015 - 2017' },
            { type: 'tenant', name: 'Tenant 2', subtitle: '2017 - 2019' },
            { type: 'tenant', name: 'Tenant 3', subtitle: '2019 - 2022' },
            { type: 'tenant', name: 'Tenant 4', subtitle: '2022 - Present' }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    const card = document.querySelector('.house-card[data-house-id="102"]');
    expect(card).not.toBeNull();

    const tenantsSection = card.querySelector('.tenants-overview-section');
    expect(tenantsSection).not.toBeNull();
    expect(tenantsSection.classList.contains('overflow-y-auto')).toBe(true);
    expect(tenantsSection.classList.contains('max-h-[118px]')).toBe(true);
    expect(tenantsSection.classList.contains('pr-1')).toBe(true);
  });

  it('stops click propagation when clicking on the scrollbar track/thumb to prevent navigating away', () => {
    const areaNode = {
      name: 'Safra C',
      children: [
        {
          id: '103',
          name: '103 - Many Tenants House',
          duration_category: 'long',
          total_documents: 15,
          children: [
            { type: 'tenant', name: 'Tenant 1', subtitle: '2010 - 2013' },
            { type: 'tenant', name: 'Tenant 2', subtitle: '2013 - 2016' },
            { type: 'tenant', name: 'Tenant 3', subtitle: '2016 - 2020' },
            { type: 'tenant', name: 'Tenant 4', subtitle: '2020 - 2023' },
            { type: 'tenant', name: 'Tenant 5', subtitle: '2023 - Present' }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    const card = document.querySelector('.house-card[data-house-id="103"]');
    const tenantsSection = card.querySelector('.tenants-overview-section');

    // Simulate clicking on the scrollbar (offsetX > clientWidth)
    Object.defineProperty(tenantsSection, 'clientWidth', { value: 200, configurable: true });

    let cardClicked = false;
    card.onclick = () => { cardClicked = true; };

    const scrollbarClickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
    Object.defineProperty(scrollbarClickEvent, 'offsetX', { value: 205 });

    tenantsSection.dispatchEvent(scrollbarClickEvent);
    expect(cardClicked).toBe(false);

    // Normal click inside tenant content (offsetX <= clientWidth) bubbles to card
    const normalClickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
    Object.defineProperty(normalClickEvent, 'offsetX', { value: 50 });

    tenantsSection.dispatchEvent(normalClickEvent);
    expect(cardClicked).toBe(true);
  });

  it('renders grey border and Vacant badge for vacant house with past tenants (e.g. house 538)', () => {
    const areaNode = {
      name: 'Safra C',
      children: [
        {
          id: '538',
          name: '538 - Vacant House',
          duration_category: null,
          current_tenant: null,
          total_documents: 3,
          children: [
            { type: 'tenant', name: 'فهد المغادر', subtitle: '2024' }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    const card = document.querySelector('.house-card[data-house-id="538"]');
    expect(card).not.toBeNull();
    expect(card.classList.contains('border-l-slate-300')).toBe(true);
    expect(card.classList.contains('border-l-rose-500')).toBe(false);
    expect(card.classList.contains('border-l-amber-500')).toBe(false);
    expect(card.classList.contains('border-l-emerald-500')).toBe(false);

    const badge = card.querySelector('.tenure-badge');
    expect(badge).not.toBeNull();
    expect(badge.textContent.trim()).toBe('Vacant');
    expect(badge.classList.contains('bg-slate-100')).toBe(true);

    const tenantItem = card.querySelector('.tenant-overview-item');
    expect(tenantItem).not.toBeNull();
    expect(tenantItem.classList.contains('bg-slate-50')).toBe(true);
    expect(tenantItem.classList.contains('bg-rose-50/70')).toBe(false);

    const tenantIcon = tenantItem.querySelector('span[title="Past Tenant"]');
    expect(tenantIcon).not.toBeNull();
    expect(tenantItem.querySelector('span[title="Residing Tenant"]')).toBeNull();
  });

  it('differentiates resident tenants and applicants in header count and cards (e.g. 4 tenants and 1 applicant)', () => {
    const areaNode = {
      name: 'Safra C',
      children: [
        {
          id: '104',
          name: '104 - Mixed House',
          duration_category: 'medium',
          total_documents: 8,
          children: [
            { type: 'tenant', name: 'Tenant 1', is_resident: 1, subtitle: '2018 - 2020' },
            { type: 'tenant', name: 'Tenant 2', is_resident: 1, subtitle: '2020 - 2022' },
            { type: 'tenant', name: 'Tenant 3', is_resident: 1, subtitle: '2022 - 2024' },
            { type: 'tenant', name: 'Tenant 4', is_resident: 1, subtitle: '2024 - Present' },
            { type: 'tenant', name: 'Applicant 1', is_resident: 0, subtitle: '2025' }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    const card = document.querySelector('.house-card[data-house-id="104"]');
    expect(card).not.toBeNull();

    const countBadge = card.querySelector('.tenants-count');
    expect(countBadge).not.toBeNull();
    expect(countBadge.textContent.trim()).toBe('4 Tenants • 1 Applicant');

    const applicantIcon = card.querySelector('span[title="Applicant • متقدم"]');
    expect(applicantIcon).not.toBeNull();
    expect(applicantIcon.classList.contains('text-purple-700')).toBe(true);

    const applicantItem = applicantIcon.closest('.tenant-overview-item');
    expect(applicantItem).not.toBeNull();
    expect(applicantItem.classList.contains('border-purple-200/60')).toBe(true);
    expect(applicantItem.classList.contains('bg-purple-50/30')).toBe(true);

    // Verify it is NOT labeled as Past Tenant
    const pastTenantIcon = applicantItem.querySelector('span[title="Past Tenant"]');
    expect(pastTenantIcon).toBeNull();
    expect(applicantItem.textContent).not.toContain('Past Tenant');

    // Verify tenure text for applicant has متقدم
    const tenureText = applicantItem.querySelector('.tenure-text');
    expect(tenureText).not.toBeNull();
    expect(tenureText.textContent.trim()).toBe('2025 • متقدم');
  });

  it('formats header count correctly for single tenant and single applicant, applicant-only, and zero counts', () => {
    const areaNode = {
      name: 'Safra C',
      children: [
        {
          id: '201',
          name: '201 - One of Each',
          duration_category: 'short',
          children: [
            { type: 'tenant', name: 'Res 1', is_resident: 1, subtitle: '2024' },
            { type: 'tenant', name: 'App 1', is_resident: 0, subtitle: '' }
          ]
        },
        {
          id: '202',
          name: '202 - Applicant Only',
          duration_category: 'short',
          children: [
            { type: 'tenant', name: 'App 1', is_resident: 0 },
            { type: 'tenant', name: 'App 2', is_resident: 0 }
          ]
        },
        {
          id: '203',
          name: '203 - Single Applicant Only',
          duration_category: 'short',
          children: [
            { type: 'tenant', name: 'App 1', is_resident: 0 }
          ]
        },
        {
          id: '204',
          name: '204 - Zero Tenants',
          duration_category: 'short',
          children: []
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    expect(document.querySelector('.house-card[data-house-id="201"] .tenants-count').textContent.trim())
      .toBe('1 Tenant • 1 Applicant');
    expect(document.querySelector('.house-card[data-house-id="202"] .tenants-count').textContent.trim())
      .toBe('2 Applicants');
    expect(document.querySelector('.house-card[data-house-id="203"] .tenants-count').textContent.trim())
      .toBe('1 Applicant');
    expect(document.querySelector('.house-card[data-house-id="204"] .tenants-count').textContent.trim())
      .toBe('0 Tenants');
  });

  it('accurately reflects document-anchored start date and updated duration category when document date is changed (e.g. house 616)', () => {
    // Initial state: House 616 with document from 1990 (>10 yrs, red)
    const initialAreaNode = {
      name: 'Safra C',
      children: [
        {
          id: '616',
          name: '616 - Historical House',
          duration_category: 'long',
          current_tenant: 'سعيد القحطاني',
          total_documents: 10,
          children: [
            {
              type: 'tenant',
              name: 'سعيد القحطاني',
              subtitle: '1990 - Present',
              duration_category: 'long',
              is_resident: 1
            }
          ]
        }
      ]
    };

    window.renderAreaGrid(initialAreaNode);

    const cardInitial = document.querySelector('.house-card[data-house-id="616"]');
    expect(cardInitial).not.toBeNull();
    expect(cardInitial.classList.contains('border-l-rose-500')).toBe(true);
    expect(cardInitial.querySelector('.tenure-badge').textContent.trim()).toBe('> 10 Yrs');
    expect(cardInitial.querySelector('.tenure-text').textContent.trim()).toBe('1990 - Present');

    // After updating the starting document date to 2024 (<5 yrs, green)
    const updatedAreaNode = {
      name: 'Safra C',
      children: [
        {
          id: '616',
          name: '616 - Historical House',
          duration_category: 'short',
          current_tenant: 'سعيد القحطاني',
          total_documents: 10,
          children: [
            {
              type: 'tenant',
              name: 'سعيد القحطاني',
              subtitle: '2024 - Present',
              duration_category: 'short',
              is_resident: 1
            }
          ]
        }
      ]
    };

    window.renderAreaGrid(updatedAreaNode);

    const cardUpdated = document.querySelector('.house-card[data-house-id="616"]');
    expect(cardUpdated).not.toBeNull();
    expect(cardUpdated.classList.contains('border-l-emerald-500')).toBe(true);
    expect(cardUpdated.classList.contains('border-l-rose-500')).toBe(false);
    expect(cardUpdated.querySelector('.tenure-badge').textContent.trim()).toBe('< 5 Yrs');
    expect(cardUpdated.querySelector('.tenure-text').textContent.trim()).toBe('2024 - Present');
  });

  it('loadAreaGrid fetches fresh tree data and re-renders house cards with updated start date', async () => {
    const updatedTree = [
      {
        id: 'area_Safra C',
        name: 'Safra C',
        children: [
          {
            id: '616',
            name: '616',
            duration_category: 'short',
            current_tenant: 'سعيد القحطاني',
            total_documents: 5,
            children: [
              {
                type: 'tenant',
                name: 'سعيد القحطاني',
                subtitle: '2024 - Present',
                duration_category: 'short',
                is_resident: 1
              }
            ]
          }
        ]
      }
    ];

    global.loadTree = vi.fn().mockImplementation(async () => {
      global.globalTreeData = updatedTree;
      window.globalTreeData = updatedTree;
    });

    await window.loadAreaGrid('Safra C');

    expect(global.loadTree).toHaveBeenCalled();
    const card = document.querySelector('.house-card[data-house-id="616"]');
    expect(card).not.toBeNull();
    expect(card.querySelector('.tenure-text').textContent.trim()).toBe('2024 - Present');
    expect(card.querySelector('.tenure-badge').textContent.trim()).toBe('< 5 Yrs');
  });

  it('ensures applicants NEVER appear before resident tenants even if listed first in house.children', () => {
    const areaNode = {
      name: 'Safra C',
      children: [
        {
          id: '777',
          name: '777 - Mixed House',
          duration_category: 'short',
          current_tenant: 'Current Resident',
          total_documents: 4,
          children: [
            {
              type: 'tenant',
              name: 'Applicant First',
              subtitle: 'Applicant',
              is_resident: 0
            },
            {
              type: 'tenant',
              name: 'Past Resident',
              subtitle: '2020 - 2022',
              is_resident: 1
            },
            {
              type: 'tenant',
              name: 'Current Resident',
              subtitle: '2022 - Present',
              is_resident: 1,
              is_active: true
            },
            {
              type: 'tenant',
              name: 'Another Applicant',
              subtitle: 'Applicant',
              is_resident: 0
            }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    const card = document.querySelector('.house-card[data-house-id="777"]');
    expect(card).not.toBeNull();

    const tenantNames = Array.from(card.querySelectorAll('.tenant-name')).map(el => el.textContent.trim());
    expect(tenantNames).toEqual([
      'Past Resident',
      'Current Resident',
      'Applicant First',
      'Another Applicant'
    ]);

    // Verify all resident rows appear before any applicant rows in DOM
    const renderedCards = Array.from(card.querySelectorAll('.tenants-overview-section > div > div'));
    const residentIndices = [];
    const applicantIndices = [];
    renderedCards.forEach((row, idx) => {
      if (row.innerHTML.includes('Applicant • متقدم')) {
        applicantIndices.push(idx);
      } else {
        residentIndices.push(idx);
      }
    });

    expect(residentIndices.length).toBe(2);
    expect(applicantIndices.length).toBe(2);
    expect(Math.max(...residentIndices)).toBeLessThan(Math.min(...applicantIndices));
  });
});

describe('Area Grid House Card Component - Integrity Compliance Badge Synchronization', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="area-grid-panel" class="flex">
        <h2 id="grid-area-title">Safra D</h2>
        <div id="grid-area-stats"></div>
        <div id="grid-tenure-legend"></div>
        <div id="area-grid-container"></div>
      </div>
    `;

    delete global.globalTreeData;
    delete window.globalTreeData;
    global.currentArea = 'Safra D';
    global.currentHouse = null;
    global.currentTenant = null;
    global.window.location = { hash: '' };

    const scriptCode = fs.readFileSync(
      path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/area-grid.js'),
      'utf8'
    );
    eval(scriptCode);
  });

  afterEach(() => {
    delete global.globalTreeData;
    delete window.globalTreeData;
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  it('evaluates house as complete 5/5 when Category 07 (Rent Deduction) is present with clean category name', () => {
    const areaNode = {
      name: 'Safra D',
      children: [
        {
          id: '504',
          name: '504 - Ahmed House',
          duration_category: 'short',
          total_documents: 10,
          active_tenant_category_counts: {
            'بيانات شخصية': 1,
            'أمر تخصيص': 1,
            'محضر تسليم مفتاح': 1,
            'عقود': 1,
            'استقطاع إيجار': 1
          },
          children: [
            { type: 'tenant', name: 'أحمد يوسف المريسل', is_resident: 1, is_active: true }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    const card = document.querySelector('.house-card[data-house-id="504"]');
    expect(card).not.toBeNull();

    // Verify 5/5 badge is rendered and no warning text is present
    expect(card.textContent).toContain('5/5');
    expect(card.textContent).not.toContain('ناقص');
    expect(card.textContent).not.toContain('استقطاع إيجار');
  });

  it('evaluates house as complete 5/5 when Category 07 is present with prefix format (07 - استقطاع إيجار)', () => {
    const areaNode = {
      name: 'Safra D',
      children: [
        {
          id: '504',
          name: '504 - Ahmed House',
          duration_category: 'short',
          total_documents: 10,
          active_tenant_category_counts: {
            '02 - بيانات شخصية': 1,
            '03 - أمر تخصيص': 1,
            '04 - محضر تسليم مفتاح': 1,
            '05 - عقود': 1,
            '07 - استقطاع إيجار': 1
          },
          children: [
            { type: 'tenant', name: 'أحمد يوسف المريسل', is_resident: 1, is_active: true }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    const card = document.querySelector('.house-card[data-house-id="504"]');
    expect(card).not.toBeNull();
    expect(card.textContent).toContain('5/5');
    expect(card.textContent).not.toContain('ناقص');
  });

  it('updates card from 4/5 warning to 5/5 complete when globalTreeData receives fresh active_tenant_category_counts', () => {
    // 1. Initial render where Category 07 was missing
    const areaNode = {
      name: 'Safra D',
      children: [
        {
          id: '504',
          name: '504 - Ahmed House',
          duration_category: 'short',
          total_documents: 9,
          active_tenant_category_counts: {
            'بيانات شخصية': 1,
            'أمر تخصيص': 1,
            'محضر تسليم مفتاح': 1,
            'عقود': 1
          },
          children: [
            { type: 'tenant', name: 'أحمد يوسف المريسل', is_resident: 1, is_active: true }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);
    let card = document.querySelector('.house-card[data-house-id="504"]');
    expect(card.textContent).toContain('4/5');
    expect(card.textContent).toContain('استقطاع إيجار');

    // 2. Global tree is updated after moving the document (e.g. via window.loadTree())
    const updatedAreaNode = {
      name: 'Safra D',
      children: [
        {
          id: '504',
          name: '504 - Ahmed House',
          duration_category: 'short',
          total_documents: 10,
          active_tenant_category_counts: {
            'بيانات شخصية': 1,
            'أمر تخصيص': 1,
            'محضر تسليم مفتاح': 1,
            'عقود': 1,
            'استقطاع إيجار': 1
          },
          children: [
            { type: 'tenant', name: 'أحمد يوسف المريسل', is_resident: 1, is_active: true }
          ]
        }
      ]
    };
    window.globalTreeData = [updatedAreaNode];

    // 3. User navigates back to grid
    window.selectAreaGrid(areaNode);

    card = document.querySelector('.house-card[data-house-id="504"]');
    expect(card.textContent).toContain('5/5');
    expect(card.textContent).not.toContain('ناقص');
  });

  it('ensures house number never truncates in crowded card header and delegates truncation to tenant count', () => {
    const areaNode = {
      name: 'Crowded Area',
      children: [
        {
          id: '552',
          name: '552 - Extra Long House Name Number Identifier',
          duration_category: 'short',
          total_documents: 8,
          active_tenant_category_counts: {
            'بيانات شخصية': 1
          },
          children: [
            { type: 'tenant', name: 'Tenant 1', is_resident: 1, is_active: true },
            { type: 'tenant', name: 'Applicant 1', is_resident: 0, is_active: false }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    const card = document.querySelector('.house-card[data-house-id="552"]');
    expect(card).not.toBeNull();

    const titleEl = card.querySelector('h3');
    expect(titleEl).not.toBeNull();
    // House number element MUST have flex-shrink-0 and whitespace-nowrap so it never shrinks into ellipsis
    expect(titleEl.classList.contains('flex-shrink-0')).toBe(true);
    expect(titleEl.classList.contains('whitespace-nowrap')).toBe(true);
    expect(titleEl.classList.contains('truncate')).toBe(false);
    expect(titleEl.textContent).toContain('🏠 552 - Extra Long House Name Number Identifier');

    // Tenant count badge MUST have truncate and min-w-0, and NOT flex-shrink-0, so it absorbs shrinkage
    const tenantCountBadge = card.querySelector('.tenants-count');
    expect(tenantCountBadge).not.toBeNull();
    expect(tenantCountBadge.classList.contains('truncate')).toBe(true);
    expect(tenantCountBadge.classList.contains('min-w-0')).toBe(true);
    expect(tenantCountBadge.classList.contains('flex-shrink-0')).toBe(false);
    expect(tenantCountBadge.getAttribute('title')).toBe('1 Tenant • 1 Applicant');
  });
});



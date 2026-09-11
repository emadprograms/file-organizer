import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('+ Add House Modal Component (Phase 107)', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="area-grid-panel" class="flex">
        <h2 id="grid-area-title">Safra C</h2>
        <div id="grid-area-stats">1 Houses</div>
        <button id="open-add-house-modal-btn" type="button">+ إضافة منزل جديد</button>
        <div id="area-grid-container"></div>
      </div>

      <div id="add-house-modal" class="hidden" tabindex="-1">
        <h3 id="add-house-modal-title">+ إضافة منزل جديد / Add House</h3>
        <p id="add-house-subtitle"></p>
        <button id="add-house-close" type="button">X</button>
        <form id="add-house-form">
          <select id="add-house-area-select" required></select>
          <input id="add-house-id-input" type="text" required />
          <input id="add-house-tenant-name-input" type="text" />
          <input id="add-house-tenant-date-input" type="date" />
          <div id="add-house-status" class="hidden"></div>
        </form>
        <button id="btn-add-house-cancel" type="button">Cancel</button>
        <button id="btn-add-house-submit" type="button">
          <span id="add-house-spinner" class="hidden"></span>
          <span id="add-house-submit-text">إضافة المنزل / Create House</span>
        </button>
      </div>
    `;

    global.currentArea = 'Safra C';
    global.globalTreeData = [
      {
        id: 'Safra C',
        name: 'Safra C',
        type: 'area',
        children: [
          { id: '500', name: '500', type: 'house', children: [] }
        ]
      },
      {
        id: 'Al-Malqa',
        name: 'Al-Malqa',
        type: 'area',
        children: []
      }
    ];

    window.showToast = vi.fn();
    window.loadTree = vi.fn().mockResolvedValue(undefined);

    const scriptCode = fs.readFileSync(
      path.resolve(__dirname, '../../../src/api/static/js/area-grid.js'),
      'utf8'
    );
    eval(scriptCode);
  });

  afterEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  it('renders dashed add house grid card at the end of house list in renderAreaGrid and opens modal on click', () => {
    const areaNode = global.globalTreeData[0]; // Safra C with 1 house
    window.renderAreaGrid(areaNode);

    const container = document.getElementById('area-grid-container');
    const houseCards = container.querySelectorAll('.house-card');
    expect(houseCards.length).toBe(1);

    const addCard = container.querySelector('#add-house-grid-card');
    expect(addCard).not.toBeNull();
    expect(addCard.classList.contains('border-dashed')).toBe(true);
    expect(addCard.textContent).toContain('إضافة منزل جديد');
    expect(addCard.textContent).toContain('Add New House');
    expect(addCard.textContent).not.toContain('انقر هنا لتسجيل منزل جديد في هذه المنطقة');

    // Click on dashed card
    const modal = document.getElementById('add-house-modal');
    expect(modal.classList.contains('hidden')).toBe(true);
    addCard.click();
    expect(modal.classList.contains('hidden')).toBe(false);

    const areaSelect = document.getElementById('add-house-area-select');
    expect(areaSelect.value).toBe('Safra C');
  });

  it('renders dashed add house grid card when area has 0 houses and supports keyboard activation', () => {
    const emptyAreaNode = global.globalTreeData[1]; // Al-Malqa with 0 houses
    window.renderAreaGrid(emptyAreaNode);

    const container = document.getElementById('area-grid-container');
    const houseCards = container.querySelectorAll('.house-card');
    expect(houseCards.length).toBe(0);

    const addCard = container.querySelector('#add-house-grid-card');
    expect(addCard).not.toBeNull();
    expect(addCard.classList.contains('border-dashed')).toBe(true);

    const modal = document.getElementById('add-house-modal');
    expect(modal.classList.contains('hidden')).toBe(true);

    // Keyboard activation (Enter key)
    addCard.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    expect(modal.classList.contains('hidden')).toBe(false);

    const areaSelect = document.getElementById('add-house-area-select');
    expect(areaSelect.value).toBe('Al-Malqa');
  });

  it('opens add house modal and populates area select from globalTreeData with currentArea selected', () => {
    const openBtn = document.getElementById('open-add-house-modal-btn');
    const modal = document.getElementById('add-house-modal');
    const areaSelect = document.getElementById('add-house-area-select');
    const dateInput = document.getElementById('add-house-tenant-date-input');

    expect(modal.classList.contains('hidden')).toBe(true);

    openBtn.click();

    expect(modal.classList.contains('hidden')).toBe(false);
    expect(areaSelect.options.length).toBe(2);
    expect(areaSelect.value).toBe('Safra C');
    expect(dateInput.value).not.toBe('');
  });

  it('closes modal when clicking cancel button, close button, backdrop, or pressing Escape', () => {
    window.openAddHouseModal('Safra C');
    const modal = document.getElementById('add-house-modal');
    expect(modal.classList.contains('hidden')).toBe(false);

    // Cancel button
    const cancelBtn = document.getElementById('btn-add-house-cancel');
    cancelBtn.click();
    expect(modal.classList.contains('hidden')).toBe(true);

    // Close button
    window.openAddHouseModal('Safra C');
    const closeBtn = document.getElementById('add-house-close');
    closeBtn.click();
    expect(modal.classList.contains('hidden')).toBe(true);

    // Escape key
    window.openAddHouseModal('Safra C');
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(modal.classList.contains('hidden')).toBe(true);

    // Backdrop click
    window.openAddHouseModal('Safra C');
    modal.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(modal.classList.contains('hidden')).toBe(true);
  });

  it('validates house_id is required before submission', async () => {
    window.openAddHouseModal('Safra C');
    const idInput = document.getElementById('add-house-id-input');
    const statusEl = document.getElementById('add-house-status');

    idInput.value = '   ';
    await window.handleAddHouseSubmit();

    expect(statusEl.classList.contains('hidden')).toBe(false);
    expect(statusEl.textContent).toContain('House number or name is required');
    expect(window.showToast).not.toHaveBeenCalled();
  });

  it('submits valid house creation, shows toast, and refreshes grid', async () => {
    window.openAddHouseModal('Safra C');
    const areaSelect = document.getElementById('add-house-area-select');
    const idInput = document.getElementById('add-house-id-input');
    const tenantInput = document.getElementById('add-house-tenant-name-input');
    const dateInput = document.getElementById('add-house-tenant-date-input');
    const modal = document.getElementById('add-house-modal');

    areaSelect.value = 'Safra C';
    idInput.value = '515';
    tenantInput.value = 'عبد الله خالد';
    dateInput.value = '2024-06-01';

    const mockResponse = {
      status: 'success',
      area_id: 'Safra C',
      house_id: '515',
      tenant_id: 2,
      message: "House '515' registered successfully in area 'Safra C'."
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    await window.handleAddHouseSubmit();

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/areas/Safra%20C/houses',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          house_id: '515',
          area_id: 'Safra C',
          initial_tenant_name: 'عبد الله خالد',
          start_date: '2024-06-01',
        })
      })
    );

    expect(modal.classList.contains('hidden')).toBe(true);
    expect(window.showToast).toHaveBeenCalledWith('تمت إضافة المنزل بنجاح', 'success');
    expect(window.loadTree).toHaveBeenCalled();
  });

  it('displays error in status element when API returns conflict or failure', async () => {
    window.openAddHouseModal('Safra C');
    const idInput = document.getElementById('add-house-id-input');
    const statusEl = document.getElementById('add-house-status');
    const submitBtn = document.getElementById('btn-add-house-submit');

    idInput.value = '500';

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ detail: "House '500' already exists in area 'Safra C'." })
    });

    await window.handleAddHouseSubmit();

    expect(statusEl.classList.contains('hidden')).toBe(false);
    expect(statusEl.textContent).toContain("House '500' already exists");
    expect(submitBtn.disabled).toBe(false);
  });

  it('verifies submit button inside add house modal has clean text without redundant plus symbols or brackets', () => {
    const submitText = document.getElementById('add-house-submit-text');
    expect(submitText.textContent).toBe('إضافة المنزل / Create House');
    expect(submitText.textContent).not.toContain('+');
    expect(submitText.textContent).not.toContain('[');
    expect(submitText.textContent).not.toContain(']');
  });
});

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('House Settings Modal Layout & UX (QCK-22)', () => {
  const htmlContent = fs.readFileSync(
    path.resolve(__dirname, '../../../src/api/static/index.html'),
    'utf8'
  );

  beforeEach(() => {
    // Set up DOM from real index.html snippet
    document.body.innerHTML = `
      <button id="btn-manage-tenants" type="button" title="House Settings • إعدادات المنزل">Settings</button>

      <div id="tenant-modal" class="hidden">
        <div id="tenant-modal-header">
          <h3 id="tenant-modal-title">House Settings • إعدادات المنزل</h3>
          <p id="tenant-modal-subtitle">Manage tenants, timelines, and house configuration.</p>
          <button id="tenant-modal-close">Close</button>
        </div>
        <div id="tenant-modal-body">
          <div id="tenants-section">
            <button id="btn-add-tenant-row" type="button">Add Tenant</button>
            <div id="tenant-modal-rows"></div>
            <div id="tenant-modal-status" class="hidden"></div>
          </div>
          <div id="danger-zone-section">
            <button id="btn-open-delete-house" type="button">Delete House</button>
          </div>
        </div>
        <div id="tenant-modal-footer">
          <button id="tenant-modal-cancel">Cancel</button>
          <button id="tenant-modal-save"><span id="tenant-save-btn-text">Save</span></button>
        </div>
      </div>
    `;

    global.currentArea = 'Safra C';
    global.currentHouse = '500';
    global.currentTenant = null;
    global.currentTimeline = [];
    global.globalTreeData = [];

    window.showToast = vi.fn();
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => []
    });

    const scriptCode = fs.readFileSync(
      path.resolve(__dirname, '../../../src/api/static/js/tenant-manager.js'),
      'utf8'
    );
    eval(scriptCode);
  });

  afterEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  it('verifies index.html has removed the massive top notes banner and contains streamlined clean sections', () => {
    expect(htmlContent).not.toContain('Reallocation Priority Rules:');
    expect(htmlContent).not.toContain('Letters explicitly addressed to a specific tenant remain assigned');
    expect(htmlContent).toContain('House Settings');
    expect(htmlContent).toContain('Tenants • المستأجرون');
    expect(htmlContent).toContain('Danger Zone • منطقة الخطر');
    expect(htmlContent).toContain('Delete House • حذف المنزل');
    expect(htmlContent).toContain('حذف هذا المنزل نهائياً مع كافة المستأجرين والوثائق والملفات من القرص');
    expect(htmlContent).not.toContain('Delete House...');
    expect(htmlContent).not.toContain('Permanently delete this house');
    expect(htmlContent).not.toContain('Delete House Permanently');
    expect(htmlContent).not.toContain('Add Tenant • إضافة مستأجر');
    expect(htmlContent).not.toContain('Save Changes • حفظ التغييرات');
  });

  it('updates modal title and subtitle with house context and useful instructions when opened', () => {
    const manageBtn = document.getElementById('btn-manage-tenants');
    const modal = document.getElementById('tenant-modal');
    const title = document.getElementById('tenant-modal-title');
    const subtitle = document.getElementById('tenant-modal-subtitle');

    expect(modal.classList.contains('hidden')).toBe(true);

    manageBtn.click();

    expect(modal.classList.contains('hidden')).toBe(false);
    expect(title.textContent).toBe('House Settings: 500 (Safra C)');
    expect(subtitle.textContent).toBe('Configure tenant residency timelines and house configuration');
  });

  it('renders tenant rows with sequential numbering and proper table alignment classes', () => {
    const addBtn = document.getElementById('btn-add-tenant-row');
    const rowsContainer = document.getElementById('tenant-modal-rows');

    addBtn.click();
    addBtn.click();
    addBtn.click();

    const rows = rowsContainer.querySelectorAll('.tenant-row');
    expect(rows.length).toBe(3);

    const rowNumbers = Array.from(rows).map(r => r.querySelector('.tenant-row-number')?.textContent);
    expect(rowNumbers).toEqual(['1', '2', '3']);

    // Check presence of structured column classes
    expect(rows[0].classList.contains('sm:grid')).toBe(true);
    expect(rows[0].classList.contains('sm:grid-cols-12')).toBe(true);
  });

  it('re-indexes row numbers sequentially when a row is removed', () => {
    const addBtn = document.getElementById('btn-add-tenant-row');
    const rowsContainer = document.getElementById('tenant-modal-rows');

    addBtn.click();
    addBtn.click();
    addBtn.click();

    let rows = rowsContainer.querySelectorAll('.tenant-row');
    expect(rows.length).toBe(3);

    // Remove middle row (index 1)
    const removeBtn = rows[1].querySelector('.btn-remove-row');
    removeBtn.click();

    rows = rowsContainer.querySelectorAll('.tenant-row');
    expect(rows.length).toBe(2);

    const renumbered = Array.from(rows).map(r => r.querySelector('.tenant-row-number')?.textContent);
    expect(renumbered).toEqual(['1', '2']);
  });

  it('toggles Present checkbox and disables/enables end date input', () => {
    const addBtn = document.getElementById('btn-add-tenant-row');
    const rowsContainer = document.getElementById('tenant-modal-rows');

    addBtn.click();
    const row = rowsContainer.querySelector('.tenant-row');
    const presentCheck = row.querySelector('.tenant-present-check');
    const endInput = row.querySelector('.tenant-end-input');

    // Initially present
    expect(presentCheck.checked).toBe(true);
    expect(endInput.disabled).toBe(true);

    // Toggle off present
    presentCheck.checked = false;
    presentCheck.dispatchEvent(new Event('change'));

    expect(endInput.disabled).toBe(false);

    // Enter date then re-check present
    endInput.value = '2025-12-31';
    presentCheck.checked = true;
    presentCheck.dispatchEvent(new Event('change'));

    expect(endInput.disabled).toBe(true);
    expect(endInput.value).toBe('');
  });

  it('enforces only one tenant can be marked present at a time', () => {
    const addBtn = document.getElementById('btn-add-tenant-row');
    const rowsContainer = document.getElementById('tenant-modal-rows');

    // Row 1
    addBtn.click();
    const rows1 = rowsContainer.querySelectorAll('.tenant-row');
    const check1 = rows1[0].querySelector('.tenant-present-check');
    const end1 = rows1[0].querySelector('.tenant-end-input');
    expect(check1.checked).toBe(true);
    expect(end1.disabled).toBe(true);

    // Row 2 added while Row 1 is present -> Row 2 should NOT be present
    addBtn.click();
    const rows2 = rowsContainer.querySelectorAll('.tenant-row');
    const check2 = rows2[1].querySelector('.tenant-present-check');
    const end2 = rows2[1].querySelector('.tenant-end-input');
    expect(check2.checked).toBe(false);
    expect(end2.disabled).toBe(false);
    expect(check1.checked).toBe(true);

    // Check Row 2 -> Row 1 should automatically be unchecked and its end date enabled
    check2.checked = true;
    check2.dispatchEvent(new Event('change'));

    expect(check2.checked).toBe(true);
    expect(end2.disabled).toBe(true);
    expect(check1.checked).toBe(false);
    expect(end1.disabled).toBe(false);

    // Check Row 1 -> Row 2 should automatically be unchecked
    check1.checked = true;
    check1.dispatchEvent(new Event('change'));

    expect(check1.checked).toBe(true);
    expect(end1.disabled).toBe(true);
    expect(check2.checked).toBe(false);
    expect(end2.disabled).toBe(false);
  });
});

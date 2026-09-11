import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Delete House Feature in Settings Modal Danger Zone', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="area-grid-panel" class="hidden"></div>
      <div id="document-viewer-panel" class="flex"></div>
      <div id="document-list">Some docs</div>
      <button id="back-to-grid-btn" class="flex"></button>
      <button id="tab-back-to-tenants" class="flex"></button>
      <div id="current-house-title">500</div>
      <div id="stats-badge">Stats</div>

      <button id="btn-manage-tenants">Settings</button>

      <!-- Tenant Modal with Danger Zone -->
      <div id="tenant-modal" class="hidden">
        <h3 id="tenant-modal-title">House Settings & Tenants</h3>
        <div id="tenant-modal-rows"></div>
        <button id="btn-add-tenant-row">Add Tenant</button>
        <div id="tenant-modal-status" class="hidden"></div>
        
        <!-- Danger Zone -->
        <div id="danger-zone">
          <button id="btn-open-delete-house" type="button">Delete House</button>
        </div>

        <button id="tenant-modal-cancel">Cancel</button>
        <button id="tenant-modal-save">
          <span id="tenant-save-btn-text">Save</span>
        </button>
        <button id="tenant-modal-close">Close</button>
      </div>

      <!-- Delete House Modal -->
      <div id="delete-house-modal" class="hidden">
        <h3 id="delete-house-title">Delete House</h3>
        <button id="delete-house-modal-close">X</button>
        <strong id="delete-house-target-name"></strong>
        <span id="delete-house-phrase-hint"></span>
        <input id="delete-house-confirm-input" type="text" />
        <div id="delete-house-status" class="hidden"></div>
        <button id="delete-house-cancel">Cancel</button>
        <button id="delete-house-confirm-btn" disabled>
          <span id="delete-house-spinner" class="hidden"></span>
          <span id="delete-house-btn-text">Delete Permanently</span>
        </button>
      </div>
    `;

    global.currentArea = 'Safra C';
    global.currentHouse = '500';
    global.currentTenant = 'Tenant 1';
    global.currentTimeline = [];
    global.globalTreeData = [
      {
        id: 'Safra C',
        name: 'Safra C',
        children: [{ id: '500', name: '500' }]
      }
    ];

    window.showToast = vi.fn();
    window.loadTree = vi.fn().mockResolvedValue(undefined);
    window.renderSidebar = vi.fn();
    window.selectAreaGrid = vi.fn();

    global.fetch = vi.fn();

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

  it('renders Danger Zone trigger button and opens confirmation modal with populated house details', () => {
    const openBtn = document.getElementById('btn-open-delete-house');
    const deleteModal = document.getElementById('delete-house-modal');
    const targetName = document.getElementById('delete-house-target-name');
    const phraseHint = document.getElementById('delete-house-phrase-hint');
    const confirmInput = document.getElementById('delete-house-confirm-input');
    const confirmBtn = document.getElementById('delete-house-confirm-btn');

    expect(deleteModal.classList.contains('hidden')).toBe(true);

    openBtn.click();

    expect(deleteModal.classList.contains('hidden')).toBe(false);
    expect(targetName.textContent).toBe('500');
    expect(phraseHint.textContent).toBe('delete 500');
    expect(confirmInput.value).toBe('');
    expect(confirmBtn.disabled).toBe(true);
  });

  it('enables the delete confirm button only when the exact confirmation phrase is typed', () => {
    window.openDeleteHouseModal();
    const confirmInput = document.getElementById('delete-house-confirm-input');
    const confirmBtn = document.getElementById('delete-house-confirm-btn');

    expect(confirmBtn.disabled).toBe(true);

    // Mismatched input
    confirmInput.value = 'delete';
    confirmInput.dispatchEvent(new Event('input'));
    expect(confirmBtn.disabled).toBe(true);

    confirmInput.value = 'delete 501';
    confirmInput.dispatchEvent(new Event('input'));
    expect(confirmBtn.disabled).toBe(true);

    // Exact input (case-insensitive)
    confirmInput.value = 'Delete 500';
    confirmInput.dispatchEvent(new Event('input'));
    expect(confirmBtn.disabled).toBe(false);

    // With trailing space
    confirmInput.value = 'delete 500 ';
    confirmInput.dispatchEvent(new Event('input'));
    expect(confirmBtn.disabled).toBe(false);
  });

  it('closes delete house modal on cancel or close button click', () => {
    window.openDeleteHouseModal();
    const deleteModal = document.getElementById('delete-house-modal');
    const cancelBtn = document.getElementById('delete-house-cancel');
    const closeBtn = document.getElementById('delete-house-modal-close');

    expect(deleteModal.classList.contains('hidden')).toBe(false);

    cancelBtn.click();
    expect(deleteModal.classList.contains('hidden')).toBe(true);

    window.openDeleteHouseModal();
    expect(deleteModal.classList.contains('hidden')).toBe(false);

    closeBtn.click();
    expect(deleteModal.classList.contains('hidden')).toBe(true);
  });

  it('executes DELETE API call, resets selection, routes back to Area Grid, and triggers refresh', async () => {
    window.openDeleteHouseModal();
    const confirmInput = document.getElementById('delete-house-confirm-input');
    const confirmBtn = document.getElementById('delete-house-confirm-btn');
    const deleteModal = document.getElementById('delete-house-modal');
    const areaGridPanel = document.getElementById('area-grid-panel');

    confirmInput.value = 'delete 500';
    confirmInput.dispatchEvent(new Event('input'));
    expect(confirmBtn.disabled).toBe(false);

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'success', message: "House '500' deleted successfully." })
    });

    confirmBtn.click();

    // Await microtasks
    await new Promise(r => setTimeout(r, 10));

    expect(global.fetch).toHaveBeenCalledWith('/api/areas/Safra%20C/houses/500', {
      method: 'DELETE'
    });

    expect(deleteModal.classList.contains('hidden')).toBe(true);
    expect(global.currentHouse).toBeNull();
    expect(global.currentTenant).toBeNull();
    expect(areaGridPanel.classList.contains('hidden')).toBe(false);
    expect(window.loadTree).toHaveBeenCalled();
    expect(window.renderSidebar).toHaveBeenCalled();
    expect(window.selectAreaGrid).toHaveBeenCalled();
    expect(window.showToast).toHaveBeenCalledWith(
      expect.stringContaining('500'),
      'success'
    );
  });

  it('displays error message inside modal and keeps confirm button active when deletion fails', async () => {
    window.openDeleteHouseModal();
    const confirmInput = document.getElementById('delete-house-confirm-input');
    const confirmBtn = document.getElementById('delete-house-confirm-btn');
    const statusEl = document.getElementById('delete-house-status');

    confirmInput.value = 'delete 500';
    confirmInput.dispatchEvent(new Event('input'));

    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: 'Database locked' })
    });

    confirmBtn.click();

    await new Promise(r => setTimeout(r, 10));

    expect(statusEl.classList.contains('hidden')).toBe(false);
    expect(statusEl.textContent).toContain('Database locked');
    expect(confirmBtn.disabled).toBe(false);
  });
});

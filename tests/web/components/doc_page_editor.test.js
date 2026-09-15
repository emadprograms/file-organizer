import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Document Page Editor (Split, Delete, Extract, Reorder)', () => {
  const indexHtml = fs.readFileSync(
    path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/index.html'),
    'utf8'
  );

  beforeEach(() => {
    // Set up DOM from index.html elements relevant to doc page editor
    document.body.innerHTML = `
      <div id="document-viewer-panel">
        <button id="viewer-edit-pages-btn" type="button"></button>
      </div>

      <div id="quick-look-modal">
        <button id="quick-look-edit-pages" type="button"></button>
      </div>

      <div id="doc-action-modal">
        <button id="btn-doc-edit-pages" type="button"></button>
      </div>

      <!-- Page Editor Modal -->
      <div id="doc-page-editor-modal" class="hidden" style="display: none;">
        <h3 id="page-editor-title"></h3>
        <p id="page-editor-subtitle"></p>
        <span id="page-editor-count-badge"></span>
        <button id="page-editor-close-btn"></button>
        <div id="page-editor-loading" class="hidden"></div>
        <div id="page-editor-grid"></div>

        <button id="btn-editor-select-all"></button>
        <button id="btn-editor-deselect-all"></button>
        <span id="page-editor-selected-count"></span>
        <button id="btn-editor-delete-selected" disabled><span class="btn-text">Delete Selected</span></button>
        <button id="btn-editor-extract-selected" disabled><span class="btn-text">Separate & Move...</span></button>
      </div>

      <!-- Extract Submodal -->
      <div id="extract-pages-submodal" class="hidden" style="display: none;">
        <span id="extract-pages-count-badge"></span>
        <select id="extract-target-category"></select>
        <div id="extract-custom-cat-container" class="hidden">
          <input id="extract-custom-cat-input" type="text" />
        </div>
        <select id="extract-target-tenant"></select>
        <input id="extract-target-title" type="text" />
        <input id="extract-target-date" type="date" />
        <input id="extract-target-notes" type="text" />
        <button id="btn-extract-cancel"></button>
        <button id="btn-extract-confirm"><span id="btn-extract-confirm-text">Confirm</span></button>
      </div>
    `;

    global.currentArea = 'Safra C';
    global.currentHouse = '101';
    global.showToast = vi.fn();

    // Load doc-page-editor.js
    const scriptCode = fs.readFileSync(
      path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-page-editor.js'),
      'utf8'
    );
    eval(scriptCode);
  });

  afterEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('verifies index.html contains all necessary editor modal containers and trigger buttons', () => {
    expect(indexHtml).toContain('id="viewer-edit-pages-btn"');
    expect(indexHtml).toContain('id="quick-look-edit-pages"');
    expect(indexHtml).toContain('id="btn-doc-edit-pages"');
    expect(indexHtml).toContain('id="doc-page-editor-modal"');
    expect(indexHtml).toContain('id="page-editor-title"');
    expect(indexHtml).toContain('id="page-editor-grid"');
    expect(indexHtml).toContain('id="btn-editor-select-all"');
    expect(indexHtml).toContain('id="btn-editor-delete-selected"');
    expect(indexHtml).toContain('id="btn-editor-extract-selected"');
    expect(indexHtml).toContain('id="extract-pages-submodal"');
    expect(indexHtml).toContain('id="extract-target-category"');
    expect(indexHtml).toContain('src="js/doc-page-editor.js');
  });

  it('opens page editor and renders page cards with 1-tap action buttons', async () => {
    const mockDoc = {
      vault_id: 'doc_12345',
      brief_arabic_title: 'خطاب صيانة متعدد الصفحات',
      category: '10 - صيانة',
      tenant: 'أحمد سالم',
      page_count: 3
    };

    await window.openPageEditor(mockDoc);

    const modal = document.getElementById('doc-page-editor-modal');
    const title = document.getElementById('page-editor-title');
    const grid = document.getElementById('page-editor-grid');

    expect(modal.classList.contains('hidden')).toBe(false);
    expect(title.textContent).toBe('خطاب صيانة متعدد الصفحات');

    const cards = grid.querySelectorAll('.page-editor-card');
    expect(cards.length).toBe(3);

    // Verify 1-tap delete button and move buttons exist on each card for tablet touch use
    const firstCard = cards[0];
    expect(firstCard.querySelector('.btn-card-delete')).not.toBeNull();
    expect(firstCard.querySelector('.btn-move-left')).not.toBeNull();
    expect(firstCard.querySelector('.btn-move-right')).not.toBeNull();
    expect(firstCard.querySelector('.card-checkbox-pill')).not.toBeNull();
  });

  it('toggles page selection and updates action buttons state and count badge', async () => {
    const mockDoc = {
      vault_id: 'doc_12345',
      brief_arabic_title: 'وثيقة مجمعة',
      category: '10 - صيانة',
      page_count: 4
    };

    await window.openPageEditor(mockDoc);

    const cards = document.querySelectorAll('.page-editor-card');
    const btnDelete = document.getElementById('btn-editor-delete-selected');
    const btnExtract = document.getElementById('btn-editor-extract-selected');
    const countBadge = document.getElementById('page-editor-selected-count');

    // Initially disabled
    expect(btnDelete.disabled).toBe(true);
    expect(btnExtract.disabled).toBe(true);

    // Click card 1 to select
    cards[0].click();
    expect(btnDelete.disabled).toBe(false);
    expect(btnExtract.disabled).toBe(false);
    expect(countBadge.textContent).toContain('1 selected');

    // Click card 2 to select
    cards[1].click();
    expect(countBadge.textContent).toContain('2 selected');

    // Click card 1 again to deselect
    cards[0].click();
    expect(countBadge.textContent).toContain('1 selected');

    // Deselect all
    document.getElementById('btn-editor-deselect-all').click();
    expect(btnDelete.disabled).toBe(true);
    expect(btnExtract.disabled).toBe(true);
    expect(countBadge.textContent).toBe('');

    // Select all
    document.getElementById('btn-editor-select-all').click();
    expect(btnDelete.disabled).toBe(false);
    expect(btnExtract.disabled).toBe(false);
    expect(countBadge.textContent).toContain('4 selected');
  });

  it('opens extract submodal with default categories and handles custom category', async () => {
    const mockDoc = {
      vault_id: 'doc_bundle_99',
      brief_arabic_title: 'وثيقة مجمعة',
      category: '10 - صيانة',
      date: '2026-05-15',
      page_count: 3
    };

    // Mock fetch for tenants
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [{ id: 1, name: 'فهد العتيبي', is_resident: 1 }]
    });

    await window.openPageEditor(mockDoc);

    // Select page 2
    const cards = document.querySelectorAll('.page-editor-card');
    cards[1].click();

    // Click Separate & Move (async function)
    const btnExtract = document.getElementById('btn-editor-extract-selected');
    await btnExtract.onclick();

    const submodal = document.getElementById('extract-pages-submodal');
    expect(submodal.classList.contains('hidden')).toBe(false);

    const catSelect = document.getElementById('extract-target-category');
    expect(catSelect.options.length).toBeGreaterThan(5);

    const customContainer = document.getElementById('extract-custom-cat-container');
    catSelect.value = '__custom__';
    catSelect.dispatchEvent(new Event('change'));
    expect(customContainer.classList.contains('hidden')).toBe(false);

    const dateInput = document.getElementById('extract-target-date');
    expect(dateInput.value).toBe('2026-05-15');
  });

  it('executes extract-pages API call with target parameters and closes editor', async () => {
    const mockDoc = {
      vault_id: 'doc_bundle_99',
      brief_arabic_title: 'حزمة وثائق',
      category: '10 - صيانة',
      area_id: 'Safra C',
      house_id: '101',
      page_count: 3
    };

    let fetchCall = null;
    global.fetch = vi.fn((url, options) => {
      if (url.includes('/extract-pages')) {
        fetchCall = { url, options };
        return Promise.resolve({
          ok: true,
          json: async () => ({
            message: 'Extracted successfully',
            new_vault_id: 'doc_extracted_88',
            new_title: '04 - محضر تسليم مفتاح',
            new_category: '04 - محضر تسليم مفتاح',
            remaining_pages: 2
          })
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => []
      });
    });

    window.openDocument = vi.fn();
    window.refreshCurrentTab = vi.fn();

    await window.openPageEditor(mockDoc);

    // Select page 2 and page 3
    const cards = document.querySelectorAll('.page-editor-card');
    cards[1].click();
    cards[2].click();

    // Open extract submodal
    document.getElementById('btn-editor-extract-selected').click();

    // Confirm extraction
    const confirmBtn = document.getElementById('btn-extract-confirm');
    await confirmBtn.onclick();

    expect(fetchCall).not.toBeNull();
    expect(fetchCall.url).toContain('/documents/doc_bundle_99/extract-pages');
    const body = JSON.parse(fetchCall.options.body);
    expect(body.page_numbers).toEqual([2, 3]);
    expect(body.target_category).toBe('04 - محضر تسليم مفتاح');
    expect(body.delete_from_source).toBe(true);

    // Verifies opened new document
    expect(window.openDocument).toHaveBeenCalledWith('doc_extracted_88', '04 - محضر تسليم مفتاح', '04 - محضر تسليم مفتاح');
  });

  it('executes delete-pages API call with confirmation prompt', async () => {
    const mockDoc = {
      vault_id: 'doc_del_test',
      brief_arabic_title: 'وثيقة للتنقيح',
      category: '10 - صيانة',
      area_id: 'Safra C',
      house_id: '101',
      page_count: 2
    };

    let deleteCall = null;
    global.fetch = vi.fn((url, options) => {
      if (url.includes('/delete-pages')) {
        deleteCall = { url, options };
        return Promise.resolve({
          ok: true,
          json: async () => ({
            message: 'Deleted successfully',
            remaining_pages: 1,
            document_deleted: false
          })
        });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });

    vi.stubGlobal('confirm', vi.fn(() => true));

    await window.openPageEditor(mockDoc);

    // Select page 1
    const cards = document.querySelectorAll('.page-editor-card');
    cards[0].click();

    const deleteBtn = document.getElementById('btn-editor-delete-selected');
    await deleteBtn.onclick();

    expect(window.confirm).toHaveBeenCalled();
    expect(deleteCall).not.toBeNull();
    expect(deleteCall.url).toContain('/documents/doc_del_test/delete-pages');
    const body = JSON.parse(deleteCall.options.body);
    expect(body.page_numbers).toEqual([1]);
  });

  it('executes single page 1-tap delete from card button with confirmation', async () => {
    const mockDoc = {
      vault_id: 'doc_card_del',
      brief_arabic_title: 'وثيقة حذف بطاقة',
      category: '10 - صيانة',
      page_count: 3
    };

    let deleteCall = null;
    global.fetch = vi.fn((url, options) => {
      if (url.includes('/delete-pages')) {
        deleteCall = { url, options };
        return Promise.resolve({
          ok: true,
          json: async () => ({
            message: 'Deleted successfully',
            remaining_pages: 2,
            document_deleted: false
          })
        });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });

    vi.stubGlobal('confirm', vi.fn(() => true));

    await window.openPageEditor(mockDoc);

    const cards = document.querySelectorAll('.page-editor-card');
    const btnCardDel = cards[1].querySelector('.btn-card-delete');
    expect(btnCardDel).not.toBeNull();

    await btnCardDel.onclick(new Event('click'));

    expect(window.confirm).toHaveBeenCalled();
    expect(deleteCall).not.toBeNull();
    const body = JSON.parse(deleteCall.options.body);
    expect(body.page_numbers).toEqual([2]);
  });

  it('cancels single page deletion when user dismisses confirm prompt', async () => {
    const mockDoc = {
      vault_id: 'doc_card_cancel',
      brief_arabic_title: 'وثيقة إلغاء الحذف',
      category: '10 - صيانة',
      page_count: 3
    };

    let fetchCalled = false;
    global.fetch = vi.fn(() => {
      fetchCalled = true;
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    vi.stubGlobal('confirm', vi.fn(() => false)); // User cancels

    await window.openPageEditor(mockDoc);

    const cards = document.querySelectorAll('.page-editor-card');
    const btnCardDel = cards[0].querySelector('.btn-card-delete');
    await btnCardDel.onclick(new Event('click'));

    expect(window.confirm).toHaveBeenCalled();
    expect(fetchCalled).toBe(false);
  });

  it('shifts page order using card move-left and move-right buttons and calls reorder API', async () => {
    const mockDoc = {
      vault_id: 'doc_reorder_test',
      brief_arabic_title: 'وثيقة إعادة ترتيب',
      category: '05 - عقود',
      area_id: 'Safra C',
      house_id: '101',
      page_count: 3
    };

    let reorderCall = null;
    global.fetch = vi.fn((url, options) => {
      if (url.includes('/reorder-pages')) {
        reorderCall = { url, options };
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'success', page_order: [2, 1, 3] })
        });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });

    await window.openPageEditor(mockDoc);

    let cards = document.querySelectorAll('.page-editor-card');
    // First card: move-left is disabled, move-right is enabled
    const btnFirstMoveLeft = cards[0].querySelector('.btn-move-left');
    const btnFirstMoveRight = cards[0].querySelector('.btn-move-right');
    expect(btnFirstMoveLeft.disabled).toBe(true);
    expect(btnFirstMoveRight.disabled).toBe(false);

    // Click move-right on first page (Page 1 shifts to pos 2, Page 2 shifts to pos 1)
    await btnFirstMoveRight.onclick(new Event('click'));

    expect(reorderCall).not.toBeNull();
    expect(reorderCall.url).toContain('/documents/doc_reorder_test/reorder-pages');
    const body = JSON.parse(reorderCall.options.body);
    expect(body.page_order).toEqual([2, 1, 3]);
  });

  it('closes page editor via Close button and Escape key', async () => {
    const mockDoc = {
      vault_id: 'doc_close_test',
      brief_arabic_title: 'وثيقة الإغلاق',
      category: '10 - صيانة',
      page_count: 2
    };

    await window.openPageEditor(mockDoc);
    const modal = document.getElementById('doc-page-editor-modal');
    expect(modal.classList.contains('hidden')).toBe(false);

    // Close via close button
    const closeBtn = document.getElementById('page-editor-close-btn');
    closeBtn.click();
    expect(modal.classList.contains('hidden')).toBe(true);

    // Re-open and close via Escape key
    await window.openPageEditor(mockDoc);
    expect(modal.classList.contains('hidden')).toBe(false);

    const escEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    document.dispatchEvent(escEvent);
    expect(modal.classList.contains('hidden')).toBe(true);
  });

  it('closes extract submodal via Cancel button and Escape key without closing main editor', async () => {
    const mockDoc = {
      vault_id: 'doc_submodal_esc',
      brief_arabic_title: 'وثيقة فرعية',
      category: '10 - صيانة',
      page_count: 2
    };

    await window.openPageEditor(mockDoc);
    const cards = document.querySelectorAll('.page-editor-card');
    cards[0].click();

    // Open submodal
    const btnExtract = document.getElementById('btn-editor-extract-selected');
    await btnExtract.onclick();

    const submodal = document.getElementById('extract-pages-submodal');
    const mainModal = document.getElementById('doc-page-editor-modal');
    expect(submodal.classList.contains('hidden')).toBe(false);
    expect(mainModal.classList.contains('hidden')).toBe(false);

    // Press Escape -> only submodal closes!
    const escEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    document.dispatchEvent(escEvent);
    expect(submodal.classList.contains('hidden')).toBe(true);
    expect(mainModal.classList.contains('hidden')).toBe(false);
  });

  it('handles API errors gracefully during extraction and deletion', async () => {
    const mockDoc = {
      vault_id: 'doc_err_test',
      brief_arabic_title: 'وثيقة اختبار الأخطاء',
      category: '10 - صيانة',
      page_count: 2
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Database error occurred' })
    });

    vi.stubGlobal('confirm', vi.fn(() => true));

    await window.openPageEditor(mockDoc);
    const cards = document.querySelectorAll('.page-editor-card');
    cards[0].click();

    // Delete fails gracefully
    const deleteBtn = document.getElementById('btn-editor-delete-selected');
    await deleteBtn.onclick();
    expect(global.showToast).toHaveBeenCalledWith('Database error occurred', 'error');

    // Extract fails gracefully
    await document.getElementById('btn-editor-extract-selected').onclick();
    const confirmExtract = document.getElementById('btn-extract-confirm');
    await confirmExtract.onclick();
    expect(global.showToast).toHaveBeenCalledWith('Database error occurred', 'error');
  });
});


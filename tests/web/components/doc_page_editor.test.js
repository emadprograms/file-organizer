import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Document Page Editor (Split, Delete, Extract, Reorder)', () => {
  const indexHtml = fs.readFileSync(
    path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/index.html'),
    'utf8'
  );

  beforeEach(() => {
    try {
      if (typeof localStorage !== 'undefined') localStorage.clear();
    } catch (e) {}

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
        <button id="btn-editor-zoom-out">-</button>
        <button id="btn-editor-zoom-reset"><span id="editor-zoom-level-label">100%</span></button>
        <button id="btn-editor-zoom-in">+</button>
        <button id="page-editor-close-btn"></button>
        <div id="page-editor-loading" class="hidden"></div>
        <div id="page-editor-grid"></div>

        <button id="btn-editor-select-all"></button>
        <button id="btn-editor-deselect-all"></button>
        <span id="page-editor-selected-count"></span>
        <button id="btn-editor-delete-selected" disabled><span class="btn-text">Delete Selected</span></button>
        <button id="btn-editor-copy-selected" disabled><span class="btn-text">Copy Pages...</span></button>
        <button id="btn-editor-extract-selected" disabled><span class="btn-text">Separate & Move...</span></button>
      </div>

      <!-- Extract Submodal -->
      <div id="extract-pages-submodal" class="hidden" style="display: none;">
        <span id="extract-pages-count-badge"></span>
        <label id="extract-mode-move-label">
          <input type="radio" id="extract-mode-move" name="extract-mode" value="move" checked />
        </label>
        <label id="extract-mode-copy-label">
          <input type="radio" id="extract-mode-copy" name="extract-mode" value="copy" />
        </label>
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
    if (typeof localStorage !== 'undefined') {
      localStorage.clear();
    }

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

    let deleteFetchCalled = false;
    global.fetch = vi.fn((url) => {
      if (typeof url === 'string' && url.includes('/delete-pages')) {
        deleteFetchCalled = true;
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    vi.stubGlobal('confirm', vi.fn(() => false)); // User cancels

    await window.openPageEditor(mockDoc);

    const cards = document.querySelectorAll('.page-editor-card');
    const btnCardDel = cards[0].querySelector('.btn-card-delete');
    await btnCardDel.onclick(new Event('click'));

    expect(window.confirm).toHaveBeenCalled();
    expect(deleteFetchCalled).toBe(false);
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

  it('displays real tenant name from SQLite metadata endpoint in the header subtitle', async () => {
    const mockDoc = {
      vault_id: 'doc_with_real_tenant',
      brief_arabic_title: 'عقد إيجار موثق',
      category: '05 - عقود',
      page_count: 2
    };

    global.fetch = vi.fn((url) => {
      if (typeof url === 'string' && url.includes('/metadata')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            vaultId: 'doc_with_real_tenant',
            tenantName: 'عبدالله السالم',
            tenantId: 42,
            category: '05 - عقود',
            arabicTitle: 'عقد إيجار موثق'
          })
        });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });

    await window.openPageEditor(mockDoc);

    const subtitle = document.getElementById('page-editor-subtitle');
    expect(subtitle.textContent).toBe('05 - عقود • عبدالله السالم');
    expect(subtitle.textContent).not.toContain('No Tenant');
  });

  it('displays Arabic "كامل المنزل (عام)" in subtitle when document has no assigned tenant and never displays "No Tenant"', async () => {
    const mockDoc = {
      vault_id: 'doc_unassigned_tenant',
      brief_arabic_title: 'فاتورة عامة',
      category: '06 - كهرباء وماء',
      page_count: 1
    };

    global.fetch = vi.fn((url) => {
      if (typeof url === 'string' && url.includes('/metadata')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            vaultId: 'doc_unassigned_tenant',
            tenantName: null,
            tenantId: 0,
            category: '06 - كهرباء وماء',
            arabicTitle: 'فاتورة عامة'
          })
        });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });

    await window.openPageEditor(mockDoc);

    const subtitle = document.getElementById('page-editor-subtitle');
    expect(subtitle.textContent).toBe('06 - كهرباء وماء • كامل المنزل (عام)');
    expect(subtitle.textContent).not.toContain('No Tenant');
  });

  it('populates general house document option and pre-selects resident tenant in extract modal', async () => {
    const mockDoc = {
      vault_id: 'doc_extract_tenant_choice',
      brief_arabic_title: 'خطاب مجمع',
      category: '10 - صيانة',
      page_count: 2,
      tenant_id: 10
    };

    global.fetch = vi.fn((url) => {
      if (typeof url === 'string' && url.includes('/tenants')) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            { id: 10, name: 'سلطان الدوسري', is_resident: 1 },
            { id: 20, name: 'خالد الحربي', is_resident: 0 }
          ]
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({ tenantId: 10, tenantName: 'سلطان الدوسري' })
      });
    });

    await window.openPageEditor(mockDoc);
    const cards = document.querySelectorAll('.page-editor-card');
    cards[0].click();

    await document.getElementById('btn-editor-extract-selected').onclick();

    const tenantSelect = document.getElementById('extract-target-tenant');
    expect(tenantSelect.options.length).toBe(3); // General + 2 tenants
    expect(tenantSelect.options[0].textContent).toContain('كامل المنزل (عام)');
    expect(tenantSelect.value).toBe('10'); // Pre-selected
  });

  it('reorders pages, resets currentPageOrder to prevent desync, and triggers viewer reload', async () => {
    const mockDoc = {
      vault_id: 'doc_reorder_desync_check',
      brief_arabic_title: 'وثيقة اختبار التزامن',
      category: '05 - عقود',
      area_id: 'Safra C',
      house_id: '101',
      page_count: 3
    };

    const reorderCalls = [];
    global.fetch = vi.fn((url, options) => {
      if (typeof url === 'string' && url.includes('/reorder-pages')) {
        reorderCalls.push(JSON.parse(options.body));
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'success', page_order: JSON.parse(options.body).page_order })
        });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });

    window.reloadCurrentDocument = vi.fn();

    await window.openPageEditor(mockDoc);

    const cards = document.querySelectorAll('.page-editor-card');
    const firstMoveRight = cards[0].querySelector('.btn-move-right');

    // First click: moves page 1 to pos 2 -> order [2, 1, 3]
    await firstMoveRight.onclick(new Event('click'));

    expect(reorderCalls.length).toBe(1);
    expect(reorderCalls[0].page_order).toEqual([2, 1, 3]);
    expect(window.reloadCurrentDocument).toHaveBeenCalledWith(true);

    // Second click: because currentPageOrder was reset to [1, 2, 3] relative to the newly saved file,
    // moving pos 2 right will swap pos 2 and pos 3 -> order [1, 3, 2]
    const updatedCards = document.querySelectorAll('.page-editor-card');
    const secondMoveRight = updatedCards[1].querySelector('.btn-move-right');
    await secondMoveRight.onclick(new Event('click'));

    expect(reorderCalls.length).toBe(2);
    expect(reorderCalls[1].page_order).toEqual([1, 3, 2]);
  });

  it('opens extract submodal in copy mode when btn-editor-copy-selected is clicked, sending delete_from_source: false and keeping editor open', async () => {
    const mockDoc = {
      vault_id: 'doc_copy_mode_test',
      brief_arabic_title: 'عقد للإيجار',
      category: '05 - عقود',
      area_id: 'Safra C',
      house_id: '101',
      page_count: 3
    };

    let extractPayload = null;
    global.fetch = vi.fn((url, options) => {
      if (typeof url === 'string' && url.includes('/extract-pages')) {
        extractPayload = JSON.parse(options.body);
        return Promise.resolve({
          ok: true,
          json: async () => ({
            status: 'success',
            new_vault_id: 'doc_new_copy',
            new_title: 'نسخة مستخرجة',
            remaining_pages: 3
          })
        });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });

    window.reloadCurrentDocument = vi.fn();
    window.refreshCurrentTab = vi.fn();
    window.loadTree = vi.fn();

    await window.openPageEditor(mockDoc);

    // Select page 1
    const cards = document.querySelectorAll('.page-editor-card');
    cards[0].click();

    const btnCopy = document.getElementById('btn-editor-copy-selected');
    expect(btnCopy.disabled).toBe(false);

    // Click Copy
    btnCopy.click();

    const submodal = document.getElementById('extract-pages-submodal');
    expect(submodal.classList.contains('hidden')).toBe(false);

    const copyRadio = document.getElementById('extract-mode-copy');
    const moveRadio = document.getElementById('extract-mode-move');
    expect(copyRadio.checked).toBe(true);
    expect(moveRadio.checked).toBe(false);

    const confirmBtn = document.getElementById('btn-extract-confirm');
    await confirmBtn.onclick(new Event('click'));

    // Verify payload had delete_from_source = false
    expect(extractPayload).not.toBeNull();
    expect(extractPayload.delete_from_source).toBe(false);
    expect(extractPayload.page_numbers).toEqual([1]);

    // In copy mode, parent editor modal remains open
    const editorModal = document.getElementById('doc-page-editor-modal');
    expect(editorModal.classList.contains('hidden')).toBe(false);

    expect(window.reloadCurrentDocument).toHaveBeenCalledWith(true);
    expect(global.showToast).toHaveBeenCalled();
  });

  it('opens extract submodal in move mode when btn-editor-extract-selected is clicked, sending delete_from_source: true', async () => {
    const mockDoc = {
      vault_id: 'doc_move_mode_test',
      brief_arabic_title: 'عقد للنقل',
      category: '05 - عقود',
      area_id: 'Safra C',
      house_id: '101',
      page_count: 3
    };

    let extractPayload = null;
    global.fetch = vi.fn((url, options) => {
      if (typeof url === 'string' && url.includes('/extract-pages')) {
        extractPayload = JSON.parse(options.body);
        return Promise.resolve({
          ok: true,
          json: async () => ({
            status: 'success',
            new_vault_id: 'doc_new_moved',
            new_title: 'نقل مستخرج',
            remaining_pages: 2
          })
        });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });

    window.reloadCurrentDocument = vi.fn();

    await window.openPageEditor(mockDoc);

    const cards = document.querySelectorAll('.page-editor-card');
    cards[1].click();

    const btnExtract = document.getElementById('btn-editor-extract-selected');
    btnExtract.click();

    const moveRadio = document.getElementById('extract-mode-move');
    const copyRadio = document.getElementById('extract-mode-copy');
    expect(moveRadio.checked).toBe(true);
    expect(copyRadio.checked).toBe(false);

    const confirmBtn = document.getElementById('btn-extract-confirm');
    await confirmBtn.onclick(new Event('click'));

    expect(extractPayload).not.toBeNull();
    expect(extractPayload.delete_from_source).toBe(true);
    expect(extractPayload.page_numbers).toEqual([2]);
  });

  it('executes delete pages with fallback to universal endpoint when area route fails', async () => {
    const mockDoc = {
      vault_id: 'doc_del_fallback_test',
      brief_arabic_title: 'وثيقة حذف مع بديل',
      category: '06 - كهرباء وماء',
      area_id: 'default',
      house_id: 'default',
      page_count: 3
    };

    const fetchedUrls = [];
    global.fetch = vi.fn((url, options) => {
      fetchedUrls.push(url);
      if (typeof url === 'string' && url.includes('/areas/') && url.includes('/delete-pages')) {
        return Promise.resolve({
          ok: false,
          status: 404,
          json: async () => ({ error: 'Not found on area route' })
        });
      }
      if (typeof url === 'string' && url.includes('/api/documents/doc_del_fallback_test/delete-pages')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            status: 'success',
            remaining_pages: 2,
            document_deleted: false
          })
        });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });

    window.confirm = vi.fn(() => true);
    window.reloadCurrentDocument = vi.fn();

    await window.openPageEditor(mockDoc);

    const cards = document.querySelectorAll('.page-editor-card');
    cards[0].click();

    const btnDelete = document.getElementById('btn-editor-delete-selected');
    await btnDelete.onclick(new Event('click'));

    // Should have called the fallback route
    expect(fetchedUrls.some(u => u.includes('/api/documents/doc_del_fallback_test/delete-pages'))).toBe(true);
    expect(window.reloadCurrentDocument).toHaveBeenCalledWith(true);
    expect(global.showToast).toHaveBeenCalled();
  });

  it('leaves extract-target-notes completely empty by default when opening extract submodal', async () => {
    const mockDoc = {
      vault_id: 'doc_notes_empty_test',
      brief_arabic_title: 'إشعار صيانة',
      filename: 'sample.pdf',
      category: '10 - صيانة',
      page_count: 2
    };

    global.fetch = vi.fn(() => Promise.resolve({ ok: true, json: async () => [] }));

    await window.openPageEditor(mockDoc);

    const cards = document.querySelectorAll('.page-editor-card');
    cards[0].click();

    const btnExtract = document.getElementById('btn-editor-extract-selected');
    btnExtract.onclick();

    const notesInput = document.getElementById('extract-target-notes');
    expect(notesInput.value).toBe('');
    expect(notesInput.value).not.toContain('Separated from');
  });

  describe('Canvas Page Card Zoom Controls (+/-, Ctrl+, Ctrl+Scroll)', () => {
    it('includes zoom controls in index.html for page editor modal header', () => {
      const fs = require('fs');
      const path = require('path');
      const indexHtml = fs.readFileSync(path.join(__dirname, '../../../src/HousingApplication.Web/wwwroot/index.html'), 'utf8');
      expect(indexHtml).toContain('id="btn-editor-zoom-out"');
      expect(indexHtml).toContain('id="btn-editor-zoom-in"');
      expect(indexHtml).toContain('id="btn-editor-zoom-reset"');
      expect(indexHtml).toContain('id="editor-zoom-level-label"');
    });

    it('adjusts zoom level and CSS custom properties on doc-page-editor-modal via buttons', async () => {
      const mockDoc = {
        vault_id: 'doc_zoom_test',
        brief_arabic_title: 'إشعار صيانة',
        filename: 'sample.pdf',
        category: '10 - صيانة',
        page_count: 2
      };
      global.fetch = vi.fn(() => Promise.resolve({ ok: true, json: async () => [] }));

      await window.openPageEditor(mockDoc);

      const modal = document.getElementById('doc-page-editor-modal');
      const btnIn = document.getElementById('btn-editor-zoom-in');
      const btnOut = document.getElementById('btn-editor-zoom-out');
      const btnReset = document.getElementById('btn-editor-zoom-reset');
      const label = document.getElementById('editor-zoom-level-label');

      expect(label.textContent).toBe('100%');

      btnIn.click();
      expect(label.textContent).toBe('120%');
      expect(modal.style.getPropertyValue('--editor-card-min-width')).toBe('280px');

      btnIn.click();
      expect(label.textContent).toBe('145%');

      btnOut.click();
      expect(label.textContent).toBe('120%');

      btnReset.click();
      expect(label.textContent).toBe('100%');
      expect(modal.style.getPropertyValue('--editor-card-min-width')).toBe('230px');
    });

    it('handles keyboard shortcuts (Ctrl+, Ctrl-, Ctrl 0) to adjust editor zoom', async () => {
      const mockDoc = {
        vault_id: 'doc_kb_zoom_test',
        brief_arabic_title: 'إشعار صيانة',
        filename: 'sample.pdf',
        category: '10 - صيانة',
        page_count: 2
      };
      global.fetch = vi.fn(() => Promise.resolve({ ok: true, json: async () => [] }));

      await window.openPageEditor(mockDoc);

      const label = document.getElementById('editor-zoom-level-label');
      expect(label.textContent).toBe('100%');

      window.dispatchEvent(new KeyboardEvent('keydown', { key: '=', ctrlKey: true, bubbles: true }));
      expect(label.textContent).toBe('120%');

      window.dispatchEvent(new KeyboardEvent('keydown', { key: '-', ctrlKey: true, bubbles: true }));
      expect(label.textContent).toBe('100%');

      window.dispatchEvent(new KeyboardEvent('keydown', { key: '0', ctrlKey: true, bubbles: true }));
      expect(label.textContent).toBe('100%');
    });

    it('handles Ctrl + Scroll wheel to adjust editor zoom with preventDefault', async () => {
      const mockDoc = {
        vault_id: 'doc_wheel_zoom_test',
        brief_arabic_title: 'إشعار صيانة',
        filename: 'sample.pdf',
        category: '10 - صيانة',
        page_count: 2
      };
      global.fetch = vi.fn(() => Promise.resolve({ ok: true, json: async () => [] }));

      await window.openPageEditor(mockDoc);

      const modal = document.getElementById('doc-page-editor-modal');
      const label = document.getElementById('editor-zoom-level-label');

      const zoomInWheel = new WheelEvent('wheel', { deltaY: -100, ctrlKey: true, cancelable: true, bubbles: true });
      modal.dispatchEvent(zoomInWheel);
      expect(label.textContent).toBe('120%');
      expect(zoomInWheel.defaultPrevented).toBe(true);

      const zoomOutWheel = new WheelEvent('wheel', { deltaY: 100, ctrlKey: true, cancelable: true, bubbles: true });
      modal.dispatchEvent(zoomOutWheel);
      expect(label.textContent).toBe('100%');
      expect(zoomOutWheel.defaultPrevented).toBe(true);
    });
  });
});



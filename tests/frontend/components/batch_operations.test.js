import { describe, it, expect, beforeEach, vi } from 'vitest';

const {
    loadCategories,
    renderCategories,
    FOLDER_PREFIXES,
    selectedDocIds,
    getSelectedDocIds,
    toggleDocSelection,
    toggleSelectAllInFolder,
    toggleSelectAllGlobal,
    deselectAllDocs,
    updateBatchActionBar,
    openBatchMoveModal,
    closeBatchMoveModal,
    handleBatchMoveSubmit,
    openBatchDeleteModal,
    closeBatchDeleteModal,
    handleBatchDeleteSubmit,
    initBatchOperations,
} = require('../../../src/api/static/js/categories-view.js');

function setupDOM() {
    document.body.innerHTML = `
        <div id="stats-badge" class="hidden"></div>
        <div id="document-list"></div>

        <div id="batch-action-bar" class="hidden">
            <span id="batch-selected-count">0 selected</span>
            <button id="btn-batch-move" type="button">Move Selected</button>
            <button id="btn-batch-delete" type="button">Delete Selected</button>
            <button id="btn-batch-deselect" type="button">Deselect</button>
        </div>

        <div id="batch-move-modal" class="hidden">
            <p id="batch-move-subtitle"></p>
            <select id="batch-move-folder-select"></select>
            <div id="batch-move-custom-folder-container" class="hidden">
                <input id="batch-move-custom-folder-input" type="text" />
            </div>
            <button id="batch-move-close" type="button"></button>
            <button id="btn-batch-move-cancel" type="button"></button>
            <button id="btn-batch-move-confirm" type="button">
                <span id="batch-move-spinner" class="hidden"></span>
                <span id="batch-move-btn-text">Move</span>
            </button>
        </div>

        <div id="batch-delete-modal" class="hidden">
            <p id="batch-delete-subtitle"></p>
            <p id="batch-delete-message"></p>
            <button id="batch-delete-close" type="button"></button>
            <button id="btn-batch-delete-cancel" type="button"></button>
            <button id="btn-batch-delete-confirm" type="button">
                <span id="batch-delete-spinner" class="hidden"></span>
                <span id="batch-delete-btn-text">Delete</span>
            </button>
        </div>
    `;
}

describe('Multi-Select Batch Document Operations (Phase 106)', () => {
    beforeEach(() => {
        setupDOM();
        global.currentArea = 'Safra C';
        global.currentHouse = '500';
        global.currentCategories = [
            {
                tenant: 'فاطمة أحمد',
                name: '05 - عقود',
                document_count: 2,
                documents: [
                    { vault_id: 'doc001', brief_arabic_title: 'عقد إيجار 1', is_manual: 0, notes: '' },
                    { vault_id: 'doc002', brief_arabic_title: 'عقد إيجار 2', is_manual: 1, notes: 'ملاحظة' }
                ]
            },
            {
                tenant: 'فاطمة أحمد',
                name: '10 - صيانة',
                document_count: 1,
                documents: [
                    { vault_id: 'doc003', brief_arabic_title: 'فاتورة صيانة', is_manual: 0, notes: '' }
                ]
            }
        ];
        global.currentTenant = null;
        global.showToast = vi.fn();
        global.refreshCurrentTab = vi.fn().mockResolvedValue(undefined);
        deselectAllDocs();
        initBatchOperations();
    });

    it('toggles selection of individual documents and updates floating action bar', () => {
        expect(getSelectedDocIds().size).toBe(0);
        const bar = document.getElementById('batch-action-bar');
        const count = document.getElementById('batch-selected-count');
        expect(bar.classList.contains('hidden')).toBe(true);

        toggleDocSelection('doc001', true);
        expect(getSelectedDocIds().has('doc001')).toBe(true);
        expect(getSelectedDocIds().size).toBe(1);
        expect(bar.classList.contains('hidden')).toBe(false);
        expect(count.textContent).toContain('1 document selected');

        toggleDocSelection('doc002', true);
        expect(getSelectedDocIds().size).toBe(2);
        expect(count.textContent).toContain('2 documents selected');

        toggleDocSelection('doc001', false);
        expect(getSelectedDocIds().has('doc001')).toBe(false);
        expect(getSelectedDocIds().size).toBe(1);

        deselectAllDocs();
        expect(getSelectedDocIds().size).toBe(0);
        expect(bar.classList.contains('hidden')).toBe(true);
        expect(count.textContent).toBe('0 selected');
    });

    it('renders checkboxes in category folder document lists', () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const checkboxes = docList.querySelectorAll('.doc-select-checkbox');
        expect(checkboxes.length).toBe(3);

        const cb1 = docList.querySelector('.doc-select-checkbox[data-vault-id="doc001"]');
        expect(cb1).not.toBeNull();
        expect(cb1.checked).toBe(false);

        // Check the box
        cb1.checked = true;
        cb1.dispatchEvent(new Event('change'));
        expect(getSelectedDocIds().has('doc001')).toBe(true);

        const bar = document.getElementById('batch-action-bar');
        expect(bar.classList.contains('hidden')).toBe(false);
    });

    it('toggles select all within a category folder', () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const folderCard = docList.querySelector('[data-category-name="05 - عقود"]');
        expect(folderCard).not.toBeNull();

        const selectAllBtn = folderCard.querySelector('.btn-select-all-folder');
        expect(selectAllBtn).not.toBeNull();
        expect(selectAllBtn.textContent).toBe('Select All');

        // Click Select All in folder
        selectAllBtn.click();
        expect(getSelectedDocIds().has('doc001')).toBe(true);
        expect(getSelectedDocIds().has('doc002')).toBe(true);
        expect(getSelectedDocIds().has('doc003')).toBe(false);
        expect(getSelectedDocIds().size).toBe(2);
        expect(selectAllBtn.textContent).toBe('Deselect All');

        // Click again to Deselect All in folder
        selectAllBtn.click();
        expect(getSelectedDocIds().has('doc001')).toBe(false);
        expect(getSelectedDocIds().has('doc002')).toBe(false);
        expect(getSelectedDocIds().size).toBe(0);
        expect(selectAllBtn.textContent).toBe('Select All');
    });

    it('toggles select all globally across all category folders', () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const globalBtn = docList.querySelector('#btn-toggle-select-all-categories');
        expect(globalBtn).not.toBeNull();
        expect(globalBtn.textContent).toContain('Select All');

        // Click Select All across all categories
        globalBtn.click();
        expect(getSelectedDocIds().size).toBe(3);
        expect(getSelectedDocIds().has('doc001')).toBe(true);
        expect(getSelectedDocIds().has('doc002')).toBe(true);
        expect(getSelectedDocIds().has('doc003')).toBe(true);

        // Click again to Deselect All
        globalBtn.click();
        expect(getSelectedDocIds().size).toBe(0);
    });

    it('opens batch move modal with standard folders and executes POST batch-move', async () => {
        toggleDocSelection('doc001', true);
        toggleDocSelection('doc002', true);

        openBatchMoveModal();
        const modal = document.getElementById('batch-move-modal');
        expect(modal.classList.contains('hidden')).toBe(false);

        const subtitle = document.getElementById('batch-move-subtitle');
        expect(subtitle.textContent).toContain('2 documents');

        const select = document.getElementById('batch-move-folder-select');
        expect(select.options.length).toBeGreaterThan(13);
        select.value = '10 - صيانة';

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                status: 'success',
                moved_count: 2,
                target_category: '10 - صيانة',
                vault_ids: ['doc001', 'doc002']
            })
        });

        await handleBatchMoveSubmit();

        expect(global.fetch).toHaveBeenCalledWith(
            '/api/areas/Safra%20C/houses/500/documents/batch-move',
            expect.objectContaining({
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vault_ids: ['doc001', 'doc002'],
                    target_category: '10 - صيانة'
                })
            })
        );

        expect(modal.classList.contains('hidden')).toBe(true);
        expect(getSelectedDocIds().size).toBe(0);
        expect(global.showToast).toHaveBeenCalledWith(expect.stringContaining('moved 2 documents'), 'success');
        expect(global.refreshCurrentTab).toHaveBeenCalledWith('Safra C', '500');
    });

    it('opens batch delete modal and executes POST batch-delete', async () => {
        toggleDocSelection('doc001', true);
        toggleDocSelection('doc003', true);

        openBatchDeleteModal();
        const modal = document.getElementById('batch-delete-modal');
        expect(modal.classList.contains('hidden')).toBe(false);

        const subtitle = document.getElementById('batch-delete-subtitle');
        expect(subtitle.textContent).toContain('2 documents');

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                status: 'success',
                deleted_count: 2,
                vault_ids: ['doc001', 'doc003']
            })
        });

        await handleBatchDeleteSubmit();

        expect(global.fetch).toHaveBeenCalledWith(
            '/api/areas/Safra%20C/houses/500/documents/batch-delete',
            expect.objectContaining({
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vault_ids: ['doc001', 'doc003']
                })
            })
        );

        expect(modal.classList.contains('hidden')).toBe(true);
        expect(getSelectedDocIds().size).toBe(0);
        expect(global.showToast).toHaveBeenCalledWith(expect.stringContaining('deleted 2 documents'), 'success');
        expect(global.refreshCurrentTab).toHaveBeenCalledWith('Safra C', '500');
    });

    it('clicking deselect button clears selection and hides floating bar', () => {
        toggleDocSelection('doc001', true);
        expect(getSelectedDocIds().size).toBe(1);

        const deselectBtn = document.getElementById('btn-batch-deselect');
        deselectBtn.click();

        expect(getSelectedDocIds().size).toBe(0);
        const bar = document.getElementById('batch-action-bar');
        expect(bar.classList.contains('hidden')).toBe(true);
    });
});

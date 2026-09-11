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
    openBatchCopyModal,
    closeBatchCopyModal,
    handleBatchCopySubmit,
    openBatchDeleteModal,
    closeBatchDeleteModal,
    handleBatchDeleteSubmit,
    initBatchOperations,
    populateBatchTenantSelect,
} = require('../../../src/api/static/js/categories-view.js');

function setupDOM() {
    document.body.innerHTML = `
        <div id="stats-badge" class="hidden"></div>
        <div id="document-list"></div>

        <div id="batch-action-bar" class="hidden">
            <span id="batch-selected-count">0 selected</span>
            <button id="btn-batch-move" type="button">Move Selected</button>
            <button id="btn-batch-copy" type="button">Copy Selected</button>
            <button id="btn-batch-delete" type="button">Delete Selected</button>
            <button id="btn-batch-deselect" type="button">Deselect</button>
        </div>

        <div id="batch-move-modal" class="hidden">
            <p id="batch-move-subtitle"></p>
            <select id="batch-move-tenant-select"></select>
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

        <div id="batch-copy-modal" class="hidden">
            <p id="batch-copy-subtitle"></p>
            <select id="batch-copy-tenant-select"></select>
            <select id="batch-copy-folder-select"></select>
            <div id="batch-copy-custom-folder-container" class="hidden">
                <input id="batch-copy-custom-folder-input" type="text" />
            </div>
            <button id="batch-copy-close" type="button"></button>
            <button id="btn-batch-copy-cancel" type="button"></button>
            <button id="btn-batch-copy-confirm" type="button">
                <span id="batch-copy-spinner" class="hidden"></span>
                <span id="batch-copy-btn-text">Copy</span>
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

    it('toggles select all within a category folder using folder select checkbox and reveals documents', () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const folderCard = docList.querySelector('[data-category-name="05 - عقود"]');
        expect(folderCard).not.toBeNull();

        const folderCheckbox = folderCard.querySelector('.folder-select-checkbox');
        expect(folderCheckbox).not.toBeNull();
        expect(folderCheckbox.checked).toBe(false);

        const docsContainer = folderCard.querySelector('.category-docs');
        expect(docsContainer).not.toBeNull();
        // Collapse folder first to verify clicking folder checkbox reveals it
        docsContainer.classList.add('hidden');
        expect(docsContainer.classList.contains('hidden')).toBe(true);

        // Click folder select checkbox: selects all docs in folder and reveals documents list
        folderCheckbox.click();
        expect(getSelectedDocIds().has('doc001')).toBe(true);
        expect(getSelectedDocIds().has('doc002')).toBe(true);
        expect(getSelectedDocIds().has('doc003')).toBe(false);
        expect(getSelectedDocIds().size).toBe(2);
        expect(folderCheckbox.checked).toBe(true);
        expect(docsContainer.classList.contains('hidden')).toBe(false);

        // Click again to deselect all in folder
        folderCheckbox.click();
        expect(getSelectedDocIds().has('doc001')).toBe(false);
        expect(getSelectedDocIds().has('doc002')).toBe(false);
        expect(getSelectedDocIds().size).toBe(0);
        expect(folderCheckbox.checked).toBe(false);

        // Also verify on a folder that is naturally collapsed (no notes)
        const maintCard = docList.querySelector('[data-category-name="10 - صيانة"]');
        const maintDocs = maintCard.querySelector('.category-docs');
        const maintCb = maintCard.querySelector('.folder-select-checkbox');
        expect(maintDocs.classList.contains('hidden')).toBe(true);
        maintCb.click();
        expect(maintDocs.classList.contains('hidden')).toBe(false);
        expect(getSelectedDocIds().has('doc003')).toBe(true);
        expect(maintCb.checked).toBe(true);
    });

    it('updates folder checkbox to indeterminate when partially selected', () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const folderCard = docList.querySelector('[data-category-name="05 - عقود"]');
        const folderCb = folderCard.querySelector('.folder-select-checkbox');
        const docCbs = folderCard.querySelectorAll('.doc-select-checkbox');
        expect(docCbs.length).toBe(2);

        // Select only first document
        docCbs[0].checked = true;
        docCbs[0].dispatchEvent(new Event('change'));

        expect(folderCb.checked).toBe(false);
        expect(folderCb.indeterminate).toBe(true);

        // Select second document
        docCbs[1].checked = true;
        docCbs[1].dispatchEvent(new Event('change'));

        expect(folderCb.checked).toBe(true);
        expect(folderCb.indeterminate).toBe(false);

        // Deselect first document
        docCbs[0].checked = false;
        docCbs[0].dispatchEvent(new Event('change'));

        expect(folderCb.checked).toBe(false);
        expect(folderCb.indeterminate).toBe(true);

        // Deselect second document
        docCbs[1].checked = false;
        docCbs[1].dispatchEvent(new Event('change'));

        expect(folderCb.checked).toBe(false);
        expect(folderCb.indeterminate).toBe(false);
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

        const folderCbs = docList.querySelectorAll('.folder-select-checkbox');
        folderCbs.forEach(cb => {
            expect(cb.checked).toBe(true);
            expect(cb.indeterminate).toBe(false);
        });

        // Click again to Deselect All
        globalBtn.click();
        expect(getSelectedDocIds().size).toBe(0);
        folderCbs.forEach(cb => {
            expect(cb.checked).toBe(false);
            expect(cb.indeterminate).toBe(false);
        });
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

    it('opens batch copy modal with standard folders and executes POST batch-copy', async () => {
        toggleDocSelection('doc001', true);
        toggleDocSelection('doc002', true);

        openBatchCopyModal();
        const modal = document.getElementById('batch-copy-modal');
        expect(modal.classList.contains('hidden')).toBe(false);

        const subtitle = document.getElementById('batch-copy-subtitle');
        expect(subtitle.textContent).toContain('2 documents');

        const select = document.getElementById('batch-copy-folder-select');
        expect(select.options.length).toBeGreaterThan(13);
        select.value = '10 - صيانة';

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                status: 'success',
                copied_count: 2,
                target_category: '10 - صيانة',
                copied_vault_ids: ['doc001_copy_1', 'doc002_copy_1']
            })
        });

        await handleBatchCopySubmit();

        expect(global.fetch).toHaveBeenCalledWith(
            '/api/areas/Safra%20C/houses/500/documents/batch-copy',
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
        expect(global.showToast).toHaveBeenCalledWith('تم نسخ الوثائق المحددة بنجاح', 'success');
        expect(global.refreshCurrentTab).toHaveBeenCalledWith('Safra C', '500');
    });

    it('validates target category selection on batch copy', async () => {
        toggleDocSelection('doc001', true);
        openBatchCopyModal();

        const select = document.getElementById('batch-copy-folder-select');
        select.value = '';

        global.fetch = vi.fn();
        await handleBatchCopySubmit();

        expect(global.showToast).toHaveBeenCalledWith(
            'Please select or specify a target category folder.',
            'error'
        );
        expect(global.fetch).not.toHaveBeenCalled();
    });

    it('handles custom folder creation in batch copy modal', async () => {
        toggleDocSelection('doc001', true);
        openBatchCopyModal();

        const select = document.getElementById('batch-copy-folder-select');
        const customContainer = document.getElementById('batch-copy-custom-folder-container');
        const customInput = document.getElementById('batch-copy-custom-folder-input');

        select.value = '__custom__';
        select.dispatchEvent(new Event('change'));

        expect(customContainer.classList.contains('hidden')).toBe(false);
        customInput.value = '99 - وثائق إضافية';

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                status: 'success',
                copied_count: 1,
                target_category: '99 - وثائق إضافية',
                copied_vault_ids: ['doc001_copy_1']
            })
        });

        await handleBatchCopySubmit();

        expect(global.fetch).toHaveBeenCalledWith(
            '/api/areas/Safra%20C/houses/500/documents/batch-copy',
            expect.objectContaining({
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vault_ids: ['doc001'],
                    target_category: '99 - وثائق إضافية'
                })
            })
        );
        expect(global.showToast).toHaveBeenCalledWith('تم نسخ الوثائق المحددة بنجاح', 'success');
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

    it('populates batch tenant select with ONLY real tenants and pre-selects document tenant by default', async () => {
        global.currentCategories = [
            {
                tenant: 'فهد السالم',
                name: '05 - عقود',
                document_count: 1,
                documents: [
                    { vault_id: 'doc001', brief_arabic_title: 'عقد', is_manual: 0, tenant_id: 10 }
                ]
            }
        ];
        toggleDocSelection('doc001', true);

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => [
                { id: 10, name: 'فهد السالم', start_date: '2023-01-01', is_active: true },
                { id: 20, name: 'سعد القحطاني', start_date: '2021-01-01', end_date: '2022-12-31', is_active: false }
            ]
        });

        await populateBatchTenantSelect('batch-move-tenant-select');

        const select = document.getElementById('batch-move-tenant-select');
        // Contains ONLY the actual house tenants - NO artificial "keep current tenant" options
        expect(select.options.length).toBe(2);
        expect(select.innerHTML).not.toContain('الاحتفاظ');
        expect(select.innerHTML).not.toContain('Keep');
        expect(select.innerHTML).not.toContain('🏛️');
        expect(select.innerHTML).not.toContain('🟢');
        expect(select.innerHTML).not.toContain('👤');

        // Real tenant options
        expect(select.options[0].value).toBe('10');
        expect(select.options[0].textContent).toBe('فهد السالم (المستأجر الحالي)');
        expect(select.options[1].value).toBe('20');
        expect(select.options[1].textContent).toBe('سعد القحطاني (2021 – 2022)');

        // Pre-selected document's current tenant by default!
        expect(select.value).toBe('10');
        expect(select.options[0].selected).toBe(true);
    });

    it('pre-selects the second tenant when selecting a document belonging to that tenant', async () => {
        global.currentCategories = [
            {
                tenant: 'سعد القحطاني',
                name: '10 - صيانة',
                document_count: 1,
                documents: [
                    { vault_id: 'doc002', brief_arabic_title: 'صيانة', tenant_id: 20 }
                ]
            }
        ];
        toggleDocSelection('doc002', true);

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => [
                { id: 10, name: 'فهد السالم', start_date: '2023-01-01', is_active: true },
                { id: 20, name: 'سعد القحطاني', start_date: '2021-01-01', end_date: '2022-12-31', is_active: false }
            ]
        });

        await populateBatchTenantSelect('batch-move-tenant-select');

        const select = document.getElementById('batch-move-tenant-select');
        expect(select.options.length).toBe(2);
        expect(select.value).toBe('20');
        expect(select.options[1].selected).toBe(true);
    });

    it('submits batch move with selected target_tenant_id', async () => {
        toggleDocSelection('doc001', true);
        openBatchMoveModal();

        const folderSelect = document.getElementById('batch-move-folder-select');
        folderSelect.value = '10 - صيانة';

        const tenantSelect = document.getElementById('batch-move-tenant-select');
        const opt = document.createElement('option');
        opt.value = '42';
        opt.textContent = '🟢 جديد';
        tenantSelect.appendChild(opt);
        tenantSelect.value = '42';

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                status: 'success',
                moved_count: 1,
                target_category: '10 - صيانة',
                vault_ids: ['doc001']
            })
        });

        await handleBatchMoveSubmit();

        expect(global.fetch).toHaveBeenCalledWith(
            '/api/areas/Safra%20C/houses/500/documents/batch-move',
            expect.objectContaining({
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vault_ids: ['doc001'],
                    target_category: '10 - صيانة',
                    target_tenant_id: 42
                })
            })
        );
    });

    it('submits batch copy with selected target_tenant_id', async () => {
        toggleDocSelection('doc001', true);
        openBatchCopyModal();

        const folderSelect = document.getElementById('batch-copy-folder-select');
        folderSelect.value = '10 - صيانة';

        const tenantSelect = document.getElementById('batch-copy-tenant-select');
        const opt = document.createElement('option');
        opt.value = '55';
        opt.textContent = '🟢 مستأجر إضافي';
        tenantSelect.appendChild(opt);
        tenantSelect.value = '55';

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                status: 'success',
                copied_count: 1,
                target_category: '10 - صيانة',
                copied_vault_ids: ['doc001_copy']
            })
        });

        await handleBatchCopySubmit();

        expect(global.fetch).toHaveBeenCalledWith(
            '/api/areas/Safra%20C/houses/500/documents/batch-copy',
            expect.objectContaining({
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vault_ids: ['doc001'],
                    target_category: '10 - صيانة',
                    target_tenant_id: 55
                })
            })
        );
    });

    it('verifies #batch-copy-modal in index.html no longer contains the amber note element', () => {
        const fs = require('fs');
        const path = require('path');
        const html = fs.readFileSync(path.resolve(__dirname, '../../../src/api/static/index.html'), 'utf-8');
        expect(html).not.toContain('النسخ يتيح ظهور الوثائق في مجلد إضافي');
        expect(html).not.toContain('ملاحظة: النسخ يتيح ظهور');
    });
});

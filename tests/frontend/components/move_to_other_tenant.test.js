import { describe, it, expect, beforeEach, vi } from 'vitest';

const {
    renderCategories,
    openBatchMoveModal,
    openBatchMoveForDoc,
    handleBatchMoveSubmit,
    removeDocFromDom,
    isMovingToOtherTenant,
    populateBatchTenantSelect,
    toggleDocSelection,
    deselectAllDocs,
    resetCategoryOpenState,
} = require('../../../src/api/static/js/categories-view.js');

function setupDOM() {
    document.body.innerHTML = `
        <div id="stats-badge" class="hidden"></div>
        <div id="document-list"></div>

        <div id="batch-action-bar" class="hidden">
            <span id="batch-selected-count">0 Selected</span>
            <button id="btn-batch-move" type="button">Move Selected</button>
            <button id="btn-batch-copy" type="button">Copy Selected</button>
            <button id="btn-batch-delete" type="button">Delete Selected</button>
            <button id="btn-batch-deselect" type="button">✕</button>
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
    `;
}

describe('Move Document(s) to Another Tenant in the Same House', () => {
    beforeEach(() => {
        resetCategoryOpenState();
        setupDOM();
        global.currentArea = 'Safra C';
        global.currentHouse = '500';
        global.currentTenant = 'خالد العتيبي';
        window.currentTenant = 'خالد العتيبي';
        global.showToast = vi.fn();
        window.showToast = global.showToast;
        window.refreshCurrentTab = vi.fn().mockResolvedValue(true);

        global.currentCategories = [
            {
                tenant: 'خالد العتيبي',
                name: '01 - بيانات أساسية',
                document_count: 2,
                documents: [
                    { vault_id: 'doc001', brief_arabic_title: 'هوية وطنية', is_manual: 0, notes: '', tenant_id: 1, tenant: 'خالد العتيبي', category: '01 - بيانات أساسية' },
                    { vault_id: 'doc002', brief_arabic_title: 'سجل تجاري', is_manual: 0, notes: '', tenant_id: 1, tenant: 'خالد العتيبي', category: '01 - بيانات أساسية' }
                ]
            },
            {
                tenant: 'خالد العتيبي',
                name: '05 - عقود',
                document_count: 1,
                documents: [
                    { vault_id: 'doc003', brief_arabic_title: 'عقد إيجار 2024', is_manual: 1, notes: '', tenant_id: 1, tenant: 'خالد العتيبي', category: '05 - عقود' }
                ]
            }
        ];
    });

    it('detects when moving to another tenant vs same tenant', () => {
        const tenantSelect = document.getElementById('batch-move-tenant-select');
        tenantSelect.dataset.sourceTenantId = '1';
        tenantSelect.dataset.sourceTenantName = 'خالد العتيبي';

        // Same tenant (target is 1)
        expect(isMovingToOtherTenant('1', ['doc001'], null)).toBe(false);

        // Different tenant (target is 2)
        expect(isMovingToOtherTenant('2', ['doc001'], null)).toBe(true);

        // Empty target tenant value (defaults to preserve tenancy)
        expect(isMovingToOtherTenant('', ['doc001'], null)).toBe(false);

        // Single doc target with tenant_id: 1, moving to 2
        expect(isMovingToOtherTenant('2', [], { vault_id: 'doc001', tenant_id: 1 })).toBe(true);

        // Single doc target with tenant_id: 2, moving to 2
        tenantSelect.dataset.sourceTenantId = '2';
        expect(isMovingToOtherTenant('2', [], { vault_id: 'doc001', tenant_id: 2 })).toBe(false);
    });

    it('removeDocFromDom removes document element and decrements folder count badge', () => {
        renderCategories();

        const docListEl = document.getElementById('document-list');
        const doc1El = docListEl.querySelector('[data-vault-id="doc001"]');
        expect(doc1El).not.toBeNull();

        const folder1 = docListEl.querySelector('.category-folder-card[data-category-name="01 - بيانات أساسية"]');
        const countBadge = folder1.querySelector('.doc-count-badge');
        expect(countBadge.textContent).toBe('2');

        const ok = removeDocFromDom('doc001', '01 - بيانات أساسية');
        expect(ok).toBe(true);

        // Document element must be removed from DOM
        expect(docListEl.querySelector('[data-vault-id="doc001"]')).toBeNull();
        // Count badge decremented to 1
        expect(countBadge.textContent).toBe('1');
        // Remaining doc is still in DOM
        expect(docListEl.querySelector('[data-vault-id="doc002"]')).not.toBeNull();
    });

    it('removeDocFromDom causes empty folder to disappear when its last document is removed', () => {
        renderCategories();

        const docListEl = document.getElementById('document-list');
        const folderContracts = docListEl.querySelector('.category-folder-card[data-category-name="05 - عقود"]');
        expect(folderContracts).not.toBeNull();
        expect(folderContracts.querySelector('.doc-count-badge').textContent).toBe('1');

        // Remove doc003 (only doc in 05 - عقود)
        removeDocFromDom('doc003', '05 - عقود');

        // Folder card must be completely removed from DOM
        expect(docListEl.querySelector('.category-folder-card[data-category-name="05 - عقود"]')).toBeNull();
    });

    it('shows empty state message when all documents are removed across all folders', () => {
        renderCategories();

        const docListEl = document.getElementById('document-list');
        removeDocFromDom('doc001', '01 - بيانات أساسية');
        removeDocFromDom('doc002', '01 - بيانات أساسية');
        removeDocFromDom('doc003', '05 - عقود');

        expect(docListEl.querySelectorAll('.category-folder-card').length).toBe(0);
        expect(docListEl.textContent).toContain('No folders found for this selection.');
    });

    it('single document move to another tenant makes document disappear and triggers refreshCurrentTab', async () => {
        renderCategories();

        const docToMove = global.currentCategories[0].documents[0]; // doc001 (tenant 1)
        openBatchMoveForDoc(docToMove);

        const modal = document.getElementById('batch-move-modal');
        expect(modal.classList.contains('hidden')).toBe(false);

        const folderSelect = document.getElementById('batch-move-folder-select');
        folderSelect.value = '01 - بيانات أساسية';

        const tenantSelect = document.getElementById('batch-move-tenant-select');
        // Source tenant is 1 (خالد العتيبي)
        tenantSelect.dataset.sourceTenantId = '1';
        tenantSelect.dataset.sourceTenantName = 'خالد العتيبي';

        const opt1 = document.createElement('option');
        opt1.value = '1';
        opt1.textContent = '🟢 خالد العتيبي';
        const opt2 = document.createElement('option');
        opt2.value = '2';
        opt2.textContent = '👤 محمد مبارك';
        tenantSelect.appendChild(opt1);
        tenantSelect.appendChild(opt2);

        // User selects Tenant 2
        tenantSelect.value = '2';

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                status: 'success',
                moved_count: 1,
                target_category: '01 - بيانات أساسية',
                vault_ids: ['doc001']
            })
        });

        await handleBatchMoveSubmit();

        // 1. Modal closed
        expect(modal.classList.contains('hidden')).toBe(true);

        // 2. Document 001 must have disappeared from the DOM!
        const docListEl = document.getElementById('document-list');
        expect(docListEl.querySelector('[data-vault-id="doc001"]')).toBeNull();

        // 3. Source folder badge updated from 2 to 1
        const folder1 = docListEl.querySelector('.category-folder-card[data-category-name="01 - بيانات أساسية"]');
        expect(folder1.querySelector('.doc-count-badge').textContent).toBe('1');

        // 4. Toast shown
        expect(global.showToast).toHaveBeenCalledWith(
            expect.stringContaining('Successfully moved document'),
            'success'
        );

        // 5. refreshCurrentTab called to sync server state
        expect(window.refreshCurrentTab).toHaveBeenCalledWith('Safra C', '500');
    });

    it('multi-select batch move to another tenant makes all selected documents disappear immediately', async () => {
        renderCategories();

        const docListEl = document.getElementById('document-list');
        expect(docListEl.querySelector('[data-vault-id="doc001"]')).not.toBeNull();
        expect(docListEl.querySelector('[data-vault-id="doc002"]')).not.toBeNull();

        // Select doc001 and doc002
        toggleDocSelection('doc001', true);
        toggleDocSelection('doc002', true);

        openBatchMoveModal();

        const folderSelect = document.getElementById('batch-move-folder-select');
        folderSelect.value = '01 - بيانات أساسية';

        const tenantSelect = document.getElementById('batch-move-tenant-select');
        tenantSelect.dataset.sourceTenantId = '1';
        tenantSelect.dataset.sourceTenantName = 'خالد العتيبي';

        const opt1 = document.createElement('option');
        opt1.value = '1';
        opt1.textContent = '🟢 خالد العتيبي';
        const opt2 = document.createElement('option');
        opt2.value = '2';
        opt2.textContent = '👤 محمد مبارك';
        tenantSelect.appendChild(opt1);
        tenantSelect.appendChild(opt2);

        // User selects Tenant 2
        tenantSelect.value = '2';

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                status: 'success',
                moved_count: 2,
                target_category: '01 - بيانات أساسية',
                vault_ids: ['doc001', 'doc002']
            })
        });

        await handleBatchMoveSubmit();

        // Both documents must be gone from DOM
        expect(docListEl.querySelector('[data-vault-id="doc001"]')).toBeNull();
        expect(docListEl.querySelector('[data-vault-id="doc002"]')).toBeNull();

        // Because doc001 and doc002 were the only docs in '01 - بيانات أساسية', the folder card must disappear
        expect(docListEl.querySelector('.category-folder-card[data-category-name="01 - بيانات أساسية"]')).toBeNull();

        // Only '05 - عقود' folder remains with doc003
        expect(docListEl.querySelector('.category-folder-card[data-category-name="05 - عقود"]')).not.toBeNull();

        // refreshCurrentTab called to sync server state
        expect(window.refreshCurrentTab).toHaveBeenCalledWith('Safra C', '500');
    });

    it('moving to SAME tenant moves document between category folders in DOM without disappearing from tenant view', async () => {
        renderCategories();

        const docListEl = document.getElementById('document-list');
        const sourceFolder = docListEl.querySelector('.category-folder-card[data-category-name="01 - بيانات أساسية"]');
        const targetFolder = docListEl.querySelector('.category-folder-card[data-category-name="05 - عقود"]');

        expect(sourceFolder.querySelector('.doc-count-badge').textContent).toBe('2');
        expect(targetFolder.querySelector('.doc-count-badge').textContent).toBe('1');

        toggleDocSelection('doc001', true);
        openBatchMoveModal();

        const folderSelect = document.getElementById('batch-move-folder-select');
        folderSelect.value = '05 - عقود';

        const tenantSelect = document.getElementById('batch-move-tenant-select');
        tenantSelect.dataset.sourceTenantId = '1';

        const opt1 = document.createElement('option');
        opt1.value = '1';
        opt1.textContent = '🟢 خالد العتيبي';
        tenantSelect.appendChild(opt1);
        tenantSelect.value = '1'; // Same tenant!

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                status: 'success',
                moved_count: 1,
                target_category: '05 - عقود',
                vault_ids: ['doc001']
            })
        });

        await handleBatchMoveSubmit();

        // Document still in the view, but moved to target folder
        expect(docListEl.querySelector('[data-vault-id="doc001"]')).not.toBeNull();
        expect(targetFolder.querySelector('[data-vault-id="doc001"]')).not.toBeNull();
        expect(sourceFolder.querySelector('.doc-count-badge').textContent).toBe('1');
        expect(targetFolder.querySelector('.doc-count-badge').textContent).toBe('2');
    });
});

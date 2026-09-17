import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

const {
    initBatchOperations,
    updateBatchActionBar,
    openBatchMergeModal,
    selectedDocIds,
    toggleDocSelection,
    deselectAllDocs
} = require('../../../src/HousingApplication.Web/wwwroot/js/categories-view.js');

const {
    initDocManager,
    openMergeModal,
    closeMergeModal,
    handleMergeDocsSubmit,
    renderMergeDocsList,
    moveMergeDocUp,
    moveMergeDocDown,
    removeMergeDoc,
    handleAddDocToMergeList,
    getActiveMergeDocs,
    openDocDropdownMenu,
    closeDocDropdownMenu
} = require('../../../src/HousingApplication.Web/wwwroot/js/doc-manager.js');

function setupDOM() {
    document.body.innerHTML = `
        <!-- Viewer Header -->
        <button id="viewer-edit-pages-btn" type="button"></button>
        <button id="viewer-merge-btn" type="button"></button>

        <!-- Doc Action Modal -->
        <div id="doc-action-modal" class="hidden">
            <button id="btn-doc-edit-pages" type="button"></button>
            <button id="btn-doc-merge" type="button"></button>
            <button id="doc-modal-cancel" type="button"></button>
            <button id="doc-modal-close" type="button"></button>
            <button id="doc-modal-submit" type="button">
                <span id="doc-modal-submit-text">Apply</span>
            </button>
            <button id="btn-doc-delete" type="button"></button>
        </div>

        <!-- Floating Batch Action Bar -->
        <div id="batch-action-bar" class="hidden">
            <span id="batch-selected-count">0 selected</span>
            <button id="btn-batch-move" type="button">Move Selected</button>
            <button id="btn-batch-copy" type="button">Copy Selected</button>
            <button id="btn-batch-merge" type="button" disabled>Merge Selected</button>
            <button id="btn-batch-delete" type="button">Delete Selected</button>
            <button id="btn-batch-deselect" type="button">Deselect</button>
        </div>

        <!-- Document Merge Modal -->
        <div id="merge-docs-modal" class="hidden">
            <h3 id="merge-docs-title">Merge Documents</h3>
            <span id="merge-docs-count-badge">0 docs • 0 pages</span>
            <div id="merge-docs-list"></div>
            <div id="merge-add-doc-container">
                <select id="merge-add-doc-select"></select>
                <button id="btn-merge-add-doc" type="button">+ Add</button>
            </div>
            <input id="merge-target-title" type="text" />
            <select id="merge-target-category"></select>
            <div id="merge-custom-cat-container" class="hidden">
                <input id="merge-custom-cat-input" type="text" />
            </div>
            <select id="merge-target-tenant"></select>
            <input id="merge-target-date" type="date" />
            <input id="merge-target-notes" type="text" />
            <input id="merge-delete-sources" type="checkbox" checked />
            <div id="merge-docs-status" class="hidden"></div>
            <button id="merge-docs-close" type="button"></button>
            <button id="btn-merge-docs-cancel" type="button"></button>
            <button id="btn-merge-docs-confirm" type="button">
                <span id="merge-docs-spinner" class="hidden"></span>
                <span id="merge-docs-btn-text">Merge</span>
            </button>
        </div>
    `;
}

describe('Document Merge Feature', () => {
    beforeEach(() => {
        setupDOM();
        selectedDocIds.clear();
        global.currentArea = 'Safra C';
        global.currentHouse = '514';
        global.currentTenant = null;
        global.showToast = vi.fn();
        global.refreshCurrentTab = vi.fn();
        global.loadTree = vi.fn();
        global.openDocument = vi.fn();
        global.openMergeModal = vi.fn(openMergeModal);
        window.openMergeModal = global.openMergeModal;

        global.currentCategories = [
            {
                name: '01 - بيانات أساسية',
                document_count: 2,
                documents: [
                    {
                        vault_id: 'doc_aaa111',
                        title: 'عقد الإيجار الأصلي',
                        brief_arabic_title: 'عقد الإيجار',
                        category: '01 - بيانات أساسية',
                        page_count: 3,
                        tenant: 'أحمد محمود',
                        tenant_id: 1,
                        primary_date: '2024-01-15'
                    },
                    {
                        vault_id: 'doc_bbb222',
                        title: 'البطاقة المدنية',
                        brief_arabic_title: 'الهوية الشخصية',
                        category: '01 - بيانات أساسية',
                        page_count: 2,
                        tenant: 'أحمد محمود',
                        tenant_id: 1,
                        primary_date: '2024-01-16'
                    }
                ]
            },
            {
                name: '05 - عقود',
                document_count: 1,
                documents: [
                    {
                        vault_id: 'doc_ccc333',
                        title: 'ملحق العقد',
                        brief_arabic_title: 'الملحق الإضافي',
                        category: '05 - عقود',
                        page_count: 1,
                        tenant: 'أحمد محمود',
                        tenant_id: 1,
                        primary_date: '2024-02-01'
                    }
                ]
            }
        ];

        global.fetch = vi.fn().mockImplementation(async (url, options) => {
            if (typeof url === 'string' && url.includes('/tenants')) {
                return {
                    ok: true,
                    json: async () => [
                        { id: 1, name: 'أحمد محمود', start_date: '2024-01-01' },
                        { id: 2, name: 'سارة خالد', start_date: '2025-01-01' }
                    ]
                };
            }
            if (typeof url === 'string' && url.includes('/merge')) {
                const body = JSON.parse(options.body);
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        merged_vault_id: 'doc_merged999',
                        merged_category: body.target_category || '01 - بيانات أساسية',
                        merged_title: body.target_title,
                        total_pages: 5,
                        source_vault_ids: body.vault_ids,
                        sources_deleted: body.delete_sources
                    })
                };
            }
            return { ok: true, json: async () => ({}) };
        });

        initBatchOperations();
        initDocManager();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('Batch Action Bar Integration', () => {
        it('disables merge button when fewer than 2 documents are selected', () => {
            const btnMerge = document.getElementById('btn-batch-merge');
            updateBatchActionBar();
            expect(btnMerge.disabled).toBe(true);

            toggleDocSelection('doc_aaa111', true);
            updateBatchActionBar();
            expect(btnMerge.disabled).toBe(true);
        });

        it('enables merge button when 2 or more documents are selected', () => {
            const btnMerge = document.getElementById('btn-batch-merge');
            toggleDocSelection('doc_aaa111', true);
            toggleDocSelection('doc_bbb222', true);
            updateBatchActionBar();
            expect(btnMerge.disabled).toBe(false);
        });

        it('openBatchMergeModal collects selected docs and calls openMergeModal', () => {
            toggleDocSelection('doc_aaa111', true);
            toggleDocSelection('doc_bbb222', true);

            openBatchMergeModal();

            expect(global.openMergeModal).toHaveBeenCalledTimes(1);
            const passedDocs = global.openMergeModal.mock.calls[0][0];
            expect(passedDocs).toHaveLength(2);
            expect(passedDocs[0].vault_id).toBe('doc_aaa111');
            expect(passedDocs[1].vault_id).toBe('doc_bbb222');
        });
    });

    describe('Merge Modal UI & Document Reordering', () => {
        it('opens merge modal with initial documents and calculates total pages', async () => {
            const doc1 = global.currentCategories[0].documents[0];
            const doc2 = global.currentCategories[0].documents[1];

            await openMergeModal([doc1, doc2]);

            const modal = document.getElementById('merge-docs-modal');
            expect(modal.classList.contains('hidden')).toBe(false);

            const badge = document.getElementById('merge-docs-count-badge');
            expect(badge.textContent).toContain('2 docs • 5 pages');

            const activeDocs = getActiveMergeDocs();
            expect(activeDocs).toHaveLength(2);
            expect(activeDocs[0].vault_id).toBe('doc_aaa111');
            expect(activeDocs[1].vault_id).toBe('doc_bbb222');

            const titleInput = document.getElementById('merge-target-title');
            expect(titleInput.value).toContain('عقد الإيجار + الهوية الشخصية');
        });

        it('allows reordering documents with moveMergeDocUp and moveMergeDocDown', async () => {
            const doc1 = global.currentCategories[0].documents[0];
            const doc2 = global.currentCategories[0].documents[1];

            await openMergeModal([doc1, doc2]);

            expect(getActiveMergeDocs()[0].vault_id).toBe('doc_aaa111');
            expect(getActiveMergeDocs()[1].vault_id).toBe('doc_bbb222');

            // Move second document UP
            moveMergeDocUp(1);
            expect(getActiveMergeDocs()[0].vault_id).toBe('doc_bbb222');
            expect(getActiveMergeDocs()[1].vault_id).toBe('doc_aaa111');

            // Move first document DOWN
            moveMergeDocDown(0);
            expect(getActiveMergeDocs()[0].vault_id).toBe('doc_aaa111');
            expect(getActiveMergeDocs()[1].vault_id).toBe('doc_bbb222');
        });

        it('allows adding an additional document from house dropdown', async () => {
            const doc1 = global.currentCategories[0].documents[0];
            const doc2 = global.currentCategories[0].documents[1];

            await openMergeModal([doc1, doc2]);
            expect(getActiveMergeDocs()).toHaveLength(2);

            const addSelect = document.getElementById('merge-add-doc-select');
            // doc_ccc333 from '05 - عقود' should be in the dropdown
            expect(addSelect.children.length).toBeGreaterThan(1);

            addSelect.value = 'doc_ccc333';
            handleAddDocToMergeList();

            expect(getActiveMergeDocs()).toHaveLength(3);
            expect(getActiveMergeDocs()[2].vault_id).toBe('doc_ccc333');

            const badge = document.getElementById('merge-docs-count-badge');
            // 3 + 2 + 1 = 6 pages
            expect(badge.textContent).toContain('3 docs • 6 pages');
        });

        it('allows removing a document from merge list', async () => {
            const doc1 = global.currentCategories[0].documents[0];
            const doc2 = global.currentCategories[0].documents[1];

            await openMergeModal([doc1, doc2]);
            expect(getActiveMergeDocs()).toHaveLength(2);

            removeMergeDoc(0);
            expect(getActiveMergeDocs()).toHaveLength(1);
            expect(getActiveMergeDocs()[0].vault_id).toBe('doc_bbb222');

            const badge = document.getElementById('merge-docs-count-badge');
            expect(badge.textContent).toContain('1 doc • 2 pages');
        });
    });

    describe('Validation & API Submission', () => {
        it('blocks submission if fewer than 2 documents are in merge list', async () => {
            const doc1 = global.currentCategories[0].documents[0];
            await openMergeModal([doc1]);

            await handleMergeDocsSubmit();

            expect(global.fetch).not.toHaveBeenCalledWith(expect.stringContaining('/merge'), expect.anything());
            const status = document.getElementById('merge-docs-status');
            expect(status.classList.contains('hidden')).toBe(false);
            expect(status.textContent).toContain('يرجى اختيار وثيقتين على الأقل للدمج');
        });

        it('blocks submission if target title is empty', async () => {
            const doc1 = global.currentCategories[0].documents[0];
            const doc2 = global.currentCategories[0].documents[1];
            await openMergeModal([doc1, doc2]);

            document.getElementById('merge-target-title').value = '   ';
            await handleMergeDocsSubmit();

            expect(global.fetch).not.toHaveBeenCalledWith(expect.stringContaining('/merge'), expect.anything());
            const status = document.getElementById('merge-docs-status');
            expect(status.classList.contains('hidden')).toBe(false);
            expect(status.textContent).toContain('عنوان للمستند المدمج');
        });

        it('submits valid merge request, calls API, refreshes tabs, and opens merged document', async () => {
            const doc1 = global.currentCategories[0].documents[0];
            const doc2 = global.currentCategories[0].documents[1];
            await openMergeModal([doc1, doc2]);

            document.getElementById('merge-target-title').value = 'عقد الإيجار الكامل مع الهوية';
            document.getElementById('merge-target-category').value = '01 - بيانات أساسية';
            document.getElementById('merge-delete-sources').checked = true;

            await handleMergeDocsSubmit();

            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/areas/Safra%20C/houses/514/documents/merge'),
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify({
                        vault_ids: ['doc_aaa111', 'doc_bbb222'],
                        target_title: 'عقد الإيجار الكامل مع الهوية',
                        target_category: '01 - بيانات أساسية',
                        target_tenant_id: 1,
                        target_date: '2024-01-15',
                        target_notes: null,
                        delete_sources: true
                    })
                })
            );

            // Modal closes
            const modal = document.getElementById('merge-docs-modal');
            expect(modal.classList.contains('hidden')).toBe(true);

            // Toast shown
            expect(global.showToast).toHaveBeenCalledWith(expect.stringContaining('تم دمج'), 'success');

            // Refresh triggered
            expect(global.refreshCurrentTab).toHaveBeenCalledWith('Safra C', '514');
            expect(global.loadTree).toHaveBeenCalled();

            // Document viewer opened with merged doc
            expect(global.openDocument).toHaveBeenCalledWith('doc_merged999', '01 - بيانات أساسية', false);
        });
    });

    describe('3-Dots Menu & Doc Modal Triggers', () => {
        it('includes Merge Document option in 3-dots dropdown menu', () => {
            const doc = global.currentCategories[0].documents[0];
            const btn = document.createElement('button');
            document.body.appendChild(btn);

            openDocDropdownMenu(new MouseEvent('click'), doc, '01 - بيانات أساسية', btn);

            const mergeItem = document.querySelector('.doc-menu-item-merge');
            expect(mergeItem).not.toBeNull();
            expect(mergeItem.textContent).toContain('Merge Document');

            mergeItem.click();
            expect(global.openMergeModal).toHaveBeenCalledTimes(1);
            expect(global.openMergeModal.mock.calls[0][0][0].vault_id).toBe('doc_aaa111');
        });

        it('wires btn-doc-merge inside doc-action-modal to openMergeModal', () => {
            const docBtn = document.getElementById('btn-doc-merge');
            expect(docBtn).not.toBeNull();
            expect(typeof docBtn.onclick).toBe('function');
        });
    });
});

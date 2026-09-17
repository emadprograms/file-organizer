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
    handleSwapMergeDocs,
    showMergeStep,
    updateMergeOrderSummary,
    handleReorderContinue,
    handlePickContinue,
    handleSaveBack,
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
            <p id="merge-docs-subtitle">Combine documents into one PDF</p>
            <span id="merge-docs-count-badge">0 docs • 0 pages</span>
            <button id="merge-docs-close" type="button"></button>

            <!-- Reorder Step (for >2 docs) -->
            <div id="merge-step-reorder" class="hidden">
                <div id="merge-docs-list"></div>
                <div id="merge-add-doc-container">
                    <select id="merge-add-doc-select"></select>
                    <button id="btn-merge-add-doc" type="button">+ Add</button>
                </div>
                <button id="btn-merge-reorder-cancel" type="button">Cancel</button>
                <button id="btn-merge-reorder-continue" type="button">Continue</button>
            </div>

            <!-- Pick Step (for 1 doc) -->
            <div id="merge-step-pick" class="hidden">
                <div id="merge-pick-first-doc-title"></div>
                <select id="merge-pick-second-select"></select>
                <button id="btn-merge-pick-cancel" type="button">Cancel</button>
                <button id="btn-merge-pick-continue" type="button">Continue</button>
            </div>

            <!-- Save Step (direct for 2 docs or after continue) -->
            <div id="merge-step-save" class="hidden">
                <div id="merge-order-banner">
                    <span id="merge-order-summary"></span>
                    <button id="btn-merge-swap-order" type="button">Swap</button>
                </div>
                <input id="merge-target-title" type="text" />
                <select id="merge-target-category"></select>
                <div id="merge-custom-cat-container" class="hidden">
                    <input id="merge-custom-cat-input" type="text" />
                </div>
                <select id="merge-target-tenant"></select>
                <input id="merge-target-date" type="hidden" />
                <input id="merge-target-notes" type="hidden" />
                <input id="merge-delete-sources" type="checkbox" checked />
                <div id="merge-docs-status" class="hidden"></div>
                <button id="btn-merge-save-back" type="button" class="hidden">Back</button>
                <button id="btn-merge-docs-cancel" type="button">Cancel</button>
                <button id="btn-merge-docs-confirm" type="button">
                    <span id="merge-docs-spinner" class="hidden"></span>
                    <span id="merge-docs-btn-text">Merge</span>
                </button>
            </div>
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
        it('opens merge modal directly to Save & Name step when exactly 2 documents are selected', async () => {
            const doc1 = global.currentCategories[0].documents[0];
            const doc2 = global.currentCategories[0].documents[1];

            await openMergeModal([doc1, doc2]);

            const modal = document.getElementById('merge-docs-modal');
            expect(modal.classList.contains('hidden')).toBe(false);

            // Step 3 (Save) should be visible; Step 1 (Reorder) should be hidden
            const saveStep = document.getElementById('merge-step-save');
            const reorderStep = document.getElementById('merge-step-reorder');
            expect(saveStep.classList.contains('hidden')).toBe(false);
            expect(reorderStep.classList.contains('hidden')).toBe(true);

            // Badge displays counts
            const badge = document.getElementById('merge-docs-count-badge');
            expect(badge.textContent).toContain('2 docs • 5 pages');

            // Name defaults to first doc's title
            const titleInput = document.getElementById('merge-target-title');
            expect(titleInput.value).toBe('عقد الإيجار');

            // Category defaults to first doc's category
            const catSelect = document.getElementById('merge-target-category');
            expect(catSelect.value).toBe('01 - بيانات أساسية');

            // Order summary shows doc 1 -> doc 2
            const orderSummary = document.getElementById('merge-order-summary');
            expect(orderSummary.textContent).toContain('عقد الإيجار → الهوية الشخصية');

            // Date is inherited from doc 1
            const dateInput = document.getElementById('merge-target-date');
            expect(dateInput.value).toBe('2024-01-15');
        });

        it('swaps document order and updates defaults when Swap button is clicked', async () => {
            const doc1 = global.currentCategories[0].documents[0];
            const doc2 = global.currentCategories[0].documents[1];

            await openMergeModal([doc1, doc2]);

            expect(getActiveMergeDocs()[0].vault_id).toBe('doc_aaa111');
            expect(getActiveMergeDocs()[1].vault_id).toBe('doc_bbb222');

            // Click Swap
            handleSwapMergeDocs();

            expect(getActiveMergeDocs()[0].vault_id).toBe('doc_bbb222');
            expect(getActiveMergeDocs()[1].vault_id).toBe('doc_aaa111');

            // Title and summary updated to doc 2
            const titleInput = document.getElementById('merge-target-title');
            expect(titleInput.value).toBe('الهوية الشخصية');

            const orderSummary = document.getElementById('merge-order-summary');
            expect(orderSummary.textContent).toContain('الهوية الشخصية → عقد الإيجار');

            const dateInput = document.getElementById('merge-target-date');
            expect(dateInput.value).toBe('2024-01-16');
        });

        it('opens rearrangement box first when more than 2 documents are selected', async () => {
            const doc1 = global.currentCategories[0].documents[0];
            const doc2 = global.currentCategories[0].documents[1];
            const doc3 = global.currentCategories[1].documents[0]; // from '05 - عقود'

            await openMergeModal([doc1, doc2, doc3]);

            const modal = document.getElementById('merge-docs-modal');
            expect(modal.classList.contains('hidden')).toBe(false);

            // Reorder step is visible; Save step is hidden
            const reorderStep = document.getElementById('merge-step-reorder');
            const saveStep = document.getElementById('merge-step-save');
            expect(reorderStep.classList.contains('hidden')).toBe(false);
            expect(saveStep.classList.contains('hidden')).toBe(true);

            expect(getActiveMergeDocs()).toHaveLength(3);

            // Move doc 3 from index 2 up to index 1 then index 0
            moveMergeDocUp(2);
            moveMergeDocUp(1);
            expect(getActiveMergeDocs()[0].vault_id).toBe('doc_ccc333');

            // Click Continue to Save & Name view
            handleReorderContinue();

            expect(reorderStep.classList.contains('hidden')).toBe(true);
            expect(saveStep.classList.contains('hidden')).toBe(false);

            // Title, category, and date inherited from the new first doc (doc_ccc333)
            const titleInput = document.getElementById('merge-target-title');
            expect(titleInput.value).toBe('الملحق الإضافي');

            const catSelect = document.getElementById('merge-target-category');
            expect(catSelect.value).toBe('05 - عقود');

            const dateInput = document.getElementById('merge-target-date');
            expect(dateInput.value).toBe('2024-02-01');
        });

        it('opens pick step when exactly 1 document is selected', async () => {
            const doc1 = global.currentCategories[0].documents[0];

            await openMergeModal([doc1]);

            const pickStep = document.getElementById('merge-step-pick');
            const saveStep = document.getElementById('merge-step-save');
            const reorderStep = document.getElementById('merge-step-reorder');
            expect(pickStep.classList.contains('hidden')).toBe(false);
            expect(saveStep.classList.contains('hidden')).toBe(true);
            expect(reorderStep.classList.contains('hidden')).toBe(true);

            const firstDocTitle = document.getElementById('merge-pick-first-doc-title');
            expect(firstDocTitle.textContent).toBe('عقد الإيجار');

            const pickSelect = document.getElementById('merge-pick-second-select');
            expect(pickSelect.children.length).toBeGreaterThan(1);

            // Pick second document and continue
            pickSelect.value = 'doc_bbb222';
            handlePickContinue();

            expect(pickStep.classList.contains('hidden')).toBe(true);
            expect(saveStep.classList.contains('hidden')).toBe(false);
            expect(getActiveMergeDocs()).toHaveLength(2);
        });

        it('allows adding an additional document from house dropdown and removing a doc', async () => {
            const doc1 = global.currentCategories[0].documents[0];
            const doc2 = global.currentCategories[0].documents[1];

            await openMergeModal([doc1, doc2]);
            expect(getActiveMergeDocs()).toHaveLength(2);

            const addSelect = document.getElementById('merge-add-doc-select');
            expect(addSelect.children.length).toBeGreaterThan(1);

            addSelect.value = 'doc_ccc333';
            handleAddDocToMergeList();

            expect(getActiveMergeDocs()).toHaveLength(3);
            expect(getActiveMergeDocs()[2].vault_id).toBe('doc_ccc333');

            const badge = document.getElementById('merge-docs-count-badge');
            // 3 + 2 + 1 = 6 pages
            expect(badge.textContent).toContain('3 docs • 6 pages');

            removeMergeDoc(0);
            expect(getActiveMergeDocs()).toHaveLength(2);
            expect(getActiveMergeDocs()[0].vault_id).toBe('doc_bbb222');
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

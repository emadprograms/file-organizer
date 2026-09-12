import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

const {
    openDocDropdownMenu,
    closeDocDropdownMenu,
    showDocInTimeline,
    showDocInCategories,
    handleToggleDocPin,
    handleDeleteSingleDoc,
} = require('../../../src/api/static/js/doc-manager.js');

const {
    renderCategories,
    openBatchMoveForDoc,
    openBatchCopyForDoc,
    getSingleTargetDoc,
    closeBatchMoveModal,
    closeBatchCopyModal,
    handleBatchMoveSubmit,
    handleBatchCopySubmit,
    deselectAllDocs,
} = require('../../../src/api/static/js/categories-view.js');

const {
    renderTimeline,
} = require('../../../src/api/static/js/timeline-view.js');

describe('Document 3-Dots Dropdown Menu & Categories Date Badge', () => {
    let mockDoc;

    beforeEach(() => {
        if (typeof deselectAllDocs === 'function') {
            deselectAllDocs();
        }
        if (typeof closeBatchMoveModal === 'function') {
            closeBatchMoveModal();
        }
        if (typeof closeBatchCopyModal === 'function') {
            closeBatchCopyModal();
        }

        document.body.innerHTML = `
            <div id="tab-timeline" class="tab-btn">Timeline</div>
            <div id="tab-categories" class="tab-btn">Categories</div>
            <div id="categories-list"></div>
            <div id="document-list"></div>
            <div id="batch-action-bar" class="hidden"></div>
            <div id="batch-move-modal" class="hidden">
                <span id="batch-move-subtitle"></span>
                <select id="batch-move-folder-select"></select>
                <button id="btn-batch-move-confirm"></button>
                <span id="batch-move-spinner" class="hidden"></span>
            </div>
            <div id="batch-copy-modal" class="hidden">
                <span id="batch-copy-subtitle"></span>
                <select id="batch-copy-folder-select"></select>
                <button id="btn-batch-copy-confirm"></button>
                <span id="batch-copy-spinner" class="hidden"></span>
            </div>
            <div id="doc-action-modal" class="hidden"></div>
        `;

        global.currentArea = 'Safra C';
        global.currentHouse = '514';
        global.currentTab = 'categories';
        global.showToast = vi.fn();
        global.refreshCurrentTab = vi.fn();
        global.loadTree = vi.fn();
        global.confirm = vi.fn().mockReturnValue(true);

        mockDoc = {
            vault_id: 'doc_abc_123',
            brief_arabic_title: 'عقد إيجار جديد',
            filename: 'contract_01.pdf',
            category: '01 - عقود وإيجارات',
            date: '2025-06-15',
            primary_tenant: 'خالد السعدي',
            area_id: 'Safra C',
            house_id: '514'
        };

        global.fetch = vi.fn().mockImplementation(async (url, options) => {
            return {
                ok: true,
                json: async () => ({ status: 'success' })
            };
        });
    });

    afterEach(() => {
        closeDocDropdownMenu();
        vi.restoreAllMocks();
        delete global.currentArea;
        delete global.currentHouse;
        delete global.currentTab;
        delete global.currentTenant;
        delete global.showToast;
        delete global.refreshCurrentTab;
        delete global.loadTree;
        delete global.confirm;
    });

    describe('Floating Dropdown Action Menu (openDocDropdownMenu)', () => {
        it('renders floating dropdown menu with 5 actions and proper styling', () => {
            const btn = document.createElement('button');
            btn.className = 'doc-menu-btn';
            document.body.appendChild(btn);

            openDocDropdownMenu(null, mockDoc, '01 - عقود وإيجارات', btn);

            const menu = document.querySelector('.doc-dropdown-menu');
            expect(menu).not.toBeNull();
            expect(menu.getAttribute('role')).toBe('menu');

            // 6 action buttons
            const renameItem = menu.querySelector('.doc-menu-item-rename');
            const moveItem = menu.querySelector('.doc-menu-item-move');
            const copyItem = menu.querySelector('.doc-menu-item-copy');
            const pinItem = menu.querySelector('.doc-menu-item-pin');
            const timelineItem = menu.querySelector('.doc-menu-item-timeline');
            const deleteItem = menu.querySelector('.doc-menu-item-delete');

            expect(renameItem).not.toBeNull();
            expect(renameItem.textContent).toContain('Rename Document');
            expect(moveItem).not.toBeNull();
            expect(moveItem.textContent).toContain('Move Document');
            expect(copyItem).not.toBeNull();
            expect(copyItem.textContent).toContain('Copy Document');
            expect(pinItem).not.toBeNull();
            expect(pinItem.textContent).toContain('Pin Document');
            expect(timelineItem).not.toBeNull();
            expect(timelineItem.textContent).toContain('Show in Timeline');
            expect(deleteItem).not.toBeNull();
            expect(deleteItem.textContent).toContain('Delete Document');
        });

        it('toggles menu closed when clicking the trigger button again', () => {
            const btn = document.createElement('button');
            document.body.appendChild(btn);

            openDocDropdownMenu(null, mockDoc, '01 - عقود وإيجارات', btn);
            expect(document.querySelector('.doc-dropdown-menu')).not.toBeNull();

            // Second click on same trigger closes it
            openDocDropdownMenu(null, mockDoc, '01 - عقود وإيجارات', btn);
            expect(document.querySelector('.doc-dropdown-menu')).toBeNull();
        });

        it('closes the dropdown menu on Escape key press', () => {
            const btn = document.createElement('button');
            document.body.appendChild(btn);

            openDocDropdownMenu(null, mockDoc, '01 - عقود وإيجارات', btn);
            expect(document.querySelector('.doc-dropdown-menu')).not.toBeNull();

            document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
            expect(document.querySelector('.doc-dropdown-menu')).toBeNull();
        });

        it('invokes inline rename on the card title when Rename is clicked', () => {
            const card = document.createElement('div');
            card.setAttribute('data-vault-id', mockDoc.vault_id);
            const titleEl = document.createElement('span');
            titleEl.className = 'doc-title-text';
            titleEl.textContent = mockDoc.brief_arabic_title;
            const btn = document.createElement('button');
            btn.className = 'doc-menu-btn';
            card.appendChild(titleEl);
            card.appendChild(btn);
            document.body.appendChild(card);

            window.handleInlineRename = vi.fn();

            openDocDropdownMenu(null, mockDoc, '01 - عقود وإيجارات', btn);
            const menu = document.querySelector('.doc-dropdown-menu');
            const renameBtn = menu.querySelector('.doc-menu-item-rename');
            renameBtn.click();

            expect(window.handleInlineRename).toHaveBeenCalledWith(
                null,
                mockDoc,
                titleEl,
                'Safra C',
                '514'
            );
            expect(document.querySelector('.doc-dropdown-menu')).toBeNull();
        });

        it('invokes openBatchMoveForDoc when Move is clicked', () => {
            const btn = document.createElement('button');
            document.body.appendChild(btn);

            window.openBatchMoveForDoc = vi.fn();

            openDocDropdownMenu(null, mockDoc, '01 - عقود وإيجارات', btn);
            const menu = document.querySelector('.doc-dropdown-menu');
            menu.querySelector('.doc-menu-item-move').click();

            expect(window.openBatchMoveForDoc).toHaveBeenCalledWith(mockDoc);
            expect(document.querySelector('.doc-dropdown-menu')).toBeNull();
        });

        it('invokes openBatchCopyForDoc when Copy is clicked', () => {
            const btn = document.createElement('button');
            document.body.appendChild(btn);

            window.openBatchCopyForDoc = vi.fn();

            openDocDropdownMenu(null, mockDoc, '01 - عقود وإيجارات', btn);
            const menu = document.querySelector('.doc-dropdown-menu');
            menu.querySelector('.doc-menu-item-copy').click();

            expect(window.openBatchCopyForDoc).toHaveBeenCalledWith(mockDoc);
            expect(document.querySelector('.doc-dropdown-menu')).toBeNull();
        });

        it('invokes handleDeleteSingleDoc when Delete is clicked', async () => {
            const btn = document.createElement('button');
            document.body.appendChild(btn);

            openDocDropdownMenu(null, mockDoc, '01 - عقود وإيجارات', btn);
            const menu = document.querySelector('.doc-dropdown-menu');
            menu.querySelector('.doc-menu-item-delete').click();

            expect(global.confirm).toHaveBeenCalled();
            expect(global.fetch).toHaveBeenCalledWith(
                '/api/areas/Safra%20C/houses/514/documents/doc_abc_123',
                { method: 'DELETE' }
            );
            await vi.waitFor(() => {
                expect(global.refreshCurrentTab).toHaveBeenCalledWith('Safra C', '514');
            });
        });

        it('renders Unpin Document when document is pinned (is_manual = 1)', () => {
            const pinnedDoc = { ...mockDoc, is_manual: 1 };
            const btn = document.createElement('button');
            document.body.appendChild(btn);

            openDocDropdownMenu(null, pinnedDoc, '01 - عقود وإيجارات', btn);

            const menu = document.querySelector('.doc-dropdown-menu');
            const unpinItem = menu.querySelector('.doc-menu-item-unpin');
            expect(unpinItem).not.toBeNull();
            expect(unpinItem.textContent).toContain('Unpin Document');
        });

        it('invokes handleToggleDocPin to pin an unpinned document via PATCH', async () => {
            const unpinnedDoc = { ...mockDoc, is_manual: 0 };
            const btn = document.createElement('button');
            document.body.appendChild(btn);

            global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'success' }) });

            openDocDropdownMenu(null, unpinnedDoc, '01 - عقود وإيجارات', btn);
            const menu = document.querySelector('.doc-dropdown-menu');
            const pinBtn = menu.querySelector('.doc-menu-item-pin');
            pinBtn.click();

            expect(global.fetch).toHaveBeenCalledWith(
                '/api/areas/Safra%20C/houses/514/documents/doc_abc_123',
                expect.objectContaining({
                    method: 'PATCH',
                    body: JSON.stringify({ is_manual: 1 })
                })
            );
            await vi.waitFor(() => {
                expect(unpinnedDoc.is_manual).toBe(1);
            });
        });

        it('invokes handleToggleDocPin to unpin a pinned document via POST reset-lock', async () => {
            const pinnedDoc = { ...mockDoc, is_manual: 1 };
            const btn = document.createElement('button');
            document.body.appendChild(btn);

            global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'success' }) });

            openDocDropdownMenu(null, pinnedDoc, '01 - عقود وإيجارات', btn);
            const menu = document.querySelector('.doc-dropdown-menu');
            const unpinBtn = menu.querySelector('.doc-menu-item-pin');
            unpinBtn.click();

            expect(global.fetch).toHaveBeenCalledWith(
                '/api/areas/Safra%20C/houses/514/documents/doc_abc_123/reset-lock',
                expect.objectContaining({
                    method: 'POST'
                })
            );
            await vi.waitFor(() => {
                expect(pinnedDoc.is_manual).toBe(0);
            });
        });

        it('renders Show in Categories instead of Show in Timeline when in timeline view', () => {
            global.currentTab = 'timeline';
            const btn = document.createElement('button');
            document.body.appendChild(btn);

            openDocDropdownMenu(null, mockDoc, '01 - عقود وإيجارات', btn);

            const menu = document.querySelector('.doc-dropdown-menu');
            const categoriesItem = menu.querySelector('.doc-menu-item-categories');
            const timelineItem = menu.querySelector('.doc-menu-item-timeline');

            expect(categoriesItem).not.toBeNull();
            expect(categoriesItem.textContent).toContain('Show in Categories');
            expect(timelineItem).toBeNull();
            global.currentTab = 'categories';
        });

        it('renders Show in Categories when trigger button is inside #timeline-container', () => {
            const timelineContainer = document.createElement('div');
            timelineContainer.id = 'timeline-container';
            const btn = document.createElement('button');
            timelineContainer.appendChild(btn);
            document.body.appendChild(timelineContainer);

            openDocDropdownMenu(null, mockDoc, '01 - عقود وإيجارات', btn);

            const menu = document.querySelector('.doc-dropdown-menu');
            const categoriesItem = menu.querySelector('.doc-menu-item-categories');
            expect(categoriesItem).not.toBeNull();
            expect(categoriesItem.textContent).toContain('Show in Categories');
        });
    });

    describe('Show in Categories Navigation (showDocInCategories)', () => {
        it('switches to categories tab, opens folder, and highlights target document', async () => {
            global.currentTab = 'timeline';
            const tabCategories = document.getElementById('tab-categories');
            const tabClickSpy = vi.spyOn(tabCategories, 'click');

            // Setup category folder and doc card in DOM
            const docList = document.getElementById('document-list');
            const folderCard = document.createElement('div');
            folderCard.className = 'category-folder-card';
            folderCard.setAttribute('data-category-name', '01 - عقود وإيجارات');
            const docsContainer = document.createElement('div');
            docsContainer.className = 'category-docs hidden';
            const targetCard = document.createElement('div');
            targetCard.setAttribute('data-vault-id', mockDoc.vault_id);
            targetCard.className = 'category-doc-item';
            docsContainer.appendChild(targetCard);
            folderCard.appendChild(docsContainer);
            docList.appendChild(folderCard);

            targetCard.scrollIntoView = vi.fn();
            window.setSelectedDoc = vi.fn();
            window.openCategoryFolder = vi.fn();

            showDocInCategories(mockDoc);

            expect(tabClickSpy).toHaveBeenCalled();
            expect(window.openCategoryFolder).toHaveBeenCalledWith('01 - عقود وإيجارات');

            await vi.waitFor(() => {
                expect(targetCard.scrollIntoView).toHaveBeenCalled();
                expect(targetCard.classList.contains('ring-4')).toBe(true);
                expect(window.setSelectedDoc).toHaveBeenCalled();
                expect(docsContainer.classList.contains('hidden')).toBe(false);
            });
        });
    });

    describe('Show in Timeline Navigation (showDocInTimeline)', () => {
        it('switches to timeline tab and highlights the target document', async () => {
            const tabTimeline = document.getElementById('tab-timeline');
            const tabClickSpy = vi.spyOn(tabTimeline, 'click');

            // Setup timeline card in DOM
            const docList = document.getElementById('document-list');
            const targetCard = document.createElement('div');
            targetCard.setAttribute('data-vault-id', mockDoc.vault_id);
            targetCard.className = 'timeline-card';
            targetCard.scrollIntoView = vi.fn();
            docList.appendChild(targetCard);

            window.setSelectedDoc = vi.fn();
            global.currentTenant = 'Different Tenant';

            showDocInTimeline(mockDoc);

            // Cleared conflicting tenant filter
            expect(global.currentTenant).toBeNull();
            // Tab clicked
            expect(tabClickSpy).toHaveBeenCalled();

            await vi.waitFor(() => {
                expect(targetCard.scrollIntoView).toHaveBeenCalled();
                expect(targetCard.classList.contains('ring-4')).toBe(true);
                expect(targetCard.classList.contains('ring-blue-500')).toBe(true);
                expect(window.setSelectedDoc).toHaveBeenCalledWith(mockDoc, mockDoc.brief_arabic_title, targetCard);
                expect(global.showToast).toHaveBeenCalledWith('Showing document in timeline.');
            });
        });
    });

    describe('Categories View Date Badge & Menu Trigger', () => {
        it('renders document date badge with light gray background directly before 3-dots button', () => {
            const testCats = [
                {
                    name: '01 - عقود وإيجارات',
                    document_count: 2,
                    documents: [
                        {
                            vault_id: 'doc_date_test_1',
                            brief_arabic_title: 'عقد شقة 10',
                            date: '2024-03-20',
                            category: '01 - عقود وإيجارات'
                        },
                        {
                            vault_id: 'doc_date_test_2',
                            brief_arabic_title: 'مستند بدون تاريخ',
                            dates: [],
                            category: '01 - عقود وإيجارات'
                        }
                    ]
                }
            ];
            window.currentCategories = testCats;
            global.currentCategories = testCats;

            renderCategories();

            const docRow1 = document.querySelector('[data-vault-id="doc_date_test_1"]');
            expect(docRow1).not.toBeNull();
            const dateBadge1 = docRow1.querySelector('.doc-date-badge');
            expect(dateBadge1).not.toBeNull();
            expect(dateBadge1.textContent.trim()).toBe('2024-03-20');
            expect(dateBadge1.className).toContain('bg-slate-100');
            expect(dateBadge1.className).toContain('text-slate-500');
            expect(dateBadge1.className).toContain('text-[9px]');
            expect(dateBadge1.className).toContain('tracking-tight');

            // Check that date badge directly precedes 3-dots button
            const menuBtn1 = docRow1.querySelector('.doc-menu-btn');
            expect(menuBtn1).not.toBeNull();
            expect(dateBadge1.nextElementSibling).toBe(menuBtn1);

            // Fallback for doc without date
            const docRow2 = document.querySelector('[data-vault-id="doc_date_test_2"]');
            expect(docRow2).not.toBeNull();
            const dateBadge2 = docRow2.querySelector('.doc-date-badge');
            expect(dateBadge2).not.toBeNull();
            expect(dateBadge2.textContent.trim()).toBe('No Date');
        });

        it('renders circular document count badge on category folder header with count and tooltip', () => {
            const testCats = [
                {
                    name: '01 - عقود وإيجارات',
                    document_count: 2,
                    documents: [
                        { vault_id: 'doc_1', brief_arabic_title: 'Doc 1' },
                        { vault_id: 'doc_2', brief_arabic_title: 'Doc 2' }
                    ]
                }
            ];
            window.currentCategories = testCats;
            global.currentCategories = testCats;

            renderCategories();

            const countBadge = document.querySelector('.doc-count-badge');
            expect(countBadge).not.toBeNull();
            expect(countBadge.textContent.trim()).toBe('2');
            expect(countBadge.className).toContain('rounded-full');
            expect(countBadge.getAttribute('title')).toBe('2 Documents');
        });

        it('clicking 3-dots button in categories view calls openDocDropdownMenu instead of modal', () => {
            const testCats = [
                {
                    name: '01 - عقود وإيجارات',
                    document_count: 1,
                    documents: [mockDoc]
                }
            ];
            window.currentCategories = testCats;
            global.currentCategories = testCats;

            window.openDocDropdownMenu = vi.fn();
            window.openDocModal = vi.fn();

            renderCategories();

            const docRow = document.querySelector(`[data-vault-id="${mockDoc.vault_id}"]`);
            expect(docRow).not.toBeNull();
            const menuBtn = docRow.querySelector('.doc-menu-btn');
            expect(menuBtn).not.toBeNull();

            menuBtn.click();

            expect(window.openDocDropdownMenu).toHaveBeenCalled();
            expect(window.openDocModal).not.toHaveBeenCalled();
        });
    });

    describe('Timeline View 3-Dots Menu Trigger', () => {
        it('clicking 3-dots button in timeline view calls openDocDropdownMenu', () => {
            const testTimeline = [mockDoc];
            window.currentTimeline = testTimeline;
            global.currentTimeline = testTimeline;
            window.openDocDropdownMenu = vi.fn();
            window.openDocModal = vi.fn();

            renderTimeline(testTimeline);

            const card = document.querySelector(`[data-vault-id="${mockDoc.vault_id}"]`);
            expect(card).not.toBeNull();
            const menuBtn = card.querySelector('.doc-menu-btn');
            expect(menuBtn).not.toBeNull();

            menuBtn.click();

            expect(window.openDocDropdownMenu).toHaveBeenCalled();
            expect(window.openDocModal).not.toHaveBeenCalled();
        });
    });

    describe('openBatchMoveForDoc & openBatchCopyForDoc helpers (single doc mode)', () => {
        it('opens move modal for single doc without activating multi-select or batch action bar', () => {
            const moveModal = document.getElementById('batch-move-modal');
            const batchBar = document.getElementById('batch-action-bar');
            const subtitle = document.getElementById('batch-move-subtitle');

            openBatchMoveForDoc(mockDoc);

            // Does not activate multi-select or add to selectedDocIds
            expect(window.selectedDocIds.has(mockDoc.vault_id)).toBe(false);
            expect(window.selectedDocIds.size).toBe(0);
            expect(batchBar.classList.contains('hidden')).toBe(true);

            // Sets singleTargetDoc
            expect(getSingleTargetDoc()).toEqual(mockDoc);

            // Opens move modal and displays document name
            expect(moveModal.classList.contains('hidden')).toBe(false);
            expect(subtitle.textContent).toContain('Move "contract_01.pdf"');
        });

        it('opens copy modal for single doc without activating multi-select or batch action bar', () => {
            const copyModal = document.getElementById('batch-copy-modal');
            const batchBar = document.getElementById('batch-action-bar');
            const subtitle = document.getElementById('batch-copy-subtitle');

            openBatchCopyForDoc(mockDoc);

            // Does not activate multi-select or add to selectedDocIds
            expect(window.selectedDocIds.has(mockDoc.vault_id)).toBe(false);
            expect(window.selectedDocIds.size).toBe(0);
            expect(batchBar.classList.contains('hidden')).toBe(true);

            // Sets singleTargetDoc
            expect(getSingleTargetDoc()).toEqual(mockDoc);

            // Opens copy modal and displays document name
            expect(copyModal.classList.contains('hidden')).toBe(false);
            expect(subtitle.textContent).toContain('Copy "contract_01.pdf"');
        });

        it('clears singleTargetDoc when closing move or copy modals', () => {
            openBatchMoveForDoc(mockDoc);
            expect(getSingleTargetDoc()).toEqual(mockDoc);
            closeBatchMoveModal();
            expect(getSingleTargetDoc()).toBeNull();

            openBatchCopyForDoc(mockDoc);
            expect(getSingleTargetDoc()).toEqual(mockDoc);
            closeBatchCopyModal();
            expect(getSingleTargetDoc()).toBeNull();
        });

        it('submits single doc move without touching multi-select state', async () => {
            openBatchMoveForDoc(mockDoc);
            const selectEl = document.getElementById('batch-move-folder-select');
            selectEl.value = '05 - عقود';

            await handleBatchMoveSubmit();

            expect(global.fetch).toHaveBeenCalledWith(
                '/api/areas/Safra%20C/houses/514/documents/batch-move',
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify({
                        vault_ids: [mockDoc.vault_id],
                        target_category: '05 - عقود'
                    })
                })
            );

            expect(window.selectedDocIds.size).toBe(0);
            expect(getSingleTargetDoc()).toBeNull();
            expect(document.getElementById('batch-move-modal').classList.contains('hidden')).toBe(true);
            expect(global.showToast).toHaveBeenCalledWith(
                expect.stringContaining('Successfully moved document'),
                'success'
            );
        });

        it('submits single doc copy without touching multi-select state', async () => {
            openBatchCopyForDoc(mockDoc);
            const selectEl = document.getElementById('batch-copy-folder-select');
            selectEl.value = '05 - عقود';

            await handleBatchCopySubmit();

            expect(global.fetch).toHaveBeenCalledWith(
                '/api/areas/Safra%20C/houses/514/documents/batch-copy',
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify({
                        vault_ids: [mockDoc.vault_id],
                        target_category: '05 - عقود'
                    })
                })
            );

            expect(window.selectedDocIds.size).toBe(0);
            expect(getSingleTargetDoc()).toBeNull();
            expect(document.getElementById('batch-copy-modal').classList.contains('hidden')).toBe(true);
            expect(global.showToast).toHaveBeenCalledWith(
                'تم نسخ الوثيقة بنجاح',
                'success'
            );
        });
    });
});

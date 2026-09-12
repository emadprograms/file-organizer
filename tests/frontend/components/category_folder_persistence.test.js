import { describe, it, expect, beforeEach, vi } from 'vitest';

const {
    renderCategories,
    openCategoryFolder,
    getOpenCategoryFolders,
    resetCategoryOpenState,
} = require('../../../src/api/static/js/categories-view.js');

function setupDOM() {
    document.body.innerHTML = `
        <div id="stats-badge" class="hidden"></div>
        <div id="document-list"></div>
    `;
}

describe('Category Folder Expansion Persistence', () => {
    beforeEach(() => {
        resetCategoryOpenState();
        setupDOM();
        global.currentArea = 'Safra C';
        global.currentHouse = '500';
        global.currentTenant = null;
        global.currentCategories = [
            {
                tenant: 'علي محمد',
                name: '01 - بيانات أساسية',
                document_count: 2,
                documents: [
                    { vault_id: 'doc001', brief_arabic_title: 'وثيقة 1', is_manual: 0, notes: '' },
                    { vault_id: 'doc002', brief_arabic_title: 'وثيقة 2', is_manual: 0, notes: '' }
                ]
            },
            {
                tenant: 'علي محمد',
                name: '05 - عقود',
                document_count: 1,
                documents: [
                    { vault_id: 'doc003', brief_arabic_title: 'عقد إيجار', is_manual: 0, notes: '' }
                ]
            },
            {
                tenant: 'علي محمد',
                name: '06 - كهرباء وماء',
                document_count: 1,
                documents: [
                    { vault_id: 'doc004', brief_arabic_title: 'فاتورة', is_manual: 0, notes: '' }
                ]
            }
        ];
    });

    it('initial render collapses folders without notes', () => {
        renderCategories();

        const cards = document.querySelectorAll('.category-folder-card');
        expect(cards.length).toBe(3);

        cards.forEach(card => {
            const docs = card.querySelector('.category-docs');
            expect(docs.classList.contains('hidden')).toBe(true);
        });
    });

    it('clicking a folder expands it, and re-rendering preserves the expanded state', () => {
        renderCategories();

        const cards = document.querySelectorAll('.category-folder-card');
        const firstCard = cards[0];
        const firstDocs = firstCard.querySelector('.category-docs');
        expect(firstDocs.classList.contains('hidden')).toBe(true);

        // Click to expand
        firstCard.click();
        expect(firstDocs.classList.contains('hidden')).toBe(false);

        // Simulate refreshCurrentTab -> renderCategories()
        renderCategories();

        const reloadedCards = document.querySelectorAll('.category-folder-card');
        const reloadedFirstDocs = reloadedCards[0].querySelector('.category-docs');
        const reloadedSecondDocs = reloadedCards[1].querySelector('.category-docs');

        // First folder should stay open
        expect(reloadedFirstDocs.classList.contains('hidden')).toBe(false);
        // Second folder should remain closed
        expect(reloadedSecondDocs.classList.contains('hidden')).toBe(true);
    });

    it('openCategoryFolder expands the folder immediately and preserves it across render', () => {
        renderCategories();

        // Target category is 06 - كهرباء وماء (index 2)
        openCategoryFolder('06 - كهرباء وماء');

        const cards = document.querySelectorAll('.category-folder-card');
        const thirdDocs = cards[2].querySelector('.category-docs');
        expect(thirdDocs.classList.contains('hidden')).toBe(false);

        // After re-render (e.g. after move completes)
        renderCategories();

        const reloadedCards = document.querySelectorAll('.category-folder-card');
        const reloadedThirdDocs = reloadedCards[2].querySelector('.category-docs');
        expect(reloadedThirdDocs.classList.contains('hidden')).toBe(false);
    });

    it('clicking an expanded folder collapses it and re-render respects the collapsed state', () => {
        renderCategories();

        const card = document.querySelector('.category-folder-card[data-category-name="05 - عقود"]');
        card.click(); // expand
        expect(card.querySelector('.category-docs').classList.contains('hidden')).toBe(false);

        card.click(); // collapse again
        expect(card.querySelector('.category-docs').classList.contains('hidden')).toBe(true);

        // Re-render
        renderCategories();

        const reloadedCard = document.querySelector('.category-folder-card[data-category-name="05 - عقود"]');
        expect(reloadedCard.querySelector('.category-docs').classList.contains('hidden')).toBe(true);
    });

    it('resets open folders when switching to a different house', () => {
        renderCategories();

        // Open first card in house 500
        const card = document.querySelectorAll('.category-folder-card')[0];
        card.click();
        expect(card.querySelector('.category-docs').classList.contains('hidden')).toBe(false);

        // Switch house
        global.currentHouse = '501';
        renderCategories();

        // Cards in new house should start collapsed
        const newHouseCards = document.querySelectorAll('.category-folder-card');
        newHouseCards.forEach(c => {
            const docs = c.querySelector('.category-docs');
            expect(docs.classList.contains('hidden')).toBe(true);
        });
    });

    it('drag and drop move preserves open folders without opening closed target folders and preserves scroll', async () => {
        const { handleCategoryDrop, handleDocDragStart } = require('../../../src/api/static/js/doc-manager.js');
        global.showToast = vi.fn();
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({ category: '06 - كهرباء وماء', vault_id: 'doc001' })
        });
        window.refreshCurrentTab = vi.fn().mockImplementation(() => {
            renderCategories();
        });

        renderCategories();

        const docListEl = document.getElementById('document-list');
        docListEl.scrollTop = 320;

        // Initially, user has source folder (01 - بيانات أساسية) open
        const sourceCard = document.querySelector('.category-folder-card[data-category-name="01 - بيانات أساسية"]');
        sourceCard.click();
        expect(sourceCard.querySelector('.category-docs').classList.contains('hidden')).toBe(false);

        // Target folder (06 - كهرباء وماء) is closed
        const targetCard = document.querySelector('.category-folder-card[data-category-name="06 - كهرباء وماء"]');
        expect(targetCard.querySelector('.category-docs').classList.contains('hidden')).toBe(true);

        // User starts dragging doc001
        const dragStartEvent = {
            dataTransfer: { setData: vi.fn(), effectAllowed: '' },
            target: { classList: { add: vi.fn(), remove: vi.fn() } }
        };
        handleDocDragStart(dragStartEvent, { vault_id: 'doc001', category: '01 - بيانات أساسية' }, '01 - بيانات أساسية');

        const dropEvent = {
            preventDefault: vi.fn(),
        };

        await handleCategoryDrop(dropEvent, '06 - كهرباء وماء', targetCard);

        expect(global.showToast).toHaveBeenCalledWith('Moved to 06 - كهرباء وماء');

        // Verify: Source folder STAYS OPEN, closed target folder STAYS CLOSED!
        expect(sourceCard.querySelector('.category-docs').classList.contains('hidden')).toBe(false);
        expect(targetCard.querySelector('.category-docs').classList.contains('hidden')).toBe(true);

        // Verify: Document element moved into target folder's docs container
        const movedDocInTarget = targetCard.querySelector('.category-docs [data-vault-id="doc001"]');
        expect(movedDocInTarget).not.toBeNull();

        // Verify: Counts updated (source 2 -> 1, target 1 -> 2)
        expect(sourceCard.querySelector('.doc-count-badge').textContent).toBe('1');
        expect(targetCard.querySelector('.doc-count-badge').textContent).toBe('2');

        // Verify: Scroll did not jump
        expect(docListEl.scrollTop).toBe(320);
    });

    it('preserves scroll position across re-renders within the same house', () => {
        renderCategories();

        const docListEl = document.getElementById('document-list');
        docListEl.scrollTop = 450;

        renderCategories();

        expect(docListEl.scrollTop).toBe(450);
    });

    it('does not jump or scroll when moving documents', async () => {
        const scrollSpy = vi.fn();
        window.HTMLElement.prototype.scrollIntoView = scrollSpy;

        renderCategories();

        const docListEl = document.getElementById('document-list');
        docListEl.scrollTop = 250;

        const { moveDocInDom } = require('../../../src/api/static/js/categories-view.js');
        const moved = moveDocInDom('doc001', '01 - بيانات أساسية', '05 - عقود');

        expect(moved).toBe(true);
        expect(docListEl.scrollTop).toBe(250);
        expect(scrollSpy).not.toHaveBeenCalled();
    });

    it('copying a document preserves open/closed folder states and updates count without scroll jump', () => {
        const scrollSpy = vi.fn();
        window.HTMLElement.prototype.scrollIntoView = scrollSpy;

        renderCategories();

        const docListEl = document.getElementById('document-list');
        docListEl.scrollTop = 180;

        // Open folder 1, folder 2 ('05 - عقود') remains closed
        const sourceCard = document.querySelector('.category-folder-card[data-category-name="01 - بيانات أساسية"]');
        sourceCard.click();
        expect(sourceCard.querySelector('.category-docs').classList.contains('hidden')).toBe(false);

        const targetCard = document.querySelector('.category-folder-card[data-category-name="05 - عقود"]');
        expect(targetCard.querySelector('.category-docs').classList.contains('hidden')).toBe(true);
        expect(targetCard.querySelector('.doc-count-badge').textContent).toBe('1');

        const { copyDocInDom } = require('../../../src/api/static/js/categories-view.js');
        const copied = copyDocInDom({
            vault_id: 'doc005_copy',
            brief_arabic_title: 'نسخة عقد',
            filename: 'contract_copy.pdf',
            category: '05 - عقود'
        }, '05 - عقود');

        expect(copied).toBe(true);

        // Open folder remains open
        expect(sourceCard.querySelector('.category-docs').classList.contains('hidden')).toBe(false);
        // Closed target folder remains closed
        expect(targetCard.querySelector('.category-docs').classList.contains('hidden')).toBe(true);

        // Target badge updated 1 -> 2
        expect(targetCard.querySelector('.doc-count-badge').textContent).toBe('2');

        // Document exists in target folder DOM
        const copiedEl = targetCard.querySelector('[data-vault-id="doc005_copy"]');
        expect(copiedEl).not.toBeNull();

        // Scroll position unchanged, no scrollIntoView
        expect(docListEl.scrollTop).toBe(180);
        expect(scrollSpy).not.toHaveBeenCalled();
    });

    it('executeBatchMove moves docs in DOM and preserves open/closed folders without scrolling', async () => {
        const scrollSpy = vi.fn();
        window.HTMLElement.prototype.scrollIntoView = scrollSpy;

        const {
            toggleDocSelection,
            openBatchMoveModal,
            handleBatchMoveSubmit
        } = require('../../../src/api/static/js/categories-view.js');

        // Setup modal elements in DOM
        const modalHtml = `
            <div id="batch-move-modal" class="hidden">
                <select id="batch-move-folder-select"></select>
                <select id="batch-move-tenant-select"></select>
                <button id="btn-batch-move-confirm"></button>
                <div id="batch-move-spinner" class="hidden"></div>
                <div id="batch-action-bar" class="hidden"></div>
                <span id="batch-selected-count"></span>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        renderCategories();

        const docListEl = document.getElementById('document-list');
        docListEl.scrollTop = 220;

        // Open folder 1 ('01 - بيانات أساسية')
        const sourceCard = document.querySelector('.category-folder-card[data-category-name="01 - بيانات أساسية"]');
        sourceCard.click();
        expect(sourceCard.querySelector('.category-docs').classList.contains('hidden')).toBe(false);

        // Folder 3 ('06 - كهرباء وماء') is closed
        const targetCard = document.querySelector('.category-folder-card[data-category-name="06 - كهرباء وماء"]');
        expect(targetCard.querySelector('.category-docs').classList.contains('hidden')).toBe(true);

        // Select doc001 and open batch move modal
        toggleDocSelection('doc001', true);
        openBatchMoveModal();

        const select = document.getElementById('batch-move-folder-select');
        select.value = '06 - كهرباء وماء';

        global.showToast = vi.fn();
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                status: 'success',
                moved_count: 1,
                target_category: '06 - كهرباء وماء'
            })
        });

        await handleBatchMoveSubmit();

        // Verify: open folder is still open, closed target folder is still closed
        expect(sourceCard.querySelector('.category-docs').classList.contains('hidden')).toBe(false);
        expect(targetCard.querySelector('.category-docs').classList.contains('hidden')).toBe(true);

        // Verify: counts updated
        expect(sourceCard.querySelector('.doc-count-badge').textContent).toBe('1');
        expect(targetCard.querySelector('.doc-count-badge').textContent).toBe('2');

        // Verify: doc moved to target docs container
        expect(targetCard.querySelector('[data-vault-id="doc001"]')).not.toBeNull();

        // Verify: scroll preserved, no scrollIntoView
        expect(docListEl.scrollTop).toBe(220);
        expect(scrollSpy).not.toHaveBeenCalled();
    });

    it('shows folder disappearing when all its documents are moved out and it becomes empty', () => {
        renderCategories();

        const docListEl = document.getElementById('document-list');
        // Folder '05 - عقود' initially exists with 1 document ('doc003')
        const initialCard = document.querySelector('.category-folder-card[data-category-name="05 - عقود"]');
        expect(initialCard).not.toBeNull();
        expect(initialCard.querySelector('.doc-count-badge').textContent).toBe('1');

        const { moveDocInDom } = require('../../../src/api/static/js/categories-view.js');
        // Move doc003 out to '06 - كهرباء وماء'
        const moved = moveDocInDom('doc003', '05 - عقود', '06 - كهرباء وماء');
        expect(moved).toBe(true);

        // Verify: Folder '05 - عقود' has disappeared from the DOM!
        const disappearedCard = document.querySelector('.category-folder-card[data-category-name="05 - عقود"]');
        expect(disappearedCard).toBeNull();

        // Verify: Target folder '06 - كهرباء وماء' count updated 1 -> 2
        const targetCard = document.querySelector('.category-folder-card[data-category-name="06 - كهرباء وماء"]');
        expect(targetCard.querySelector('.doc-count-badge').textContent).toBe('2');
        expect(targetCard.querySelector('[data-vault-id="doc003"]')).not.toBeNull();
    });

    it('shows new folder appearing at sorted position when document is moved into a new folder', () => {
        renderCategories();

        const docListEl = document.getElementById('document-list');
        // '03 - فواتير' does not exist initially in DOM
        expect(document.querySelector('.category-folder-card[data-category-name="03 - فواتير"]')).toBeNull();

        const { moveDocInDom } = require('../../../src/api/static/js/categories-view.js');
        // Move doc001 into new folder '03 - فواتير'
        const moved = moveDocInDom('doc001', '01 - بيانات أساسية', '03 - فواتير');
        expect(moved).toBe(true);

        // Verify: New folder '03 - فواتير' now appears in the DOM!
        const newFolderCard = document.querySelector('.category-folder-card[data-category-name="03 - فواتير"]');
        expect(newFolderCard).not.toBeNull();
        expect(newFolderCard.querySelector('.doc-count-badge').textContent).toBe('1');

        // Verify: Document is inside the new folder and visible
        const movedDoc = newFolderCard.querySelector('[data-vault-id="doc001"]');
        expect(movedDoc).not.toBeNull();
        expect(newFolderCard.querySelector('.category-docs').classList.contains('hidden')).toBe(false);

        // Verify: Sorted order in DOM ('01 - بيانات أساسية', '03 - فواتير', '05 - عقود', '06 - كهرباء وماء')
        const allCards = Array.from(document.querySelectorAll('.category-folder-card'));
        const names = allCards.map(c => c.getAttribute('data-category-name'));
        expect(names).toEqual(['01 - بيانات أساسية', '03 - فواتير', '05 - عقود', '06 - كهرباء وماء']);
    });

    it('handles folder disappearing and re-appearing when moving document out and then back in', () => {
        renderCategories();

        const { moveDocInDom } = require('../../../src/api/static/js/categories-view.js');

        // 1. Move doc003 out of '05 - عقود' to '06 - كهرباء وماء' -> '05 - عقود' disappears
        moveDocInDom('doc003', '05 - عقود', '06 - كهرباء وماء');
        expect(document.querySelector('.category-folder-card[data-category-name="05 - عقود"]')).toBeNull();

        // 2. Move doc003 back from '06 - كهرباء وماء' to '05 - عقود' -> '05 - عقود' re-appears!
        moveDocInDom('doc003', '06 - كهرباء وماء', '05 - عقود');
        const reappearedCard = document.querySelector('.category-folder-card[data-category-name="05 - عقود"]');
        expect(reappearedCard).not.toBeNull();
        expect(reappearedCard.querySelector('.doc-count-badge').textContent).toBe('1');
        expect(reappearedCard.querySelector('[data-vault-id="doc003"]')).not.toBeNull();

        // Verify: Sorted position is preserved ('01', '05', '06')
        const allCards = Array.from(document.querySelectorAll('.category-folder-card'));
        const names = allCards.map(c => c.getAttribute('data-category-name'));
        expect(names).toEqual(['01 - بيانات أساسية', '05 - عقود', '06 - كهرباء وماء']);
    });
});



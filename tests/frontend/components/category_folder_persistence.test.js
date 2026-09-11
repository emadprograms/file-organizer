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

    it('drag and drop move preserves the source open folder and expands the target folder', async () => {
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

        expect(window.refreshCurrentTab).toHaveBeenCalled();

        // After refresh, BOTH source and target folders should be open!
        const reloadedSource = document.querySelector('.category-folder-card[data-category-name="01 - بيانات أساسية"]');
        const reloadedTarget = document.querySelector('.category-folder-card[data-category-name="06 - كهرباء وماء"]');
        const otherFolder = document.querySelector('.category-folder-card[data-category-name="05 - عقود"]');

        expect(reloadedSource.querySelector('.category-docs').classList.contains('hidden')).toBe(false);
        expect(reloadedTarget.querySelector('.category-docs').classList.contains('hidden')).toBe(false);
        expect(otherFolder.querySelector('.category-docs').classList.contains('hidden')).toBe(true);
    });
});

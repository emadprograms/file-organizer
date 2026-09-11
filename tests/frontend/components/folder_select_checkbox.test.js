import { describe, it, expect, beforeEach, vi } from 'vitest';

const {
    renderCategories,
    selectedDocIds,
    getSelectedDocIds,
    toggleDocSelection,
    toggleSelectAllInFolder,
    updateFolderCheckboxState,
    toggleSelectAllGlobal,
    deselectAllDocs,
    initBatchOperations,
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
    `;
}

describe('Folder Select Checkbox (QCK-12)', () => {
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
                    { vault_id: 'doc002', brief_arabic_title: 'عقد إيجار 2', is_manual: 1, notes: '' }
                ]
            },
            {
                tenant: 'فاطمة أحمد',
                name: '06 - كهرباء وماء',
                document_count: 1,
                documents: [
                    { vault_id: 'doc003', brief_arabic_title: 'فاتورة كهرباء', is_manual: 0, notes: '' }
                ]
            },
            {
                tenant: 'فاطمة أحمد',
                name: '13 - رسائل متنوعة',
                document_count: 0,
                documents: []
            }
        ];
        global.currentTenant = null;
        global.showToast = vi.fn();
        deselectAllDocs();
        initBatchOperations();
    });

    it('renders folder select checkbox before folder icon box for categories with documents', () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const folderCard = docList.querySelector('[data-category-name="05 - عقود"]');
        expect(folderCard).not.toBeNull();

        const flexContainer = folderCard.querySelector('.flex.items-center.gap-2');
        expect(flexContainer).not.toBeNull();

        const firstChild = flexContainer.children[0];
        const secondChild = flexContainer.children[1];

        expect(firstChild.classList.contains('folder-select-checkbox')).toBe(true);
        expect(firstChild.tagName).toBe('INPUT');
        expect(firstChild.type).toBe('checkbox');

        expect(secondChild.classList.contains('folder-icon-box')).toBe(true);
    });

    it('renders an alignment spacer instead of a checkbox for empty categories', () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const emptyCard = docList.querySelector('[data-category-name="13 - رسائل متنوعة"]');
        expect(emptyCard).not.toBeNull();

        const checkbox = emptyCard.querySelector('.folder-select-checkbox');
        expect(checkbox).toBeNull();

        const flexContainer = emptyCard.querySelector('.flex.items-center.gap-2');
        const firstChild = flexContainer.children[0];
        expect(firstChild.tagName).toBe('SPAN');
        expect(firstChild.classList.contains('w-3.5')).toBe(true);
        expect(firstChild.classList.contains('h-3.5')).toBe(true);
    });

    it('clicking folder checkbox opens collapsed folder dialog and reveals documents while selecting all', () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const folderCard = docList.querySelector('[data-category-name="05 - عقود"]');
        const folderCb = folderCard.querySelector('.folder-select-checkbox');
        const docsContainer = folderCard.querySelector('.category-docs');

        // Folders without notes are collapsed by default with 'hidden'
        expect(docsContainer.classList.contains('hidden')).toBe(true);
        expect(folderCb.checked).toBe(false);

        // Click folder checkbox
        folderCb.click();

        // Documents container revealed
        expect(docsContainer.classList.contains('hidden')).toBe(false);

        // Both docs in folder are selected
        expect(getSelectedDocIds().has('doc001')).toBe(true);
        expect(getSelectedDocIds().has('doc002')).toBe(true);
        expect(getSelectedDocIds().has('doc003')).toBe(false);
        expect(getSelectedDocIds().size).toBe(2);

        // Folder checkbox is checked
        expect(folderCb.checked).toBe(true);
        expect(folderCb.indeterminate).toBe(false);

        // Document checkboxes in folder are checked
        const docCbs = folderCard.querySelectorAll('.doc-select-checkbox');
        docCbs.forEach(cb => expect(cb.checked).toBe(true));
    });

    it('clicking folder checkbox again deselects all documents in the folder', () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const folderCard = docList.querySelector('[data-category-name="05 - عقود"]');
        const folderCb = folderCard.querySelector('.folder-select-checkbox');

        // Select all in folder
        folderCb.click();
        expect(getSelectedDocIds().size).toBe(2);
        expect(folderCb.checked).toBe(true);

        // Deselect all in folder
        folderCb.click();
        expect(getSelectedDocIds().has('doc001')).toBe(false);
        expect(getSelectedDocIds().has('doc002')).toBe(false);
        expect(getSelectedDocIds().size).toBe(0);
        expect(folderCb.checked).toBe(false);
        expect(folderCb.indeterminate).toBe(false);

        const docCbs = folderCard.querySelectorAll('.doc-select-checkbox');
        docCbs.forEach(cb => expect(cb.checked).toBe(false));
    });

    it('sets folder checkbox to indeterminate when partially selected via document checkboxes', () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const folderCard = docList.querySelector('[data-category-name="05 - عقود"]');
        const folderCb = folderCard.querySelector('.folder-select-checkbox');
        const docCbs = folderCard.querySelectorAll('.doc-select-checkbox');

        expect(folderCb.checked).toBe(false);
        expect(folderCb.indeterminate).toBe(false);

        // Check doc001 only
        docCbs[0].checked = true;
        docCbs[0].dispatchEvent(new Event('change'));

        expect(folderCb.checked).toBe(false);
        expect(folderCb.indeterminate).toBe(true);

        // Check doc002 as well -> fully selected
        docCbs[1].checked = true;
        docCbs[1].dispatchEvent(new Event('change'));

        expect(folderCb.checked).toBe(true);
        expect(folderCb.indeterminate).toBe(false);

        // Uncheck doc001 -> back to indeterminate
        docCbs[0].checked = false;
        docCbs[0].dispatchEvent(new Event('change'));

        expect(folderCb.checked).toBe(false);
        expect(folderCb.indeterminate).toBe(true);

        // Uncheck doc002 -> completely unchecked
        docCbs[1].checked = false;
        docCbs[1].dispatchEvent(new Event('change'));

        expect(folderCb.checked).toBe(false);
        expect(folderCb.indeterminate).toBe(false);
    });

    it('synchronizes all folder checkboxes on global select all and global deselect all', () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const globalBtn = docList.querySelector('#btn-toggle-select-all-categories');
        const folderCbs = docList.querySelectorAll('.folder-select-checkbox');

        expect(folderCbs.length).toBe(2); // 05 - عقود and 06 - كهرباء وماء
        folderCbs.forEach(cb => expect(cb.checked).toBe(false));

        // Global Select All
        globalBtn.click();
        expect(getSelectedDocIds().size).toBe(3);
        folderCbs.forEach(cb => {
            expect(cb.checked).toBe(true);
            expect(cb.indeterminate).toBe(false);
        });

        // Global Deselect All
        globalBtn.click();
        expect(getSelectedDocIds().size).toBe(0);
        folderCbs.forEach(cb => {
            expect(cb.checked).toBe(false);
            expect(cb.indeterminate).toBe(false);
        });
    });

    it('preserves pre-checked state on re-render when documents are already selected', () => {
        toggleDocSelection('doc001', true);
        toggleDocSelection('doc002', true);

        renderCategories();
        const docList = document.getElementById('document-list');
        const folderCard = docList.querySelector('[data-category-name="05 - عقود"]');
        const folderCb = folderCard.querySelector('.folder-select-checkbox');

        expect(folderCb.checked).toBe(true);
        expect(folderCb.indeterminate).toBe(false);
    });

    it('preserves indeterminate state on re-render when partially selected', () => {
        toggleDocSelection('doc001', true);

        renderCategories();
        const docList = document.getElementById('document-list');
        const folderCard = docList.querySelector('[data-category-name="05 - عقود"]');
        const folderCb = folderCard.querySelector('.folder-select-checkbox');

        expect(folderCb.checked).toBe(false);
        expect(folderCb.indeterminate).toBe(true);
    });
});

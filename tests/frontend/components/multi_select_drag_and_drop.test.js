import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

const {
    renderCategories,
    selectedDocIds,
    toggleDocSelection,
    deselectAllDocs,
} = require('../../../src/api/static/js/categories-view.js');

const {
    handleDocDragStart,
    handleDocDragEnd,
    handleCategoryDragOver,
    handleCategoryDragLeave,
    handleCategoryDrop,
    handleTenantTreeDragOver,
    handleTenantTreeDragLeave,
    handleTenantTreeDrop,
} = require('../../../src/api/static/js/doc-manager.js');

function setupDOM() {
    document.body.innerHTML = `
        <div id="stats-badge" class="hidden"></div>
        <div id="batch-action-bar" class="hidden">
            <span id="batch-selected-count">0 selected</span>
            <button id="btn-batch-move" type="button">Move Selected</button>
            <button id="btn-batch-deselect" type="button">Deselect</button>
        </div>
        <div id="document-list-panel">
            <div id="document-list"></div>
        </div>
        <div id="document-viewer-panel" class="hidden">
            <span id="viewer-title"></span>
            <iframe id="pdf-frame"></iframe>
        </div>
        <div id="welcome-panel"></div>
        <div id="resizer-2" class="hidden"></div>
    `;
}

function createTouchEvent(type, clientX, clientY) {
    const event = new Event(type, { bubbles: true, cancelable: true });
    const touch = { clientX, clientY, identifier: 1, target: null };
    if (type === 'touchend' || type === 'touchcancel') {
        event.changedTouches = [touch];
        event.touches = [];
    } else {
        event.touches = [touch];
        event.changedTouches = [touch];
    }
    return event;
}

describe('Multi-Select Drag and Drop for Tabs (Tablets) & Computers (Desktop)', () => {
    beforeEach(() => {
        setupDOM();
        deselectAllDocs();
        window._lastTouchTimestamp = 0;

        global.currentArea = 'Safra C';
        global.currentHouse = '500';
        global.currentCategories = [
            {
                tenant: 'فاطمة أحمد',
                name: '01 - بيانات أساسية',
                document_count: 2,
                documents: [
                    {
                        vault_id: 'doc001',
                        brief_arabic_title: 'بطاقة هوية',
                        filename: 'id_card.pdf',
                        is_manual: 0,
                        notes: '',
                        category: '01 - بيانات أساسية'
                    },
                    {
                        vault_id: 'doc002',
                        brief_arabic_title: 'جواز سفر',
                        filename: 'passport.pdf',
                        is_manual: 0,
                        notes: '',
                        category: '01 - بيانات أساسية'
                    }
                ]
            },
            {
                tenant: 'فاطمة أحمد',
                name: '05 - عقود',
                document_count: 1,
                documents: [
                    {
                        vault_id: 'doc003',
                        brief_arabic_title: 'عقد إيجار شقة',
                        filename: 'contract.pdf',
                        is_manual: 0,
                        notes: '',
                        category: '05 - عقود'
                    }
                ]
            },
            {
                tenant: 'فاطمة أحمد',
                name: '06 - كهرباء وماء',
                document_count: 0,
                documents: []
            }
        ];

        global.showToast = vi.fn();
        window.showToast = global.showToast;
        global.openDocument = vi.fn();
        window.openDocument = global.openDocument;

        global.fetch = vi.fn().mockImplementation(async (url, options) => {
            if (url.includes('/batch-move')) {
                const body = JSON.parse(options.body);
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        moved_count: body.vault_ids.length,
                        target_category: body.target_category,
                        vault_ids: body.vault_ids
                    })
                };
            }
            if (url.includes('/tenants')) {
                return {
                    ok: true,
                    json: async () => ([
                        { id: 10, name: 'فاطمة أحمد' },
                        { id: 20, name: 'علي حسن' }
                    ])
                };
            }
            return {
                ok: true,
                json: async () => ({
                    status: 'success',
                    category: '06 - كهرباء وماء',
                    vault_id: 'doc001'
                })
            };
        });
    });

    afterEach(() => {
        deselectAllDocs();
        vi.restoreAllMocks();
        delete window.draggedDoc;
        delete window.isTouchDragging;
        const avatar = document.getElementById('touch-drag-avatar');
        if (avatar) avatar.remove();
    });

    describe('Computers (Desktop HTML5 Mouse Drag & Drop)', () => {
        it('handleDocDragStart captures all selected documents and dims them in DOM', () => {
            renderCategories();
            toggleDocSelection('doc001', true);
            toggleDocSelection('doc002', true);
            expect(selectedDocIds.size).toBe(2);

            const docEl1 = document.querySelector('[data-vault-id="doc001"]');
            const docEl2 = document.querySelector('[data-vault-id="doc002"]');
            expect(docEl1).not.toBeNull();
            expect(docEl2).not.toBeNull();

            const dragStartEvent = {
                dataTransfer: {
                    setData: vi.fn(),
                    setDragImage: vi.fn(),
                    effectAllowed: ''
                },
                target: docEl1
            };

            handleDocDragStart(dragStartEvent, { vault_id: 'doc001', category: '01 - بيانات أساسية' }, '01 - بيانات أساسية');

            expect(window.draggedDoc).not.toBeNull();
            expect(window.draggedDoc.isMulti).toBe(true);
            expect(window.draggedDoc.count).toBe(2);
            expect(window.draggedDoc.vault_ids).toEqual(['doc001', 'doc002']);

            expect(dragStartEvent.dataTransfer.setData).toHaveBeenCalledWith('text/plain', 'doc001');
            expect(dragStartEvent.dataTransfer.setData).toHaveBeenCalledWith('application/json', expect.stringContaining('"count":2'));

            // DOM dimming
            expect(docEl1.classList.contains('opacity-40')).toBe(true);
            expect(docEl1.classList.contains('ring-2')).toBe(true);
            expect(docEl2.classList.contains('opacity-40')).toBe(true);
            expect(docEl2.classList.contains('ring-2')).toBe(true);
        });

        it('handleDocDragEnd un-dims all selected documents and clears draggedDoc', () => {
            renderCategories();
            toggleDocSelection('doc001', true);
            toggleDocSelection('doc002', true);

            const docEl1 = document.querySelector('[data-vault-id="doc001"]');
            const docEl2 = document.querySelector('[data-vault-id="doc002"]');

            const dragStartEvent = {
                dataTransfer: { setData: vi.fn(), setDragImage: vi.fn(), effectAllowed: '' },
                target: docEl1
            };
            handleDocDragStart(dragStartEvent, { vault_id: 'doc001', category: '01 - بيانات أساسية' }, '01 - بيانات أساسية');

            handleDocDragEnd({ target: docEl1 });

            expect(window.draggedDoc).toBeNull();
            expect(docEl1.classList.contains('opacity-40')).toBe(false);
            expect(docEl1.classList.contains('ring-2')).toBe(false);
            expect(docEl2.classList.contains('opacity-40')).toBe(false);
            expect(docEl2.classList.contains('ring-2')).toBe(false);
        });

        it('handleCategoryDrop with multi-select calls batch-move endpoint, moves items in DOM, and clears selection', async () => {
            renderCategories();
            toggleDocSelection('doc001', true);
            toggleDocSelection('doc002', true);

            const docEl1 = document.querySelector('[data-vault-id="doc001"]');
            const targetCard = document.querySelector('.category-folder-card[data-category-name="06 - كهرباء وماء"]');
            expect(targetCard).not.toBeNull();

            const dragStartEvent = {
                dataTransfer: { setData: vi.fn(), setDragImage: vi.fn(), effectAllowed: '' },
                target: docEl1
            };
            handleDocDragStart(dragStartEvent, { vault_id: 'doc001', category: '01 - بيانات أساسية' }, '01 - بيانات أساسية');

            await handleCategoryDrop({ preventDefault: vi.fn() }, '06 - كهرباء وماء', targetCard);

            // Verifies batch-move was called with both vault IDs
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/documents/batch-move'),
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify({
                        vault_ids: ['doc001', 'doc002'],
                        target_category: '06 - كهرباء وماء'
                    })
                })
            );

            // Verify toast message
            expect(global.showToast).toHaveBeenCalledWith('Successfully moved 2 documents to "06 - كهرباء وماء"');

            // Verify selection was cleared
            expect(selectedDocIds.size).toBe(0);

            // Verify documents were moved in DOM
            const docInTarget1 = targetCard.querySelector('[data-vault-id="doc001"]');
            const docInTarget2 = targetCard.querySelector('[data-vault-id="doc002"]');
            expect(docInTarget1).not.toBeNull();
            expect(docInTarget2).not.toBeNull();
        });

        it('dragging an unselected doc while others are selected drags only that single doc', async () => {
            renderCategories();
            toggleDocSelection('doc001', true);
            toggleDocSelection('doc002', true);

            // Drag doc003 which is NOT selected
            const docEl3 = document.querySelector('[data-vault-id="doc003"]');
            const targetCard = document.querySelector('.category-folder-card[data-category-name="06 - كهرباء وماء"]');

            const dragStartEvent = {
                dataTransfer: { setData: vi.fn(), effectAllowed: '' },
                target: docEl3
            };
            handleDocDragStart(dragStartEvent, { vault_id: 'doc003', category: '05 - عقود' }, '05 - عقود');

            expect(window.draggedDoc.isMulti).toBe(false);
            expect(window.draggedDoc.vault_ids).toEqual(['doc003']);

            await handleCategoryDrop({ preventDefault: vi.fn() }, '06 - كهرباء وماء', targetCard);

            // Verifies single PATCH was used, not batch-move
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/documents/doc003'),
                expect.objectContaining({ method: 'PATCH' })
            );
            expect(global.showToast).toHaveBeenCalledWith('Moved to 06 - كهرباء وماء');
        });

        it('dropping multi-selected documents on sidebar tenant assigns all documents and deselects', async () => {
            renderCategories();
            toggleDocSelection('doc001', true);
            toggleDocSelection('doc002', true);

            const docEl1 = document.querySelector('[data-vault-id="doc001"]');
            const dragStartEvent = {
                dataTransfer: { setData: vi.fn(), effectAllowed: '' },
                target: docEl1
            };
            handleDocDragStart(dragStartEvent, { vault_id: 'doc001', category: '01 - بيانات أساسية' }, '01 - بيانات أساسية');

            const tenantBtn = document.createElement('button');
            await handleTenantTreeDrop({ preventDefault: vi.fn() }, 'علي حسن', tenantBtn, 'Safra C/500');

            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/documents/doc001'),
                expect.objectContaining({ method: 'PATCH', body: JSON.stringify({ tenant_id: 20, is_manual: 1 }) })
            );
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/documents/doc002'),
                expect.objectContaining({ method: 'PATCH', body: JSON.stringify({ tenant_id: 20, is_manual: 1 }) })
            );

            expect(global.showToast).toHaveBeenCalledWith('Assigned 2 documents to علي حسن');
            expect(selectedDocIds.size).toBe(0);
        });
    });

    describe('Tabs (Tablet Touchscreen Drag & Drop)', () => {
        beforeEach(() => {
            vi.useFakeTimers();
        });

        afterEach(() => {
            vi.useRealTimers();
        });

        it('press-and-hold (>=280ms) on a selected doc activates multi-touch drag with count badge and multi-dimming', () => {
            renderCategories();
            toggleDocSelection('doc001', true);
            toggleDocSelection('doc002', true);
            toggleDocSelection('doc003', true);
            expect(selectedDocIds.size).toBe(3);

            const docEl1 = document.querySelector('[data-vault-id="doc001"]');
            const docEl2 = document.querySelector('[data-vault-id="doc002"]');
            const docEl3 = document.querySelector('[data-vault-id="doc003"]');

            // Touchstart and hold
            docEl1.dispatchEvent(createTouchEvent('touchstart', 100, 200));
            vi.advanceTimersByTime(290);

            // Drag mode MUST be active with multi-selection data
            expect(window.isTouchDragging).toBe(true);
            expect(window.draggedDoc).not.toBeNull();
            expect(window.draggedDoc.isMulti).toBe(true);
            expect(window.draggedDoc.count).toBe(3);
            expect(window.draggedDoc.vault_ids).toEqual(['doc001', 'doc002', 'doc003']);

            // Floating avatar exists with count badge
            const avatar = document.getElementById('touch-drag-avatar');
            expect(avatar).not.toBeNull();
            expect(avatar.textContent).toContain('بطاقة هوية');
            const countBadge = avatar.querySelector('.touch-drag-count-badge');
            expect(countBadge).not.toBeNull();
            expect(countBadge.textContent).toBe('3');

            // All 3 selected documents are dimmed
            expect(docEl1.classList.contains('opacity-40')).toBe(true);
            expect(docEl2.classList.contains('opacity-40')).toBe(true);
            expect(docEl3.classList.contains('opacity-40')).toBe(true);
        });

        it('releasing finger over target folder card executes batch-move and clears selection and avatar', async () => {
            renderCategories();
            toggleDocSelection('doc001', true);
            toggleDocSelection('doc002', true);

            const docEl1 = document.querySelector('[data-vault-id="doc001"]');
            const targetCard = document.querySelector('.category-folder-card[data-category-name="06 - كهرباء وماء"]');

            // Touchstart and hold
            docEl1.dispatchEvent(createTouchEvent('touchstart', 100, 200));
            vi.advanceTimersByTime(290);
            expect(window.isTouchDragging).toBe(true);

            const originalElementFromPoint = document.elementFromPoint;
            document.elementFromPoint = vi.fn().mockReturnValue(targetCard);

            try {
                docEl1.dispatchEvent(createTouchEvent('touchend', 150, 350));

                // Await promises
                await vi.runAllTimersAsync();

                expect(window.isTouchDragging).toBe(false);
                expect(document.getElementById('touch-drag-avatar')).toBeNull();

                // Batch move was called
                expect(global.fetch).toHaveBeenCalledWith(
                    expect.stringContaining('/documents/batch-move'),
                    expect.objectContaining({
                        method: 'POST',
                        body: JSON.stringify({
                            vault_ids: ['doc001', 'doc002'],
                            target_category: '06 - كهرباء وماء'
                        })
                    })
                );

                expect(global.showToast).toHaveBeenCalledWith('Successfully moved 2 documents to "06 - كهرباء وماء"');
                expect(selectedDocIds.size).toBe(0);
            } finally {
                document.elementFromPoint = originalElementFromPoint;
            }
        });

        it('canceling touch drag (touchcancel) cleanly resets all dimming and removes avatar', () => {
            renderCategories();
            toggleDocSelection('doc001', true);
            toggleDocSelection('doc002', true);

            const docEl1 = document.querySelector('[data-vault-id="doc001"]');
            const docEl2 = document.querySelector('[data-vault-id="doc002"]');

            docEl1.dispatchEvent(createTouchEvent('touchstart', 100, 200));
            vi.advanceTimersByTime(290);
            expect(window.isTouchDragging).toBe(true);

            docEl1.dispatchEvent(createTouchEvent('touchcancel', 100, 200));

            expect(window.isTouchDragging).toBe(false);
            expect(window.draggedDoc).toBeNull();
            expect(document.getElementById('touch-drag-avatar')).toBeNull();
            expect(docEl1.classList.contains('opacity-40')).toBe(false);
            expect(docEl2.classList.contains('opacity-40')).toBe(false);
        });

        it('touch drag on single unselected doc does not show count badge and only moves that doc', async () => {
            renderCategories();
            // No selection
            expect(selectedDocIds.size).toBe(0);
            global.fetch.mockClear();

            const docEl1 = document.querySelector('[data-vault-id="doc001"]');
            const targetCard = document.querySelector('.category-folder-card[data-category-name="06 - كهرباء وماء"]');

            docEl1.dispatchEvent(createTouchEvent('touchstart', 100, 200));
            vi.advanceTimersByTime(290);

            expect(window.isTouchDragging).toBe(true);
            expect(window.draggedDoc.isMulti).toBe(false);
            expect(window.draggedDoc.vault_ids).toEqual(['doc001']);

            const avatar = document.getElementById('touch-drag-avatar');
            expect(avatar.querySelector('.touch-drag-count-badge')).toBeNull();

            const originalElementFromPoint = document.elementFromPoint;
            document.elementFromPoint = vi.fn().mockReturnValue(targetCard);

            try {
                docEl1.dispatchEvent(createTouchEvent('touchend', 150, 350));
                await vi.runAllTimersAsync();

                expect(global.fetch).toHaveBeenCalledWith(
                    expect.stringContaining('/documents/doc001'),
                    expect.objectContaining({ method: 'PATCH' })
                );
                expect(global.showToast).toHaveBeenCalledWith('Moved to 06 - كهرباء وماء');
            } finally {
                document.elementFromPoint = originalElementFromPoint;
            }
        });
    });
});

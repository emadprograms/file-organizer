import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

const {
    renderCategories,
    handleInlineRename: handleInlineRenameCategories,
    isTouchEvent: isTouchEventCategories,
    isTouchOrMobileDevice: isTouchOrMobileDeviceCategories,
} = require('../../../src/api/static/js/categories-view.js');

const {
    renderTimeline,
    handleInlineRename: handleInlineRenameTimeline,
    isTouchEvent: isTouchEventTimeline,
} = require('../../../src/api/static/js/timeline-view.js');

function setupDOM() {
    document.body.innerHTML = `
        <div id="stats-badge" class="hidden"></div>
        <div id="document-list"></div>
        <div id="document-viewer-panel" class="hidden">
            <span id="viewer-title"></span>
            <span id="viewer-peek-badge" class="hidden"></span>
            <iframe id="pdf-frame"></iframe>
            <a id="viewer-download"></a>
            <div id="pdf-canvas-container" class="hidden"></div>
            <div id="viewer-zoom-controls" class="hidden"></div>
        </div>
        <div id="welcome-panel"></div>
        <div id="resizer-2" class="hidden"></div>
    `;
}

describe('Touchscreen & Mobile Interactions Protection (Android Tablet Support)', () => {
    beforeEach(() => {
        setupDOM();
        window._lastTouchTimestamp = 0;

        global.currentArea = 'Safra C';
        global.currentHouse = '500';
        global.currentCategories = [
            {
                tenant: 'فاطمة أحمد',
                name: '05 - عقود',
                document_count: 1,
                documents: [
                    {
                        vault_id: 'doc_touch_01',
                        brief_arabic_title: 'عقد إيجار شقة',
                        filename: 'contract.pdf',
                        is_manual: 0,
                        notes: '',
                        category: '05 - عقود'
                    }
                ]
            }
        ];
        global.currentTimeline = [
            {
                vault_id: 'doc_touch_01',
                brief_arabic_title: 'عقد إيجار شقة',
                filename: 'contract.pdf',
                dates: ['2026-05-01'],
                primary_tenant: 'فاطمة أحمد',
                category: '05 - عقود',
                is_manual: 0,
                notes: ''
            }
        ];
        global.currentTenant = null;
        global.showToast = vi.fn();
        global.openDocument = vi.fn();
        window.openDocument = global.openDocument;
        global.setSelectedDoc = vi.fn();
        window.setSelectedDoc = global.setSelectedDoc;
        global.fetch = vi.fn().mockImplementation(async () => ({
            ok: true,
            json: async () => ({ status: 'success' })
        }));
    });

    afterEach(() => {
        vi.restoreAllMocks();
        window._lastTouchTimestamp = 0;
        delete global.currentArea;
        delete global.currentHouse;
        delete global.currentCategories;
        delete global.currentTimeline;
        delete global.currentTenant;
        delete global.showToast;
        delete global.openDocument;
        delete window.openDocument;
        delete global.setSelectedDoc;
        delete window.setSelectedDoc;
        delete global.fetch;
    });

    describe('isTouchEvent Detection', () => {
        it('detects pointerType touch and pen as touch events', () => {
            const touchEvent = new MouseEvent('dblclick');
            touchEvent.pointerType = 'touch';
            expect(isTouchEventCategories(touchEvent)).toBe(true);
            expect(isTouchEventTimeline(touchEvent)).toBe(true);

            const penEvent = new MouseEvent('dblclick');
            penEvent.pointerType = 'pen';
            expect(isTouchEventCategories(penEvent)).toBe(true);
            expect(isTouchEventTimeline(penEvent)).toBe(true);
        });

        it('detects recent window touch timestamp as touch interaction', () => {
            window._lastTouchTimestamp = Date.now();
            const genericEvent = new MouseEvent('dblclick');
            expect(isTouchEventCategories(genericEvent)).toBe(true);
            expect(isTouchEventTimeline(genericEvent)).toBe(true);
        });

        it('returns false for desktop mouse events without recent touch', () => {
            window._lastTouchTimestamp = 0;
            const mouseEvent = new MouseEvent('dblclick');
            mouseEvent.pointerType = 'mouse';
            expect(isTouchEventCategories(mouseEvent)).toBe(false);
            expect(isTouchEventTimeline(mouseEvent)).toBe(false);
        });

        it('returns false when event is null (allowing programmatic 3-dots menu rename)', () => {
            expect(isTouchEventCategories(null)).toBe(false);
            expect(isTouchEventTimeline(null)).toBe(false);
        });
    });

    describe('Categories View - File Click & Double Click on Touchscreens', () => {
        it('tapping or double-clicking document title with touch pointerType opens the document and NEVER triggers rename', () => {
            renderCategories();
            const docList = document.getElementById('document-list');
            const titleSpan = docList.querySelector('.doc-title-text');
            expect(titleSpan).not.toBeNull();

            // Simulate touch dblclick event
            const touchDblClick = new MouseEvent('dblclick', { bubbles: true, cancelable: true });
            touchDblClick.pointerType = 'touch';
            titleSpan.dispatchEvent(touchDblClick);

            // Must NOT create inline rename input
            expect(titleSpan.querySelector('.inline-rename-input')).toBeNull();
            expect(titleSpan.textContent).toBe('عقد إيجار شقة');

            // Must call openDocument to open the file
            expect(global.openDocument).toHaveBeenCalledWith('doc_touch_01', 'عقد إيجار شقة', '05 - عقود');
        });

        it('tapping document title on touchscreen device (recent touch) opens the document and NEVER triggers rename', () => {
            renderCategories();
            const docList = document.getElementById('document-list');
            const titleSpan = docList.querySelector('.doc-title-text');

            // Simulate recent screen tap
            window._lastTouchTimestamp = Date.now();

            const dblClickEvent = new MouseEvent('dblclick', { bubbles: true, cancelable: true });
            titleSpan.dispatchEvent(dblClickEvent);

            // Must NOT create inline rename input
            expect(titleSpan.querySelector('.inline-rename-input')).toBeNull();
            expect(global.openDocument).toHaveBeenCalledWith('doc_touch_01', 'عقد إيجار شقة', '05 - عقود');
        });

        it('desktop mouse double-click continues to trigger inline rename when no touch is present', () => {
            renderCategories();
            const docList = document.getElementById('document-list');
            const titleSpan = docList.querySelector('.doc-title-text');

            window._lastTouchTimestamp = 0;
            const mouseDblClick = new MouseEvent('dblclick', { bubbles: true, cancelable: true });
            mouseDblClick.pointerType = 'mouse';
            titleSpan.dispatchEvent(mouseDblClick);

            // Must create inline rename input for mouse users
            expect(titleSpan.querySelector('.inline-rename-input')).not.toBeNull();
        });

        it('programmatic rename from 3-dot menu works even on touch devices (event is null)', () => {
            renderCategories();
            const docList = document.getElementById('document-list');
            const titleSpan = docList.querySelector('.doc-title-text');

            window._lastTouchTimestamp = Date.now(); // user is on touch device
            handleInlineRenameCategories(null, global.currentCategories[0].documents[0], titleSpan, 'Safra C', '500');

            // Must open rename input because it was explicitly requested via 3-dot menu
            expect(titleSpan.querySelector('.inline-rename-input')).not.toBeNull();
        });
    });

    describe('Timeline View - File Click & Double Click on Touchscreens', () => {
        it('tapping or double-clicking timeline document title with touch pointerType opens the document and NEVER triggers rename', () => {
            renderTimeline();
            const docList = document.getElementById('document-list');
            const titleH4 = docList.querySelector('.doc-title-text');
            expect(titleH4).not.toBeNull();

            const touchDblClick = new MouseEvent('dblclick', { bubbles: true, cancelable: true });
            touchDblClick.pointerType = 'touch';
            titleH4.dispatchEvent(touchDblClick);

            // Must NOT create inline rename input
            expect(titleH4.querySelector('.inline-rename-input')).toBeNull();
            expect(global.openDocument).toHaveBeenCalledWith('doc_touch_01', 'عقد إيجار شقة', '05 - عقود');
        });

        it('desktop mouse double-click in timeline continues to trigger inline rename', () => {
            renderTimeline();
            const docList = document.getElementById('document-list');
            const titleH4 = docList.querySelector('.doc-title-text');

            window._lastTouchTimestamp = 0;
            const mouseDblClick = new MouseEvent('dblclick', { bubbles: true, cancelable: true });
            mouseDblClick.pointerType = 'mouse';
            titleH4.dispatchEvent(mouseDblClick);

            expect(titleH4.querySelector('.inline-rename-input')).not.toBeNull();
        });
    });

    describe('Touchscreen Press-and-Hold Drag-and-Drop Document Move Support', () => {
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

        beforeEach(() => {
            vi.useFakeTimers();
        });

        afterEach(() => {
            vi.useRealTimers();
            const avatar = document.getElementById('touch-drag-avatar');
            if (avatar) avatar.remove();
            delete window.isTouchDragging;
            delete window.draggedDoc;
            delete window._justFinishedTouchDrag;
        });

        it('short touch tap (< 280ms) does NOT activate touch drag mode and opens the document normally', () => {
            renderCategories();
            const docList = document.getElementById('document-list');
            const docEl = docList.querySelector('.category-doc-item');
            expect(docEl).not.toBeNull();

            // Touch start
            docEl.dispatchEvent(createTouchEvent('touchstart', 100, 200));

            // Fast forward 100ms (< 280ms hold threshold)
            vi.advanceTimersByTime(100);

            // Touch end
            docEl.dispatchEvent(createTouchEvent('touchend', 100, 200));

            // Drag mode must NOT be active and no avatar created
            expect(window.isTouchDragging).toBeFalsy();
            expect(document.getElementById('touch-drag-avatar')).toBeNull();

            // Normal click opens document
            docEl.click();
            expect(global.openDocument).toHaveBeenCalledWith('doc_touch_01', 'عقد إيجار شقة', '05 - عقود');
        });

        it('swiping finger > 8px before 280ms cancels drag timer so user can scroll normally', () => {
            renderCategories();
            const docList = document.getElementById('document-list');
            const docEl = docList.querySelector('.category-doc-item');

            // Touch start
            docEl.dispatchEvent(createTouchEvent('touchstart', 100, 200));

            // Move 25px vertically before hold threshold fires
            vi.advanceTimersByTime(50);
            docEl.dispatchEvent(createTouchEvent('touchmove', 100, 225));

            // Advance past 280ms timer
            vi.advanceTimersByTime(300);

            // Drag mode must remain inactive
            expect(window.isTouchDragging).toBeFalsy();
            expect(document.getElementById('touch-drag-avatar')).toBeNull();
        });

        it('pressing and holding document title >= 280ms activates touch drag mode with avatar and source dimming', () => {
            renderCategories();
            const docList = document.getElementById('document-list');
            const docEl = docList.querySelector('.category-doc-item');

            // Touch start and hold still
            docEl.dispatchEvent(createTouchEvent('touchstart', 100, 200));

            // Advance 280ms
            vi.advanceTimersByTime(290);

            // Drag mode MUST be active
            expect(window.isTouchDragging).toBe(true);
            expect(window.draggedDoc).not.toBeNull();
            expect(window.draggedDoc.vault_id).toBe('doc_touch_01');
            expect(window.draggedDoc.category).toBe('05 - عقود');

            // Floating drag avatar must be visible with document title and document icon (without 'Move' text)
            const avatar = document.getElementById('touch-drag-avatar');
            expect(avatar).not.toBeNull();
            expect(avatar.textContent).toContain('عقد إيجار شقة');
            expect(avatar.textContent).not.toContain('Move');
            expect(avatar.innerHTML).toContain('M9 12h6m-6 4h6m2 5H7');

            // Source element must have dimming & highlight classes
            expect(docEl.classList.contains('opacity-40')).toBe(true);
            expect(docEl.classList.contains('ring-2')).toBe(true);
        });

        it('touchmove during active drag updates avatar position and highlights target category folder card', () => {
            renderCategories();
            const docList = document.getElementById('document-list');
            const docEl = docList.querySelector('.category-doc-item');

            // Add a second category folder card to test drop target hovering
            const targetFolderCard = document.createElement('div');
            targetFolderCard.className = 'category-folder-card';
            targetFolderCard.setAttribute('data-category-name', '06 - كهرباء وماء');
            docList.appendChild(targetFolderCard);

            // Activate drag
            docEl.dispatchEvent(createTouchEvent('touchstart', 100, 200));
            vi.advanceTimersByTime(290);
            expect(window.isTouchDragging).toBe(true);

            // Mock elementFromPoint to return target folder card
            const originalElementFromPoint = document.elementFromPoint;
            document.elementFromPoint = vi.fn().mockReturnValue(targetFolderCard);

            try {
                // Move finger over target folder card
                docEl.dispatchEvent(createTouchEvent('touchmove', 150, 350));

                // Target card must get active highlight classes
                expect(targetFolderCard.classList.contains('drag-over-active')).toBe(true);
                expect(targetFolderCard.classList.contains('ring-2')).toBe(true);

                // Move finger away from card
                document.elementFromPoint = vi.fn().mockReturnValue(document.body);
                docEl.dispatchEvent(createTouchEvent('touchmove', 20, 20));

                // Highlight must be removed
                expect(targetFolderCard.classList.contains('drag-over-active')).toBe(false);
            } finally {
                document.elementFromPoint = originalElementFromPoint;
            }
        });

        it('releasing finger over target folder card executes move via handleCategoryDrop and suppresses click', async () => {
            renderCategories();
            const docList = document.getElementById('document-list');
            const docEl = docList.querySelector('.category-doc-item');

            const targetFolderCard = document.createElement('div');
            targetFolderCard.className = 'category-folder-card';
            targetFolderCard.setAttribute('data-category-name', '06 - كهرباء وماء');
            docList.appendChild(targetFolderCard);

            window.handleCategoryDrop = vi.fn().mockResolvedValue(true);

            // Activate drag
            docEl.dispatchEvent(createTouchEvent('touchstart', 100, 200));
            vi.advanceTimersByTime(290);
            expect(window.isTouchDragging).toBe(true);

            const originalElementFromPoint = document.elementFromPoint;
            document.elementFromPoint = vi.fn().mockReturnValue(targetFolderCard);

            try {
                // Release finger over target folder card
                docEl.dispatchEvent(createTouchEvent('touchend', 150, 350));

                // handleCategoryDrop must be invoked with target category
                expect(window.handleCategoryDrop).toHaveBeenCalledWith(
                    expect.anything(),
                    '06 - كهرباء وماء',
                    targetFolderCard
                );

                // State and avatar must be cleanly reset
                expect(window.isTouchDragging).toBe(false);
                expect(document.getElementById('touch-drag-avatar')).toBeNull();
                expect(docEl.classList.contains('opacity-40')).toBe(false);

                // Subsequent click must be suppressed (within 600ms)
                global.openDocument.mockClear();
                docEl.click();
                expect(global.openDocument).not.toHaveBeenCalled();
            } finally {
                document.elementFromPoint = originalElementFromPoint;
                delete window.handleCategoryDrop;
            }
        });

        it('releasing finger over same folder card does NOT trigger a move', () => {
            renderCategories();
            const docList = document.getElementById('document-list');
            const docEl = docList.querySelector('.category-doc-item');
            const sourceCard = docList.querySelector('.category-folder-card');

            window.handleCategoryDrop = vi.fn();

            // Activate drag
            docEl.dispatchEvent(createTouchEvent('touchstart', 100, 200));
            vi.advanceTimersByTime(290);
            expect(window.isTouchDragging).toBe(true);

            const originalElementFromPoint = document.elementFromPoint;
            document.elementFromPoint = vi.fn().mockReturnValue(sourceCard);

            try {
                // Release finger over the same folder card ('05 - عقود')
                docEl.dispatchEvent(createTouchEvent('touchend', 100, 200));

                // Must NOT invoke move
                expect(window.handleCategoryDrop).not.toHaveBeenCalled();
                expect(window.isTouchDragging).toBe(false);
                expect(document.getElementById('touch-drag-avatar')).toBeNull();
            } finally {
                document.elementFromPoint = originalElementFromPoint;
                delete window.handleCategoryDrop;
            }
        });
    });
});


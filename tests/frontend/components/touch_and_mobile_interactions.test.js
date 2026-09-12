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
});

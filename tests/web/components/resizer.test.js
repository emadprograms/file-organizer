import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

const resizerScriptPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/resizer.js');
const cssPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/css/styles.css');

function createTouchEvent(type, clientX, clientY = 300, identifier = 1) {
    const event = new Event(type, { bubbles: true, cancelable: true });
    const touch = { clientX, clientY, identifier, target: null };
    if (type === 'touchend' || type === 'touchcancel') {
        event.changedTouches = [touch];
        event.touches = [];
    } else {
        event.touches = [touch];
        event.changedTouches = [touch];
    }
    return event;
}

describe('Tenant Sidebar & Main Sidebar Resizer (Tablet Touch & Pointer Support)', () => {
    let store = {};
    const localStorageMock = {
        getItem: vi.fn(key => (key in store ? store[key] : null)),
        setItem: vi.fn((key, val) => { store[key] = String(val); }),
        removeItem: vi.fn(key => { delete store[key]; }),
        clear: vi.fn(() => { store = {}; })
    };

    function setupDOM() {
        document.body.innerHTML = `
            <div id="app-root" style="display: flex; width: 1000px; height: 800px;">
                <aside id="main-sidebar" style="width: 288px;"></aside>
                <div id="resizer-1" class="w-1 cursor-col-resize"></div>
                <main id="main-container" style="display: flex; flex: 1; width: 712px;">
                    <div id="document-list-panel" style="width: 33%; min-width: 260px; max-width: 60vw;"></div>
                    <div id="resizer-2" class="w-1 cursor-col-resize"></div>
                    <div id="document-viewer-panel" style="flex: 1;"></div>
                </main>
            </div>
        `;
    }

    beforeEach(() => {
        store = {};
        Object.defineProperty(window, 'localStorage', {
            value: localStorageMock,
            configurable: true,
            writable: true
        });
        setupDOM();

        // Load resizer.js
        const resizerCode = fs.readFileSync(resizerScriptPath, 'utf8');
        eval(resizerCode);
    });

    afterEach(() => {
        document.body.innerHTML = '';
        vi.restoreAllMocks();
    });

    describe('Tablet Touch Events on Tenant Sidebar (resizer-2)', () => {
        it('adjusts tenant sidebar width via touchstart and touchmove on tablets', () => {
            const panel = document.getElementById('document-list-panel');
            const resizer = document.getElementById('resizer-2');
            const mainContainer = document.getElementById('main-container');

            // Mock parent width to 1000px for percentage math
            vi.spyOn(mainContainer, 'getBoundingClientRect').mockReturnValue({
                width: 1000,
                height: 800,
                top: 0,
                left: 0,
                bottom: 800,
                right: 1000
            });
            vi.spyOn(panel, 'getBoundingClientRect').mockReturnValue({
                width: 330,
                height: 800,
                top: 0,
                left: 0,
                bottom: 800,
                right: 330
            });

            window.setupResizer('resizer-2', 'document-list-panel', true);

            // 1. Touchstart
            const touchStart = createTouchEvent('touchstart', 330);
            resizer.dispatchEvent(touchStart);

            expect(resizer.classList.contains('is-resizing')).toBe(true);
            expect(document.body.style.cursor).toBe('col-resize');
            expect(document.body.style.userSelect).toBe('none');

            // 2. Touchmove dragging to right (+120px => 450px = 45%)
            const touchMove = createTouchEvent('touchmove', 450);
            document.dispatchEvent(touchMove);

            expect(panel.style.width).toBe('45%');

            // 3. Touchend
            const touchEnd = createTouchEvent('touchend', 450);
            document.dispatchEvent(touchEnd);

            expect(resizer.classList.contains('is-resizing')).toBe(false);
            expect(document.body.style.cursor).toBe('default');
            expect(document.body.style.userSelect).toBe('');
            expect(localStorage.setItem).toHaveBeenCalledWith('document_list_panel_width', '45%');
        });

        it('clamps tenant sidebar percentage between 20% and 60% during tablet touch drag', () => {
            const panel = document.getElementById('document-list-panel');
            const resizer = document.getElementById('resizer-2');
            const mainContainer = document.getElementById('main-container');

            vi.spyOn(mainContainer, 'getBoundingClientRect').mockReturnValue({ width: 1000, height: 800 });
            vi.spyOn(panel, 'getBoundingClientRect').mockReturnValue({ width: 330, height: 800 });

            window.setupResizer('resizer-2', 'document-list-panel', true);

            // Start touch drag
            resizer.dispatchEvent(createTouchEvent('touchstart', 330));

            // Drag way too far left (e.g. clientX = 50 => newWidth = 50 => 5%)
            document.dispatchEvent(createTouchEvent('touchmove', 50));
            expect(panel.style.width).toBe('20%');

            // Drag way too far right (e.g. clientX = 950 => newWidth = 950 => 95%)
            document.dispatchEvent(createTouchEvent('touchmove', 950));
            expect(panel.style.width).toBe('60%');

            document.dispatchEvent(createTouchEvent('touchend', 950));
            expect(localStorage.setItem).toHaveBeenCalledWith('document_list_panel_width', '60%');
        });

        it('restores persisted tenant sidebar width from localStorage on setup', () => {
            store['document_list_panel_width'] = '42%';

            window.setupResizer('resizer-2', 'document-list-panel', true);

            const panel = document.getElementById('document-list-panel');
            expect(panel.style.width).toBe('42%');
        });

        it('terminates resizing cleanly when touchcancel event occurs', () => {
            const panel = document.getElementById('document-list-panel');
            const resizer = document.getElementById('resizer-2');
            const mainContainer = document.getElementById('main-container');

            vi.spyOn(mainContainer, 'getBoundingClientRect').mockReturnValue({ width: 1000, height: 800 });
            vi.spyOn(panel, 'getBoundingClientRect').mockReturnValue({ width: 330, height: 800 });

            window.setupResizer('resizer-2', 'document-list-panel', true);

            resizer.dispatchEvent(createTouchEvent('touchstart', 330));
            expect(resizer.classList.contains('is-resizing')).toBe(true);

            // touchcancel fires (e.g. incoming tablet notification or gesture conflict)
            document.dispatchEvent(createTouchEvent('touchcancel', 330));
            expect(resizer.classList.contains('is-resizing')).toBe(false);
            expect(document.body.style.cursor).toBe('default');
        });
    });

    describe('Tablet Touch Events on Main Sidebar (resizer-1)', () => {
        it('adjusts main sidebar pixel width smoothly via touch events', () => {
            const panel = document.getElementById('main-sidebar');
            const resizer = document.getElementById('resizer-1');

            vi.spyOn(panel, 'getBoundingClientRect').mockReturnValue({ width: 288, height: 800 });

            window.setupResizer('resizer-1', 'main-sidebar', false);

            resizer.dispatchEvent(createTouchEvent('touchstart', 288));
            document.dispatchEvent(createTouchEvent('touchmove', 360));
            expect(panel.style.width).toBe('360px');

            document.dispatchEvent(createTouchEvent('touchend', 360));
            expect(localStorage.setItem).toHaveBeenCalledWith('sidebar_width', '360px');
        });
    });

    describe('Desktop Mouse Interactions & Backward Compatibility', () => {
        it('supports mouse drag on tenant sidebar and main sidebar without regressions', () => {
            const panel = document.getElementById('document-list-panel');
            const resizer = document.getElementById('resizer-2');
            const mainContainer = document.getElementById('main-container');

            vi.spyOn(mainContainer, 'getBoundingClientRect').mockReturnValue({ width: 1000, height: 800 });
            vi.spyOn(panel, 'getBoundingClientRect').mockReturnValue({ width: 330, height: 800 });

            window.setupResizer('resizer-2', 'document-list-panel', true);

            resizer.dispatchEvent(new MouseEvent('mousedown', { clientX: 330 }));
            expect(resizer.classList.contains('is-resizing')).toBe(true);

            document.dispatchEvent(new MouseEvent('mousemove', { clientX: 400 }));
            expect(panel.style.width).toBe('40%');

            document.dispatchEvent(new MouseEvent('mouseup'));
            expect(resizer.classList.contains('is-resizing')).toBe(false);
            expect(localStorage.setItem).toHaveBeenCalledWith('document_list_panel_width', '40%');
        });
    });

    describe('Tablet CSS Architecture & Touch Target Accessibility', () => {
        it('verifies touch-action: none and expanded pseudo-element hit area in styles.css', () => {
            const cssContent = fs.readFileSync(cssPath, 'utf8');

            expect(cssContent).toContain('#resizer-1');
            expect(cssContent).toContain('#resizer-2');
            expect(cssContent).toMatch(/#resizer-1,\s*#resizer-2\s*\{[^}]*touch-action:\s*none/);
            expect(cssContent).toMatch(/#resizer-1::before,\s*#resizer-2::before\s*\{[^}]*position:\s*absolute/);
            expect(cssContent).toMatch(/#resizer-1\.is-resizing,\s*#resizer-2\.is-resizing/);
        });
    });
});

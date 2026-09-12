import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

const sidebarScriptPath = path.resolve(__dirname, '../../../src/api/static/js/sidebar.js');
const resizerScriptPath = path.resolve(__dirname, '../../../src/api/static/js/resizer.js');

describe('Sidebar Collapse and Expand Component', () => {
    let store = {};
    const localStorageMock = {
        getItem: vi.fn(key => (key in store ? store[key] : null)),
        setItem: vi.fn((key, val) => { store[key] = String(val); }),
        removeItem: vi.fn(key => { delete store[key]; }),
        clear: vi.fn(() => { store = {}; })
    };

    function setupDOM() {
        document.body.innerHTML = `
            <div class="flex h-screen w-full overflow-hidden">
                <aside id="main-sidebar" class="bg-slate-900 text-slate-300 overflow-y-auto flex flex-col relative group" style="width: 288px;">
                    <div class="p-4 border-b border-slate-800 flex items-center justify-between">
                        <span>File Organizer</span>
                        <div class="flex items-center gap-1.5">
                            <span>v11.0</span>
                            <button id="sidebar-collapse-btn" type="button" title="Collapse sidebar (Ctrl+B)">Collapse</button>
                        </div>
                    </div>
                    <div id="house-list"></div>
                </aside>
                <div id="resizer-1" class="w-1 cursor-col-resize"></div>
                <div class="flex-1 flex flex-col">
                    <header id="top-navbar" class="flex items-center justify-between">
                        <div class="flex items-center gap-2.5">
                            <button id="sidebar-toggle-btn" type="button" title="Toggle sidebar (Ctrl+B)" aria-expanded="true">Toggle</button>
                            <h1 id="current-house-title">Select an Area</h1>
                        </div>
                    </header>
                </div>
            </div>
            <input id="test-input" type="text" />
            <div id="test-editable" contenteditable="true"></div>
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

        // Load sidebar.js in clean environment
        const sidebarCode = fs.readFileSync(sidebarScriptPath, 'utf8');
        eval(sidebarCode);

        const resizerCode = fs.readFileSync(resizerScriptPath, 'utf8');
        eval(resizerCode);
    });

    afterEach(() => {
        document.body.innerHTML = '';
        vi.restoreAllMocks();
    });

    it('identifies expanded state by default', () => {
        const sidebar = document.getElementById('main-sidebar');
        expect(sidebar.classList.contains('hidden')).toBe(false);
        expect(window.isSidebarCollapsed()).toBe(false);
    });

    it('collapses sidebar and hides resizer when toggleSidebar(true) is called', () => {
        const sidebar = document.getElementById('main-sidebar');
        const resizer = document.getElementById('resizer-1');
        const toggleBtn = document.getElementById('sidebar-toggle-btn');

        window.toggleSidebar(true);

        expect(sidebar.classList.contains('hidden')).toBe(true);
        expect(resizer.classList.contains('hidden')).toBe(true);
        expect(window.isSidebarCollapsed()).toBe(true);
        expect(localStorage.setItem).toHaveBeenCalledWith('sidebar_collapsed', 'true');
        expect(toggleBtn.getAttribute('aria-expanded')).toBe('false');
        expect(toggleBtn.title).toContain('Expand');
    });

    it('expands sidebar and restores resizer when toggleSidebar(false) is called', () => {
        const sidebar = document.getElementById('main-sidebar');
        const resizer = document.getElementById('resizer-1');
        const toggleBtn = document.getElementById('sidebar-toggle-btn');

        window.toggleSidebar(true);
        expect(window.isSidebarCollapsed()).toBe(true);

        window.toggleSidebar(false);
        expect(sidebar.classList.contains('hidden')).toBe(false);
        expect(resizer.classList.contains('hidden')).toBe(false);
        expect(window.isSidebarCollapsed()).toBe(false);
        expect(localStorage.setItem).toHaveBeenCalledWith('sidebar_collapsed', 'false');
        expect(toggleBtn.getAttribute('aria-expanded')).toBe('true');
        expect(toggleBtn.title).toContain('Collapse');
    });

    it('toggles sidebar on clicking sidebar-toggle-btn in top-navbar', () => {
        window.initSidebarCollapse();
        const toggleBtn = document.getElementById('sidebar-toggle-btn');

        // Click to collapse
        toggleBtn.click();
        expect(window.isSidebarCollapsed()).toBe(true);

        // Click to expand
        toggleBtn.click();
        expect(window.isSidebarCollapsed()).toBe(false);
    });

    it('collapses sidebar on clicking sidebar-collapse-btn in sidebar header', () => {
        window.initSidebarCollapse();
        const collapseBtn = document.getElementById('sidebar-collapse-btn');

        collapseBtn.click();
        expect(window.isSidebarCollapsed()).toBe(true);
    });

    it('restores collapsed state on initialization if persisted in localStorage', () => {
        store['sidebar_collapsed'] = 'true';
        window.initSidebarCollapse();

        expect(window.isSidebarCollapsed()).toBe(true);
        const sidebar = document.getElementById('main-sidebar');
        expect(sidebar.classList.contains('hidden')).toBe(true);
    });

    it('saves and restores custom sidebar width across collapse/expand', () => {
        const sidebar = document.getElementById('main-sidebar');
        sidebar.style.width = '340px';

        window.toggleSidebar(true);
        expect(localStorage.setItem).toHaveBeenCalledWith('sidebar_width', '340px');

        // Emulate width wiped while collapsed
        sidebar.style.width = '0px';

        window.toggleSidebar(false);
        expect(sidebar.style.width).toBe('340px');
    });

    it('handles Ctrl+B / Cmd+B keyboard shortcut to toggle sidebar', () => {
        window.initSidebarCollapse();

        // Dispatch Ctrl+B
        const event = new KeyboardEvent('keydown', {
            key: 'b',
            ctrlKey: true,
            bubbles: true,
            cancelable: true
        });
        document.dispatchEvent(event);
        expect(window.isSidebarCollapsed()).toBe(true);

        // Dispatch Cmd+B (MetaKey)
        const metaEvent = new KeyboardEvent('keydown', {
            key: 'B',
            metaKey: true,
            bubbles: true,
            cancelable: true
        });
        document.dispatchEvent(metaEvent);
        expect(window.isSidebarCollapsed()).toBe(false);
    });

    it('ignores Ctrl+B / Cmd+B when typing in an input or contenteditable element', () => {
        window.initSidebarCollapse();

        const input = document.getElementById('test-input');
        input.focus();

        const event = new KeyboardEvent('keydown', {
            key: 'b',
            ctrlKey: true,
            bubbles: true,
            cancelable: true
        });
        input.dispatchEvent(event);

        // Should not have collapsed
        expect(window.isSidebarCollapsed()).toBe(false);
    });

    it('resizer saves width to localStorage on mouseup', () => {
        window.setupResizer('resizer-1', 'main-sidebar', false);
        const resizer = document.getElementById('resizer-1');
        const sidebar = document.getElementById('main-sidebar');

        // Simulate mousedown
        resizer.dispatchEvent(new MouseEvent('mousedown', { clientX: 288 }));
        sidebar.style.width = '350px';

        // Simulate mouseup
        document.dispatchEvent(new MouseEvent('mouseup'));
        expect(localStorage.setItem).toHaveBeenCalledWith('sidebar_width', '350px');
    });
});

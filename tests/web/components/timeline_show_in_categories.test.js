import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Timeline to Categories Navigation & Tab Responsiveness', () => {
    let routerModule;
    let docManagerModule;

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="document-list-panel">
                <div id="tab-back-to-tenants" class="hidden"></div>
                <div class="tabs">
                    <button id="tab-categories" class="flex-1 min-w-0 py-1.5 px-2.5 text-xs font-semibold rounded-md bg-white text-blue-600 shadow-xs flex items-center justify-center gap-1.5 transition-all overflow-hidden whitespace-nowrap">
                        <svg id="tab-categories-icon" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
                        </svg>
                        <span id="tab-categories-label">Folders</span>
                    </button>
                    <button id="tab-timeline" class="flex-1 min-w-0 py-1.5 px-2.5 text-xs font-medium rounded-md text-slate-600 hover:text-slate-900 flex items-center justify-center gap-1.5 transition-all overflow-hidden whitespace-nowrap">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2z"/>
                        </svg>
                        <span id="tab-timeline-label">Timeline</span>
                    </button>
                </div>
                <div id="document-list">
                    <div data-vault-id="doc_test_1" class="category-folder-card" data-category-name="06 - كهرباء وماء">
                        <div class="category-docs">
                            <div data-vault-id="doc_test_1" class="doc-card">Doc 1</div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="current-house-title"></div>
            <div id="area-grid-panel" class="hidden"></div>
            <div id="back-to-grid-btn" class="hidden"></div>
            <div id="welcome-panel" class="hidden"></div>
            <div id="document-viewer-panel" class="hidden"></div>
            <div id="resizer-2" class="hidden"></div>
        `;

        global.currentArea = 'Safra C';
        global.currentHouse = '514';
        global.currentTenant = null;
        global.currentTab = 'timeline';
        window.currentArea = 'Safra C';
        window.currentHouse = '514';
        window.currentTenant = null;
        window.currentTab = 'timeline';
        window.globalTreeData = [];
        window.showToast = vi.fn();
        window.loadCategories = vi.fn();
        window.loadTimeline = vi.fn();
        window.loadHouseProfile = vi.fn();
        window.setSelectedDoc = vi.fn();
        window.openCategoryFolder = vi.fn();

        // Load router.js
        routerModule = require('../../../src/HousingApplication.Web/wwwroot/js/router.js');
        window.switchMainTab = routerModule.switchMainTab;
        window.handleHashChange = routerModule.handleHashChange;
        window.selectHouse = routerModule.selectHouse;
        window.refreshCurrentTab = routerModule.refreshCurrentTab;
        window.safeDecodeURIComponent = routerModule.safeDecodeURIComponent;

        // Load doc-manager.js
        docManagerModule = require('../../../src/HousingApplication.Web/wwwroot/js/doc-manager.js');

        // Wire up tab click events as done in app.js
        const tabTimeline = document.getElementById('tab-timeline');
        const tabCategories = document.getElementById('tab-categories');

        tabTimeline.addEventListener('click', () => {
            if (typeof window.switchMainTab === 'function') {
                window.switchMainTab('timeline');
            }
        });

        tabCategories.addEventListener('click', () => {
            if (typeof window.switchMainTab === 'function') {
                window.switchMainTab('categories');
            }
        });
    });

    afterEach(() => {
        document.body.innerHTML = '';
        vi.restoreAllMocks();
        delete window.switchMainTab;
        delete window.refreshCurrentTab;
        delete window.selectHouse;
        delete window.safeDecodeURIComponent;
        delete window.handleHashChange;
    });

    it('switchMainTab updates both local and window.currentTab and switches DOM active classes', () => {
        const tabTimeline = document.getElementById('tab-timeline');
        const tabCategories = document.getElementById('tab-categories');

        window.switchMainTab('timeline');
        expect(window.currentTab).toBe('timeline');
        expect(tabTimeline.className).toContain('text-blue-600');
        expect(tabCategories.className).toContain('text-slate-600');

        window.switchMainTab('categories');
        expect(window.currentTab).toBe('categories');
        expect(tabCategories.className).toContain('text-blue-600');
        expect(tabTimeline.className).toContain('text-slate-600');
    });

    it('showDocInCategories switches tab to categories without locking tab state', async () => {
        const tabTimeline = document.getElementById('tab-timeline');
        const tabCategories = document.getElementById('tab-categories');

        // Initially in timeline view
        window.switchMainTab('timeline');
        expect(window.currentTab).toBe('timeline');

        const testDoc = {
            vault_id: 'doc_test_1',
            area: 'Safra C',
            house: '514',
            primary_tenant: 'علي الحداد',
            category: '06 - كهرباء وماء',
            brief_arabic_title: 'فاتورة ماء'
        };

        // Call showDocInCategories
        docManagerModule.showDocInCategories(testDoc);

        // Verify categories tab is now active
        expect(window.currentTab).toBe('categories');
        expect(tabCategories.className).toContain('text-blue-600');
        expect(tabTimeline.className).toContain('text-slate-600');
        expect(window._pendingOpenCategory).toBe('06 - كهرباء وماء');

        // Now test responsiveness: user clicks Timeline tab
        tabTimeline.click();
        expect(window.currentTab).toBe('timeline');
        expect(tabTimeline.className).toContain('text-blue-600');
        expect(tabCategories.className).toContain('text-slate-600');
        expect(window.loadTimeline).toHaveBeenCalledWith('Safra C', '514');

        // Now test responsiveness: user clicks Categories tab again
        tabCategories.click();
        expect(window.currentTab).toBe('categories');
        expect(tabCategories.className).toContain('text-blue-600');
        expect(tabTimeline.className).toContain('text-slate-600');
        expect(window.loadCategories).toHaveBeenCalled();
    });

    it('safeDecodeURIComponent handles encoded, decoded, and malformed strings gracefully', () => {
        const { safeDecodeURIComponent } = routerModule;
        expect(safeDecodeURIComponent('%D8%A7%D9%84%D8%AE%D8%A8%D8%B1')).toBe('الخبر');
        expect(safeDecodeURIComponent('الخبر')).toBe('الخبر');
        // Malformed URI string with bare % that would throw URIError with plain decodeURIComponent
        expect(safeDecodeURIComponent('100%_valid%E0%A4%A')).toBe('100%_valid%E0%A4%A');
        expect(safeDecodeURIComponent('')).toBe('');
        expect(safeDecodeURIComponent(null)).toBe('');
    });

    it('handleHashChange routes correctly without throwing URIError on complex or percent characters', async () => {
        window.location.hash = '#/area/%D8%A7%D9%84%D8%AE%D8%A8%D8%B1/house/514/tenant/514_%D8%B9%D9%84%D9%8A';

        expect(() => {
            window.handleHashChange();
        }).not.toThrow();

        expect(window.currentArea).toBe('الخبر');
        expect(window.currentHouse).toBe('514');
        expect(window.currentTenant).toBe('علي');
    });
});

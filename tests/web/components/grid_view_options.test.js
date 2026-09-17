import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Header Bar View Options & Settings Popover Component', () => {
    const htmlPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/index.html');
    const htmlContent = fs.readFileSync(htmlPath, 'utf8');

    const areaGridPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/area-grid.js');
    const areaGrid = require(areaGridPath);

    let store = {};
    const localStorageMock = {
        getItem: vi.fn(key => (key in store ? store[key] : null)),
        setItem: vi.fn((key, val) => { store[key] = String(val); }),
        removeItem: vi.fn(key => { delete store[key]; }),
        clear: vi.fn(() => { store = {}; })
    };

    const testAreaNode = {
        name: 'Area 1',
        children: [
            {
                id: '10',
                name: '10',
                current_tenant: 'Ahmed Ali',
                active_tenant_category_counts: {
                    '02 - بيانات شخصية': 1,
                    '03 - أمر تخصيص': 1,
                    '04 - محضر تسليم مفتاح': 1,
                    '05 - عقود': 1,
                    '07 - استقطاع إيجار': 1
                },
                children: [{ name: 'Ahmed Ali', is_resident: 1, start_date: '2020-01-01' }]
            },
            {
                id: '20',
                name: '20',
                current_tenant: 'Mohamed Salem',
                active_tenant_category_counts: {
                    '02 - بيانات شخصية': 1
                },
                children: [{ name: 'Mohamed Salem', is_resident: 1, start_date: '2023-01-01' }]
            },
            {
                id: '30',
                name: '30',
                current_tenant: null,
                children: []
            }
        ]
    };

    beforeEach(() => {
        store = {};
        vi.stubGlobal('localStorage', localStorageMock);
        document.body.innerHTML = htmlContent;

        global.currentArea = '';
        global.currentHouse = null;
        global.currentTenant = null;
        window.currentArea = '';
        window.currentHouse = null;
        window.currentTenant = null;
    });

    afterEach(() => {
        document.body.innerHTML = '';
        store = {};
        vi.restoreAllMocks();
    });

    describe('HTML Structure and Layout Verification', () => {
        it('verifies index.html places View Options button and popover inside #top-navbar', () => {
            const topNavbar = document.getElementById('top-navbar');
            expect(topNavbar).not.toBeNull();

            const wrapper = topNavbar.querySelector('#grid-view-options-wrapper');
            expect(wrapper).not.toBeNull();
            expect(wrapper.classList.contains('hidden')).toBe(true);

            const btn = wrapper.querySelector('#btn-grid-view-options');
            expect(btn).not.toBeNull();
            expect(btn.textContent).toContain('View');

            const badge = btn.querySelector('#grid-view-active-filter-badge');
            expect(badge).not.toBeNull();

            const popover = wrapper.querySelector('#grid-view-popover');
            expect(popover).not.toBeNull();
            expect(popover.classList.contains('hidden')).toBe(true);
        });

        it('verifies popover contains Filter and Sort sections, while tenure duration legend is outside in #top-navbar', () => {
            const popover = document.getElementById('grid-view-popover');
            expect(popover).not.toBeNull();

            // Filter section inside popover
            const integrityToolbar = popover.querySelector('#grid-integrity-toolbar');
            expect(integrityToolbar).not.toBeNull();
            expect(popover.querySelector('#grid-integrity-pills')).not.toBeNull();
            expect(popover.querySelector('#grid-integrity-summary')).not.toBeNull();

            // Sort section inside popover
            const sortContainer = popover.querySelector('#grid-house-sort-container');
            expect(sortContainer).not.toBeNull();
            const sortSelect = sortContainer.querySelector('#grid-house-sort-select');
            expect(sortSelect).not.toBeNull();
            expect(sortSelect.options.length).toBe(4);

            // Legend section is positioned outside the popover directly in #top-navbar
            const topNavbar = document.getElementById('top-navbar');
            const tenureLegend = topNavbar.querySelector('#grid-tenure-legend');
            expect(tenureLegend).not.toBeNull();
            expect(popover.querySelector('#grid-tenure-legend')).toBeNull();
            expect(tenureLegend.textContent).toContain('< 5y');
            expect(tenureLegend.textContent).toContain('5–10y');
            expect(tenureLegend.textContent).toContain('> 10y');
            expect(tenureLegend.textContent).toContain('Vacant');
        });

        it('verifies #area-grid-panel does NOT contain separate filter toolbar and area grid container sits cleanly at the top', () => {
            const areaGridPanel = document.getElementById('area-grid-panel');
            expect(areaGridPanel).not.toBeNull();

            // The separate toolbar must not be inside area-grid-panel
            const toolbarInsidePanel = areaGridPanel.querySelector(':scope > #grid-integrity-toolbar');
            expect(toolbarInsidePanel).toBeNull();

            // The house cards container is directly inside area-grid-panel
            const container = areaGridPanel.querySelector('#area-grid-container');
            expect(container).not.toBeNull();
            expect(container.parentElement.id).toBe('area-grid-panel');
        });
    });

    describe('Interactive Behavior & Popover Management', () => {
        it('shows View Options button and populates pills and sort when renderAreaGrid is called', () => {
            areaGrid.renderAreaGrid(testAreaNode);

            const wrapper = document.getElementById('grid-view-options-wrapper');
            expect(wrapper.classList.contains('hidden')).toBe(false);

            // Popover remains closed until clicked
            const popover = document.getElementById('grid-view-popover');
            expect(popover.classList.contains('hidden')).toBe(true);

            // Active filter badge is hidden for 'all'
            const badge = document.getElementById('grid-view-active-filter-badge');
            expect(badge.classList.contains('hidden')).toBe(true);

            // Filter pills are rendered inside the popover
            const pills = popover.querySelectorAll('.grid-filter-pill');
            expect(pills.length).toBe(4);
        });

        it('toggles popover open and closed when clicking #btn-grid-view-options', () => {
            areaGrid.renderAreaGrid(testAreaNode);
            areaGrid.initGridViewOptions();

            const btn = document.getElementById('btn-grid-view-options');
            const popover = document.getElementById('grid-view-popover');
            const chevron = document.getElementById('grid-view-chevron');

            // Click to open
            btn.click();
            expect(popover.classList.contains('hidden')).toBe(false);
            expect(btn.getAttribute('aria-expanded')).toBe('true');
            expect(chevron.classList.contains('rotate-180')).toBe(true);

            // Click to close
            btn.click();
            expect(popover.classList.contains('hidden')).toBe(true);
            expect(btn.getAttribute('aria-expanded')).toBe('false');
            expect(chevron.classList.contains('rotate-180')).toBe(false);
        });

        it('closes popover on Escape keydown', () => {
            areaGrid.renderAreaGrid(testAreaNode);
            areaGrid.initGridViewOptions();

            const btn = document.getElementById('btn-grid-view-options');
            const popover = document.getElementById('grid-view-popover');

            btn.click();
            expect(popover.classList.contains('hidden')).toBe(false);

            // Press Escape
            const escapeEvent = new KeyboardEvent('keydown', { key: 'Escape' });
            document.dispatchEvent(escapeEvent);

            expect(popover.classList.contains('hidden')).toBe(true);
        });

        it('closes popover when clicking outside of it', () => {
            areaGrid.renderAreaGrid(testAreaNode);
            areaGrid.initGridViewOptions();

            const btn = document.getElementById('btn-grid-view-options');
            const popover = document.getElementById('grid-view-popover');

            btn.click();
            expect(popover.classList.contains('hidden')).toBe(false);

            // Click outside (e.g. on main container)
            document.dispatchEvent(new MouseEvent('click', { bubbles: true }));

            expect(popover.classList.contains('hidden')).toBe(true);
        });

        it('updates active filter badge dynamically when selecting filters', () => {
            areaGrid.renderAreaGrid(testAreaNode);

            const badge = document.getElementById('grid-view-active-filter-badge');

            // Filter incomplete
            areaGrid.setIntegrityFilter('incomplete');
            expect(badge.classList.contains('hidden')).toBe(false);
            expect(badge.textContent).toBe('Incomplete (1)');
            expect(badge.className).toContain('text-amber-800');

            // Filter complete
            areaGrid.setIntegrityFilter('complete');
            expect(badge.classList.contains('hidden')).toBe(false);
            expect(badge.textContent).toBe('Complete (1)');
            expect(badge.className).toContain('text-emerald-800');

            // Filter vacant
            areaGrid.setIntegrityFilter('vacant');
            expect(badge.classList.contains('hidden')).toBe(false);
            expect(badge.textContent).toBe('Vacant (1)');
            expect(badge.className).toContain('text-slate-800');

            // Filter all (default)
            areaGrid.setIntegrityFilter('all');
            expect(badge.classList.contains('hidden')).toBe(true);
            expect(badge.textContent).toBe('');
        });

        it('hides View Options button and closes popover when navigating to a house', () => {
            areaGrid.renderAreaGrid(testAreaNode);
            areaGrid.openGridViewOptions();

            const wrapper = document.getElementById('grid-view-options-wrapper');
            const popover = document.getElementById('grid-view-popover');
            expect(wrapper.classList.contains('hidden')).toBe(false);
            expect(popover.classList.contains('hidden')).toBe(false);

            areaGrid.openHouseFromGrid('Area 1', '10');

            expect(wrapper.classList.contains('hidden')).toBe(true);
            expect(popover.classList.contains('hidden')).toBe(true);
        });
    });
});

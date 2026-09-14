import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Top Header Bar House Sorting Component (House Number & Longest Tenant Stay)', () => {
    const htmlPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/index.html');
    const htmlContent = fs.readFileSync(htmlPath, 'utf8');

    const cssPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/css/styles.css');
    const cssContent = fs.readFileSync(cssPath, 'utf8');

    const areaGridPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/area-grid.js');
    const areaGrid = require(areaGridPath);

    let store = {};
    const localStorageMock = {
        getItem: vi.fn(key => (key in store ? store[key] : null)),
        setItem: vi.fn((key, val) => { store[key] = String(val); }),
        removeItem: vi.fn(key => { delete store[key]; }),
        clear: vi.fn(() => { store = {}; })
    };

    beforeEach(() => {
        store = {};
        vi.stubGlobal('localStorage', localStorageMock);
        document.body.innerHTML = `
            <header id="top-navbar">
                <button id="back-to-grid-btn" class="hidden"></button>
                <h1 id="current-house-title"></h1>
                <span id="grid-area-title" class="hidden"></span>
                <div id="stats-badge" class="hidden"></div>
                <div id="grid-area-stats" class="hidden">0 Houses</div>
                
                <div id="grid-house-sort-container" class="hidden items-center gap-2">
                    <select id="grid-house-sort-select">
                        <option value="number">House Number</option>
                        <option value="longest_stay">Longest Stay</option>
                    </select>
                </div>

                <div id="grid-tenure-legend" class="hidden"></div>
            </header>
            <div id="welcome-panel" class="hidden"></div>
            <div id="document-list-panel" class="hidden"></div>
            <div id="document-viewer-panel" class="hidden"></div>
            <div id="database-inspector-panel" class="hidden"></div>
            <div id="resizer-2" class="hidden"></div>
            <div id="tab-back-to-tenants" class="hidden"></div>
            <div id="area-grid-panel" class="hidden">
                <div id="area-grid-container"></div>
            </div>
        `;

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

    describe('HTML Structure and CSS Styling', () => {
        it('verifies index.html has #grid-house-sort-container in #top-navbar with correct options', () => {
            document.body.innerHTML = htmlContent;

            const topNavbar = document.getElementById('top-navbar');
            expect(topNavbar).not.toBeNull();

            const sortContainer = topNavbar.querySelector('#grid-house-sort-container');
            expect(sortContainer).not.toBeNull();
            expect(sortContainer.classList.contains('hidden')).toBe(true);

            const select = sortContainer.querySelector('#grid-house-sort-select');
            expect(select).not.toBeNull();

            const options = Array.from(select.querySelectorAll('option')).map(o => ({ value: o.value, text: o.textContent.trim() }));
            expect(options).toEqual([
                { value: 'number', text: 'House Number' },
                { value: 'longest_stay', text: 'Longest Stay' }
            ]);
        });

        it('verifies styles.css provides transparent, borderless styling for sort select in light and dark modes', () => {
            expect(cssContent).toContain('#grid-house-sort-select');
            expect(cssContent).toContain('background-color: transparent !important;');
            expect(cssContent).toContain('border: none !important;');
            expect(cssContent).toMatch(/html\.dark #grid-house-sort-select/);
            expect(cssContent).toMatch(/html\.dark #grid-house-sort-select option/);
        });
    });

    describe('Sorting Comparison Logic', () => {
        it('compares house numbers naturally (e.g., 2 before 10, 101 before 616)', () => {
            const h1 = { name: '2' };
            const h2 = { name: '10' };
            const h3 = { name: '101' };
            const h4 = { name: '616' };

            const list = [h4, h1, h3, h2];
            list.sort(areaGrid.compareHouseNumbers);

            expect(list.map(h => h.name)).toEqual(['2', '10', '101', '616']);
        });

        it('compares alphanumeric house names naturally (e.g., House 2 before House 10)', () => {
            const h1 = { name: 'House 2' };
            const h2 = { name: 'House 10' };
            const h3 = { name: 'House 101' };

            const list = [h2, h3, h1];
            list.sort(areaGrid.compareHouseNumbers);

            expect(list.map(h => h.name)).toEqual(['House 2', 'House 10', 'House 101']);
        });

        it('calculates max stay days for houses from tenant start and end dates', () => {
            const houseLong = {
                name: '101',
                children: [
                    { type: 'tenant', is_resident: 1, start_date: '1990-01-01', end_date: 'Present' }
                ]
            };
            const houseShort = {
                name: '102',
                children: [
                    { type: 'tenant', is_resident: 1, start_date: '2023-01-01', end_date: 'Present' }
                ]
            };
            const houseVacant = {
                name: '103',
                children: []
            };

            const stayLong = areaGrid.getHouseMaxStayDays(houseLong);
            const stayShort = areaGrid.getHouseMaxStayDays(houseShort);
            const stayVacant = areaGrid.getHouseMaxStayDays(houseVacant);

            expect(stayLong).toBeGreaterThan(stayShort);
            expect(stayShort).toBeGreaterThan(stayVacant);
            expect(stayVacant).toBe(0);
        });

        it('ignores applicants (is_resident = 0) when computing resident tenant stay', () => {
            const houseWithApplicantOnly = {
                name: '104',
                children: [
                    { type: 'tenant', is_resident: 0, start_date: '1985-01-01', end_date: 'Present' }
                ]
            };

            const stay = areaGrid.getHouseMaxStayDays(houseWithApplicantOnly);
            expect(stay).toBe(0);
        });

        it('sorts by longest tenant stay in descending order with house number tie-breaker', () => {
            const hVacant1 = { name: '5', children: [] };
            const hVacant2 = { name: '2', children: [] };
            const hMedium = {
                name: '20',
                children: [{ type: 'tenant', is_resident: 1, start_date: '2018-01-01', end_date: 'Present' }]
            };
            const hLong = {
                name: '10',
                children: [{ type: 'tenant', is_resident: 1, start_date: '1995-01-01', end_date: 'Present' }]
            };
            const hShort = {
                name: '1',
                children: [{ type: 'tenant', is_resident: 1, start_date: '2024-01-01', end_date: 'Present' }]
            };

            const list = [hVacant1, hMedium, hShort, hVacant2, hLong];
            list.sort(areaGrid.compareHouseLongestStay);

            expect(list.map(h => h.name)).toEqual(['10', '20', '1', '2', '5']);
        });

        it('prioritizes current active resident tenure over past tenants (active tenure contract)', () => {
            // House with short active tenant (2024 ~ 2y) but long past tenant (1980-2010 ~ 30y)
            const houseRecentWithLongPast = {
                id: 'H1',
                name: 'H1',
                current_tenant: 'Current Bob',
                duration_category: 'short',
                subtitle: 'Since 2024 (2y)',
                children: [
                    { type: 'tenant', is_resident: 1, name: 'Old Charlie', start_date: '1980-01-01', end_date: '2010-01-01', subtitle: '1980 - 2010' },
                    { type: 'tenant', is_resident: 1, name: 'Current Bob', start_date: '2024-01-01', end_date: 'Present', subtitle: '2024 - Present', duration_category: 'short' }
                ]
            };

            // House with long active tenant (2008 ~ 18y) and no past tenants
            const houseLongResident = {
                id: 'H2',
                name: 'H2',
                current_tenant: 'Long Alice',
                duration_category: 'long',
                subtitle: 'Since 2008 (18y)',
                children: [
                    { type: 'tenant', is_resident: 1, name: 'Long Alice', start_date: '2008-01-01', end_date: 'Present', subtitle: '2008 - Present', duration_category: 'long' }
                ]
            };

            // Active stay for H1 must be ~2 years, NOT 30 years
            const stayH1 = areaGrid.getHouseMaxStayDays(houseRecentWithLongPast);
            const stayH2 = areaGrid.getHouseMaxStayDays(houseLongResident);

            expect(stayH2).toBeGreaterThan(stayH1);

            // Sorting by longest stay must place H2 (18y) BEFORE H1 (2y)
            const list = [houseRecentWithLongPast, houseLongResident];
            list.sort(areaGrid.compareHouseLongestStay);
            expect(list.map(h => h.id)).toEqual(['H2', 'H1']);
        });

        it('always places vacant houses after occupied houses regardless of past history', () => {
            // Vacant house with 35-year past tenant
            const vacantHouseOld = {
                id: 'HV-Old',
                name: 'HV-Old',
                current_tenant: null,
                duration_category: null,
                subtitle: '1970 - 2005',
                children: [
                    { type: 'tenant', is_resident: 1, name: 'Past Legend', start_date: '1970-01-01', end_date: '2005-01-01', subtitle: '1970 - 2005' }
                ]
            };

            // Occupied house with brand new resident (6 months)
            const occupiedHouseNew = {
                id: 'H-New',
                name: 'H-New',
                current_tenant: 'Fresh Resident',
                duration_category: 'short',
                subtitle: 'Since 2025',
                children: [
                    { type: 'tenant', is_resident: 1, name: 'Fresh Resident', start_date: '2025-09-01', end_date: 'Present', subtitle: '2025 - Present', duration_category: 'short' }
                ]
            };

            // Completely empty vacant house
            const vacantHouseZero = {
                id: 'HV-Empty',
                name: 'HV-Empty',
                current_tenant: null,
                duration_category: null,
                children: []
            };

            const list = [vacantHouseOld, vacantHouseZero, occupiedHouseNew];
            list.sort(areaGrid.compareHouseLongestStay);

            // Occupied house must be first, then vacant with history, then vacant with zero
            expect(list.map(h => h.id)).toEqual(['H-New', 'HV-Old', 'HV-Empty']);
        });

        it('resolves stay correctly from house.subtitle and duration_category when children lack start_date', () => {
            const houseFromSubtitle = {
                id: 'H-Sub',
                name: 'H-Sub',
                current_tenant: 'John Doe',
                duration_category: 'long',
                subtitle: 'Since 1990 (36y)',
                children: [
                    { type: 'tenant', is_resident: 1, name: 'John Doe', subtitle: '1990 - Present', duration_category: 'long' }
                ]
            };

            const stay = areaGrid.getHouseMaxStayDays(houseFromSubtitle);
            // 36 years * 365.25 is ~13,149 days
            expect(stay).toBeGreaterThan(30 * 365);
        });

        it('handles Arabic tenure text and DD/MM/YYYY date formatting correctly', () => {
            const houseArabic = {
                id: 'H-Ar',
                name: 'H-Ar',
                current_tenant: 'مستأجر عربي',
                subtitle: 'بدء الإيجار 2012 (مستمر)',
                children: [
                    { type: 'tenant', is_resident: 1, name: 'مستأجر عربي', start_date: '15/06/2012', end_date: 'الآن', subtitle: '2012 - الآن' }
                ]
            };

            expect(areaGrid.isHouseOccupied(houseArabic)).toBe(true);
            const stay = areaGrid.getHouseMaxStayDays(houseArabic);
            // From 2012 to current year is at least 13 years (~4,700+ days)
            expect(stay).toBeGreaterThan(12 * 365);
        });
    });

    describe('Area Grid Integration and User Interaction', () => {
        const testAreaNode = {
            name: 'Safra Area',
            children: [
                {
                    id: '10',
                    name: '10',
                    children: [{ type: 'tenant', is_resident: 1, start_date: '1995-01-01', end_date: 'Present' }]
                },
                {
                    id: '2',
                    name: '2',
                    children: [{ type: 'tenant', is_resident: 1, start_date: '2024-01-01', end_date: 'Present' }]
                },
                {
                    id: '101',
                    name: '101',
                    children: [{ type: 'tenant', is_resident: 1, start_date: '2015-01-01', end_date: 'Present' }]
                },
                {
                    id: '1',
                    name: '1',
                    children: []
                }
            ]
        };

        it('renders houses in House Number order by default', () => {
            areaGrid.renderAreaGrid(testAreaNode);

            const container = document.getElementById('area-grid-container');
            const renderedCards = Array.from(container.querySelectorAll('.house-card'));
            const renderedHouseIds = renderedCards.map(c => c.dataset.houseId);

            // Default 'number' natural sort: 1, 2, 10, 101
            expect(renderedHouseIds).toEqual(['1', '2', '10', '101']);

            const sortSelect = document.getElementById('grid-house-sort-select');
            expect(sortSelect.value).toBe('number');
        });

        it('renders houses in Longest Tenant Stay order when stored preference is longest_stay', () => {
            localStorage.setItem('house_sort_by', 'longest_stay');

            areaGrid.renderAreaGrid(testAreaNode);

            const container = document.getElementById('area-grid-container');
            const renderedCards = Array.from(container.querySelectorAll('.house-card'));
            const renderedHouseIds = renderedCards.map(c => c.dataset.houseId);

            // Stays:
            // 10 (1995 ~ 31y)
            // 101 (2015 ~ 11y)
            // 2 (2024 ~ 2y)
            // 1 (vacant = 0y)
            expect(renderedHouseIds).toEqual(['10', '101', '2', '1']);

            const sortSelect = document.getElementById('grid-house-sort-select');
            expect(sortSelect.value).toBe('longest_stay');
        });

        it('re-renders grid immediately when user changes the sort select dropdown and persists to localStorage', () => {
            areaGrid.renderAreaGrid(testAreaNode);

            const sortSelect = document.getElementById('grid-house-sort-select');
            expect(sortSelect.value).toBe('number');

            // Simulate user selecting "Longest Stay"
            sortSelect.value = 'longest_stay';
            sortSelect.dispatchEvent(new Event('change'));

            expect(localStorage.getItem('house_sort_by')).toBe('longest_stay');

            const container = document.getElementById('area-grid-container');
            const renderedCards = Array.from(container.querySelectorAll('.house-card'));
            const renderedHouseIds = renderedCards.map(c => c.dataset.houseId);

            expect(renderedHouseIds).toEqual(['10', '101', '2', '1']);

            // Switch back to House Number
            sortSelect.value = 'number';
            sortSelect.dispatchEvent(new Event('change'));

            expect(localStorage.getItem('house_sort_by')).toBe('number');

            const reCards = Array.from(container.querySelectorAll('.house-card'));
            expect(reCards.map(c => c.dataset.houseId)).toEqual(['1', '2', '10', '101']);
        });

        it('always keeps the add-house-grid-card at the end of the grid regardless of sort order', () => {
            areaGrid.renderAreaGrid(testAreaNode);

            const container = document.getElementById('area-grid-container');
            let lastCard = container.lastElementChild;
            expect(lastCard.id).toBe('add-house-grid-card');

            const sortSelect = document.getElementById('grid-house-sort-select');
            sortSelect.value = 'longest_stay';
            sortSelect.dispatchEvent(new Event('change'));

            lastCard = container.lastElementChild;
            expect(lastCard.id).toBe('add-house-grid-card');
        });

        it('shows sort container in Area Overview mode and hides it when opening a house card', () => {
            areaGrid.renderAreaGrid(testAreaNode);

            const sortContainer = document.getElementById('grid-house-sort-container');
            expect(sortContainer.classList.contains('hidden')).toBe(false);
            expect(sortContainer.classList.contains('flex')).toBe(true);

            areaGrid.openHouseFromGrid('Safra Area', '10');

            expect(sortContainer.classList.contains('hidden')).toBe(true);
        });
    });
});

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Tenant File Integrity & Compliance Check (Idea B + Idea C)', () => {
    const areaGridPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/area-grid.js');
    const areaGrid = require(areaGridPath);

    const houseProfilePath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/house-profile.js');
    const houseProfile = require(houseProfilePath);

    const ingestStationPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/ingest-station.js');
    const ingestStation = require(ingestStationPath);

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
                        <option value="integrity_worst">Compliance: Missing First</option>
                        <option value="integrity_best">Compliance: Complete First</option>
                    </select>
                </div>

                <div id="grid-tenure-legend" class="hidden"></div>
            </header>
            <div id="welcome-panel" class="hidden"></div>
            <div id="document-list-panel">
                <div id="document-list"></div>
            </div>
            <div id="document-viewer-panel" class="hidden"></div>
            <div id="database-inspector-panel" class="hidden"></div>
            <div id="resizer-2" class="hidden"></div>
            <div id="tab-back-to-tenants" class="hidden"></div>
            <div id="area-grid-panel" class="hidden">
                <div id="grid-integrity-toolbar" class="mb-4 flex items-center justify-between">
                    <div id="grid-integrity-pills"></div>
                    <div id="grid-integrity-summary"></div>
                </div>
                <div id="area-grid-container"></div>
            </div>

            <!-- Ingest Station Modal -->
            <div id="ingest-station-modal" class="hidden">
                <div id="ingest-station-card">
                    <button id="btn-ingest-close">Close</button>
                    
                    <button type="button" id="tab-mode-single" class="bg-blue-600 text-white shadow-2xs font-semibold"></button>
                    <button type="button" id="tab-mode-broadcast"></button>
                    <button type="button" id="tab-mode-housebatch"></button>

                    <div id="section-mode-single">
                        <div id="ingest-file-dropzone">
                            <input id="ingest-file-input" type="file" accept=".pdf" />
                        </div>
                        <div id="ingest-file-info" class="hidden">
                            <p id="ingest-file-name"></p>
                            <p id="ingest-file-size"></p>
                            <button id="btn-remove-file">Change</button>
                        </div>
                        <div id="ingest-preview-container" class="hidden">
                            <iframe id="ingest-pdf-preview" src="about:blank"></iframe>
                        </div>

                        <select id="ingest-area-select">
                            <option value="">Select Area...</option>
                            <option value="Safra">Safra</option>
                        </select>
                        <select id="ingest-house-select">
                            <option value="">Select House...</option>
                            <option value="101">101</option>
                        </select>
                        <select id="ingest-tenant-select">
                            <option value="">(Auto-detect or Select Tenant)</option>
                            <option value="Ahmad Al-Mansoor">Ahmad Al-Mansoor</option>
                        </select>
                        <button id="btn-toggle-new-tenant">+ Add New Tenant</button>
                        <div id="ingest-new-tenant-container" class="hidden">
                            <input id="ingest-new-tenant-input" type="text" />
                        </div>
                        <select id="ingest-category-select">
                            <option value="02 - بيانات شخصية">02 - بيانات شخصية</option>
                            <option value="03 - أمر تخصيص">03 - أمر تخصيص</option>
                            <option value="04 - محضر تسليم مفتاح">04 - محضر تسليم مفتاح</option>
                            <option value="05 - عقود">05 - عقود</option>
                            <option value="07 - استقطاع إيجار">07 - استقطاع إيجار</option>
                            <option value="13 - رسائل متنوعة" selected>13 - رسائل متنوعة</option>
                        </select>
                        <input id="ingest-title-input" type="text" />
                        <input id="ingest-date-input" type="date" />
                        <textarea id="ingest-notes-input"></textarea>
                    </div>

                    <div id="section-mode-broadcast" class="hidden">
                        <div id="broadcast-dropzone"></div>
                        <div id="broadcast-file-info" class="hidden"></div>
                        <div id="broadcast-preview-container" class="hidden"></div>
                        <select id="broadcast-category-select">
                            <option value="09 - إشعارات" selected>09 - إشعارات</option>
                        </select>
                        <input id="broadcast-title-input" type="text" />
                        <input id="broadcast-date-input" type="date" />
                        <select id="broadcast-area-select"></select>
                    </div>

                    <div id="section-mode-housebatch" class="hidden">
                        <div id="housebatch-dropzone"></div>
                        <div id="housebatch-queue-container" class="hidden">
                            <div id="housebatch-queue-list"></div>
                        </div>
                    </div>

                    <div id="ingest-batch-progress" class="hidden">
                        <span id="ingest-batch-progress-text"></span>
                        <span id="ingest-batch-progress-pct"></span>
                        <div id="ingest-batch-progress-bar"></div>
                    </div>
                    <div id="ingest-status-msg" class="hidden"></div>
                    <button id="btn-ingest-submit">Submit</button>
                    <span id="ingest-submit-spinner" class="hidden"></span>
                    <span id="ingest-submit-text">Submit</span>
                </div>
            </div>
        `;

        global.currentArea = '';
        global.currentHouse = null;
        global.currentTenant = null;
        window.currentArea = '';
        window.currentHouse = null;
        window.currentTenant = null;
        window.isStaticMode = false;
        window.showToast = vi.fn();

        areaGrid.setIntegrityFilter('all');
    });

    afterEach(() => {
        document.body.innerHTML = '';
        store = {};
        vi.restoreAllMocks();
    });

    describe('1. Mandatory Integrity Categories Specification', () => {
        it('exports the 5 exact mandatory categories with correct IDs and Arabic/English labels in both modules', () => {
            const expected = [
                { id: '02', key: 'بيانات شخصية', prefix: '02 - بيانات شخصية' },
                { id: '03', key: 'أمر تخصيص', prefix: '03 - أمر تخصيص' },
                { id: '04', key: 'محضر تسليم مفتاح', prefix: '04 - محضر تسليم مفتاح' },
                { id: '05', key: 'عقود', prefix: '05 - عقود' },
                { id: '07', key: 'استقطاع إيجار', prefix: '07 - استقطاع إيجار' },
            ];

            expect(areaGrid.MANDATORY_INTEGRITY_CATEGORIES).toHaveLength(5);
            expect(houseProfile.MANDATORY_INTEGRITY_CATEGORIES).toHaveLength(5);

            expected.forEach(exp => {
                const matchArea = areaGrid.MANDATORY_INTEGRITY_CATEGORIES.find(c => c.id === exp.id);
                expect(matchArea).toBeDefined();
                expect(matchArea.key).toBe(exp.key);
                expect(matchArea.prefix).toBe(exp.prefix);

                const matchProfile = houseProfile.MANDATORY_INTEGRITY_CATEGORIES.find(c => c.id === exp.id);
                expect(matchProfile).toBeDefined();
                expect(matchProfile.key).toBe(exp.key);
                expect(matchProfile.prefix).toBe(exp.prefix);
            });
        });
    });

    describe('2. Area Grid Integrity Computation (computeHouseIntegrity)', () => {
        it('identifies complete occupied house when all 5 categories exist (clean names)', () => {
            const house = {
                id: '101',
                name: '101',
                current_tenant: 'Ahmad Al-Mansoor',
                category_counts: {
                    'بيانات شخصية': 2,
                    'أمر تخصيص': 1,
                    'محضر تسليم مفتاح': 1,
                    'عقود': 4,
                    'استقطاع إيجار': 12,
                    'فواتير': 3
                }
            };

            const integrity = areaGrid.computeHouseIntegrity(house);
            expect(integrity.isOccupied).toBe(true);
            expect(integrity.isVacant).toBe(false);
            expect(integrity.presentCount).toBe(5);
            expect(integrity.missingCount).toBe(0);
            expect(integrity.isComplete).toBe(true);
            expect(integrity.status).toBe('complete');
            expect(integrity.label).toBe('5/5');
            expect(integrity.missingCategories).toEqual([]);
        });

        it('identifies complete occupied house when categories have numeric prefixes', () => {
            const house = {
                id: '102',
                name: '102',
                current_tenant: 'Khalid',
                category_counts: {
                    '02 - بيانات شخصية': 1,
                    '03 - أمر تخصيص': 1,
                    '04 - محضر تسليم مفتاح': 1,
                    '05 - عقود': 2,
                    '07 - استقطاع إيجار': 5
                }
            };

            const integrity = areaGrid.computeHouseIntegrity(house);
            expect(integrity.isComplete).toBe(true);
            expect(integrity.presentCount).toBe(5);
            expect(integrity.missingCount).toBe(0);
            expect(integrity.status).toBe('complete');
        });

        it('identifies incomplete occupied house and lists exactly which categories are missing', () => {
            const house = {
                id: '103',
                name: '103',
                current_tenant: 'Saeed',
                category_counts: {
                    'بيانات شخصية': 1,
                    'أمر تخصيص': 1,
                    'محضر تسليم مفتاح': 1
                    // 'عقود' and 'استقطاع إيجار' are missing!
                }
            };

            const integrity = areaGrid.computeHouseIntegrity(house);
            expect(integrity.isOccupied).toBe(true);
            expect(integrity.isVacant).toBe(false);
            expect(integrity.presentCount).toBe(3);
            expect(integrity.missingCount).toBe(2);
            expect(integrity.isComplete).toBe(false);
            expect(integrity.status).toBe('incomplete');
            expect(integrity.label).toBe('3/5');
            expect(integrity.missingCategories).toHaveLength(2);
            expect(integrity.missingCategories.map(c => c.id)).toEqual(['05', '07']);
        });

        it('handles occupied house with 0 mandatory categories present', () => {
            const house = {
                id: '104',
                name: '104',
                current_tenant: 'New Tenant',
                category_counts: {
                    'رسائل متنوعة': 1
                }
            };

            const integrity = areaGrid.computeHouseIntegrity(house);
            expect(integrity.presentCount).toBe(0);
            expect(integrity.missingCount).toBe(5);
            expect(integrity.isComplete).toBe(false);
            expect(integrity.status).toBe('incomplete');
            expect(integrity.label).toBe('0/5');
            expect(integrity.missingCategories).toHaveLength(5);
        });

        it('classifies vacant house with no current tenant and no resident children', () => {
            const vacantHouse = {
                id: '105',
                name: '105',
                current_tenant: null,
                children: []
            };

            const integrity = areaGrid.computeHouseIntegrity(vacantHouse);
            expect(integrity.isOccupied).toBe(false);
            expect(integrity.isVacant).toBe(true);
            expect(integrity.presentCount).toBe(0);
            expect(integrity.missingCount).toBe(0);
            expect(integrity.isComplete).toBe(false);
            expect(integrity.status).toBe('vacant');
            expect(integrity.label).toBe('Vacant');
            expect(integrity.missingCategories).toEqual([]);
        });

        it('treats house with applicant children only as vacant', () => {
            const applicantHouse = {
                id: '106',
                name: '106',
                current_tenant: null,
                children: [
                    { type: 'tenant', is_resident: 0, name: 'Applicant One' }
                ]
            };

            const integrity = areaGrid.computeHouseIntegrity(applicantHouse);
            expect(integrity.isVacant).toBe(true);
            expect(integrity.isOccupied).toBe(false);
            expect(integrity.status).toBe('vacant');
        });
    });

    describe('3. Compliance Sorting Logic', () => {
        const hComplete = {
            id: 'H-55',
            name: '55',
            current_tenant: 'Complete Tenant',
            category_counts: { 'بيانات شخصية': 1, 'أمر تخصيص': 1, 'محضر تسليم مفتاح': 1, 'عقود': 1, 'استقطاع إيجار': 1 }
        };
        const hIncomplete3 = {
            id: 'H-33',
            name: '33',
            current_tenant: 'Tenant 3',
            category_counts: { 'بيانات شخصية': 1, 'أمر تخصيص': 1, 'محضر تسليم مفتاح': 1 }
        };
        const hIncomplete1 = {
            id: 'H-11',
            name: '11',
            current_tenant: 'Tenant 1',
            category_counts: { 'بيانات شخصية': 1 }
        };
        const hVacant = {
            id: 'H-99',
            name: '99',
            current_tenant: null,
            children: []
        };

        it('compareHouseIntegrityWorst sorts incomplete occupied houses (worst first) -> complete -> vacant', () => {
            const list = [hComplete, hVacant, hIncomplete3, hIncomplete1];
            list.sort(areaGrid.compareHouseIntegrityWorst);

            // Worst first: H-11 (1/5) -> H-33 (3/5) -> H-55 (5/5 complete) -> H-99 (vacant)
            expect(list.map(h => h.id)).toEqual(['H-11', 'H-33', 'H-55', 'H-99']);
        });

        it('compareHouseIntegrityBest sorts complete occupied houses first -> incomplete (best first) -> vacant', () => {
            const list = [hIncomplete1, hVacant, hComplete, hIncomplete3];
            list.sort(areaGrid.compareHouseIntegrityBest);

            // Best first: H-55 (5/5 complete) -> H-33 (3/5) -> H-11 (1/5) -> H-99 (vacant)
            expect(list.map(h => h.id)).toEqual(['H-55', 'H-33', 'H-11', 'H-99']);
        });

        it('uses natural house number as tie-breaker when integrity scores are equal', () => {
            const hA = {
                id: 'H-2',
                name: '2',
                current_tenant: 'Tenant A',
                category_counts: { 'بيانات شخصية': 1 }
            };
            const hB = {
                id: 'H-10',
                name: '10',
                current_tenant: 'Tenant B',
                category_counts: { 'بيانات شخصية': 1 }
            };

            const list = [hB, hA];
            list.sort(areaGrid.compareHouseIntegrityWorst);
            expect(list.map(h => h.id)).toEqual(['H-2', 'H-10']);
        });
    });

    describe('4. Area Grid UI, Filter Toolbar & House Card Badges (Idea B)', () => {
        const testAreaNode = {
            name: 'Safra Area',
            children: [
                {
                    id: '10',
                    name: '10',
                    current_tenant: 'Tenant 10',
                    category_counts: { 'بيانات شخصية': 1, 'أمر تخصيص': 1, 'محضر تسليم مفتاح': 1, 'عقود': 1, 'استقطاع إيجار': 1 },
                    children: [{ type: 'tenant', is_resident: 1, name: 'Tenant 10' }]
                },
                {
                    id: '20',
                    name: '20',
                    current_tenant: 'Tenant 20',
                    category_counts: { 'بيانات شخصية': 1, 'أمر تخصيص': 1 },
                    children: [{ type: 'tenant', is_resident: 1, name: 'Tenant 20' }]
                },
                {
                    id: '30',
                    name: '30',
                    current_tenant: null,
                    children: []
                }
            ]
        };

        it('renders integrity filter toolbar with accurate live counts', () => {
            areaGrid.renderAreaGrid(testAreaNode);

            const toolbar = document.getElementById('grid-integrity-toolbar');
            expect(toolbar).not.toBeNull();
            expect(toolbar.classList.contains('hidden')).toBe(false);

            const pills = document.querySelectorAll('.grid-filter-pill');
            expect(pills.length).toBe(4);

            const allPill = document.querySelector('.grid-filter-pill[data-filter="all"]');
            const incompletePill = document.querySelector('.grid-filter-pill[data-filter="incomplete"]');
            const completePill = document.querySelector('.grid-filter-pill[data-filter="complete"]');
            const vacantPill = document.querySelector('.grid-filter-pill[data-filter="vacant"]');

            expect(allPill.textContent).toContain('3');
            expect(incompletePill.textContent).toContain('1');
            expect(completePill.textContent).toContain('1');
            expect(vacantPill.textContent).toContain('1');
        });

        it('filters grid to show only incomplete houses when incomplete pill is clicked', () => {
            areaGrid.renderAreaGrid(testAreaNode);

            const incompletePill = document.querySelector('.grid-filter-pill[data-filter="incomplete"]');
            incompletePill.click();

            expect(areaGrid.getIntegrityFilter()).toBe('incomplete');

            const container = document.getElementById('area-grid-container');
            const renderedCards = Array.from(container.querySelectorAll('.house-card'));
            expect(renderedCards.map(c => c.dataset.houseId)).toEqual(['20']);

            // Add house card remains present
            expect(document.getElementById('add-house-grid-card')).not.toBeNull();
        });

        it('filters grid to show only complete houses when complete pill is clicked', () => {
            areaGrid.renderAreaGrid(testAreaNode);

            const completePill = document.querySelector('.grid-filter-pill[data-filter="complete"]');
            completePill.click();

            expect(areaGrid.getIntegrityFilter()).toBe('complete');

            const container = document.getElementById('area-grid-container');
            const renderedCards = Array.from(container.querySelectorAll('.house-card'));
            expect(renderedCards.map(c => c.dataset.houseId)).toEqual(['10']);
        });

        it('filters grid to show only vacant houses when vacant pill is clicked', () => {
            areaGrid.renderAreaGrid(testAreaNode);

            const vacantPill = document.querySelector('.grid-filter-pill[data-filter="vacant"]');
            vacantPill.click();

            expect(areaGrid.getIntegrityFilter()).toBe('vacant');

            const container = document.getElementById('area-grid-container');
            const renderedCards = Array.from(container.querySelectorAll('.house-card'));
            expect(renderedCards.map(c => c.dataset.houseId)).toEqual(['30']);
        });

        it('renders empty celebratory notice and preserves add-house-grid-card when incomplete filter has no matches', () => {
            const allCompleteArea = {
                name: 'All Complete',
                children: [
                    {
                        id: '1',
                        name: '1',
                        current_tenant: 'T1',
                        category_counts: { 'بيانات شخصية': 1, 'أمر تخصيص': 1, 'محضر تسليم مفتاح': 1, 'عقود': 1, 'استقطاع إيجار': 1 },
                        children: [{ type: 'tenant', is_resident: 1, name: 'T1' }]
                    }
                ]
            };

            areaGrid.renderAreaGrid(allCompleteArea);
            const incompletePill = document.querySelector('.grid-filter-pill[data-filter="incomplete"]');
            incompletePill.click();

            const container = document.getElementById('area-grid-container');
            expect(container.textContent).toContain('All Houses Compliant!');
            expect(container.textContent).toContain('Every occupied house in this area has all 5 mandatory documents in place.');
            expect(document.getElementById('add-house-grid-card')).not.toBeNull();

            // Clicking reset button restores 'all' filter
            const resetBtn = container.querySelector('.btn-reset-grid-filter');
            expect(resetBtn).not.toBeNull();
            resetBtn.click();
            expect(areaGrid.getIntegrityFilter()).toBe('all');
        });

        it('renders house card integrity badges and missing documents strip on cards', () => {
            areaGrid.renderAreaGrid(testAreaNode);

            const container = document.getElementById('area-grid-container');

            // Complete card (10): has emerald badge with ✓ 5/5
            const card10 = container.querySelector('[data-house-id="10"]');
            const badge10 = card10.querySelector('.integrity-badge');
            expect(badge10).not.toBeNull();
            expect(badge10.textContent).toContain('5/5');
            expect(badge10.classList.contains('bg-emerald-50')).toBe(true);
            expect(card10.querySelector('.missing-docs-strip')).toBeNull();

            // Incomplete card (20): has amber badge with ⚠️ 2/5 and missing docs strip
            const card20 = container.querySelector('[data-house-id="20"]');
            const badge20 = card20.querySelector('.integrity-badge');
            expect(badge20).not.toBeNull();
            expect(badge20.textContent).toContain('2/5');
            expect(badge20.classList.contains('bg-amber-50')).toBe(true);

            const missingStrip = card20.querySelector('.missing-docs-strip');
            expect(missingStrip).not.toBeNull();
            expect(missingStrip.textContent).toContain('ناقص:');
            expect(missingStrip.textContent).toContain('محضر تسليم مفتاح');
            expect(missingStrip.textContent).toContain('عقود');
            expect(missingStrip.textContent).toContain('استقطاع إيجار');

            // Warning is anchored in the fixed card-bottom-zone right above card footer, NOT under tenant list
            expect(card20.querySelector('.card-warning-divider')).not.toBeNull();
            expect(card20.querySelector('.card-footer .missing-docs-strip')).toBeNull();
            expect(card20.querySelector('.card-bottom-zone .missing-docs-strip')).not.toBeNull();
            expect(card20.querySelector('.card-main-content .missing-docs-strip')).toBeNull();
            expect(card20.querySelector('.tenants-overview-section .missing-docs-strip')).toBeNull();

            // Vacant card (30): has neutral badge with شاغر and no strip
            const card30 = container.querySelector('[data-house-id="30"]');
            const badge30 = card30.querySelector('.integrity-badge');
            expect(badge30).not.toBeNull();
            expect(badge30.textContent).toContain('شاغر');
            expect(card30.querySelector('.missing-docs-strip')).toBeNull();
        });

        it('sorts grid when compliance sort options are selected from header dropdown', () => {
            areaGrid.renderAreaGrid(testAreaNode);

            const sortSelect = document.getElementById('grid-house-sort-select');

            // Select "integrity_worst"
            sortSelect.value = 'integrity_worst';
            sortSelect.dispatchEvent(new Event('change'));

            expect(localStorage.getItem('house_sort_by')).toBe('integrity_worst');

            let container = document.getElementById('area-grid-container');
            let cards = Array.from(container.querySelectorAll('.house-card'));
            // Incomplete house 20 first, then complete 10, then vacant 30
            expect(cards.map(c => c.dataset.houseId)).toEqual(['20', '10', '30']);

            // Select "integrity_best"
            sortSelect.value = 'integrity_best';
            sortSelect.dispatchEvent(new Event('change'));

            expect(localStorage.getItem('house_sort_by')).toBe('integrity_best');

            cards = Array.from(container.querySelectorAll('.house-card'));
            // Complete house 10 first, then incomplete 20, then vacant 30
            expect(cards.map(c => c.dataset.houseId)).toEqual(['10', '20', '30']);
        });
    });

    describe('5. House Profile Compliance Checklist Computation (computeTenantCompliance)', () => {
        it('calculates compliance accurately strictly from activeTenant without leaking past tenant archive counts (House 500 scenario)', () => {
            // House 500: Active tenant Fawaz has 1 contract. Past tenant Abdullah had 2 contracts.
            // Archive has 3 contracts total. The compliance checklist must show 1 contract, NOT 3!
            const mockHouse500Profile = {
                area_id: 'Safra',
                house_id: '500',
                tenants: [
                    {
                        name: 'فواز خليل الطارش',
                        is_active: true,
                        is_resident: 1,
                        categories: ['02 - بيانات شخصية', '03 - أمر تخصيص', '04 - محضر تسليم مفتاح', '05 - عقود'],
                        category_counts: {
                            'بيانات شخصية': 1,
                            'أمر تخصيص': 1,
                            'محضر تسليم مفتاح': 1,
                            'عقود': 1 // Exactly 1 contract for active resident
                        }
                    },
                    {
                        name: 'عبد الله حميدة رضا فرج',
                        is_active: false,
                        is_resident: 1,
                        categories: ['عقود', '07 - استقطاع إيجار'],
                        category_counts: {
                            'عقود': 2,
                            'استقطاع إيجار': 4
                        }
                    }
                ],
                archive: {
                    categories: [
                        { category: '02 - بيانات شخصية', document_count: 1 },
                        { category: '03 - أمر تخصيص', document_count: 1 },
                        { category: '04 - محضر تسليم مفتاح', document_count: 1 },
                        { category: '05 - عقود', document_count: 3 }, // 1 (Fawaz) + 2 (Abdullah) = 3
                        { category: '07 - استقطاع إيجار', document_count: 4 } // Only Abdullah had it
                    ]
                }
            };

            const tenant = mockHouse500Profile.tenants[0];
            const comp = houseProfile.computeTenantCompliance(mockHouse500Profile, tenant);

            expect(comp.isOccupied).toBe(true);
            expect(comp.isVacant).toBe(false);
            expect(comp.totalRequired).toBe(5);
            expect(comp.presentCount).toBe(4); // 02, 03, 04, 05
            expect(comp.missingCount).toBe(1); // 07 is missing for Fawaz (even though Abdullah had 4 in archive!)
            expect(comp.isComplete).toBe(false);

            expect(comp.missingCategories).toHaveLength(1);
            expect(comp.missingCategories[0].id).toBe('07');

            // Crucial House 500 assertion: Fawaz has 1 contract, NOT 3!
            const item05 = comp.items.find(i => i.id === '05');
            expect(item05.exists).toBe(true);
            expect(item05.documentCount).toBe(1);

            // Rent deduction: past tenant had it in archive, but Fawaz doesn't have it
            const item07 = comp.items.find(i => i.id === '07');
            expect(item07.exists).toBe(false);
            expect(item07.documentCount).toBe(0);
        });

        it('returns vacant structure when no active resident tenant is provided', () => {
            const comp = houseProfile.computeTenantCompliance({ area_id: 'Safra', house_id: '102' }, null);
            expect(comp.isVacant).toBe(true);
            expect(comp.isOccupied).toBe(false);
            expect(comp.presentCount).toBe(0);
            expect(comp.missingCount).toBe(0);
            expect(comp.isComplete).toBe(false);
        });
    });

    describe('6. House Profile Compliance Checklist UI & Ingestion Trigger (Idea C)', () => {
        it('renders vacant message banner when house has no active resident tenant', () => {
            const vacantProfile = {
                area_id: 'Safra',
                house_id: '103',
                tenants: [],
                archive: { categories: [] }
            };

            houseProfile.renderHouseProfile(vacantProfile);

            const checklistCard = document.querySelector('.tenant-compliance-card');
            expect(checklistCard).not.toBeNull();
            expect(checklistCard.textContent).toContain('المنزل شاغر حالياً');
            expect(checklistCard.textContent).toContain('شاغر');
        });

        it('renders interactive compliance checklist with green checkmarks and upload buttons for missing docs', () => {
            const mockProfile = {
                area_id: 'Safra',
                house_id: '101',
                tenants: [
                    {
                        name: 'Ali Hassan',
                        is_active: true,
                        is_resident: 1,
                        categories: ['02 - بيانات شخصية', '03 - أمر تخصيص', '04 - محضر تسليم مفتاح']
                    }
                ],
                archive: {
                    categories: []
                }
            };

            houseProfile.renderHouseProfile(mockProfile);

            const card = document.querySelector('.tenant-compliance-card');
            expect(card).not.toBeNull();
            expect(card.textContent).toContain('فحص اكتمال ملف الساكن');
            expect(card.textContent).toContain('Ali Hassan');
            expect(card.textContent).toContain('3/5 ناقص ⚠️');

            // Open by default: compliance body is visible and not hidden
            const bodyContainer = card.querySelector('.compliance-body-container');
            expect(bodyContainer).not.toBeNull();
            expect(bodyContainer.classList.contains('hidden')).toBe(false);

            // Divider cleanly separates compliance card from the residents section
            const divider = document.querySelector('.tenant-section-divider');
            expect(divider).not.toBeNull();
            expect(card.nextElementSibling).toBe(divider);

            // 3 present items, 2 missing items
            const presentItems = card.querySelectorAll('.compliance-item[data-category-prefix]');
            expect(presentItems.length).toBe(3);

            const uploadButtons = card.querySelectorAll('.btn-compliance-upload');
            expect(uploadButtons.length).toBe(2);

            const catPrefixes = Array.from(uploadButtons).map(b => b.dataset.catPrefix);
            expect(catPrefixes).toEqual(['05 - عقود', '07 - استقطاع إيجار']);

            // Button has clean single SVG plus icon and text 'رفع' without duplicate text '+'
            uploadButtons.forEach(btn => {
                expect(btn.textContent.trim()).toBe('رفع');
                expect(btn.querySelector('svg')).not.toBeNull();
            });
        });

        it('clicking upload button invokes openIngestStationWithPreset with exact parameters', () => {
            const mockProfile = {
                area_id: 'Safra',
                house_id: '101',
                tenants: [
                    {
                        name: 'Ali Hassan',
                        is_active: true,
                        is_resident: 1,
                        categories: ['02 - بيانات شخصية']
                    }
                ],
                archive: { categories: [] }
            };

            window.openIngestStationWithPreset = vi.fn();

            houseProfile.renderHouseProfile(mockProfile);

            const uploadBtn = document.querySelector('.btn-compliance-upload[data-cat-prefix="05 - عقود"]');
            expect(uploadBtn).not.toBeNull();

            uploadBtn.click();

            expect(window.openIngestStationWithPreset).toHaveBeenCalledWith({
                area: 'Safra',
                house: '101',
                tenant: 'Ali Hassan',
                category: '05 - عقود'
            });
        });

        it('clicking a present category item navigates to the tenant folder URL hash', () => {
            const mockProfile = {
                area_id: 'Safra',
                house_id: '101',
                tenants: [
                    {
                        name: 'Ali Hassan',
                        is_active: true,
                        is_resident: 1,
                        categories: ['02 - بيانات شخصية']
                    }
                ],
                archive: { categories: [] }
            };

            houseProfile.renderHouseProfile(mockProfile);

            const presentItem = document.querySelector('.compliance-item[data-category-prefix="02 - بيانات شخصية"]');
            expect(presentItem).not.toBeNull();

            presentItem.click();

            expect(window.location.hash).toContain('/area/Safra/house/101/tenant/101_Ali%20Hassan');
        });

        it('renders 5/5 complete badge and emerald styling when all documents are present', () => {
            const completeProfile = {
                area_id: 'Safra',
                house_id: '105',
                tenants: [
                    {
                        name: 'Mariam',
                        is_active: true,
                        is_resident: 1,
                        categories: ['02 - بيانات شخصية', '03 - أمر تخصيص', '04 - محضر تسليم مفتاح', '05 - عقود', '07 - استقطاع إيجار']
                    }
                ],
                archive: { categories: [] }
            };

            houseProfile.renderHouseProfile(completeProfile);

            const card = document.querySelector('.tenant-compliance-card');
            expect(card.textContent).toContain('مكتمل 5/5 ✓');
            expect(card.querySelectorAll('.btn-compliance-upload').length).toBe(0);
            expect(card.querySelectorAll('.compliance-item[data-category-prefix]').length).toBe(5);
        });
    });

    describe('7. Ingest Station Preset Integration', () => {
        it('pre-fills Area, House, Tenant, and matches Category dropdown when opened with preset', () => {
            window.globalTreeData = [
                {
                    name: 'Safra',
                    children: [
                        { name: '101' }
                    ]
                }
            ];

            ingestStation.initIngestStation();

            const preset = {
                area: 'Safra',
                house: '101',
                tenant: 'Ahmad Al-Mansoor',
                category: '07 - استقطاع إيجار'
            };

            ingestStation.openIngestStationWithPreset(preset);

            const modal = document.getElementById('ingest-station-modal');
            expect(modal.classList.contains('hidden')).toBe(false);

            const areaSelect = document.getElementById('ingest-area-select');
            const houseSelect = document.getElementById('ingest-house-select');
            const catSelect = document.getElementById('ingest-category-select');

            expect(areaSelect.value).toBe('Safra');
            expect(houseSelect.value).toBe('101');
            expect(catSelect.value).toBe('07 - استقطاع إيجار');
        });
    });
});

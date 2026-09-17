import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

const {
    openChangeDocDateModal,
    closeChangeDocDateModal,
    saveChangeDocDate,
} = require('../../../src/HousingApplication.Web/wwwroot/js/doc-manager.js');

const {
    renderTimeline,
    reorderTimelineCard,
    loadTimeline,
} = require('../../../src/HousingApplication.Web/wwwroot/js/timeline-view.js');

describe('Timeline View Document Date Change & Tab Preservation', () => {
    let mockDocs;

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="tab-timeline" class="flex-1 min-w-0 py-1.5 px-2.5 text-xs font-semibold rounded-md bg-white text-blue-600 shadow-xs flex items-center justify-center gap-1.5">Timeline</div>
            <div id="tab-categories" class="flex-1 min-w-0 py-1.5 px-2.5 text-xs font-medium rounded-md text-slate-600 flex items-center justify-center gap-1.5">Folders</div>
            <span id="tab-categories-label">Folders</span>
            <span id="tab-timeline-label">Timeline</span>
            <div id="current-house-title"></div>
            <div id="document-list-panel">
                <div id="document-list"></div>
            </div>
            <div id="stats-badge" class="hidden"></div>
            <div id="area-grid-panel" class="hidden"></div>
            <div id="welcome-panel" class="hidden"></div>
            <div id="document-viewer-panel" class="hidden"></div>
            <div id="resizer-2" class="hidden"></div>
        `;

        mockDocs = [
            {
                vault_id: 'doc_1',
                brief_arabic_title: 'Document 1',
                dates: ['2025-01-01'],
                primary_date: '2025-01-01',
                category: '01 - الهوية',
                primary_tenant: 'Tenant A',
                area_id: 'Area 1',
                house_id: '10'
            },
            {
                vault_id: 'doc_2',
                brief_arabic_title: 'Document 2',
                dates: ['2023-01-01'],
                primary_date: '2023-01-01',
                category: '02 - عقود',
                primary_tenant: 'Tenant A',
                area_id: 'Area 1',
                house_id: '10'
            },
            {
                vault_id: 'doc_3',
                brief_arabic_title: 'Document 3',
                dates: ['2021-01-01'],
                primary_date: '2021-01-01',
                category: '03 - فواتير',
                primary_tenant: 'Tenant A',
                area_id: 'Area 1',
                house_id: '10'
            }
        ];

        global.currentArea = 'Area 1';
        global.currentHouse = '10';
        global.currentTenant = 'Tenant A';
        global.currentTab = 'timeline';
        window.currentArea = 'Area 1';
        window.currentHouse = '10';
        window.currentTenant = 'Tenant A';
        window.currentTab = 'timeline';
        window.currentTimeline = [...mockDocs];

        global.isStaticMode = false;
        window.isStaticMode = false;
        global.showToast = vi.fn();
        window.showToast = global.showToast;
        global.loadTree = vi.fn();
        window.loadTree = global.loadTree;

        global.fetch = vi.fn().mockImplementation(async (url) => ({
            ok: true,
            json: async () => (String(url).includes('/timeline') ? mockDocs : { success: true })
        }));

        const routerCode = fs.readFileSync(
            path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/router.js'),
            'utf8'
        );
        eval(routerCode);
        vi.spyOn(window, 'refreshCurrentTab');
    });

    afterEach(() => {
        document.body.innerHTML = '';
        vi.restoreAllMocks();
    });

    it('renders timeline cards with data-date and correct chronological order', () => {
        renderTimeline(mockDocs);

        const docListEl = document.getElementById('document-list');
        const cards = docListEl.querySelectorAll('div[data-vault-id]');
        expect(cards.length).toBe(3);

        expect(cards[0].getAttribute('data-vault-id')).toBe('doc_1');
        expect(cards[0].getAttribute('data-date')).toBe('2025-01-01');

        expect(cards[1].getAttribute('data-vault-id')).toBe('doc_2');
        expect(cards[1].getAttribute('data-date')).toBe('2023-01-01');

        expect(cards[2].getAttribute('data-vault-id')).toBe('doc_3');
        expect(cards[2].getAttribute('data-date')).toBe('2021-01-01');
    });

    it('reorders card to top when date is moved to future date', () => {
        renderTimeline(mockDocs);

        // Move doc_2 from 2023 to 2026 (newer than doc_1 2025)
        reorderTimelineCard('doc_2', '2026-06-01');

        const docListEl = document.getElementById('document-list');
        const cards = docListEl.querySelectorAll('div[data-vault-id]');
        expect(cards[0].getAttribute('data-vault-id')).toBe('doc_2');
        expect(cards[0].getAttribute('data-date')).toBe('2026-06-01');
        expect(cards[0].querySelector('.font-mono span').textContent).toBe('2026-06-01');

        expect(cards[1].getAttribute('data-vault-id')).toBe('doc_1');
        expect(cards[2].getAttribute('data-vault-id')).toBe('doc_3');
    });

    it('reorders card to bottom when date is moved to oldest date', () => {
        renderTimeline(mockDocs);

        // Move doc_1 from 2025 to 2019 (older than doc_3 2021)
        reorderTimelineCard('doc_1', '2019-01-01');

        const docListEl = document.getElementById('document-list');
        const cards = docListEl.querySelectorAll('div[data-vault-id]');
        expect(cards[0].getAttribute('data-vault-id')).toBe('doc_2');
        expect(cards[1].getAttribute('data-vault-id')).toBe('doc_3');
        expect(cards[2].getAttribute('data-vault-id')).toBe('doc_1');
        expect(cards[2].getAttribute('data-date')).toBe('2019-01-01');
    });

    it('reorders card to middle position correctly', () => {
        renderTimeline(mockDocs);

        // Move doc_3 from 2021 to 2024 (between doc_1 2025 and doc_2 2023)
        reorderTimelineCard('doc_3', '2024-05-10');

        const docListEl = document.getElementById('document-list');
        const cards = docListEl.querySelectorAll('div[data-vault-id]');
        expect(cards[0].getAttribute('data-vault-id')).toBe('doc_1');
        expect(cards[1].getAttribute('data-vault-id')).toBe('doc_3');
        expect(cards[2].getAttribute('data-vault-id')).toBe('doc_2');
    });

    it('changing date via saveChangeDocDate while on timeline maintains currentTab as timeline and does NOT call loadTree', async () => {
        renderTimeline(mockDocs);
        expect(global.currentTab).toBe('timeline');

        const docToUpdate = mockDocs[1]; // doc_2
        openChangeDocDateModal(docToUpdate);

        const input = document.getElementById('change-doc-date-input');
        input.value = '2026-03-15';

        await saveChangeDocDate();

        // 1. Tab MUST stay as 'timeline'
        expect(global.currentTab).toBe('timeline');
        expect(window.currentTab).toBe('timeline');

        // 2. loadTree must NOT be called (would reload sidebar and clobber view)
        expect(global.loadTree).not.toHaveBeenCalled();

        // 3. refreshCurrentTab was called to sync with server
        expect(window.refreshCurrentTab).toHaveBeenCalledWith('Area 1', '10');

        // 4. Card in DOM is repositioned to the top
        const docListEl = document.getElementById('document-list');
        const cards = docListEl.querySelectorAll('div[data-vault-id]');
        expect(cards[0].getAttribute('data-vault-id')).toBe('doc_2');
        expect(cards[0].getAttribute('data-date')).toBe('2026-03-15');
    });

    it('handleHashChange preserves currentTab as timeline when context has not changed', () => {
        window.location.hash = '#/area/Area 1/house/10/tenant/10_Tenant A';
        global.currentArea = 'Area 1';
        global.currentHouse = '10';
        global.currentTenant = 'Tenant A';
        global.currentTab = 'timeline';

        window.handleHashChange();

        expect(global.currentTab).toBe('timeline');
        const tabTimeline = document.getElementById('tab-timeline');
        expect(tabTimeline.className).toContain('text-blue-600');
    });

    it('loadTimeline performs silent update when cards are already in DOM without clearing innerHTML', async () => {
        renderTimeline(mockDocs);

        const docListEl = document.getElementById('document-list');
        docListEl.scrollTop = 120;

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => [
                {
                    vault_id: 'doc_1',
                    brief_arabic_title: 'Document 1',
                    dates: ['2025-01-01'],
                    primary_tenant: 'Tenant A'
                }
            ]
        });

        await loadTimeline('Area 1', '10');

        // Inner HTML was not blanked to "Loading documents..."
        expect(docListEl.innerHTML).not.toContain('Loading documents...');
        expect(docListEl.scrollTop).toBe(120);
    });
});

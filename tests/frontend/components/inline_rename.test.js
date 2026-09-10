import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

const {
    renderCategories,
    handleInlineRename,
} = require('../../../src/api/static/js/categories-view.js');

const {
    renderTimeline,
    handleInlineRename: handleInlineRenameTimeline,
} = require('../../../src/api/static/js/timeline-view.js');

function setupDOM() {
    document.body.innerHTML = `
        <div id="stats-badge" class="hidden"></div>
        <div id="document-list"></div>
    `;
}

describe('Double-Click Inline Document Renaming (QCK-05)', () => {
    beforeEach(() => {
        setupDOM();
        global.currentArea = 'Safra C';
        global.currentHouse = '500';
        global.currentCategories = [
            {
                tenant: 'فاطمة أحمد',
                name: '05 - عقود',
                document_count: 1,
                documents: [
                    {
                        vault_id: 'doc001',
                        brief_arabic_title: 'عقد إيجار شقة',
                        filename: 'contract.pdf',
                        is_manual: 0,
                        notes: ''
                    }
                ]
            }
        ];
        global.currentTimeline = [
            {
                vault_id: 'doc_time_1',
                brief_arabic_title: 'إشعار صيانة قديم',
                filename: 'maintenance.pdf',
                dates: ['2026-05-01'],
                primary_tenant: 'علي حسن',
                category: '10 - صيانة',
                is_manual: 0,
                notes: ''
            }
        ];
        global.currentTenant = null;
        global.showToast = vi.fn();
        global.openDocument = vi.fn();
        global.setSelectedDoc = vi.fn();
        global.fetch = vi.fn().mockImplementation(async () => ({
            ok: true,
            json: async () => ({ status: 'success' })
        }));
    });

    afterEach(() => {
        vi.restoreAllMocks();
        delete global.currentArea;
        delete global.currentHouse;
        delete global.currentCategories;
        delete global.currentTimeline;
        delete global.currentTenant;
        delete global.showToast;
        delete global.openDocument;
        delete global.setSelectedDoc;
        delete global.fetch;
    });

    it('transforms document title into an input element pre-filled with original title on double-click in Categories view', () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const titleSpan = docList.querySelector('.doc-title-text');
        expect(titleSpan).not.toBeNull();
        expect(titleSpan.textContent).toBe('عقد إيجار شقة');
        expect(titleSpan.title).toBe('Double-click to rename');

        titleSpan.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true }));

        const input = titleSpan.querySelector('.inline-rename-input');
        expect(input).not.toBeNull();
        expect(input.value).toBe('عقد إيجار شقة');
        expect(input.classList.contains('inline-rename-input')).toBe(true);
    });

    it('commits rename on Enter key, calls PATCH endpoint, updates in-memory doc, updates DOM, and shows success toast', async () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const titleSpan = docList.querySelector('.doc-title-text');

        titleSpan.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true }));
        const input = titleSpan.querySelector('.inline-rename-input');
        expect(input).not.toBeNull();

        input.value = 'عقد إيجار جديد 2026';
        input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));

        // Allow microtasks / async fetch to settle
        await new Promise(resolve => setTimeout(resolve, 10));

        expect(global.fetch).toHaveBeenCalledTimes(1);
        const [url, options] = global.fetch.mock.calls[0];
        expect(url).toBe('/api/areas/Safra%20C/houses/500/documents/doc001');
        expect(options.method).toBe('PATCH');
        expect(JSON.parse(options.body)).toEqual({ arabic_title: 'عقد إيجار جديد 2026' });

        // Verify in-memory document updated
        const targetDoc = global.currentCategories[0].documents[0];
        expect(targetDoc.brief_arabic_title).toBe('عقد إيجار جديد 2026');
        expect(targetDoc.filename).toBe('عقد إيجار جديد 2026');

        // Verify DOM updated
        expect(titleSpan.querySelector('.inline-rename-input')).toBeNull();
        expect(titleSpan.textContent).toBe('عقد إيجار جديد 2026');
        expect(titleSpan.title).toBe('Double-click to rename');

        // Verify toast
        expect(global.showToast).toHaveBeenCalledWith('Document renamed successfully.');
    });

    it('cancels rename and restores original title on Escape without triggering fetch', async () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const titleSpan = docList.querySelector('.doc-title-text');

        titleSpan.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true }));
        const input = titleSpan.querySelector('.inline-rename-input');
        expect(input).not.toBeNull();

        input.value = 'تعديل سيتم إلغاؤه';
        input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));

        await new Promise(resolve => setTimeout(resolve, 10));

        expect(global.fetch).not.toHaveBeenCalled();
        expect(titleSpan.querySelector('.inline-rename-input')).toBeNull();
        expect(titleSpan.textContent).toBe('عقد إيجار شقة');
        expect(global.currentCategories[0].documents[0].brief_arabic_title).toBe('عقد إيجار شقة');
    });

    it('commits when changed on blur and restores without fetch when unchanged', async () => {
        // Case 1: Unchanged on blur
        renderCategories();
        let docList = document.getElementById('document-list');
        let titleSpan = docList.querySelector('.doc-title-text');

        titleSpan.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true }));
        let input = titleSpan.querySelector('.inline-rename-input');
        expect(input).not.toBeNull();

        // blur with unchanged value
        input.dispatchEvent(new FocusEvent('blur', { bubbles: true }));
        await new Promise(resolve => setTimeout(resolve, 10));

        expect(global.fetch).not.toHaveBeenCalled();
        expect(titleSpan.textContent).toBe('عقد إيجار شقة');

        // Case 2: Changed on blur
        titleSpan.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true }));
        input = titleSpan.querySelector('.inline-rename-input');
        expect(input).not.toBeNull();

        input.value = 'عقد معدل عند البلور';
        input.dispatchEvent(new FocusEvent('blur', { bubbles: true }));
        await new Promise(resolve => setTimeout(resolve, 10));

        expect(global.fetch).toHaveBeenCalledTimes(1);
        expect(JSON.parse(global.fetch.mock.calls[0][1].body)).toEqual({ arabic_title: 'عقد معدل عند البلور' });
        expect(titleSpan.textContent).toBe('عقد معدل عند البلور');
        expect(global.showToast).toHaveBeenCalledWith('Document renamed successfully.');
    });

    it('cancels and restores original without triggering fetch when submitting empty or whitespace title', async () => {
        renderCategories();
        const docList = document.getElementById('document-list');
        const titleSpan = docList.querySelector('.doc-title-text');

        titleSpan.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true }));
        const input = titleSpan.querySelector('.inline-rename-input');

        input.value = '   ';
        input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
        await new Promise(resolve => setTimeout(resolve, 10));

        expect(global.fetch).not.toHaveBeenCalled();
        expect(titleSpan.querySelector('.inline-rename-input')).toBeNull();
        expect(titleSpan.textContent).toBe('عقد إيجار شقة');
    });

    it('handles HTTP error gracefully by showing error toast and reverting to original title', async () => {
        global.fetch = vi.fn().mockImplementation(async () => ({
            ok: false,
            json: async () => ({ detail: 'Database error: locked' })
        }));

        renderCategories();
        const docList = document.getElementById('document-list');
        const titleSpan = docList.querySelector('.doc-title-text');

        titleSpan.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true }));
        const input = titleSpan.querySelector('.inline-rename-input');

        input.value = 'عنوان فاشل';
        input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
        await new Promise(resolve => setTimeout(resolve, 10));

        expect(global.fetch).toHaveBeenCalledTimes(1);
        expect(global.showToast).toHaveBeenCalledWith('Failed to rename document: Database error: locked', 'error');
        expect(titleSpan.textContent).toBe('عقد إيجار شقة');
        expect(global.currentCategories[0].documents[0].brief_arabic_title).toBe('عقد إيجار شقة');
    });

    it('double-clicking in Timeline View transforms title, isolates event propagation from card click, and commits on Enter', async () => {
        renderTimeline();
        const docList = document.getElementById('document-list');
        const titleH4 = docList.querySelector('.doc-title-text');
        expect(titleH4).not.toBeNull();
        expect(titleH4.textContent).toBe('إشعار صيانة قديم');

        // Double-click transforms <h4>
        titleH4.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true }));
        const input = titleH4.querySelector('.inline-rename-input');
        expect(input).not.toBeNull();
        expect(input.value).toBe('إشعار صيانة قديم');

        // Clicking inside input should stop propagation and NOT trigger card.onclick
        input.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
        expect(global.openDocument).not.toHaveBeenCalled();

        // Type new title and press Enter
        input.value = 'إشعار صيانة دورية 2026';
        input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
        await new Promise(resolve => setTimeout(resolve, 10));

        expect(global.fetch).toHaveBeenCalledTimes(1);
        const [url, options] = global.fetch.mock.calls[0];
        expect(url).toBe('/api/areas/Safra%20C/houses/500/documents/doc_time_1');
        expect(options.method).toBe('PATCH');
        expect(JSON.parse(options.body)).toEqual({ arabic_title: 'إشعار صيانة دورية 2026' });

        expect(titleH4.textContent).toBe('إشعار صيانة دورية 2026');
        expect(global.currentTimeline[0].brief_arabic_title).toBe('إشعار صيانة دورية 2026');
        expect(global.showToast).toHaveBeenCalledWith('Document renamed successfully.');

        // Verify openDocument was still not called during renaming
        expect(global.openDocument).not.toHaveBeenCalled();

        // Now clicking the card directly opens document with the new title
        const card = docList.querySelector('[data-vault-id="doc_time_1"]');
        card.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
        expect(global.openDocument).toHaveBeenCalledWith('doc_time_1', 'إشعار صيانة دورية 2026');
    });
});

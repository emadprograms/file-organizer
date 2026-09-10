import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

const {
    initDocManager,
    openDocModal,
    closeDocModal,
    handleDeleteDoc,
} = require('../../../src/api/static/js/doc-manager.js');

function setupDOM() {
    document.body.innerHTML = `
        <div id="doc-action-modal" class="hidden">
            <h3 id="doc-modal-title"></h3>
            <input id="doc-modal-arabic-title" type="text" />
            <select id="doc-modal-folder-select"></select>
            <div id="doc-custom-folder-container" class="hidden">
                <input id="doc-custom-folder-input" type="text" />
            </div>
            <select id="doc-modal-tenant-select"></select>
            <div id="doc-manual-banner" class="hidden"></div>
            <button id="btn-doc-reset-lock" type="button"></button>
            <div id="doc-modal-status" class="hidden"></div>
            <button id="btn-mode-move" type="button"></button>
            <button id="btn-mode-copy" type="button"></button>
            <button id="doc-modal-close" type="button"></button>
            <button id="doc-modal-cancel" type="button"></button>
            <button id="doc-modal-submit" type="button">
                <span id="doc-modal-submit-text">Apply</span>
            </button>
            <button id="btn-doc-delete" type="button">
                <span>Delete Document</span>
            </button>
        </div>
    `;
}

describe('Document Manager - Deletion Feature', () => {
    beforeEach(() => {
        setupDOM();
        global.currentArea = 'Safra C';
        global.currentHouse = '514';
        global.currentCategories = [];
        global.showToast = vi.fn();
        global.refreshCurrentTab = vi.fn();
        global.loadTree = vi.fn();
        window.confirm = vi.fn();
        global.fetch = vi.fn().mockImplementation(async (url, options) => {
            if (typeof url === 'string' && url.includes('/tenants')) {
                return {
                    ok: true,
                    json: async () => [{ id: 1, name: 'فاطمة أحمد', start_date: '2022-01-01' }]
                };
            }
            return {
                ok: true,
                json: async () => ({ status: 'success' })
            };
        });

        initDocManager();
    });

    afterEach(() => {
        vi.restoreAllMocks();
        delete global.currentArea;
        delete global.currentHouse;
        delete global.currentCategories;
        delete global.showToast;
        delete global.refreshCurrentTab;
        delete global.loadTree;
    });

    it('cancels deletion when user declines confirmation prompt', async () => {
        window.confirm.mockReturnValue(false);

        await openDocModal({
            vault_id: 'doc_123',
            brief_arabic_title: 'فاتورة تجريبية',
            category: '06 - كهرباء وماء',
        });

        const deleteBtn = document.getElementById('btn-doc-delete');
        deleteBtn.click();

        expect(window.confirm).toHaveBeenCalledTimes(1);
        // fetch should only have been called for tenants during openDocModal, never with DELETE method
        const deleteCalls = global.fetch.mock.calls.filter(call => call[1]?.method === 'DELETE');
        expect(deleteCalls.length).toBe(0);
        expect(document.getElementById('doc-action-modal').classList.contains('hidden')).toBe(false);
    });

    it('successfully deletes document on confirmation and refreshes UI', async () => {
        window.confirm.mockReturnValue(true);
        global.fetch.mockImplementation(async (url, options) => {
            if (typeof url === 'string' && url.includes('/tenants')) {
                return {
                    ok: true,
                    json: async () => [{ id: 1, name: 'فاطمة أحمد', start_date: '2022-01-01' }]
                };
            }
            if (options?.method === 'DELETE') {
                return {
                    ok: true,
                    json: async () => ({ status: 'success', message: 'Document doc_123 deleted' })
                };
            }
            return { ok: true, json: async () => ({}) };
        });

        await openDocModal({
            vault_id: 'doc_123',
            brief_arabic_title: 'فاتورة تجريبية',
            category: '06 - كهرباء وماء',
        });

        const deleteBtn = document.getElementById('btn-doc-delete');
        deleteBtn.click();

        await vi.waitFor(() => {
            expect(global.showToast).toHaveBeenCalledWith('Document deleted successfully.');
        });

        expect(window.confirm).toHaveBeenCalledTimes(1);
        expect(global.fetch).toHaveBeenCalledWith(
            '/api/areas/Safra%20C/houses/514/documents/doc_123',
            { method: 'DELETE' }
        );

        expect(document.getElementById('doc-action-modal').classList.contains('hidden')).toBe(true);
        expect(global.refreshCurrentTab).toHaveBeenCalledWith('Safra C', '514');
        expect(global.loadTree).toHaveBeenCalled();
    });

    it('displays error in status element when deletion fails', async () => {
        window.confirm.mockReturnValue(true);
        global.fetch.mockImplementation(async (url, options) => {
            if (typeof url === 'string' && url.includes('/tenants')) {
                return {
                    ok: true,
                    json: async () => [{ id: 1, name: 'فاطمة أحمد', start_date: '2022-01-01' }]
                };
            }
            if (options?.method === 'DELETE') {
                return {
                    ok: false,
                    json: async () => ({ detail: 'Failed to remove document file' })
                };
            }
            return { ok: true, json: async () => ({}) };
        });

        await openDocModal({
            vault_id: 'doc_123',
            brief_arabic_title: 'فاتورة تجريبية',
            category: '06 - كهرباء وماء',
        });

        const deleteBtn = document.getElementById('btn-doc-delete');
        deleteBtn.click();

        await vi.waitFor(() => {
            const statusEl = document.getElementById('doc-modal-status');
            expect(statusEl.textContent).toBe('Failed to remove document file');
        });

        const statusEl = document.getElementById('doc-modal-status');
        expect(statusEl.classList.contains('block')).toBe(true);
        expect(deleteBtn.disabled).toBe(false);
    });
});

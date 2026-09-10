import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

const {
    initDocManager,
    openDocModal,
    closeDocModal,
    handleDeleteDoc,
    getResolvedArea,
    getResolvedHouse,
    getAreaFromHash,
    getHouseFromHash,
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
        window.location.hash = '';
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
        delete window.currentArea;
        delete window.currentHouse;
        window.location.hash = '';
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

        const modal = document.getElementById('doc-action-modal');
        expect(modal.classList.contains('hidden')).toBe(true);
        expect(modal.style.display).toBe('none');
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

    it('sets style.display = "none" and adds hidden class on closeDocModal', async () => {
        await openDocModal({
            vault_id: 'doc_123',
            brief_arabic_title: 'فاتورة تجريبية',
            category: '06 - كهرباء وماء',
        });
        const modal = document.getElementById('doc-action-modal');
        expect(modal.classList.contains('hidden')).toBe(false);
        expect(modal.style.display).toBe('flex');

        closeDocModal();

        expect(modal.classList.contains('hidden')).toBe(true);
        expect(modal.classList.contains('flex')).toBe(false);
        expect(modal.style.display).toBe('none');
    });

    it('resolves area and house from window.currentArea and window.currentHouse when not on global and closes modal', async () => {
        delete global.currentArea;
        delete global.currentHouse;
        window.currentArea = 'Safra C';
        window.currentHouse = '514';

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
                    json: async () => ({ status: 'success', message: 'Document doc_999 deleted' })
                };
            }
            return { ok: true, json: async () => ({}) };
        });

        await openDocModal({
            vault_id: 'doc_999',
            brief_arabic_title: 'مستند بدون منطقة',
            category: '05 - عقود',
        });

        const modal = document.getElementById('doc-action-modal');
        expect(modal.classList.contains('hidden')).toBe(false);

        const deleteBtn = document.getElementById('btn-doc-delete');
        deleteBtn.click();

        await vi.waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                '/api/areas/Safra%20C/houses/514/documents/doc_999',
                { method: 'DELETE' }
            );
        });

        expect(modal.classList.contains('hidden')).toBe(true);
        expect(modal.style.display).toBe('none');
        expect(global.refreshCurrentTab).toHaveBeenCalledWith('Safra C', '514');
    });

    it('falls back to URL hash resolution when global and window properties are absent', async () => {
        delete global.currentArea;
        delete global.currentHouse;
        delete window.currentArea;
        delete window.currentHouse;
        window.location.hash = '#/area/Safra%20C/house/514';

        expect(getResolvedArea()).toBe('Safra C');
        expect(getResolvedHouse()).toBe('514');

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
                    json: async () => ({ status: 'success' })
                };
            }
            return { ok: true, json: async () => ({}) };
        });

        await openDocModal({
            vault_id: 'doc_hash_1',
            brief_arabic_title: 'مستند تجزئة الرابط',
            category: '01 - بيانات أساسية',
        });

        const modal = document.getElementById('doc-action-modal');
        const deleteBtn = document.getElementById('btn-doc-delete');
        deleteBtn.click();

        await vi.waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                '/api/areas/Safra%20C/houses/514/documents/doc_hash_1',
                { method: 'DELETE' }
            );
        });

        expect(modal.classList.contains('hidden')).toBe(true);
        expect(modal.style.display).toBe('none');
    });

    it('ensures modal remains closed even if refreshCurrentTab rejects with an error', async () => {
        window.confirm.mockReturnValue(true);
        global.refreshCurrentTab = vi.fn().mockRejectedValue(new Error('Network failure during tab refresh'));
        window.refreshCurrentTab = global.refreshCurrentTab;

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
                    json: async () => ({ status: 'success' })
                };
            }
            return { ok: true, json: async () => ({}) };
        });

        await openDocModal({
            vault_id: 'doc_error_refresh',
            brief_arabic_title: 'مستند خطأ التحديث',
            category: '06 - كهرباء وماء',
        });

        const modal = document.getElementById('doc-action-modal');
        const deleteBtn = document.getElementById('btn-doc-delete');
        deleteBtn.click();

        await vi.waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                '/api/areas/Safra%20C/houses/514/documents/doc_error_refresh',
                { method: 'DELETE' }
            );
        });

        // Modal must be closed despite refresh rejection
        expect(modal.classList.contains('hidden')).toBe(true);
        expect(modal.style.display).toBe('none');
        expect(global.refreshCurrentTab).toHaveBeenCalled();
    });
});

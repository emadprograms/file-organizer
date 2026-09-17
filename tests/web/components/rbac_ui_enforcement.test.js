import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('RBAC UI Enforcement & Zero-Delete Guards for Contributors (Phase 118)', () => {
    const htmlPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/index.html');
    const authJsPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/auth-manager.js');
    const docManagerPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-manager.js');
    const categoriesViewPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/categories-view.js');
    const tenantManagerPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/tenant-manager.js');
    const docPageEditorPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-page-editor.js');

    const htmlContent = fs.readFileSync(htmlPath, 'utf8');
    const authJsContent = fs.readFileSync(authJsPath, 'utf8');
    const docManagerContent = fs.readFileSync(docManagerPath, 'utf8');
    const categoriesViewContent = fs.readFileSync(categoriesViewPath, 'utf8');
    const tenantManagerContent = fs.readFileSync(tenantManagerPath, 'utf8');
    const docPageEditorContent = fs.readFileSync(docPageEditorPath, 'utf8');

    beforeEach(() => {
        document.body.innerHTML = htmlContent;
        window.showToast = vi.fn();
        window.confirm = vi.fn().mockReturnValue(true);

        // Load scripts in JSDOM
        new Function(authJsContent)();
        new Function(docManagerContent)();
        new Function(categoriesViewContent)();
        new Function(tenantManagerContent)();
        new Function(docPageEditorContent)();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('Admin Users (Full Access: Emad, Bubshait, Ehtezaz, Mustafa)', () => {
        beforeEach(() => {
            window.authManager.currentUser = {
                id: 1,
                username: 'Emad',
                displayName: 'Emad',
                role: 'Admin',
                canDelete: true
            };
        });

        it('displays Delete Document in 3-dots dropdown menu for Admins', () => {
            const triggerBtn = document.createElement('button');
            document.body.appendChild(triggerBtn);

            const doc = { vault_id: 'v-admin-1', brief_arabic_title: 'عقد إيجار' };
            window.openDocDropdownMenu(null, doc, '05 - عقود', triggerBtn);

            const menu = document.querySelector('.doc-dropdown-menu');
            expect(menu).not.toBeNull();

            const deleteItem = menu.querySelector('.doc-menu-item-delete');
            expect(deleteItem).not.toBeNull();
            expect(deleteItem.textContent).toContain('Delete Document');
        });

        it('shows Delete Document button in Document Action Modal for Admins', () => {
            const btnDocDelete = document.getElementById('btn-doc-delete');
            expect(btnDocDelete).not.toBeNull();

            const doc = { vault_id: 'v-admin-2', brief_arabic_title: 'فاتورة' };
            window.openDocModal(doc, 'move');

            expect(btnDocDelete.classList.contains('hidden')).toBe(false);
        });

        it('enables Delete Sources in Merge Modal for Admins', () => {
            const doc1 = { vault_id: 'v1', brief_arabic_title: 'Doc 1' };
            const doc2 = { vault_id: 'v2', brief_arabic_title: 'Doc 2' };

            window.openMergeModal([doc1, doc2]);

            const deleteSourcesCheckbox = document.getElementById('merge-delete-sources');
            expect(deleteSourcesCheckbox).not.toBeNull();
            expect(deleteSourcesCheckbox.disabled).toBe(false);
            expect(deleteSourcesCheckbox.checked).toBe(true);
        });

        it('shows Delete Selected button in Batch Action Bar for Admins', () => {
            const btnBatchDelete = document.getElementById('btn-batch-delete');
            expect(btnBatchDelete).not.toBeNull();

            // Simulate selecting 2 documents
            window.selectedDocIds = new Set(['v1', 'v2']);
            window.updateBatchActionBar();

            expect(btnBatchDelete.classList.contains('hidden')).toBe(false);
        });

        it('renders Delete Page button on page cards in Page Editor for Admins', () => {
            const doc = { vault_id: 'v-admin-3', page_count: 3 };
            window.openPageEditor(doc);

            // Check the toolbar delete selected button
            const btnEditorDeleteSelected = document.getElementById('btn-editor-delete-selected');
            expect(btnEditorDeleteSelected.classList.contains('hidden')).toBe(false);
        });

        it('displays Danger Zone / Delete House in House Settings Modal for Admins', () => {
            window.currentHouse = '101';
            window.currentArea = 'North';

            window.openTenantModal();

            const dangerZone = document.getElementById('house-settings-danger-zone');
            expect(dangerZone).not.toBeNull();
            expect(dangerZone.classList.contains('hidden')).toBe(false);
        });
    });

    describe('Contributor Users (Read & Upload Only: Nawaf, Naseem, Mulla, Mariam, Shaima, Mona)', () => {
        beforeEach(() => {
            window.authManager.currentUser = {
                id: 5,
                username: 'Nawaf',
                displayName: 'Nawaf',
                role: 'Contributor',
                canDelete: false
            };
        });

        it('hides Delete Document from 3-dots dropdown menu for Contributors', () => {
            const triggerBtn = document.createElement('button');
            document.body.appendChild(triggerBtn);

            const doc = { vault_id: 'v-contrib-1', brief_arabic_title: 'وثيقة فحص' };
            window.openDocDropdownMenu(null, doc, '03 - إثباتات شخصية', triggerBtn);

            const menu = document.querySelector('.doc-dropdown-menu');
            expect(menu).not.toBeNull();

            const deleteItem = menu.querySelector('.doc-menu-item-delete');
            expect(deleteItem).toBeNull(); // Must not exist in menu
        });

        it('hides Delete Document button in Document Action Modal for Contributors', () => {
            const btnDocDelete = document.getElementById('btn-doc-delete');
            expect(btnDocDelete).not.toBeNull();

            const doc = { vault_id: 'v-contrib-2', brief_arabic_title: 'فاتورة ماء' };
            window.openDocModal(doc, 'move');

            expect(btnDocDelete.classList.contains('hidden')).toBe(true);
        });

        it('unchecks and disables Delete Sources in Merge Modal for Contributors', () => {
            const doc1 = { vault_id: 'v10', brief_arabic_title: 'Doc 10' };
            const doc2 = { vault_id: 'v20', brief_arabic_title: 'Doc 20' };

            window.openMergeModal([doc1, doc2]);

            const deleteSourcesCheckbox = document.getElementById('merge-delete-sources');
            expect(deleteSourcesCheckbox).not.toBeNull();
            expect(deleteSourcesCheckbox.checked).toBe(false);
            expect(deleteSourcesCheckbox.disabled).toBe(true);
        });

        it('hides Delete Selected button in Batch Action Bar for Contributors', () => {
            const btnBatchDelete = document.getElementById('btn-batch-delete');
            expect(btnBatchDelete).not.toBeNull();

            window.selectedDocIds = new Set(['v10', 'v20']);
            window.updateBatchActionBar();

            expect(btnBatchDelete.classList.contains('hidden')).toBe(true);
        });

        it('hides Delete Selected Pages button in Document Page Editor for Contributors', () => {
            const doc = { vault_id: 'v-contrib-3', page_count: 2 };
            window.openPageEditor(doc);

            const btnEditorDeleteSelected = document.getElementById('btn-editor-delete-selected');
            expect(btnEditorDeleteSelected.classList.contains('hidden')).toBe(true);
        });

        it('hides Danger Zone / Delete House in House Settings Modal for Contributors', () => {
            window.currentHouse = '102';
            window.currentArea = 'South';

            window.openTenantModal();

            const dangerZone = document.getElementById('house-settings-danger-zone');
            expect(dangerZone).not.toBeNull();
            expect(dangerZone.classList.contains('hidden')).toBe(true);
        });

        it('blocks execution and displays toast notification if openDeleteHouseModal is called by Contributor', () => {
            window.currentHouse = '102';
            window.currentArea = 'South';

            window.openDeleteHouseModal();

            const deleteHouseModal = document.getElementById('delete-house-modal');
            expect(deleteHouseModal.classList.contains('hidden')).toBe(true);
            expect(window.showToast).toHaveBeenCalledWith(
                expect.stringContaining('عذراً: ليس لديك صلاحية حذف المنازل'),
                'error'
            );
        });
    });
});

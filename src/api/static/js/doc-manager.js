// ── Document Management & Drag-and-Drop Controller ────────────────────────
(function() {
    let draggedDoc = null;
    let activeDocModalDoc = null;
    let activeDocModalCategory = null;
    let activeDocModalMode = 'move'; // 'move' or 'copy'

    let docActionModal = null;
    let docModalTitle = null;
    let docModalArabicTitle = null;
    let docModalFolderSelect = null;
    let docCustomFolderContainer = null;
    let docCustomFolderInput = null;
    let docModalTenantSelect = null;
    let docManualBanner = null;
    let btnDocResetLock = null;
    let btnDocDelete = null;
    let docModalStatus = null;
    let docModalCancel = null;
    let docModalClose = null;
    let docModalSubmit = null;
    let docModalSubmitText = null;
    let btnModeMove = null;
    let btnModeCopy = null;

    const STANDARD_FOLDERS = [
        "01 - بيانات أساسية",
        "02 - بيانات شخصية",
        "03 - أمر تخصيص",
        "04 - محضر تسليم مفتاح",
        "05 - عقود",
        "06 - كهرباء وماء",
        "07 - استقطاع إيجار",
        "08 - وقف استقطاع بدل",
        "09 - إشعارات",
        "10 - صيانة",
        "11 - صور ومعاينات",
        "12 - تعديلات",
        "13 - رسائل متنوعة",
    ];

    function initDocManager() {
        docActionModal = document.getElementById('doc-action-modal');
        docModalTitle = document.getElementById('doc-modal-title');
        docModalArabicTitle = document.getElementById('doc-modal-arabic-title');
        docModalFolderSelect = document.getElementById('doc-modal-folder-select');
        docCustomFolderContainer = document.getElementById('doc-custom-folder-container');
        docCustomFolderInput = document.getElementById('doc-custom-folder-input');
        docModalTenantSelect = document.getElementById('doc-modal-tenant-select');
        docManualBanner = document.getElementById('doc-manual-banner');
        btnDocResetLock = document.getElementById('btn-doc-reset-lock');
        btnDocDelete = document.getElementById('btn-doc-delete');
        docModalStatus = document.getElementById('doc-modal-status');
        docModalCancel = document.getElementById('doc-modal-cancel');
        docModalClose = document.getElementById('doc-modal-close');
        docModalSubmit = document.getElementById('doc-modal-submit');
        docModalSubmitText = document.getElementById('doc-modal-submit-text');
        btnModeMove = document.getElementById('btn-mode-move');
        btnModeCopy = document.getElementById('btn-mode-copy');

        if (docModalClose) docModalClose.onclick = closeDocModal;
        if (docModalCancel) docModalCancel.onclick = closeDocModal;
        if (docModalSubmit) docModalSubmit.onclick = saveDocModal;
        if (btnDocResetLock) btnDocResetLock.onclick = resetDocLock;
        if (btnDocDelete) btnDocDelete.onclick = (e) => handleDeleteDoc(e);
        if (btnModeMove) btnModeMove.onclick = () => setDocModalMode('move');
        if (btnModeCopy) btnModeCopy.onclick = () => setDocModalMode('copy');
    }

    function getAreaFromHash() {
        if (typeof window !== 'undefined' && window.location && window.location.hash) {
            const match = window.location.hash.match(/#\/area\/([^/]+)/);
            if (match) return decodeURIComponent(match[1]).replace(/^area_/, '');
        }
        return '';
    }

    function getHouseFromHash() {
        if (typeof window !== 'undefined' && window.location && window.location.hash) {
            const match = window.location.hash.match(/house\/([^/]+)/);
            if (match) return decodeURIComponent(match[1]);
        }
        return '';
    }

    function getResolvedArea(explicitDoc = null) {
        if (explicitDoc && explicitDoc.area_id) return explicitDoc.area_id;
        if (activeDocModalDoc && activeDocModalDoc.area_id) return activeDocModalDoc.area_id;
        if (typeof currentArea !== 'undefined' && currentArea) return currentArea;
        if (typeof window !== 'undefined' && window.currentArea) return window.currentArea;
        return getAreaFromHash();
    }

    function getResolvedHouse(explicitDoc = null) {
        if (explicitDoc && explicitDoc.house_id) return explicitDoc.house_id;
        if (activeDocModalDoc && activeDocModalDoc.house_id) return activeDocModalDoc.house_id;
        if (typeof currentHouse !== 'undefined' && currentHouse) return currentHouse;
        if (typeof window !== 'undefined' && window.currentHouse) return window.currentHouse;
        return getHouseFromHash();
    }

    function handleDocDragStart(e, doc, fromCategory) {
        draggedDoc = {
            vault_id: doc.vault_id,
            title: doc.brief_arabic_title || doc.filename || '',
            category: fromCategory || doc.category || '',
            tenant: doc.tenant || doc.primary_tenant || '',
            tenant_id: doc.tenant_id,
            house_id: getResolvedHouse(doc),
            area_id: getResolvedArea(doc),
        };
        e.dataTransfer.setData('text/plain', doc.vault_id);
        e.dataTransfer.effectAllowed = 'copyMove';
        setTimeout(() => {
            if (e.target && e.target.classList) e.target.classList.add('opacity-40');
        }, 0);
    }

    function handleDocDragEnd(e) {
        if (e.target && e.target.classList) e.target.classList.remove('opacity-40');
        draggedDoc = null;
        document.querySelectorAll('.drag-over-active').forEach(el => {
            el.classList.remove('drag-over-active', 'border-blue-500', 'bg-blue-50/60', 'ring-2', 'ring-blue-400', 'bg-slate-700/80');
        });
    }

    function handleCategoryDragOver(e, card) {
        if (!draggedDoc || !draggedDoc.vault_id) return;
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        card.classList.add('drag-over-active', 'border-blue-500', 'bg-blue-50/60', 'ring-2', 'ring-blue-400');
    }

    function handleCategoryDragLeave(e, card) {
        card.classList.remove('drag-over-active', 'border-blue-500', 'bg-blue-50/60', 'ring-2', 'ring-blue-400');
    }

    async function handleCategoryDrop(e, targetCategory, card) {
        e.preventDefault();
        card.classList.remove('drag-over-active', 'border-blue-500', 'bg-blue-50/60', 'ring-2', 'ring-blue-400');
        if (!draggedDoc || !draggedDoc.vault_id) return;
        if (draggedDoc.category === targetCategory) return;

        const area = getResolvedArea(draggedDoc);
        const house = getResolvedHouse(draggedDoc);

        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(draggedDoc.vault_id)}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category: targetCategory, is_manual: 1 })
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Failed to move document');
            }
            const data = await res.json();
            showToast(`Moved to ${data.category || targetCategory}`);
            if (typeof window.refreshCurrentTab === 'function') {
                await window.refreshCurrentTab(area, house);
            }
        } catch (err) {
            console.error(err);
            showToast(err.message, 'error');
        }
    }

    function handleTenantTreeDragOver(e, btn, parentPath) {
        if (!draggedDoc || !draggedDoc.vault_id) return;
        const house = getResolvedHouse(draggedDoc);
        if (parentPath && house && !parentPath.includes(encodeURIComponent(house)) && !parentPath.includes(house)) {
            return;
        }
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        btn.classList.add('drag-over-active', 'bg-slate-700/80', 'ring-2', 'ring-blue-400');
    }

    function handleTenantTreeDragLeave(e, btn) {
        btn.classList.remove('drag-over-active', 'bg-slate-700/80', 'ring-2', 'ring-blue-400');
    }

    async function handleTenantTreeDrop(e, tenantName, btn, parentPath) {
        e.preventDefault();
        btn.classList.remove('drag-over-active', 'bg-slate-700/80', 'ring-2', 'ring-blue-400');
        if (!draggedDoc || !draggedDoc.vault_id) return;
        const area = getResolvedArea(draggedDoc);
        const house = getResolvedHouse(draggedDoc);
        if (parentPath && house && !parentPath.includes(encodeURIComponent(house)) && !parentPath.includes(house)) {
            showToast('Cannot move document to another house.', 'error');
            return;
        }

        try {
            const tRes = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/tenants`);
            if (!tRes.ok) throw new Error('Failed to load tenants');
            const tenants = await tRes.json();
            const target = tenants.find(t => t.name.trim() === tenantName.trim());
            if (!target) throw new Error('Tenant not found');

            const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(draggedDoc.vault_id)}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tenant_id: target.id, is_manual: 1 })
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Failed to assign tenant');
            }
            showToast(`Assigned to ${tenantName}`);
            if (typeof window.refreshCurrentTab === 'function') {
                await window.refreshCurrentTab(area, house);
            }
        } catch (err) {
            console.error(err);
            showToast(err.message, 'error');
        }
    }

    async function openDocModal(doc, currentCategory = null) {
        if (!doc) return;
        activeDocModalDoc = {
            ...doc,
            area_id: getResolvedArea(doc),
            house_id: getResolvedHouse(doc),
        };
        try {
            doc.area_id = activeDocModalDoc.area_id;
            doc.house_id = activeDocModalDoc.house_id;
        } catch (_) {}

        activeDocModalCategory = currentCategory || doc.category || '';
        setDocModalMode('move');

        if (!docActionModal) return;
        docModalTitle.textContent = doc.brief_arabic_title || doc.filename || 'Manage Document';
        docModalArabicTitle.value = doc.brief_arabic_title || '';
        docCustomFolderInput.value = '';
        docCustomFolderContainer.classList.add('hidden');
        docModalStatus.classList.add('hidden');

        if (doc.is_manual) {
            docManualBanner.classList.remove('hidden');
        } else {
            docManualBanner.classList.add('hidden');
        }

        populateFolderOptions(activeDocModalCategory);
        await populateTenantOptions(doc.tenant_id, doc.tenant || doc.primary_tenant);

        docActionModal.style.display = 'flex';
        docActionModal.classList.remove('hidden');
        docActionModal.classList.add('flex');
    }

    function closeDocModal() {
        if (!docActionModal) return;
        docActionModal.classList.add('hidden');
        docActionModal.classList.remove('flex');
        docActionModal.style.display = 'none';
        activeDocModalDoc = null;
    }

    function setDocModalMode(mode) {
        activeDocModalMode = mode;
        if (!btnModeMove || !btnModeCopy) return;
        if (mode === 'move') {
            btnModeMove.className = 'px-2.5 py-0.5 rounded-md font-semibold bg-white text-blue-600 shadow-2xs';
            btnModeCopy.className = 'px-2.5 py-0.5 rounded-md font-semibold text-slate-600 hover:text-slate-900';
            docModalSubmitText.textContent = '💾 Apply Changes';
        } else {
            btnModeCopy.className = 'px-2.5 py-0.5 rounded-md font-semibold bg-white text-blue-600 shadow-2xs';
            btnModeMove.className = 'px-2.5 py-0.5 rounded-md font-semibold text-slate-600 hover:text-slate-900';
            docModalSubmitText.textContent = '📄 Duplicate Document';
        }
    }

    function populateFolderOptions(selectedCategory) {
        if (!docModalFolderSelect) return;
        docModalFolderSelect.innerHTML = '';
        const existingFolderNames = new Set(STANDARD_FOLDERS);
        if (typeof currentCategories !== 'undefined' && currentCategories) {
            currentCategories.forEach(c => {
                const count = typeof c.document_count === 'number'
                    ? c.document_count
                    : (Array.isArray(c.documents) ? c.documents.length : 0);
                // Only include custom folders if they contain documents or are standard folders
                if (c.name && (count > 0 || STANDARD_FOLDERS.includes(c.name))) {
                    existingFolderNames.add(c.name);
                }
            });
        }
        if (selectedCategory) {
            existingFolderNames.add(selectedCategory);
        }

        const sorted = Array.from(existingFolderNames).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));

        sorted.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f;
            opt.textContent = f;
            if (selectedCategory && (f === selectedCategory || f.includes(selectedCategory) || selectedCategory.includes(f))) {
                opt.selected = true;
            }
            docModalFolderSelect.appendChild(opt);
        });

        const newOpt = document.createElement('option');
        newOpt.value = '__NEW_CUSTOM_FOLDER__';
        newOpt.textContent = '➕ Create new folder...';
        docModalFolderSelect.appendChild(newOpt);

        docModalFolderSelect.onchange = () => {
            if (docModalFolderSelect.value === '__NEW_CUSTOM_FOLDER__') {
                docCustomFolderContainer.classList.remove('hidden');
                docCustomFolderInput.focus();
            } else {
                docCustomFolderContainer.classList.add('hidden');
            }
        };
    }

    async function populateTenantOptions(selectedTenantId, selectedTenantName) {
        if (!docModalTenantSelect) return;
        docModalTenantSelect.innerHTML = '';
        try {
            const area = getResolvedArea(activeDocModalDoc);
            const house = getResolvedHouse(activeDocModalDoc);
            if (!area || !house) return;
            const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/tenants`);
            if (!res.ok) return;
            const tenants = await res.json();
            const seen = new Set();

            tenants.forEach(t => {
                const normName = (t.name || '').trim().toLowerCase();
                if (t.id != null && seen.has(`id:${t.id}`)) return;
                if (normName && seen.has(`name:${normName}`)) return;
                if (t.id != null) seen.add(`id:${t.id}`);
                if (normName) seen.add(`name:${normName}`);

                const opt = document.createElement('option');
                opt.value = t.id;
                opt.textContent = t.name + (t.start_date ? ` (${t.start_date.substring(0, 4)})` : '');
                if (selectedTenantId && t.id === selectedTenantId) {
                    opt.selected = true;
                } else if (!selectedTenantId && selectedTenantName && (t.name.trim() === selectedTenantName.trim() || selectedTenantName.includes(t.name.trim()))) {
                    opt.selected = true;
                }
                docModalTenantSelect.appendChild(opt);
            });
        } catch (err) {
            console.error('Failed to load tenants for modal:', err);
        }
    }

    async function saveDocModal() {
        if (!activeDocModalDoc || !activeDocModalDoc.vault_id) return;
        const area = getResolvedArea(activeDocModalDoc);
        const house = getResolvedHouse(activeDocModalDoc);

        docModalSubmit.disabled = true;
        const origBtnText = docModalSubmitText.textContent;
        docModalSubmitText.textContent = 'Saving...';

        try {
            let chosenCategory = docModalFolderSelect.value;
            if (chosenCategory === '__NEW_CUSTOM_FOLDER__') {
                const customVal = docCustomFolderInput.value.trim();
                if (!customVal) {
                    throw new Error('Please enter a folder name.');
                }
                chosenCategory = customVal;
            }

            const newTitle = docModalArabicTitle.value.trim();
            const newTenantId = parseInt(docModalTenantSelect.value);

            if (activeDocModalMode === 'copy') {
                const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(activeDocModalDoc.vault_id)}/copy`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        target_title: newTitle || undefined,
                        target_category: chosenCategory || undefined,
                        target_tenant_id: newTenantId || undefined,
                    })
                });
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Failed to copy document');
                }
                showToast('Document duplicated successfully');
            } else {
                const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(activeDocModalDoc.vault_id)}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        arabic_title: newTitle,
                        category: chosenCategory,
                        tenant_id: newTenantId,
                        is_manual: 1
                    })
                });
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Failed to update document');
                }
                showToast('Document updated successfully');
            }

            closeDocModal();
            if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                await window.refreshCurrentTab(area, house);
            } else if (typeof refreshCurrentTab === 'function') {
                await refreshCurrentTab(area, house);
            }
        } catch (err) {
            docModalStatus.textContent = err.message;
            docModalStatus.className = 'px-6 py-1 text-xs font-semibold text-rose-600 block';
            docModalStatus.classList.remove('hidden');
        } finally {
            docModalSubmit.disabled = false;
            docModalSubmitText.textContent = origBtnText;
        }
    }

    async function resetDocLock() {
        if (!activeDocModalDoc || !activeDocModalDoc.vault_id) return;
        const area = getResolvedArea(activeDocModalDoc);
        const house = getResolvedHouse(activeDocModalDoc);
        btnDocResetLock.disabled = true;
        btnDocResetLock.textContent = 'Resetting...';
        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(activeDocModalDoc.vault_id)}/reset-lock`, {
                method: 'POST',
            });
            if (!res.ok) throw new Error('Failed to reset lock');
            showToast('Reset to automatic successfully');
            closeDocModal();
            if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                await window.refreshCurrentTab(area, house);
            } else if (typeof refreshCurrentTab === 'function') {
                await refreshCurrentTab(area, house);
            }
        } catch (err) {
            docModalStatus.textContent = err.message;
            docModalStatus.className = 'px-6 py-1 text-xs font-semibold text-rose-600 block';
            docModalStatus.classList.remove('hidden');
        } finally {
            btnDocResetLock.disabled = false;
            btnDocResetLock.textContent = 'Reset to Auto';
        }
    }

    let isDeletingDoc = false;

    async function handleDeleteDoc(e) {
        if (e) {
            if (typeof e.preventDefault === 'function') e.preventDefault();
            if (typeof e.stopPropagation === 'function') e.stopPropagation();
        }

        if (isDeletingDoc) return;

        if (!activeDocModalDoc || !activeDocModalDoc.vault_id) {
            console.warn('[DocManager] handleDeleteDoc: activeDocModalDoc or vault_id missing', activeDocModalDoc);
            closeDocModal();
            return;
        }

        const confirmFn = (typeof window !== 'undefined' && typeof window.confirm === 'function') ? window.confirm : confirm;
        const confirmed = confirmFn('Are you sure you want to permanently delete this document? This will remove the file and all its records.');
        if (!confirmed) return;

        isDeletingDoc = true;

        if (btnDocDelete) {
            btnDocDelete.disabled = true;
            btnDocDelete.innerHTML = '<span>Deleting...</span>';
        }

        const area = getResolvedArea(activeDocModalDoc);
        const house = getResolvedHouse(activeDocModalDoc);
        const vaultId = activeDocModalDoc.vault_id;

        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(vaultId)}`, {
                method: 'DELETE'
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || errData.message || 'Failed to delete document');
            }

            closeDocModal();

            try {
                if (typeof showToast === 'function') {
                    showToast('Document deleted successfully.');
                } else if (typeof window !== 'undefined' && typeof window.showToast === 'function') {
                    window.showToast('Document deleted successfully.');
                }
                if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                    await window.refreshCurrentTab(area, house);
                } else if (typeof refreshCurrentTab === 'function') {
                    await refreshCurrentTab(area, house);
                }
                if (typeof window !== 'undefined' && typeof window.loadTree === 'function') {
                    await window.loadTree();
                } else if (typeof loadTree === 'function') {
                    await loadTree();
                }
            } catch (refreshErr) {
                console.error('Error refreshing UI after document deletion:', refreshErr);
            }
        } catch (err) {
            console.error('Failed to delete document:', err);
            if (docModalStatus) {
                docModalStatus.textContent = err.message;
                docModalStatus.className = 'px-6 py-1 text-xs font-semibold text-rose-600 block';
                docModalStatus.classList.remove('hidden');
            }
            if (typeof showToast === 'function') {
                showToast(err.message, 'error');
            } else if (typeof window !== 'undefined' && typeof window.showToast === 'function') {
                window.showToast(err.message, 'error');
            }
        } finally {
            isDeletingDoc = false;
            if (btnDocDelete) {
                btnDocDelete.disabled = false;
                btnDocDelete.innerHTML = `
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                    <span>Delete Document</span>
                `;
            }
        }
    }

    // Expose globals
    window.openDocModal = openDocModal;
    window.closeDocModal = closeDocModal;
    window.handleDeleteDoc = handleDeleteDoc;
    window.populateFolderOptions = populateFolderOptions;
    window.STANDARD_FOLDERS = STANDARD_FOLDERS;
    window.handleDocDragStart = handleDocDragStart;
    window.handleDocDragEnd = handleDocDragEnd;
    window.handleCategoryDragOver = handleCategoryDragOver;
    window.handleCategoryDragLeave = handleCategoryDragLeave;
    window.handleCategoryDrop = handleCategoryDrop;
    window.handleTenantTreeDragOver = handleTenantTreeDragOver;
    window.handleTenantTreeDragLeave = handleTenantTreeDragLeave;
    window.handleTenantTreeDrop = handleTenantTreeDrop;
    window.getAreaFromHash = getAreaFromHash;
    window.getHouseFromHash = getHouseFromHash;
    window.getResolvedArea = getResolvedArea;
    window.getResolvedHouse = getResolvedHouse;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            initDocManager,
            openDocModal,
            closeDocModal,
            handleDeleteDoc,
            setDocModalMode,
            saveDocModal,
            resetDocLock,
            STANDARD_FOLDERS,
            getAreaFromHash,
            getHouseFromHash,
            getResolvedArea,
            getResolvedHouse,
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDocManager);
    } else {
        initDocManager();
    }
})();


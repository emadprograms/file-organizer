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

    let docModalDate = null;
    let changeDocDateModal = null;
    let changeDocDateInput = null;
    let changeDocDateTitle = null;
    let changeDocDateSubtitle = null;
    let changeDocDateStatus = null;
    let btnChangeDateCancel = null;
    let btnChangeDateClose = null;
    let btnChangeDateSave = null;
    let btnChangeDateSaveText = null;
    let activeDateModalDoc = null;
    let activeDateModalOriginalDoc = null;

    let mergeDocsModal = null;
    let mergeDocsClose = null;
    let btnMergeDocsCancel = null;
    let btnMergeDocsConfirm = null;
    let mergeDocsList = null;
    let mergeTargetTitle = null;
    let mergeTargetCategory = null;
    let mergeCustomCatContainer = null;
    let mergeCustomCatInput = null;
    let mergeTargetTenant = null;
    let mergeTargetDate = null;
    let mergeTargetNotes = null;
    let mergeDeleteSources = null;
    let mergeDocsStatus = null;
    let mergeDocsCountBadge = null;
    let mergeDocsSpinner = null;
    let mergeDocsBtnText = null;

    let mergeStepReorder = null;
    let mergeStepSave = null;
    let mergeOrderBanner = null;
    let mergeOrderSummary = null;
    let btnMergeSwapOrder = null;
    let btnMergeReorderCancel = null;
    let btnMergeReorderContinue = null;
    let btnMergeSaveBack = null;
    let initialMergeCount = 0;

    let activeMergeDocs = [];
    let activeMergeFallbackCategory = null;

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
        docModalDate = document.getElementById('doc-modal-date');
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

        changeDocDateModal = document.getElementById('change-doc-date-modal');
        changeDocDateInput = document.getElementById('change-doc-date-input');
        changeDocDateTitle = document.getElementById('change-doc-date-title');
        changeDocDateSubtitle = document.getElementById('change-doc-date-subtitle');
        changeDocDateStatus = document.getElementById('change-doc-date-status');
        btnChangeDateCancel = document.getElementById('btn-change-date-cancel');
        btnChangeDateClose = document.getElementById('change-doc-date-close');
        btnChangeDateSave = document.getElementById('btn-change-date-save');
        btnChangeDateSaveText = document.getElementById('btn-change-date-save-text');

        if (docModalClose) docModalClose.onclick = closeDocModal;
        if (docModalCancel) docModalCancel.onclick = closeDocModal;
        if (docModalSubmit) docModalSubmit.onclick = saveDocModal;
        if (btnDocResetLock) btnDocResetLock.onclick = resetDocLock;
        if (btnDocDelete) btnDocDelete.onclick = (e) => handleDeleteDoc(e);
        if (btnModeMove) btnModeMove.onclick = () => setDocModalMode('move');
        if (btnModeCopy) btnModeCopy.onclick = () => setDocModalMode('copy');

        if (btnChangeDateClose) btnChangeDateClose.onclick = closeChangeDocDateModal;
        if (btnChangeDateCancel) btnChangeDateCancel.onclick = closeChangeDocDateModal;
        if (btnChangeDateSave) btnChangeDateSave.onclick = saveChangeDocDate;

        const btnDocEditPages = document.getElementById('btn-doc-edit-pages');
        if (btnDocEditPages) {
            btnDocEditPages.onclick = () => {
                if (activeDocModalDoc && typeof window.openPageEditor === 'function') {
                    const docToEdit = { ...activeDocModalDoc };
                    const catToEdit = activeDocModalCategory;
                    closeDocModal();
                    window.openPageEditor(docToEdit, catToEdit);
                }
            };
        }

        const btnDocMerge = document.getElementById('btn-doc-merge');
        if (btnDocMerge) {
            btnDocMerge.onclick = () => {
                if (activeDocModalDoc && typeof openMergeModal === 'function') {
                    const docToMerge = { ...activeDocModalDoc };
                    closeDocModal();
                    openMergeModal([docToMerge]);
                }
            };
        }

        mergeDocsModal = document.getElementById('merge-docs-modal');
        mergeDocsClose = document.getElementById('merge-docs-close');
        btnMergeDocsCancel = document.getElementById('btn-merge-docs-cancel');
        btnMergeDocsConfirm = document.getElementById('btn-merge-docs-confirm');
        mergeDocsList = document.getElementById('merge-docs-list');
        mergeAddDocSelect = document.getElementById('merge-add-doc-select');
        btnMergeAddDoc = document.getElementById('btn-merge-add-doc');
        mergeTargetTitle = document.getElementById('merge-target-title');
        mergeTargetCategory = document.getElementById('merge-target-category');
        mergeCustomCatContainer = document.getElementById('merge-custom-cat-container');
        mergeCustomCatInput = document.getElementById('merge-custom-cat-input');
        mergeTargetTenant = document.getElementById('merge-target-tenant');
        mergeTargetDate = document.getElementById('merge-target-date');
        mergeTargetNotes = document.getElementById('merge-target-notes');
        mergeDeleteSources = document.getElementById('merge-delete-sources');
        mergeDocsStatus = document.getElementById('merge-docs-status');
        mergeDocsCountBadge = document.getElementById('merge-docs-count-badge');
        mergeDocsSpinner = document.getElementById('merge-docs-spinner');
        mergeDocsBtnText = document.getElementById('merge-docs-btn-text');

        mergeStepReorder = document.getElementById('merge-step-reorder');
        mergeStepSave = document.getElementById('merge-step-save');
        mergeOrderBanner = document.getElementById('merge-order-banner');
        mergeOrderSummary = document.getElementById('merge-order-summary');
        btnMergeSwapOrder = document.getElementById('btn-merge-swap-order');
        btnMergeReorderCancel = document.getElementById('btn-merge-reorder-cancel');
        btnMergeReorderContinue = document.getElementById('btn-merge-reorder-continue');
        btnMergeSaveBack = document.getElementById('btn-merge-save-back');

        if (mergeDocsClose) mergeDocsClose.onclick = closeMergeModal;
        if (btnMergeDocsCancel) btnMergeDocsCancel.onclick = closeMergeModal;
        if (btnMergeDocsConfirm) btnMergeDocsConfirm.onclick = handleMergeDocsSubmit;
        if (btnMergeSwapOrder) btnMergeSwapOrder.onclick = handleSwapMergeDocs;
        if (btnMergeReorderCancel) btnMergeReorderCancel.onclick = closeMergeModal;
        if (btnMergeReorderContinue) btnMergeReorderContinue.onclick = handleReorderContinue;
        if (btnMergeSaveBack) btnMergeSaveBack.onclick = handleSaveBack;
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

    function getActiveSelectedDocIds() {
        if (typeof window !== 'undefined') {
            if (window.selectedDocIds instanceof Set) return window.selectedDocIds;
            if (typeof window.getSelectedDocIds === 'function') {
                const s = window.getSelectedDocIds();
                if (s instanceof Set) return s;
                if (Array.isArray(s)) return new Set(s);
            }
        }
        if (typeof selectedDocIds !== 'undefined' && selectedDocIds instanceof Set) {
            return selectedDocIds;
        }
        return new Set();
    }

    function handleDocDragStart(e, doc, fromCategory) {
        const activeSelected = getActiveSelectedDocIds();
        const isPartOfSelection = activeSelected.has(doc.vault_id);
        const targetVaultIds = isPartOfSelection ? Array.from(activeSelected) : [doc.vault_id];
        const isMulti = targetVaultIds.length > 1;

        draggedDoc = {
            vault_id: doc.vault_id,
            vault_ids: targetVaultIds,
            isMulti: isMulti,
            count: targetVaultIds.length,
            title: doc.brief_arabic_title || doc.filename || '',
            category: fromCategory || doc.category || '',
            tenant: doc.tenant || doc.primary_tenant || '',
            tenant_id: doc.tenant_id,
            house_id: getResolvedHouse(doc),
            area_id: getResolvedArea(doc),
        };
        if (typeof window !== 'undefined') {
            window.draggedDoc = draggedDoc;
        }

        if (e && e.dataTransfer) {
            if (typeof e.dataTransfer.setData === 'function') {
                e.dataTransfer.setData('text/plain', doc.vault_id);
                try {
                    e.dataTransfer.setData('application/json', JSON.stringify({
                        vault_id: doc.vault_id,
                        vault_ids: targetVaultIds,
                        count: targetVaultIds.length
                    }));
                } catch (_) {}
            }
            e.dataTransfer.effectAllowed = 'copyMove';

            if (isMulti && typeof e.dataTransfer.setDragImage === 'function' && typeof document !== 'undefined' && document.createElement) {
                try {
                    const dragBadge = document.createElement('div');
                    dragBadge.id = 'desktop-drag-avatar';
                    dragBadge.style.cssText = 'position: absolute; top: -1000px; left: -1000px; z-index: 10000; padding: 6px 12px; background-color: #1e293b; color: #ffffff; border-radius: 9999px; font-size: 12px; font-weight: 600; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); display: flex; align-items: center; gap: 8px; pointer-events: none;';
                    dragBadge.innerHTML = `<span>Moving ${targetVaultIds.length} items</span>`;
                    document.body.appendChild(dragBadge);
                    e.dataTransfer.setDragImage(dragBadge, 15, 15);
                    setTimeout(() => {
                        if (dragBadge.parentNode) dragBadge.remove();
                    }, 0);
                } catch (_) {}
            }
        }

        const applyDimming = () => {
            if (isMulti) {
                targetVaultIds.forEach(id => {
                    const el = (typeof document !== 'undefined') ? document.querySelector(`[data-vault-id="${id}"]`) : null;
                    if (el && el.classList) el.classList.add('opacity-40', 'ring-2', 'ring-blue-400');
                });
            } else if (e && e.target && e.target.classList) {
                e.target.classList.add('opacity-40');
            }
        };
        applyDimming();
        setTimeout(applyDimming, 0);
    }

    function handleDocDragEnd(e) {
        if (typeof document !== 'undefined') {
            document.querySelectorAll('.opacity-40, .ring-blue-400').forEach(el => {
                el.classList.remove('opacity-40', 'ring-2', 'ring-blue-400');
            });
            document.querySelectorAll('.drag-over-active').forEach(el => {
                el.classList.remove('drag-over-active', 'border-blue-500', 'bg-blue-50/60', 'ring-2', 'ring-blue-400', 'bg-slate-700/80');
            });
        } else if (e && e.target && e.target.classList) {
            e.target.classList.remove('opacity-40');
        }
        draggedDoc = null;
        if (typeof window !== 'undefined') {
            window.draggedDoc = null;
        }
    }

    function handleCategoryDragOver(e, card) {
        const activeDragged = draggedDoc || (typeof window !== 'undefined' && window.draggedDoc);
        if (!activeDragged || (!activeDragged.vault_id && (!activeDragged.vault_ids || activeDragged.vault_ids.length === 0))) return;
        if (e && typeof e.preventDefault === 'function') e.preventDefault();
        if (e && e.dataTransfer) e.dataTransfer.dropEffect = 'move';
        if (card && card.classList) card.classList.add('drag-over-active', 'border-blue-500', 'bg-blue-50/60', 'ring-2', 'ring-blue-400');
    }

    function handleCategoryDragLeave(e, card) {
        if (card && card.classList) card.classList.remove('drag-over-active', 'border-blue-500', 'bg-blue-50/60', 'ring-2', 'ring-blue-400');
    }

    async function handleCategoryDrop(e, targetCategory, card) {
        if (e && typeof e.preventDefault === 'function') e.preventDefault();
        if (card && card.classList) {
            card.classList.remove('drag-over-active', 'border-blue-500', 'bg-blue-50/60', 'ring-2', 'ring-blue-400');
        }
        const activeDragged = draggedDoc || (typeof window !== 'undefined' && window.draggedDoc);
        if (!activeDragged) return;

        const vaultIds = (activeDragged.vault_ids && activeDragged.vault_ids.length > 0)
            ? activeDragged.vault_ids
            : (activeDragged.vault_id ? [activeDragged.vault_id] : []);

        if (vaultIds.length === 0) return;

        const isMulti = vaultIds.length > 1;

        // If single doc and it is already in targetCategory, skip
        if (!isMulti && activeDragged.category === targetCategory) return;

        const area = getResolvedArea(activeDragged);
        const house = getResolvedHouse(activeDragged);
        const sourceCategory = activeDragged.category;

        try {
            if (isMulti) {
                const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/batch-move`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        vault_ids: vaultIds,
                        target_category: targetCategory
                    })
                });
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || errData.error || 'Failed to move documents');
                }
                const data = await res.json();
                const finalCategory = data.target_category || targetCategory;
                const movedCount = (typeof data.moved_count === 'number') ? data.moved_count : vaultIds.length;

                if (typeof window !== 'undefined' && typeof window.deselectAllDocs === 'function') {
                    window.deselectAllDocs();
                } else if (typeof deselectAllDocs === 'function') {
                    deselectAllDocs();
                }

                showToast(`Successfully moved ${movedCount} documents to "${finalCategory}"`);

                let allMovedInDom = true;
                if (typeof window !== 'undefined' && typeof window.moveDocInDom === 'function') {
                    vaultIds.forEach(id => {
                        const ok = window.moveDocInDom(id, null, finalCategory);
                        if (!ok) allMovedInDom = false;
                    });
                } else {
                    allMovedInDom = false;
                }
                if (!allMovedInDom && typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                    await window.refreshCurrentTab(area, house);
                }
                if (typeof window !== 'undefined' && typeof window.loadTree === 'function') {
                    await window.loadTree();
                }
            } else {
                const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(activeDragged.vault_id)}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ category: targetCategory, is_manual: 1 })
                });
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Failed to move document');
                }
                const data = await res.json();
                const finalCategory = data.category || targetCategory;

                const activeSelected = getActiveSelectedDocIds();
                if (activeSelected.has(activeDragged.vault_id)) {
                    if (typeof window !== 'undefined' && typeof window.deselectAllDocs === 'function') {
                        window.deselectAllDocs();
                    } else if (typeof deselectAllDocs === 'function') {
                        deselectAllDocs();
                    }
                }

                showToast(`Moved to ${finalCategory}`);

                let movedInDom = false;
                if (typeof window !== 'undefined' && typeof window.moveDocInDom === 'function') {
                    movedInDom = window.moveDocInDom(activeDragged.vault_id, sourceCategory, finalCategory);
                }
                if (!movedInDom && typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                    await window.refreshCurrentTab(area, house);
                }
                if (typeof window !== 'undefined' && typeof window.loadTree === 'function') {
                    await window.loadTree();
                }
            }
        } catch (err) {
            console.error(err);
            showToast(err.message, 'error');
        } finally {
            draggedDoc = null;
            if (typeof window !== 'undefined') {
                window.draggedDoc = null;
            }
        }
    }

    function handleTenantTreeDragOver(e, btn, parentPath) {
        const activeDragged = draggedDoc || (typeof window !== 'undefined' && window.draggedDoc);
        if (!activeDragged || (!activeDragged.vault_id && (!activeDragged.vault_ids || activeDragged.vault_ids.length === 0))) return;
        const house = getResolvedHouse(activeDragged);
        if (parentPath && house && !parentPath.includes(encodeURIComponent(house)) && !parentPath.includes(house)) {
            return;
        }
        if (e && typeof e.preventDefault === 'function') e.preventDefault();
        if (e && e.dataTransfer) e.dataTransfer.dropEffect = 'move';
        if (btn && btn.classList) btn.classList.add('drag-over-active', 'bg-slate-700/80', 'ring-2', 'ring-blue-400');
    }

    function handleTenantTreeDragLeave(e, btn) {
        if (btn && btn.classList) btn.classList.remove('drag-over-active', 'bg-slate-700/80', 'ring-2', 'ring-blue-400');
    }

    async function handleTenantTreeDrop(e, tenantName, btn, parentPath) {
        if (e && typeof e.preventDefault === 'function') e.preventDefault();
        if (btn && btn.classList) {
            btn.classList.remove('drag-over-active', 'bg-slate-700/80', 'ring-2', 'ring-blue-400');
        }
        const activeDragged = draggedDoc || (typeof window !== 'undefined' && window.draggedDoc);
        if (!activeDragged) return;

        const vaultIds = (activeDragged.vault_ids && activeDragged.vault_ids.length > 0)
            ? activeDragged.vault_ids
            : (activeDragged.vault_id ? [activeDragged.vault_id] : []);
        if (vaultIds.length === 0) return;

        const area = getResolvedArea(activeDragged);
        const house = getResolvedHouse(activeDragged);
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

            const isMulti = vaultIds.length > 1;
            if (isMulti) {
                const patchPromises = vaultIds.map(vid =>
                    fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(vid)}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ tenant_id: target.id, is_manual: 1 })
                    })
                );
                const responses = await Promise.all(patchPromises);
                const anyFailed = responses.some(r => !r.ok);
                if (anyFailed) {
                    throw new Error('Some documents failed to update tenant');
                }
                if (typeof window !== 'undefined' && typeof window.deselectAllDocs === 'function') {
                    window.deselectAllDocs();
                } else if (typeof deselectAllDocs === 'function') {
                    deselectAllDocs();
                }
                if (typeof window !== 'undefined' && typeof window.removeDocFromDom === 'function') {
                    vaultIds.forEach(vid => window.removeDocFromDom(vid));
                }
                showToast(`Assigned ${vaultIds.length} documents to ${tenantName}`);
            } else {
                const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(activeDragged.vault_id)}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tenant_id: target.id, is_manual: 1 })
                });
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Failed to assign tenant');
                }
                if (typeof window !== 'undefined' && typeof window.removeDocFromDom === 'function') {
                    window.removeDocFromDom(activeDragged.vault_id);
                }
                showToast(`Assigned to ${tenantName}`);
            }

            if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                await window.refreshCurrentTab(area, house);
            }
            if (typeof window !== 'undefined' && typeof window.loadTree === 'function') {
                await window.loadTree();
            } else if (typeof loadTree === 'function') {
                await loadTree();
            }
        } catch (err) {
            console.error(err);
            showToast(err.message, 'error');
        } finally {
            draggedDoc = null;
            if (typeof window !== 'undefined') {
                window.draggedDoc = null;
            }
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
        if (docModalDate) {
            const rawDate = doc.date || doc.primary_date || (Array.isArray(doc.dates) && doc.dates[0]) || '';
            let isoDate = '';
            if (rawDate) {
                const match = String(rawDate).trim().match(/^\d{4}-\d{2}-\d{2}/);
                isoDate = match ? match[0] : String(rawDate).trim();
            }
            docModalDate.value = isoDate;
        }
        docCustomFolderInput.value = '';
        docCustomFolderContainer.classList.add('hidden');
        docModalStatus.classList.add('hidden');

        if (doc.is_manual) {
            docManualBanner.classList.remove('hidden');
        } else {
            docManualBanner.classList.add('hidden');
        }

        resetDeleteButton();

        if (btnDocDelete) {
            const canDelete = (typeof window !== 'undefined' && window.authManager) ? window.authManager.hasDeletePermission() : true;
            btnDocDelete.classList.toggle('hidden', !canDelete);
        }

        populateFolderOptions(activeDocModalCategory);
        await populateTenantOptions(doc.tenant_id, doc.tenant || doc.primary_tenant);

        docActionModal.style.display = 'flex';
        docActionModal.classList.remove('hidden');
        docActionModal.classList.add('flex');
    }

    function closeDocModal() {
        if (!docActionModal) return;
        resetDeleteButton();
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
            const newDate = docModalDate ? docModalDate.value.trim() : undefined;

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
                const resData = await res.json().catch(() => null);
                showToast('Document duplicated successfully');
                closeDocModal();
                let domHandled = false;
                if (resData && typeof window.copyDocInDom === 'function') {
                    domHandled = window.copyDocInDom(resData, chosenCategory);
                }
                if (!domHandled) {
                    if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                        await window.refreshCurrentTab(area, house);
                    } else if (typeof refreshCurrentTab === 'function') {
                        await refreshCurrentTab(area, house);
                    }
                }
            } else {
                const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(activeDocModalDoc.vault_id)}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        arabic_title: newTitle,
                        category: chosenCategory,
                        tenant_id: newTenantId,
                        primary_date: newDate !== undefined ? newDate : undefined,
                        is_manual: 1
                    })
                });
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Failed to update document');
                }
                const resData = await res.json().catch(() => null);
                const finalCategory = (resData && resData.category) || chosenCategory;
                showToast('Document updated successfully');
                closeDocModal();
                let domHandled = false;
                const isDifferentTenant = newTenantId && activeDocModalDoc.tenant_id && String(newTenantId) !== String(activeDocModalDoc.tenant_id);
                if (isDifferentTenant) {
                    if (typeof window !== 'undefined' && typeof window.removeDocFromDom === 'function') {
                        window.removeDocFromDom(activeDocModalDoc.vault_id, activeDocModalDoc.category);
                    }
                    if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                        await window.refreshCurrentTab(area, house);
                    } else if (typeof refreshCurrentTab === 'function') {
                        await refreshCurrentTab(area, house);
                    }
                } else {
                    if (typeof window.moveDocInDom === 'function') {
                        domHandled = window.moveDocInDom(activeDocModalDoc.vault_id, activeDocModalDoc.category, finalCategory);
                        if (domHandled && newTitle) {
                            const titleEl = document.querySelector(`[data-vault-id="${activeDocModalDoc.vault_id}"] .doc-title-text`);
                            if (titleEl) titleEl.textContent = newTitle;
                        }
                    }
                    if (!domHandled) {
                        if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                            await window.refreshCurrentTab(area, house);
                        } else if (typeof refreshCurrentTab === 'function') {
                            await refreshCurrentTab(area, house);
                        }
                    }
                }
                if (typeof window !== 'undefined' && typeof window.loadTree === 'function') {
                    await window.loadTree();
                } else if (typeof loadTree === 'function') {
                    await loadTree();
                }
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
    let isDeleteArmed = false;
    let deleteConfirmTimeout = null;

    function resetDeleteButton() {
        if (deleteConfirmTimeout) {
            clearTimeout(deleteConfirmTimeout);
            deleteConfirmTimeout = null;
        }
        isDeleteArmed = false;
        if (btnDocDelete) {
            btnDocDelete.disabled = false;
            btnDocDelete.className = 'px-3.5 py-2 text-xs font-bold text-rose-600 hover:text-white bg-rose-50 hover:bg-rose-600 border border-rose-200 rounded-xl transition-all mr-auto flex items-center gap-1.5 cursor-pointer shadow-2xs';
            const canDelete = (typeof window !== 'undefined' && window.authManager) ? window.authManager.hasDeletePermission() : true;
            if (!canDelete) {
                btnDocDelete.classList.add('hidden');
            } else {
                btnDocDelete.classList.remove('hidden');
            }
            btnDocDelete.innerHTML = `
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                <span>Delete Document</span>
            `;
        }
    }

    function getIsDeleteArmed() {
        return isDeleteArmed;
    }

    async function handleDeleteDoc(e) {
        if (e) {
            if (typeof e.preventDefault === 'function') e.preventDefault();
            if (typeof e.stopPropagation === 'function') e.stopPropagation();
        }

        if (isDeletingDoc) return;

        const canDelete = (typeof window !== 'undefined' && window.authManager) ? window.authManager.hasDeletePermission() : true;
        if (!canDelete) {
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('عذراً: ليس لديك صلاحية حذف الوثائق (قراءة ورفع فقط) • Deletion is restricted for Contributor accounts.', 'error');
            return;
        }

        if (!activeDocModalDoc || !activeDocModalDoc.vault_id) {
            console.warn('[DocManager] handleDeleteDoc: activeDocModalDoc or vault_id missing', activeDocModalDoc);
            closeDocModal();
            return;
        }

        // Step 1: Arm confirmation state on first click
        if (!isDeleteArmed) {
            isDeleteArmed = true;
            if (btnDocDelete) {
                btnDocDelete.className = 'px-3.5 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 border border-rose-700 rounded-xl transition-all mr-auto flex items-center gap-1.5 cursor-pointer shadow-sm animate-pulse';
                btnDocDelete.innerHTML = `
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                    <span>⚠️ Confirm Delete?</span>
                `;
            }
            if (deleteConfirmTimeout) clearTimeout(deleteConfirmTimeout);
            deleteConfirmTimeout = setTimeout(() => {
                resetDeleteButton();
            }, 4000);
            return;
        }

        // Step 2: Second click within 4s executes permanent deletion
        if (deleteConfirmTimeout) {
            clearTimeout(deleteConfirmTimeout);
            deleteConfirmTimeout = null;
        }
        isDeleteArmed = false;
        isDeletingDoc = true;

        if (btnDocDelete) {
            btnDocDelete.disabled = true;
            btnDocDelete.className = 'px-3.5 py-2 text-xs font-bold text-white bg-rose-500 border border-rose-600 rounded-xl transition-all mr-auto flex items-center gap-1.5 cursor-not-allowed opacity-80';
            btnDocDelete.innerHTML = `
                <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
                <span>Deleting...</span>
            `;
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
                    showToast('Document permanently deleted.');
                } else if (typeof window !== 'undefined' && typeof window.showToast === 'function') {
                    window.showToast('Document permanently deleted.');
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
            resetDeleteButton();
        }
    }

    // ── Floating 3-Dots Action Dropdown Menu ────────────────────────────────
    let activeDocDropdown = null;
    let activeMenuCleanup = null;

    function closeDocDropdownMenu() {
        if (activeMenuCleanup) {
            activeMenuCleanup();
            activeMenuCleanup = null;
        }
        activeDocDropdown = null;
    }

    function openDocDropdownMenu(e, doc, currentCategory, triggerBtn) {
        if (e) {
            if (typeof e.stopPropagation === 'function') e.stopPropagation();
            if (typeof e.preventDefault === 'function') e.preventDefault();
        }
        if (!doc || !triggerBtn) return;

        // Toggle: if clicking the trigger of the already open menu, close it
        if (activeDocDropdown && activeDocDropdown.triggerBtn === triggerBtn) {
            closeDocDropdownMenu();
            return;
        }

        closeDocDropdownMenu();

        const canDelete = (typeof window !== 'undefined' && window.authManager) ? window.authManager.hasDeletePermission() : true;

        const menu = document.createElement('div');
        menu.className = 'doc-dropdown-menu fixed z-50 bg-white rounded-xl shadow-xl border border-slate-200 py-1 min-w-[190px] text-xs font-sans animate-in fade-in zoom-in-95 duration-100';
        menu.setAttribute('role', 'menu');

        const isPinned = Boolean(doc && doc.is_manual);
        const pinActionHtml = isPinned
            ? `
            <button type="button" class="doc-menu-item-pin doc-menu-item-unpin w-full px-3.5 py-2 text-left flex items-center gap-2.5 font-medium text-slate-700 hover:bg-amber-50 hover:text-amber-700 transition-colors cursor-pointer" title="Unlock document and reset to auto-reconciliation">
                <svg class="w-3.5 h-3.5 text-amber-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"/></svg>
                <span>Unpin Document</span>
            </button>
            `
            : `
            <button type="button" class="doc-menu-item-pin w-full px-3.5 py-2 text-left flex items-center gap-2.5 font-medium text-slate-700 hover:bg-amber-50 hover:text-amber-700 transition-colors cursor-pointer" title="Pin document to preserve its tenant assignment">
                <svg class="w-3.5 h-3.5 text-amber-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
                <span>Pin Document</span>
            </button>
            `;

        const isTimeline = Boolean(
            (triggerBtn && triggerBtn.closest && triggerBtn.closest('#timeline-container')) ||
            (typeof currentTab !== 'undefined' && currentTab === 'timeline') ||
            (typeof window !== 'undefined' && window.currentTab === 'timeline')
        );

        const navActionHtml = isTimeline
            ? `
            <button type="button" class="doc-menu-item-categories w-full px-3.5 py-2 text-left flex items-center gap-2.5 font-medium text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 transition-colors cursor-pointer">
                <svg class="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                <span>Show in Categories</span>
            </button>
            `
            : `
            <button type="button" class="doc-menu-item-timeline w-full px-3.5 py-2 text-left flex items-center gap-2.5 font-medium text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 transition-colors cursor-pointer">
                <svg class="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                <span>Show in Timeline</span>
            </button>
            `;

        menu.innerHTML = `
            <button type="button" class="doc-menu-item-rename w-full px-3.5 py-2 text-left flex items-center gap-2.5 font-medium text-slate-700 hover:bg-blue-50 hover:text-blue-700 transition-colors cursor-pointer">
                <svg class="w-3.5 h-3.5 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                <span>Rename Document</span>
            </button>
            <button type="button" class="doc-menu-item-date w-full px-3.5 py-2 text-left flex items-center gap-2.5 font-medium text-slate-700 hover:bg-purple-50 hover:text-purple-700 transition-colors cursor-pointer" title="Change document date">
                <svg class="w-3.5 h-3.5 text-purple-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                <span>Change Date</span>
            </button>
            <button type="button" class="doc-menu-item-move w-full px-3.5 py-2 text-left flex items-center gap-2.5 font-medium text-slate-700 hover:bg-amber-50 hover:text-amber-700 transition-colors cursor-pointer">
                <svg class="w-3.5 h-3.5 text-amber-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 13l3-3m0 0l-3-3m3 3H9"/></svg>
                <span>Move Document</span>
            </button>
            <button type="button" class="doc-menu-item-copy w-full px-3.5 py-2 text-left flex items-center gap-2.5 font-medium text-slate-700 hover:bg-indigo-50 hover:text-indigo-700 transition-colors cursor-pointer">
                <svg class="w-3.5 h-3.5 text-indigo-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2"/></svg>
                <span>Copy Document</span>
            </button>
            <button type="button" class="doc-menu-item-edit-pages w-full px-3.5 py-2 text-left flex items-center gap-2.5 font-medium text-amber-700 hover:bg-amber-50 transition-colors cursor-pointer" title="Edit, split, reorder, or delete pages in this document • تعديل وفصل الصفحات">
                <svg class="w-3.5 h-3.5 text-amber-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879a3 3 0 11-4.242-4.242L10.758 10M12 12L9.121 9.121m0 0a3 3 0 10-4.242 4.242L7.758 16"/></svg>
                <span>✂️ Edit &amp; Split Pages</span>
            </button>
            ${pinActionHtml}
            ${navActionHtml}
            ${canDelete ? `
            <hr class="my-1 border-slate-100" />
            <button type="button" class="doc-menu-item-delete w-full px-3.5 py-2 text-left flex items-center gap-2.5 font-medium text-rose-600 hover:bg-rose-50 hover:text-rose-700 transition-colors cursor-pointer">
                <svg class="w-3.5 h-3.5 text-rose-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                <span>Delete Document</span>
            </button>
            ` : ''}
        `;

        const btnEditPages = menu.querySelector('.doc-menu-item-edit-pages');
        if (btnEditPages) {
            btnEditPages.onclick = (ev) => {
                ev.stopPropagation();
                closeDocDropdownMenu();
                if (typeof window !== 'undefined' && typeof window.openPageEditor === 'function') {
                    window.openPageEditor(doc, currentCategory);
                }
            };
        }

        const btnRename = menu.querySelector('.doc-menu-item-rename');
        if (btnRename) {
            btnRename.onclick = (ev) => {
                ev.stopPropagation();
                closeDocDropdownMenu();
                const card = triggerBtn.closest('div[data-vault-id]') || document.querySelector(`div[data-vault-id="${doc.vault_id}"]`);
                const titleEl = card ? card.querySelector('.doc-title-text') : null;
                if (titleEl) {
                    const area = getResolvedArea(doc);
                    const house = getResolvedHouse(doc);
                    const isTimelineTab = (typeof window !== 'undefined' && window.currentTab === 'timeline') || (titleEl && titleEl.tagName === 'H4');
                    if (isTimelineTab && typeof window.handleInlineRenameTimeline === 'function') {
                        window.handleInlineRenameTimeline(null, doc, titleEl, area, house);
                    } else if (typeof window.handleInlineRename === 'function') {
                        window.handleInlineRename(null, doc, titleEl, area, house);
                    } else if (typeof window.handleInlineRenameTimeline === 'function') {
                        window.handleInlineRenameTimeline(null, doc, titleEl, area, house);
                    }
                }
            };
        }

        const btnDate = menu.querySelector('.doc-menu-item-date');
        if (btnDate) {
            btnDate.onclick = (ev) => {
                ev.stopPropagation();
                closeDocDropdownMenu();
                if (typeof window !== 'undefined' && typeof window.openChangeDocDateModal === 'function') {
                    window.openChangeDocDateModal(doc);
                } else if (typeof openChangeDocDateModal === 'function') {
                    openChangeDocDateModal(doc);
                }
            };
        }

        const btnMove = menu.querySelector('.doc-menu-item-move');
        if (btnMove) {
            btnMove.onclick = (ev) => {
                ev.stopPropagation();
                closeDocDropdownMenu();
                if (typeof window.openBatchMoveForDoc === 'function') {
                    window.openBatchMoveForDoc(doc);
                } else if (typeof window.openBatchMoveModal === 'function') {
                    window.openBatchMoveModal();
                }
            };
        }

        const btnCopy = menu.querySelector('.doc-menu-item-copy');
        if (btnCopy) {
            btnCopy.onclick = (ev) => {
                ev.stopPropagation();
                closeDocDropdownMenu();
                if (typeof window.openBatchCopyForDoc === 'function') {
                    window.openBatchCopyForDoc(doc);
                } else if (typeof window.openBatchCopyModal === 'function') {
                    window.openBatchCopyModal();
                }
            };
        }

        const btnPin = menu.querySelector('.doc-menu-item-pin');
        if (btnPin) {
            btnPin.onclick = async (ev) => {
                ev.stopPropagation();
                closeDocDropdownMenu();
                await handleToggleDocPin(doc);
            };
        }

        const btnCategories = menu.querySelector('.doc-menu-item-categories');
        if (btnCategories) {
            btnCategories.onclick = (ev) => {
                ev.stopPropagation();
                closeDocDropdownMenu();
                showDocInCategories(doc);
            };
        }

        const btnTimeline = menu.querySelector('.doc-menu-item-timeline');
        if (btnTimeline) {
            btnTimeline.onclick = (ev) => {
                ev.stopPropagation();
                closeDocDropdownMenu();
                showDocInTimeline(doc);
            };
        }

        const btnDelete = menu.querySelector('.doc-menu-item-delete');
        if (btnDelete) {
            btnDelete.onclick = (ev) => {
                ev.stopPropagation();
                closeDocDropdownMenu();
                handleDeleteSingleDoc(doc);
            };
        }

        document.body.appendChild(menu);

        const rect = triggerBtn.getBoundingClientRect();
        const menuWidth = 190;
        let top = rect.bottom + 4;
        let left = rect.right - menuWidth;
        if (left < 10) left = 10;
        const windowHeight = (typeof window !== 'undefined' && window.innerHeight) ? window.innerHeight : 800;
        if (top + 260 > windowHeight) {
            top = Math.max(10, rect.top - 260);
        }
        menu.style.top = `${top}px`;
        menu.style.left = `${left}px`;

        const onDocClick = (evt) => {
            if (!menu.contains(evt.target) && evt.target !== triggerBtn && !triggerBtn.contains(evt.target)) {
                closeDocDropdownMenu();
            }
        };
        const onDocKeydown = (evt) => {
            if (evt.key === 'Escape') closeDocDropdownMenu();
        };

        document.addEventListener('keydown', onDocKeydown, true);
        setTimeout(() => {
            document.addEventListener('click', onDocClick, true);
        }, 10);

        activeMenuCleanup = () => {
            document.removeEventListener('click', onDocClick, true);
            document.removeEventListener('keydown', onDocKeydown, true);
            if (menu.parentNode) menu.parentNode.removeChild(menu);
            activeDocDropdown = null;
        };

        activeDocDropdown = { menu, triggerBtn, doc };
    }

    function showDocInTimeline(doc) {
        if (!doc || !doc.vault_id) return;
        const vaultId = doc.vault_id;

        const area = getResolvedArea(doc);
        const house = getResolvedHouse(doc);
        const activeArea = (typeof currentArea !== 'undefined' ? currentArea : (typeof window !== 'undefined' ? window.currentArea : ''));
        const activeHouse = (typeof currentHouse !== 'undefined' ? currentHouse : (typeof window !== 'undefined' ? window.currentHouse : ''));

        if (area && house && (activeArea !== area || activeHouse !== house)) {
            if (typeof currentArea !== 'undefined') currentArea = area;
            if (typeof window !== 'undefined') window.currentArea = area;
            if (typeof currentHouse !== 'undefined') currentHouse = house;
            if (typeof window !== 'undefined') window.currentHouse = house;
            if (typeof window.refreshCurrentTab === 'function') {
                window.refreshCurrentTab(area, house);
            }
        }

        // If a tenant filter is restricting the timeline and doesn't match this document, clear it
        if (typeof window.currentTenant !== 'undefined' && window.currentTenant && doc.primary_tenant && doc.primary_tenant !== window.currentTenant) {
            window.currentTenant = null;
            if (typeof currentTenant !== 'undefined') currentTenant = null;
        }

        // Switch tab to timeline if not currently on timeline
        const tabTimeline = document.getElementById('tab-timeline');
        if (tabTimeline && (typeof currentTab === 'undefined' || currentTab !== 'timeline')) {
            tabTimeline.click();
        }

        const findAndHighlight = (attempts = 0) => {
            const card = document.querySelector(`#document-list [data-vault-id="${vaultId}"]`);
            if (card) {
                if (typeof card.scrollIntoView === 'function') {
                    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                card.classList.add('ring-4', 'ring-blue-500', 'bg-blue-50', 'shadow-md', 'transition-all');
                setTimeout(() => {
                    card.classList.remove('ring-4', 'ring-blue-500', 'bg-blue-50', 'shadow-md');
                }, 2500);

                const docTitle = doc.brief_arabic_title || doc.filename || 'Document';
                if (typeof window.setSelectedDoc === 'function') {
                    window.setSelectedDoc(doc, docTitle, card);
                }
                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
                if (toast) toast('Showing document in timeline.');
            } else if (attempts < 15) {
                setTimeout(() => findAndHighlight(attempts + 1), 100);
            } else {
                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
                if (toast) toast('Document displayed in timeline.');
            }
        };

        setTimeout(() => findAndHighlight(0), 50);
    }

    function showDocInCategories(doc) {
        if (!doc || !doc.vault_id) return;
        const vaultId = doc.vault_id;

        const area = getResolvedArea(doc);
        const house = getResolvedHouse(doc);
        const docTenant = doc.primary_tenant || doc.tenant || null;
        const docCategory = doc.category || '';

        // Register pending folder to open across tab switches and renders
        if (docCategory && typeof window !== 'undefined') {
            window._pendingOpenCategory = docCategory;
        }

        // Switch active tenant if document specifies a primary tenant
        if (docTenant) {
            if (typeof currentTenant !== 'undefined') currentTenant = docTenant;
            if (typeof window !== 'undefined') window.currentTenant = docTenant;
        }

        // Switch tab to categories if not currently on categories
        if (typeof currentTab !== 'undefined') currentTab = 'categories';
        if (typeof window !== 'undefined') window.currentTab = 'categories';

        const tabCategories = document.getElementById('tab-categories');
        const tabTimeline = document.getElementById('tab-timeline');
        if (tabCategories) {
            tabCategories.className = "flex-1 min-w-0 py-1.5 px-2.5 text-xs font-semibold rounded-md bg-white text-blue-600 shadow-xs flex items-center justify-center gap-1.5 transition-all overflow-hidden whitespace-nowrap";
        }
        if (tabTimeline) {
            tabTimeline.className = "flex-1 min-w-0 py-1.5 px-2.5 text-xs font-medium rounded-md text-slate-600 hover:text-slate-900 flex items-center justify-center gap-1.5 transition-all overflow-hidden whitespace-nowrap";
        }

        // Navigate to tenant route if tenant is specified, or trigger categories refresh
        if (area && house && docTenant) {
            const targetTenantId = `${house}_${docTenant}`;
            const targetHash = `#/area/${encodeURIComponent(area)}/house/${encodeURIComponent(house)}/tenant/${encodeURIComponent(targetTenantId)}`;

            if (tabCategories) {
                tabCategories.click();
            }

            if (typeof window !== 'undefined' && window.location && window.location.hash !== targetHash) {
                window.location.hash = targetHash;
            } else if (typeof window !== 'undefined' && typeof window.selectHouse === 'function') {
                window.selectHouse(area, house, docTenant);
            } else if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                window.refreshCurrentTab(area, house);
            } else if (typeof refreshCurrentTab === 'function') {
                refreshCurrentTab(area, house);
            }
        } else {
            if (tabCategories) {
                tabCategories.click();
            } else if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                window.refreshCurrentTab(area, house);
            } else if (typeof refreshCurrentTab === 'function') {
                refreshCurrentTab(area, house);
            }
        }

        // Ensure target category folder is open in categories-view
        if (docCategory && typeof window !== 'undefined' && typeof window.openCategoryFolder === 'function') {
            window.openCategoryFolder(docCategory);
        }

        const findAndHighlight = (attempts = 0) => {
            if (docCategory) {
                if (typeof window !== 'undefined' && typeof window.openCategoryFolder === 'function') {
                    window.openCategoryFolder(docCategory);
                }
                const folderCards = document.querySelectorAll('.category-folder-card');
                for (const folderCard of folderCards) {
                    const cardCat = folderCard.getAttribute('data-category-name');
                    const isMatch = (cardCat === docCategory) || 
                        (typeof window !== 'undefined' && typeof window.isCategoryMatch === 'function' && window.isCategoryMatch(cardCat, docCategory));
                    if (isMatch) {
                        const docsContainer = folderCard.querySelector('.category-docs');
                        if (docsContainer && docsContainer.classList.contains('hidden')) {
                            docsContainer.classList.remove('hidden');
                        }
                    }
                }
            }

            const card = document.querySelector(`#document-list [data-vault-id="${vaultId}"]`);
            if (card) {
                const parentFolder = card.closest('.category-folder-card');
                if (parentFolder) {
                    const folderCat = parentFolder.getAttribute('data-category-name');
                    if (folderCat && typeof window !== 'undefined' && typeof window.openCategoryFolder === 'function') {
                        window.openCategoryFolder(folderCat);
                    }
                }
                const parentDocs = card.closest('.category-docs');
                if (parentDocs && parentDocs.classList.contains('hidden')) {
                    parentDocs.classList.remove('hidden');
                }

                if (typeof card.scrollIntoView === 'function') {
                    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                card.classList.add('ring-4', 'ring-blue-500', 'bg-blue-50', 'shadow-md', 'transition-all');
                setTimeout(() => {
                    card.classList.remove('ring-4', 'ring-blue-500', 'bg-blue-50', 'shadow-md');
                }, 2500);

                const docTitle = doc.brief_arabic_title || doc.filename || 'Document';
                if (typeof window !== 'undefined' && typeof window.setSelectedDoc === 'function') {
                    window.setSelectedDoc(doc, docTitle, card);
                }
                if (typeof window !== 'undefined') {
                    window._pendingOpenCategory = null;
                }
                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
                if (toast) toast('Showing document in categories.');
            } else if (attempts < 30) {
                setTimeout(() => findAndHighlight(attempts + 1), 100);
            } else {
                if (typeof window !== 'undefined') {
                    window._pendingOpenCategory = null;
                }
                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
                if (toast) toast('Document displayed in categories.');
            }
        };

        setTimeout(() => findAndHighlight(0), 50);
    }

    async function handleToggleDocPin(doc) {
        if (!doc || !doc.vault_id) return;
        const isPinned = Boolean(doc.is_manual);
        const area = getResolvedArea(doc);
        const house = getResolvedHouse(doc);
        const isStatic = (typeof isStaticMode !== 'undefined' && isStaticMode) || (typeof window !== 'undefined' && window.isStaticMode);

        if (isPinned) {
            // Unpin document & reset to auto-reconciliation
            if (isStatic) {
                doc.is_manual = 0;
                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
                if (toast) toast('Document unpinned & reset to auto.');
                if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                    await window.refreshCurrentTab(area, house);
                } else if (typeof refreshCurrentTab === 'function') {
                    await refreshCurrentTab(area, house);
                }
                return;
            }

            try {
                const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(doc.vault_id)}/reset-lock`, {
                    method: 'POST'
                });
                if (!res.ok) {
                    // Fallback to PATCH if reset-lock endpoint is unavailable
                    const patchRes = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(doc.vault_id)}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ is_manual: 0 })
                    });
                    if (!patchRes.ok) throw new Error('Failed to unpin document');
                }
                doc.is_manual = 0;
                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
                if (toast) toast('Document unpinned & reset to auto.');
                if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                    await window.refreshCurrentTab(area, house);
                } else if (typeof refreshCurrentTab === 'function') {
                    await refreshCurrentTab(area, house);
                }
            } catch (err) {
                console.error('Error unpinning document:', err);
                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
                if (toast) toast(err.message || 'Failed to unpin document');
            }
        } else {
            // Pin document to preserve manual assignment
            if (isStatic) {
                doc.is_manual = 1;
                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
                if (toast) toast('Document pinned.');
                if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                    await window.refreshCurrentTab(area, house);
                } else if (typeof refreshCurrentTab === 'function') {
                    await refreshCurrentTab(area, house);
                }
                return;
            }

            try {
                const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(doc.vault_id)}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ is_manual: 1 })
                });
                if (!res.ok) throw new Error('Failed to pin document');
                doc.is_manual = 1;
                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
                if (toast) toast('Document pinned.');
                if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                    await window.refreshCurrentTab(area, house);
                } else if (typeof refreshCurrentTab === 'function') {
                    await refreshCurrentTab(area, house);
                }
            } catch (err) {
                console.error('Error pinning document:', err);
                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
                if (toast) toast(err.message || 'Failed to pin document');
            }
        }
    }

    async function handleDeleteSingleDoc(doc) {
        if (!doc || !doc.vault_id) return;

        const canDelete = (typeof window !== 'undefined' && window.authManager) ? window.authManager.hasDeletePermission() : true;
        if (!canDelete) {
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('عذراً: ليس لديك صلاحية حذف الوثائق (قراءة ورفع فقط) • Deletion is restricted for Contributor accounts.', 'error');
            return;
        }

        const docTitle = doc.brief_arabic_title || doc.filename || 'Document';
        const confirmed = (typeof window.confirm === 'function') ? window.confirm(`Are you sure you want to delete "${docTitle}"?`) : true;
        if (!confirmed) return;

        const area = getResolvedArea(doc);
        const house = getResolvedHouse(doc);

        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(doc.vault_id)}`, {
                method: 'DELETE'
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || errData.message || 'Failed to delete document');
            }

            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('Document permanently deleted.');

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
        } catch (err) {
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('Failed to delete document: ' + err.message, 'error');
        }
    }

    function ensureDateModalElements() {
        if (!changeDocDateModal || (typeof document !== 'undefined' && document.body && !document.body.contains(changeDocDateModal))) {
            changeDocDateModal = document.getElementById('change-doc-date-modal');
            changeDocDateInput = document.getElementById('change-doc-date-input');
            changeDocDateTitle = document.getElementById('change-doc-date-title');
            changeDocDateSubtitle = document.getElementById('change-doc-date-subtitle');
            changeDocDateStatus = document.getElementById('change-doc-date-status');
            btnChangeDateCancel = document.getElementById('btn-change-date-cancel');
            btnChangeDateClose = document.getElementById('change-doc-date-close');
            btnChangeDateSave = document.getElementById('btn-change-date-save');
            btnChangeDateSaveText = document.getElementById('btn-change-date-save-text');
        }

        if (!changeDocDateModal && typeof document !== 'undefined' && document.body) {
            const container = document.createElement('div');
            container.id = 'change-doc-date-modal';
            container.className = 'fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center hidden p-4';
            container.innerHTML = `
                <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full flex flex-col overflow-hidden">
                    <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/70">
                        <div>
                            <h3 class="text-base font-bold text-slate-900 tracking-tight" id="change-doc-date-title">Change Document Date</h3>
                            <p class="text-xs text-slate-500 truncate max-w-[260px]" id="change-doc-date-subtitle">Update document date</p>
                        </div>
                        <button id="change-doc-date-close" type="button" class="text-slate-400 hover:text-slate-600 p-1 rounded-lg">✕</button>
                    </div>
                    <div class="p-6 space-y-4">
                        <div>
                            <label for="change-doc-date-input" class="block text-xs font-bold text-slate-700 mb-1.5">Document Date (التاريخ)</label>
                            <input id="change-doc-date-input" type="date" class="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl" />
                        </div>
                        <div id="change-doc-date-status" class="py-1 text-xs font-medium hidden"></div>
                    </div>
                    <div class="px-6 py-4 border-t border-slate-100 bg-slate-50/70 flex justify-end gap-3">
                        <button id="btn-change-date-cancel" type="button" class="px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-xl">Cancel</button>
                        <button id="btn-change-date-save" type="button" class="px-4 py-2 text-xs font-bold text-white bg-purple-600 rounded-xl"><span id="btn-change-date-save-text">Save Date</span></button>
                    </div>
                </div>
            `;
            document.body.appendChild(container);
            changeDocDateModal = container;
            changeDocDateInput = container.querySelector('#change-doc-date-input');
            changeDocDateTitle = container.querySelector('#change-doc-date-title');
            changeDocDateSubtitle = container.querySelector('#change-doc-date-subtitle');
            changeDocDateStatus = container.querySelector('#change-doc-date-status');
            btnChangeDateCancel = container.querySelector('#btn-change-date-cancel');
            btnChangeDateClose = container.querySelector('#change-doc-date-close');
            btnChangeDateSave = container.querySelector('#btn-change-date-save');
            btnChangeDateSaveText = container.querySelector('#btn-change-date-save-text');
        }

        if (btnChangeDateClose) btnChangeDateClose.onclick = closeChangeDocDateModal;
        if (btnChangeDateCancel) btnChangeDateCancel.onclick = closeChangeDocDateModal;
        if (btnChangeDateSave) btnChangeDateSave.onclick = saveChangeDocDate;
    }

    function openChangeDocDateModal(doc) {
        if (!doc) return;
        activeDateModalOriginalDoc = doc;
        activeDateModalDoc = {
            ...doc,
            area_id: getResolvedArea(doc),
            house_id: getResolvedHouse(doc),
        };
        try {
            doc.area_id = activeDateModalDoc.area_id;
            doc.house_id = activeDateModalDoc.house_id;
        } catch (_) {}

        ensureDateModalElements();

        if (changeDocDateSubtitle) {
            changeDocDateSubtitle.textContent = doc.brief_arabic_title || doc.filename || 'Document';
        }

        if (changeDocDateStatus) {
            changeDocDateStatus.classList.add('hidden');
            changeDocDateStatus.textContent = '';
        }

        if (changeDocDateInput) {
            const rawDate = doc.date || doc.primary_date || (Array.isArray(doc.dates) && doc.dates[0]) || '';
            let isoDate = '';
            if (rawDate) {
                const trimmed = String(rawDate).trim();
                const match = trimmed.match(/^\d{4}-\d{2}-\d{2}/);
                isoDate = match ? match[0] : trimmed;
            }
            changeDocDateInput.value = isoDate;
            changeDocDateInput.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    saveChangeDocDate();
                }
            };
        }

        if (btnChangeDateSave) btnChangeDateSave.disabled = false;
        if (btnChangeDateSaveText) btnChangeDateSaveText.textContent = 'Save Date';

        if (changeDocDateModal) {
            changeDocDateModal.classList.remove('hidden');
            changeDocDateModal.classList.add('flex');
            changeDocDateModal.style.display = 'flex';
        }

        if (changeDocDateInput) {
            setTimeout(() => {
                try { changeDocDateInput.focus(); } catch (_) {}
            }, 50);
        }
    }

    function closeChangeDocDateModal() {
        ensureDateModalElements();
        if (changeDocDateModal) {
            changeDocDateModal.classList.add('hidden');
            changeDocDateModal.classList.remove('flex');
            changeDocDateModal.style.display = 'none';
        }
        activeDateModalDoc = null;
        activeDateModalOriginalDoc = null;
    }

    async function saveChangeDocDate() {
        if (!activeDateModalDoc || !activeDateModalDoc.vault_id) return;
        ensureDateModalElements();

        const newDate = changeDocDateInput ? changeDocDateInput.value.trim() : '';

        if (btnChangeDateSave) btnChangeDateSave.disabled = true;
        if (btnChangeDateSaveText) btnChangeDateSaveText.textContent = 'Saving...';

        const area = getResolvedArea(activeDateModalDoc);
        const house = getResolvedHouse(activeDateModalDoc);
        const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);

        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(activeDateModalDoc.vault_id)}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    primary_date: newDate,
                    is_manual: 1
                })
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || errData.error || errData.message || 'Failed to update document date');
            }

            // Update in-memory references
            activeDateModalDoc.primary_date = newDate;
            activeDateModalDoc.date = newDate;
            activeDateModalDoc.dates = newDate ? [newDate] : [];
            activeDateModalDoc.is_manual = 1;

            if (activeDateModalOriginalDoc) {
                activeDateModalOriginalDoc.primary_date = newDate;
                activeDateModalOriginalDoc.date = newDate;
                activeDateModalOriginalDoc.dates = newDate ? [newDate] : [];
                activeDateModalOriginalDoc.is_manual = 1;
            }

            if (activeDocDropdown && activeDocDropdown.doc && activeDocDropdown.doc.vault_id === activeDateModalDoc.vault_id) {
                activeDocDropdown.doc.primary_date = newDate;
                activeDocDropdown.doc.date = newDate;
                activeDocDropdown.doc.dates = newDate ? [newDate] : [];
                activeDocDropdown.doc.is_manual = 1;
            }

            // Update DOM date badge in Categories View and Timeline View
            const docCards = document.querySelectorAll(`div[data-vault-id="${activeDateModalDoc.vault_id}"]`);
            docCards.forEach(card => {
                const dateBadge = card.querySelector('.doc-date-badge');
                if (dateBadge) {
                    dateBadge.textContent = newDate || 'No Date';
                }
                const timelineDateSpan = card.querySelector('.font-mono span');
                if (timelineDateSpan) {
                    timelineDateSpan.textContent = newDate || 'No Date';
                }
                card.setAttribute('data-date', newDate || '0000-00-00');
            });

            // If on timeline, immediately re-adjust document position in the timeline
            const isTimeline = (typeof currentTab !== 'undefined' && currentTab === 'timeline') ||
                               (typeof window !== 'undefined' && window.currentTab === 'timeline');
            if (isTimeline) {
                if (typeof window !== 'undefined' && typeof window.reorderTimelineCard === 'function') {
                    window.reorderTimelineCard(activeDateModalDoc.vault_id, newDate);
                } else if (typeof reorderTimelineCard === 'function') {
                    reorderTimelineCard(activeDateModalDoc.vault_id, newDate);
                }
            }

            if (toast) {
                toast('Document date updated successfully', 'success');
            }

            closeChangeDocDateModal();

            try {
                if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                    await window.refreshCurrentTab(area, house);
                } else if (typeof refreshCurrentTab === 'function') {
                    await refreshCurrentTab(area, house);
                }
            } catch (refErr) {
                console.warn('Refresh after date change warning:', refErr);
            }
        } catch (err) {
            console.error('Failed to save document date:', err);
            if (changeDocDateStatus) {
                changeDocDateStatus.textContent = err.message || 'Error updating date';
                changeDocDateStatus.className = 'py-1 text-xs font-medium text-rose-600';
                changeDocDateStatus.classList.remove('hidden');
            }
            if (toast) {
                toast(err.message || 'Error updating date', 'error');
            }
            if (btnChangeDateSave) btnChangeDateSave.disabled = false;
            if (btnChangeDateSaveText) btnChangeDateSaveText.textContent = 'Save Date';
        }
    }

    // ── Document Merge Modal Helpers & Handlers ─────────────────────────────
    function populateMergeCategoryOptions(selectedCategory) {
        if (!mergeTargetCategory) return;
        mergeTargetCategory.innerHTML = '';
        const existingFolderNames = new Set(STANDARD_FOLDERS);
        if (typeof currentCategories !== 'undefined' && currentCategories) {
            currentCategories.forEach(c => {
                const count = typeof c.document_count === 'number'
                    ? c.document_count
                    : (Array.isArray(c.documents) ? c.documents.length : 0);
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
            mergeTargetCategory.appendChild(opt);
        });

        const newOpt = document.createElement('option');
        newOpt.value = '__NEW_CUSTOM_FOLDER__';
        newOpt.textContent = '➕ Create new folder...';
        mergeTargetCategory.appendChild(newOpt);

        mergeTargetCategory.onchange = () => {
            if (mergeTargetCategory.value === '__NEW_CUSTOM_FOLDER__') {
                if (mergeCustomCatContainer) mergeCustomCatContainer.classList.remove('hidden');
                if (mergeCustomCatInput) mergeCustomCatInput.focus();
            } else {
                if (mergeCustomCatContainer) mergeCustomCatContainer.classList.add('hidden');
            }
        };
    }

    async function populateMergeTenantOptions(selectedTenantId, selectedTenantName) {
        if (!mergeTargetTenant) return;
        mergeTargetTenant.innerHTML = '';
        try {
            const area = getResolvedArea(activeMergeDocs[0]);
            const house = getResolvedHouse(activeMergeDocs[0]);
            if (!area || !house) return;
            const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/tenants`);
            if (!res.ok) return;
            const tenants = await res.json();
            const seen = new Set();

            const unassignedOpt = document.createElement('option');
            unassignedOpt.value = '';
            unassignedOpt.textContent = '-- No Specific Tenant (General / عام) --';
            mergeTargetTenant.appendChild(unassignedOpt);

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
                mergeTargetTenant.appendChild(opt);
            });
        } catch (err) {
            console.error('Failed to load tenants for merge modal:', err);
        }
    }

    function populateMergeAddDocSelect() {
        if (!mergeAddDocSelect) return;
        mergeAddDocSelect.innerHTML = '<option value="">-- إضافة مستند آخر للدمج / Select doc to add --</option>';
        const activeVaultIds = new Set(activeMergeDocs.map(d => d.vault_id));
        const cats = (typeof currentCategories !== 'undefined' ? currentCategories : (typeof window !== 'undefined' ? window.currentCategories : [])) || [];
        
        cats.forEach(c => {
            if (!c.documents) return;
            c.documents.forEach(doc => {
                if (doc.vault_id && !activeVaultIds.has(doc.vault_id)) {
                    const opt = document.createElement('option');
                    opt.value = doc.vault_id;
                    const docTitle = doc.brief_arabic_title || doc.title || doc.file_name || doc.filename || 'Document';
                    const pages = doc.page_count || doc.pages_count || 1;
                    opt.textContent = `[${c.name || 'عام'}] ${docTitle} (${pages} ${pages === 1 ? 'page' : 'pages'})`;
                    opt.dataset.doc = JSON.stringify(doc);
                    mergeAddDocSelect.appendChild(opt);
                }
            });
        });
    }

    function showMergeStep(step) {
        if (mergeStepReorder) mergeStepReorder.classList.toggle('hidden', step !== 'reorder');
        if (mergeStepSave) mergeStepSave.classList.toggle('hidden', step !== 'save');
    }

    function updateMergeOrderSummary() {
        if (mergeOrderSummary) {
            if (activeMergeDocs.length === 2) {
                const t1 = activeMergeDocs[0].brief_arabic_title || activeMergeDocs[0].title || 'وثيقة 1';
                const t2 = activeMergeDocs[1].brief_arabic_title || activeMergeDocs[1].title || 'وثيقة 2';
                mergeOrderSummary.textContent = `${t1} → ${t2}`;
            } else if (activeMergeDocs.length > 2) {
                mergeOrderSummary.textContent = activeMergeDocs.map((d, i) => `${i + 1}. ${d.brief_arabic_title || d.title || 'وثيقة'}`).join(' → ');
            } else if (activeMergeDocs.length === 1) {
                mergeOrderSummary.textContent = activeMergeDocs[0].brief_arabic_title || activeMergeDocs[0].title || 'وثيقة 1';
            } else {
                mergeOrderSummary.textContent = '';
            }
        }
        const totalPages = activeMergeDocs.reduce((acc, d) => acc + (d.page_count || d.pages_count || 1), 0);
        if (mergeDocsCountBadge) {
            mergeDocsCountBadge.textContent = `${activeMergeDocs.length} ${activeMergeDocs.length === 1 ? 'doc' : 'docs'} • ${totalPages} pages`;
        }
    }

    function handleSwapMergeDocs() {
        if (activeMergeDocs.length < 2) return;
        const tmp = activeMergeDocs[0];
        activeMergeDocs[0] = activeMergeDocs[1];
        activeMergeDocs[1] = tmp;

        const newFirst = activeMergeDocs[0];
        if (mergeTargetTitle) {
            mergeTargetTitle.value = newFirst.brief_arabic_title || newFirst.title || newFirst.file_name || newFirst.filename || 'مستند مدمج';
        }
        const newCat = newFirst.category || newFirst.folder || activeMergeFallbackCategory || '01 - بيانات أساسية';
        if (mergeTargetCategory) {
            mergeTargetCategory.value = newCat;
        }
        if (mergeTargetTenant && newFirst.tenant_id != null) {
            mergeTargetTenant.value = String(newFirst.tenant_id);
        }
        if (mergeTargetDate) {
            const rawDate = newFirst.primary_date || newFirst.date || (newFirst.dates && newFirst.dates[0]);
            if (rawDate) mergeTargetDate.value = String(rawDate).substring(0, 10);
        }

        updateMergeOrderSummary();
    }

    function handleReorderContinue() {
        if (activeMergeDocs.length < 2) {
            if (mergeDocsStatus) {
                mergeDocsStatus.textContent = 'يرجى اختيار وثيقتين على الأقل للدمج / Please select at least 2 documents to merge';
                mergeDocsStatus.className = 'p-3 rounded-xl text-xs font-medium bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-300 border border-rose-200 dark:border-rose-900/60';
                mergeDocsStatus.classList.remove('hidden');
            }
            return;
        }

        const firstDoc = activeMergeDocs[0];
        if (mergeTargetTitle) {
            mergeTargetTitle.value = firstDoc.brief_arabic_title || firstDoc.title || firstDoc.file_name || firstDoc.filename || 'مستند مدمج';
        }
        const targetCat = firstDoc.category || firstDoc.folder || activeMergeFallbackCategory || '01 - بيانات أساسية';
        if (mergeTargetCategory) {
            mergeTargetCategory.value = targetCat;
        }
        if (mergeTargetTenant && firstDoc.tenant_id != null) {
            mergeTargetTenant.value = String(firstDoc.tenant_id);
        }
        if (mergeTargetDate) {
            const rawDate = firstDoc.primary_date || firstDoc.date || (firstDoc.dates && firstDoc.dates[0]);
            if (rawDate) mergeTargetDate.value = String(rawDate).substring(0, 10);
        }

        updateMergeOrderSummary();
        showMergeStep('save');
        if (btnMergeSaveBack) btnMergeSaveBack.classList.remove('hidden');
        if (btnMergeSwapOrder) btnMergeSwapOrder.classList.toggle('hidden', activeMergeDocs.length !== 2);
    }

    function handleSaveBack() {
        showMergeStep('reorder');
        renderMergeDocsList();
    }

    function renderMergeDocsList() {
        if (!mergeDocsList) return;
        mergeDocsList.innerHTML = '';

        updateMergeOrderSummary();

        if (activeMergeDocs.length === 0) {
            const emptyEl = document.createElement('div');
            emptyEl.className = 'p-3 text-xs text-slate-400 text-center';
            emptyEl.textContent = 'لا توجد مستندات محددة للدمج / No documents selected';
            mergeDocsList.appendChild(emptyEl);
            return;
        }

        activeMergeDocs.forEach((doc, idx) => {
            const row = document.createElement('div');
            row.className = 'flex items-center justify-between p-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-2xs gap-2 transition-all';

            const title = doc.brief_arabic_title || doc.title || doc.file_name || doc.filename || 'وثيقة';
            const cat = doc.category || doc.folder || activeMergeFallbackCategory || 'عام';
            const tenant = doc.tenant || doc.tenant_name || '';
            const pages = doc.page_count || doc.pages_count || 1;

            row.innerHTML = `
                <div class="flex items-center gap-2 min-w-0 flex-1">
                    <div class="flex flex-col gap-0.5 flex-shrink-0">
                        <button type="button" class="btn-merge-up w-5 h-4 flex items-center justify-center rounded bg-slate-100 dark:bg-slate-700 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 disabled:opacity-25 disabled:pointer-events-none text-[9px] cursor-pointer transition-colors" ${idx === 0 ? 'disabled' : ''} title="Move Earlier • تقديم">▲</button>
                        <button type="button" class="btn-merge-down w-5 h-4 flex items-center justify-center rounded bg-slate-100 dark:bg-slate-700 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 disabled:opacity-25 disabled:pointer-events-none text-[9px] cursor-pointer transition-colors" ${idx === activeMergeDocs.length - 1 ? 'disabled' : ''} title="Move Later • تأخير">▼</button>
                    </div>
                    <span class="w-6 h-6 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 font-mono text-xs font-bold flex items-center justify-center flex-shrink-0 border border-emerald-100 dark:border-emerald-800/60">${idx + 1}</span>
                    <div class="min-w-0 flex-1">
                        <div class="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate" title="${title}">${title}</div>
                        <div class="flex items-center gap-1.5 mt-0.5 text-[10px] text-slate-500 dark:text-slate-400">
                            <span class="truncate max-w-[120px]">${cat}</span>
                            ${tenant ? `<span>•</span><span class="truncate max-w-[100px] text-purple-600 dark:text-purple-400">${tenant}</span>` : ''}
                            <span>•</span>
                            <span class="font-mono">${pages} ${pages === 1 ? 'page' : 'pages'}</span>
                        </div>
                    </div>
                </div>
                <button type="button" class="btn-merge-remove text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 p-1 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/50 transition-colors cursor-pointer flex-shrink-0" title="Remove from merge list">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
            `;

            const btnUp = row.querySelector('.btn-merge-up');
            if (btnUp) btnUp.onclick = () => moveMergeDocUp(idx);

            const btnDown = row.querySelector('.btn-merge-down');
            if (btnDown) btnDown.onclick = () => moveMergeDocDown(idx);

            const btnRemove = row.querySelector('.btn-merge-remove');
            if (btnRemove) btnRemove.onclick = () => removeMergeDoc(idx);

            mergeDocsList.appendChild(row);
        });
    }

    function moveMergeDocUp(index) {
        if (index <= 0 || index >= activeMergeDocs.length) return;
        const tmp = activeMergeDocs[index];
        activeMergeDocs[index] = activeMergeDocs[index - 1];
        activeMergeDocs[index - 1] = tmp;
        renderMergeDocsList();
    }

    function moveMergeDocDown(index) {
        if (index < 0 || index >= activeMergeDocs.length - 1) return;
        const tmp = activeMergeDocs[index];
        activeMergeDocs[index] = activeMergeDocs[index + 1];
        activeMergeDocs[index + 1] = tmp;
        renderMergeDocsList();
    }

    function removeMergeDoc(index) {
        if (index < 0 || index >= activeMergeDocs.length) return;
        activeMergeDocs.splice(index, 1);
        if (activeMergeDocs.length < 2) {
            closeMergeModal();
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('تم إلغاء الدمج لقلة المستندات المحددة / Merge cancelled: fewer than 2 documents', 'warning');
            return;
        }
        renderMergeDocsList();
    }

    async function openMergeModal(initialDocs, fallbackCategory = null) {
        if (!mergeDocsModal) return;

        activeMergeDocs = Array.isArray(initialDocs) ? [...initialDocs] : (initialDocs ? [initialDocs] : []);
        initialMergeCount = activeMergeDocs.length;
        activeMergeFallbackCategory = fallbackCategory;

        if (activeMergeDocs.length < 2) {
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('يرجى تحديد وثيقتين على الأقل للدمج / Please select at least 2 documents to merge', 'warning');
            return;
        }

        if (mergeDocsStatus) {
            mergeDocsStatus.textContent = '';
            mergeDocsStatus.classList.add('hidden');
        }

        const firstDoc = activeMergeDocs[0] || null;
        const defaultCat = (firstDoc && (firstDoc.category || firstDoc.folder)) || fallbackCategory || '01 - بيانات أساسية';
        populateMergeCategoryOptions(defaultCat);
        if (mergeCustomCatContainer) mergeCustomCatContainer.classList.add('hidden');
        if (mergeCustomCatInput) mergeCustomCatInput.value = '';

        if (mergeDeleteSources) {
            const isRestricted = Boolean(typeof window !== 'undefined' && window.authManager && window.authManager.currentUser && !window.authManager.hasDeletePermission());
            const canDelete = !isRestricted;
            mergeDeleteSources.checked = canDelete;
            mergeDeleteSources.disabled = !canDelete;
            const container = mergeDeleteSources.closest('label') || mergeDeleteSources.parentElement;
            if (container) {
                container.title = isRestricted ? 'حذف المستندات المصدر محجوب للموظفين • Deletion restricted for Contributors' : '';
                container.classList.toggle('opacity-50', isRestricted);
            }
        }

        const defaultTenantId = firstDoc ? (firstDoc.tenant_id || null) : null;
        const defaultTenantName = firstDoc ? (firstDoc.tenant || firstDoc.tenant_name || null) : null;
        await populateMergeTenantOptions(defaultTenantId, defaultTenantName);

        // Pre-fill target title with first doc's name by default
        if (mergeTargetTitle) {
            mergeTargetTitle.value = firstDoc ? (firstDoc.brief_arabic_title || firstDoc.title || firstDoc.file_name || firstDoc.filename || 'مستند مدمج') : 'مستند مدمج';
        }

        // Pre-fill target date inheriting from first doc
        if (mergeTargetDate) {
            const rawDate = firstDoc ? (firstDoc.primary_date || firstDoc.date || (firstDoc.dates && firstDoc.dates[0])) : null;
            mergeTargetDate.value = rawDate ? String(rawDate).substring(0, 10) : new Date().toISOString().substring(0, 10);
        }

        if (mergeTargetNotes) {
            mergeTargetNotes.value = '';
        }

        updateMergeOrderSummary();

        if (activeMergeDocs.length === 2) {
            showMergeStep('save');
            if (btnMergeSaveBack) btnMergeSaveBack.classList.add('hidden');
            if (mergeOrderBanner) mergeOrderBanner.classList.remove('hidden');
            if (btnMergeSwapOrder) btnMergeSwapOrder.classList.remove('hidden');
        } else {
            showMergeStep('reorder');
            renderMergeDocsList();
            if (btnMergeSaveBack) btnMergeSaveBack.classList.remove('hidden');
        }

        mergeDocsModal.classList.remove('hidden');
        mergeDocsModal.classList.add('flex');
    }

    function closeMergeModal() {
        if (!mergeDocsModal) return;
        mergeDocsModal.classList.add('hidden');
        mergeDocsModal.classList.remove('flex');
        activeMergeDocs = [];
        initialMergeCount = 0;
        if (mergeDocsStatus) {
            mergeDocsStatus.textContent = '';
            mergeDocsStatus.classList.add('hidden');
        }
        if (btnMergeDocsConfirm) btnMergeDocsConfirm.disabled = false;
        if (mergeDocsSpinner) mergeDocsSpinner.classList.add('hidden');
    }

    async function handleMergeDocsSubmit() {
        if (activeMergeDocs.length < 2) {
            if (mergeDocsStatus) {
                mergeDocsStatus.textContent = 'يرجى اختيار وثيقتين على الأقل للدمج / Please select at least 2 documents to merge';
                mergeDocsStatus.className = 'p-3 rounded-xl text-xs font-medium bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-300 border border-rose-200 dark:border-rose-900/60';
                mergeDocsStatus.classList.remove('hidden');
            }
            return;
        }

        const title = mergeTargetTitle ? mergeTargetTitle.value.trim() : '';
        if (!title) {
            if (mergeTargetTitle) mergeTargetTitle.focus();
            if (mergeDocsStatus) {
                mergeDocsStatus.textContent = 'يرجى إدخال عنوان للمستند المدمج / Target document title is required';
                mergeDocsStatus.className = 'p-3 rounded-xl text-xs font-medium bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-300 border border-rose-200 dark:border-rose-900/60';
                mergeDocsStatus.classList.remove('hidden');
            }
            return;
        }

        let cat = mergeTargetCategory ? mergeTargetCategory.value : '';
        if (cat === '__NEW_CUSTOM_FOLDER__') {
            cat = mergeCustomCatInput ? mergeCustomCatInput.value.trim() : '';
        }
        if (!cat) {
            if (mergeDocsStatus) {
                mergeDocsStatus.textContent = 'يرجى اختيار المجلد المستهدف / Target category folder is required';
                mergeDocsStatus.className = 'p-3 rounded-xl text-xs font-medium bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-300 border border-rose-200 dark:border-rose-900/60';
                mergeDocsStatus.classList.remove('hidden');
            }
            return;
        }

        const area = getResolvedArea(activeMergeDocs[0]);
        const house = getResolvedHouse(activeMergeDocs[0]);
        if (!area || !house) {
            if (mergeDocsStatus) {
                mergeDocsStatus.textContent = 'لا يمكن تحديد المنطقة والمنزل الحاليين / Cannot resolve active area and house';
                mergeDocsStatus.className = 'p-3 rounded-xl text-xs font-medium bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-300 border border-rose-200 dark:border-rose-900/60';
                mergeDocsStatus.classList.remove('hidden');
            }
            return;
        }

        const tenantVal = mergeTargetTenant && mergeTargetTenant.value ? parseInt(mergeTargetTenant.value, 10) : null;
        const dateVal = mergeTargetDate && mergeTargetDate.value ? mergeTargetDate.value : null;
        const notesVal = mergeTargetNotes && mergeTargetNotes.value ? mergeTargetNotes.value.trim() : null;
        const isRestricted = (typeof window !== 'undefined' && window.authManager && window.authManager.currentUser && !window.authManager.hasDeletePermission());
        const canDelete = !isRestricted;
        const deleteSources = canDelete && mergeDeleteSources ? mergeDeleteSources.checked : false;

        const payload = {
            vault_ids: activeMergeDocs.map(d => d.vault_id),
            target_title: title,
            target_category: cat,
            target_tenant_id: tenantVal,
            target_date: dateVal,
            target_notes: notesVal,
            delete_sources: deleteSources
        };

        if (btnMergeDocsConfirm) btnMergeDocsConfirm.disabled = true;
        if (mergeDocsSpinner) mergeDocsSpinner.classList.remove('hidden');
        if (mergeDocsStatus) mergeDocsStatus.classList.add('hidden');

        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/merge`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || errData.error || errData.message || 'Failed to merge documents');
            }

            const data = await res.json();
            closeMergeModal();

            if (typeof window !== 'undefined' && typeof window.deselectAllDocs === 'function') {
                window.deselectAllDocs();
            }

            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) {
                toast(`تم دمج ${data.total_pages || ''} صفحة في مستند جديد بنجاح!`, 'success');
            }

            if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                await window.refreshCurrentTab(area, house);
            }
            if (typeof window !== 'undefined' && typeof window.loadTree === 'function') {
                await window.loadTree();
            }

            if (data.merged_vault_id && typeof window !== 'undefined' && typeof window.openDocument === 'function') {
                window.openDocument(data.merged_vault_id, data.merged_category || cat, false);
            }
        } catch (err) {
            console.error('Merge error:', err);
            if (mergeDocsStatus) {
                mergeDocsStatus.textContent = err.message || 'Failed to merge documents';
                mergeDocsStatus.className = 'p-3 rounded-xl text-xs font-medium bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-300 border border-rose-200 dark:border-rose-900/60';
                mergeDocsStatus.classList.remove('hidden');
            }
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) {
                toast(err.message || 'Failed to merge documents', 'error');
            }
        } finally {
            if (btnMergeDocsConfirm) btnMergeDocsConfirm.disabled = false;
            if (mergeDocsSpinner) mergeDocsSpinner.classList.add('hidden');
        }
    }

    // Expose globals
    window.openDocModal = openDocModal;
    window.closeDocModal = closeDocModal;
    window.openDocDropdownMenu = openDocDropdownMenu;
    window.closeDocDropdownMenu = closeDocDropdownMenu;
    window.openChangeDocDateModal = openChangeDocDateModal;
    window.closeChangeDocDateModal = closeChangeDocDateModal;
    window.saveChangeDocDate = saveChangeDocDate;
    window.openMergeModal = openMergeModal;
    window.closeMergeModal = closeMergeModal;
    window.handleMergeDocsSubmit = handleMergeDocsSubmit;
    window.renderMergeDocsList = renderMergeDocsList;
    window.moveMergeDocUp = moveMergeDocUp;
    window.moveMergeDocDown = moveMergeDocDown;
    window.removeMergeDoc = removeMergeDoc;
    window.getActiveMergeDocs = () => activeMergeDocs;
    window.showDocInTimeline = showDocInTimeline;
    window.showDocInCategories = showDocInCategories;
    window.handleToggleDocPin = handleToggleDocPin;
    window.handleDeleteSingleDoc = handleDeleteSingleDoc;
    window.handleDeleteDoc = handleDeleteDoc;
    window.resetDeleteButton = resetDeleteButton;
    window.getIsDeleteArmed = getIsDeleteArmed;
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
    window.handleSwapMergeDocs = handleSwapMergeDocs;
    window.showMergeStep = showMergeStep;
    window.updateMergeOrderSummary = updateMergeOrderSummary;
    window.handleReorderContinue = handleReorderContinue;
    window.handleSaveBack = handleSaveBack;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            initDocManager,
            openDocModal,
            closeDocModal,
            openDocDropdownMenu,
            closeDocDropdownMenu,
            openChangeDocDateModal,
            closeChangeDocDateModal,
            saveChangeDocDate,
            openMergeModal,
            closeMergeModal,
            handleMergeDocsSubmit,
            renderMergeDocsList,
            moveMergeDocUp,
            moveMergeDocDown,
            removeMergeDoc,
            getActiveMergeDocs: () => activeMergeDocs,
            handleSwapMergeDocs,
            showMergeStep,
            updateMergeOrderSummary,
            handleReorderContinue,
            handleSaveBack,
            showDocInTimeline,
            showDocInCategories,
            handleToggleDocPin,
            handleDeleteSingleDoc,
            handleDeleteDoc,
            resetDeleteButton,
            getIsDeleteArmed,
            setDocModalMode,
            saveDocModal,
            resetDocLock,
            STANDARD_FOLDERS,
            getAreaFromHash,
            getHouseFromHash,
            getResolvedArea,
            getResolvedHouse,
            handleCategoryDrop,
            handleCategoryDragOver,
            handleDocDragStart,
            handleDocDragEnd,
            handleTenantTreeDrop,
            handleTenantTreeDragOver,
            getActiveSelectedDocIds,
        };
    }

    if (typeof window !== 'undefined') {
        window.addEventListener('auth:user-changed', () => {
            const btnDocDelete = document.getElementById('btn-doc-delete');
            if (btnDocDelete) {
                const canDelete = window.authManager ? window.authManager.hasDeletePermission() : true;
                btnDocDelete.classList.toggle('hidden', !canDelete);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDocManager);
    } else {
        initDocManager();
    }
})();


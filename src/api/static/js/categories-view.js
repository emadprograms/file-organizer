// ── Categories / Folder Hierarchy Component ──────────────────────────────
(function() {
    const FOLDER_PREFIXES = {
        "بيانات أساسية": "01",
        "بيانات شخصية": "02",
        "أمر تخصيص": "03",
        "محضر تسليم مفتاح": "04",
        "عقود": "05",
        "كهرباء وماء": "06",
        "استقطاع إيجار": "07",
        "وقف استقطاع بدل": "08",
        "إشعارات": "09",
        "صيانة": "10",
        "صور ومعاينات": "11",
        "تعديلات": "12",
        "رسائل متنوعة": "13"
    };

    const EMPTY_FOLDER_SVG = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>`;

    const FOLDER_ICONS = {
        // 01 - بيانات أساسية: Property/Home icon (base master data)
        "01": `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>`,
        // 02 - بيانات شخصية: User profile icon (personal identity & civil data)
        "02": `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>`,
        // 03 - أمر تخصيص: Official decree clipboard check / allocation certificate
        "03": `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>`,
        // 04 - محضر تسليم مفتاح: Key icon (key handover & receipt record)
        "04": `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/></svg>`,
        // 05 - عقود: Contract / legal document text icon
        "05": `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>`,
        // 06 - كهرباء وماء: Lightning bolt utility icon (electricity & water)
        "06": `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>`,
        // 07 - استقطاع إيجار: Banknote / cash deduction icon
        "07": `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/></svg>`,
        // 08 - وقف استقطاع بدل: Stop / ban deduction icon
        "08": `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"/></svg>`,
        // 09 - إشعارات: Notification bell icon
        "09": `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>`,
        // 10 - صيانة: Maintenance wrench icon
        "10": `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/></svg>`,
        // 11 - صور ومعاينات: Camera photos & inspection icon
        "11": `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg>`,
        // 12 - تعديلات: Edit pencil / renovation alteration icon
        "12": `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>`,
        // 13 - رسائل متنوعة: Mail / correspondence envelope icon
        "13": `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>`
    };

    function getFolderIconSvg(name) {
        if (!name) return EMPTY_FOLDER_SVG;
        const clean = String(name).trim();

        // 1. Check numeric prefix (e.g., "01 - ...", "05 - ...", "14 - ...")
        const match = clean.match(/^(\d+)\s*-\s*(.+)$/);
        if (match) {
            const num = parseInt(match[1], 10);
            if (num >= 1 && num <= 13) {
                const key = String(num).padStart(2, '0');
                if (FOLDER_ICONS[key]) return FOLDER_ICONS[key];
            } else {
                // 14 onwards: user custom folder -> empty folder icon
                return EMPTY_FOLDER_SVG;
            }
        }

        // 2. Check if clean name matches standard categories (without prefix)
        if (FOLDER_PREFIXES[clean]) {
            const key = FOLDER_PREFIXES[clean];
            if (FOLDER_ICONS[key]) return FOLDER_ICONS[key];
        }

        for (const [folderName, prefix] of Object.entries(FOLDER_PREFIXES)) {
            if (clean.endsWith(folderName) || clean.includes(folderName)) {
                if (FOLDER_ICONS[prefix]) return FOLDER_ICONS[prefix];
            }
        }

        // Custom folder (14 onwards or unlisted custom name)
        return EMPTY_FOLDER_SVG;
    }

    const selectedDocIds = new Set();

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function getNoteSnippet(notes, maxLen = 14) {
        if (typeof window !== 'undefined' && typeof window.getNoteSnippet === 'function') return window.getNoteSnippet(notes, maxLen);
        if (!notes || typeof notes !== 'string') return '';
        const clean = notes.trim().replace(/\s+/g, ' ');
        if (!clean) return '';
        if (clean.length <= maxLen) return clean;
        return clean.substring(0, maxLen).trim() + '…';
    }

    function isStandardCategoryName(name) {
        if (!name) return false;
        const clean = name.trim();
        if (FOLDER_PREFIXES[clean]) return true;
        for (const [folderName, prefix] of Object.entries(FOLDER_PREFIXES)) {
            if (clean === `${prefix} - ${folderName}` || clean.endsWith(folderName)) return true;
        }
        return false;
    }

    function getSelectedDocIds() {
        return selectedDocIds;
    }

    function toggleDocSelection(vaultId, isSelected) {
        if (!vaultId) return;
        if (isSelected) {
            selectedDocIds.add(vaultId);
        } else {
            selectedDocIds.delete(vaultId);
        }
        const globalBtn = document.getElementById('btn-toggle-select-all-categories');
        if (globalBtn) {
            const allDocCbs = document.querySelectorAll('.doc-select-checkbox');
            const allChecked = allDocCbs.length > 0 && Array.from(allDocCbs).every(cb => cb.checked);
            globalBtn.textContent = allChecked ? 'Deselect All' : 'Select All';
        }
        updateBatchActionBar();
    }

    function updateFolderCheckboxState(card, cat) {
        const folderCb = card ? card.querySelector('.folder-select-checkbox') : null;
        if (!folderCb) return;
        const docs = (cat && cat.documents) ? cat.documents : [];
        if (docs.length === 0) {
            folderCb.checked = false;
            folderCb.indeterminate = false;
            return;
        }
        const docIds = docs.map(d => d.vault_id).filter(Boolean);
        const selectedCount = docIds.filter(id => selectedDocIds.has(id)).length;
        if (selectedCount === 0) {
            folderCb.checked = false;
            folderCb.indeterminate = false;
        } else if (selectedCount === docIds.length) {
            folderCb.checked = true;
            folderCb.indeterminate = false;
        } else {
            folderCb.checked = false;
            folderCb.indeterminate = true;
        }
    }

    function toggleSelectAllInFolder(cat, card) {
        if (!cat.documents || cat.documents.length === 0) return;
        const docIds = cat.documents.map(d => d.vault_id).filter(Boolean);
        const allSelected = docIds.every(id => selectedDocIds.has(id));

        if (allSelected) {
            docIds.forEach(id => selectedDocIds.delete(id));
        } else {
            docIds.forEach(id => selectedDocIds.add(id));
            const docsContainer = card.querySelector('.category-docs');
            if (docsContainer) {
                docsContainer.classList.remove('hidden');
            }
        }

        const cbs = card.querySelectorAll('.doc-select-checkbox');
        cbs.forEach(cb => {
            const vid = cb.getAttribute('data-vault-id');
            cb.checked = selectedDocIds.has(vid);
        });

        const folderCb = card.querySelector('.folder-select-checkbox');
        if (folderCb) {
            folderCb.checked = !allSelected;
            folderCb.indeterminate = false;
        }

        const selectAllBtn = card.querySelector('.btn-select-all-folder');
        if (selectAllBtn) {
            selectAllBtn.textContent = allSelected ? 'Select All' : 'Deselect All';
        }

        const globalBtn = document.getElementById('btn-toggle-select-all-categories');
        if (globalBtn) {
            const allDocCbs = document.querySelectorAll('.doc-select-checkbox');
            const allChecked = allDocCbs.length > 0 && Array.from(allDocCbs).every(cb => cb.checked);
            globalBtn.textContent = allChecked ? 'Deselect All' : 'Select All';
        }

        updateBatchActionBar();
    }

    function toggleSelectAllGlobal(categories) {
        const allDocIds = [];
        categories.forEach(c => {
            if (c.documents) {
                c.documents.forEach(d => {
                    if (d.vault_id) allDocIds.push(d.vault_id);
                });
            }
        });
        if (allDocIds.length === 0) return;
        const allSelected = allDocIds.every(id => selectedDocIds.has(id));
        if (allSelected) {
            deselectAllDocs();
        } else {
            allDocIds.forEach(id => selectedDocIds.add(id));
            const cbs = document.querySelectorAll('.doc-select-checkbox');
            cbs.forEach(cb => { cb.checked = true; });
            const folderCbs = document.querySelectorAll('.folder-select-checkbox');
            folderCbs.forEach(cb => { cb.checked = true; cb.indeterminate = false; });
            const folderBtns = document.querySelectorAll('.btn-select-all-folder');
            folderBtns.forEach(btn => { btn.textContent = 'Deselect All'; });
            const globalBtn = document.getElementById('btn-toggle-select-all-categories');
            if (globalBtn) globalBtn.textContent = 'Deselect All';
            updateBatchActionBar();
        }
    }

    function deselectAllDocs() {
        selectedDocIds.clear();
        const cbs = document.querySelectorAll('.doc-select-checkbox');
        cbs.forEach(cb => { cb.checked = false; });
        const folderCbs = document.querySelectorAll('.folder-select-checkbox');
        folderCbs.forEach(cb => { cb.checked = false; cb.indeterminate = false; });
        const folderBtns = document.querySelectorAll('.btn-select-all-folder');
        folderBtns.forEach(btn => { btn.textContent = 'Select All'; });
        const globalBtn = document.getElementById('btn-toggle-select-all-categories');
        if (globalBtn) globalBtn.textContent = 'Select All';
        updateBatchActionBar();
    }

    function updateBatchActionBar() {
        const bar = document.getElementById('batch-action-bar');
        const countEl = document.getElementById('batch-selected-count');
        if (!bar) return;

        const count = selectedDocIds.size;
        if (count > 0) {
            bar.classList.remove('hidden');
            bar.classList.add('flex');
            if (countEl) {
                countEl.textContent = `${count} ${count === 1 ? 'document' : 'documents'} selected`;
            }
        } else {
            bar.classList.add('hidden');
            bar.classList.remove('flex');
            if (countEl) {
                countEl.textContent = '0 selected';
            }
        }
    }

    function getBatchAreaFromHash() {
        if (typeof window !== 'undefined' && window.location && window.location.hash) {
            const match = window.location.hash.match(/#\/area\/([^/]+)/);
            if (match) return decodeURIComponent(match[1]).replace(/^area_/, '');
        }
        return '';
    }

    function getBatchHouseFromHash() {
        if (typeof window !== 'undefined' && window.location && window.location.hash) {
            const match = window.location.hash.match(/house\/([^/]+)/);
            if (match) return decodeURIComponent(match[1]);
        }
        return '';
    }

    function getBatchResolvedArea() {
        if (typeof currentArea !== 'undefined' && currentArea) return currentArea;
        if (typeof window !== 'undefined' && window.currentArea) return window.currentArea;
        return getBatchAreaFromHash();
    }

    function getBatchResolvedHouse() {
        if (typeof currentHouse !== 'undefined' && currentHouse) return currentHouse;
        if (typeof window !== 'undefined' && window.currentHouse) return window.currentHouse;
        return getBatchHouseFromHash();
    }

    function formatBatchTenantLabel(t) {
        if (!t) return '';
        const isActive = t.is_active != null 
            ? Boolean(t.is_active) 
            : (!t.end_date || String(t.end_date).toLowerCase() === 'present' || String(t.end_date).toLowerCase() === 'none' || t.end_date === '');
        let label = t.name || 'Tenant';
        if (isActive) {
            label += ' (المستأجر الحالي)';
        } else if (t.start_date) {
            const startYear = String(t.start_date).substring(0, 4);
            const endYear = (t.end_date && String(t.end_date).length >= 4) ? String(t.end_date).substring(0, 4) : '';
            label += endYear ? ` (${startYear} – ${endYear})` : ` (${startYear})`;
        }
        return label;
    }

    function getBatchSelectedDocsInfo() {
        const activeCats = (typeof currentCategories !== 'undefined' && currentCategories) 
            ? currentCategories 
            : (typeof window !== 'undefined' && window.currentCategories ? window.currentCategories : []);
        
        const tenantIds = new Set();
        const tenantNames = new Set();
        const inMemoryTenants = [];
        const seenTenantKeys = new Set();

        if (Array.isArray(activeCats)) {
            for (const cat of activeCats) {
                const catTenant = cat.tenant || '';
                if (cat.documents && Array.isArray(cat.documents)) {
                    for (const doc of cat.documents) {
                        const tId = doc.tenant_id;
                        const tName = doc.tenant || catTenant;
                        if (tName) {
                            const key = tId != null ? `id_${tId}` : `name_${tName.trim().toLowerCase()}`;
                            if (!seenTenantKeys.has(key)) {
                                seenTenantKeys.add(key);
                                inMemoryTenants.push({ id: tId, name: tName, is_active: false });
                            }
                        }
                        if (selectedDocIds.has(doc.vault_id)) {
                            if (tId != null) tenantIds.add(tId);
                            if (tName) tenantNames.add(tName);
                        }
                    }
                } else if (catTenant) {
                    const key = `name_${catTenant.trim().toLowerCase()}`;
                    if (!seenTenantKeys.has(key)) {
                        seenTenantKeys.add(key);
                        inMemoryTenants.push({ id: null, name: catTenant, is_active: false });
                    }
                }
            }
        }

        const activeTenant = (typeof currentTenant !== 'undefined' && currentTenant)
            ? currentTenant
            : (typeof window !== 'undefined' && window.currentTenant ? window.currentTenant : null);

        const targetTenantId = tenantIds.size > 0 ? Array.from(tenantIds)[0] : null;
        const targetTenantName = tenantNames.size > 0 ? Array.from(tenantNames)[0] : (activeTenant || null);

        return {
            tenantIds: Array.from(tenantIds),
            tenantNames: Array.from(tenantNames),
            singleTenantId: targetTenantId,
            singleTenantName: targetTenantName,
            inMemoryTenants
        };
    }

    function renderTenantOptions(select, tenantsList, info) {
        if (!select) return;
        const prevVal = select.value;
        select.innerHTML = '';

        if (!tenantsList || tenantsList.length === 0) return;

        let matchedOption = null;

        tenantsList.forEach((t) => {
            if (!t || (!t.name && t.id == null)) return;
            const opt = document.createElement('option');
            opt.value = t.id != null ? String(t.id) : '';
            opt.textContent = formatBatchTenantLabel(t);
            
            if (!matchedOption) {
                if (info.singleTenantId != null && t.id != null && String(t.id) === String(info.singleTenantId)) {
                    matchedOption = opt;
                } else if (info.singleTenantName && t.name && t.name.trim().toLowerCase() === info.singleTenantName.trim().toLowerCase()) {
                    matchedOption = opt;
                }
            }
            select.appendChild(opt);
        });

        if (prevVal && Array.from(select.options).some(o => o.value === prevVal)) {
            select.value = prevVal;
        } else if (matchedOption) {
            matchedOption.selected = true;
        } else if (select.options.length > 0) {
            select.options[0].selected = true;
        }
    }

    async function populateBatchTenantSelect(selectId) {
        const select = document.getElementById(selectId);
        if (!select) return;

        const info = getBatchSelectedDocsInfo();
        renderTenantOptions(select, info.inMemoryTenants, info);

        const activeArea = getBatchResolvedArea();
        const activeHouse = getBatchResolvedHouse();
        const isStatic = (typeof isStaticMode !== 'undefined' && isStaticMode) || (typeof window !== 'undefined' && window.isStaticMode);

        if (isStatic || !activeArea || !activeHouse) {
            return;
        }

        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(activeArea)}/houses/${encodeURIComponent(activeHouse)}/tenants`);
            if (!res.ok) return;
            const dbTenants = await res.json();
            if (Array.isArray(dbTenants) && dbTenants.length > 0) {
                const seenKeys = new Set();
                const combinedTenants = [];
                dbTenants.forEach(t => {
                    const k = t.id != null ? `id_${t.id}` : `name_${(t.name || '').trim().toLowerCase()}`;
                    seenKeys.add(k);
                    combinedTenants.push(t);
                });
                info.inMemoryTenants.forEach(t => {
                    const k = t.id != null ? `id_${t.id}` : `name_${(t.name || '').trim().toLowerCase()}`;
                    if (!seenKeys.has(k)) {
                        seenKeys.add(k);
                        combinedTenants.push(t);
                    }
                });
                renderTenantOptions(select, combinedTenants, info);
            }
        } catch (err) {
            // Silently fallback to in-memory category tenants
        }
    }

    function openBatchMoveModal() {
        if (selectedDocIds.size === 0) return;
        const modal = document.getElementById('batch-move-modal');
        const select = document.getElementById('batch-move-folder-select');
        const subtitle = document.getElementById('batch-move-subtitle');
        const customContainer = document.getElementById('batch-move-custom-folder-container');
        const customInput = document.getElementById('batch-move-custom-folder-input');

        if (!modal || !select) return;

        populateBatchTenantSelect('batch-move-tenant-select');

        if (subtitle) {
            subtitle.textContent = `Move ${selectedDocIds.size} ${selectedDocIds.size === 1 ? 'document' : 'documents'} to a target category folder.`;
        }

        if (customContainer) customContainer.classList.add('hidden');
        if (customInput) customInput.value = '';

        select.innerHTML = '';
        const stdOptGroup = document.createElement('optgroup');
        stdOptGroup.label = 'Standard Folders';
        for (const [folderName, prefix] of Object.entries(FOLDER_PREFIXES)) {
            const opt = document.createElement('option');
            const formatted = `${prefix} - ${folderName}`;
            opt.value = formatted;
            opt.textContent = formatted;
            stdOptGroup.appendChild(opt);
        }
        select.appendChild(stdOptGroup);

        const customFolders = new Set();
        const activeCats = (typeof currentCategories !== 'undefined' ? currentCategories : (typeof window !== 'undefined' ? window.currentCategories : [])) || [];
        if (Array.isArray(activeCats)) {
            activeCats.forEach(c => {
                if (c && c.name && !isStandardCategoryName(c.name)) {
                    customFolders.add(c.name);
                }
            });
        }
        if (customFolders.size > 0) {
            const custGroup = document.createElement('optgroup');
            custGroup.label = 'Custom Folders';
            Array.from(customFolders).sort().forEach(cf => {
                const opt = document.createElement('option');
                opt.value = cf;
                opt.textContent = cf;
                custGroup.appendChild(opt);
            });
            select.appendChild(custGroup);
        }

        const newOpt = document.createElement('option');
        newOpt.value = '__custom__';
        newOpt.textContent = '+ Create New Folder...';
        select.appendChild(newOpt);

        select.onchange = () => {
            if (select.value === '__custom__') {
                if (customContainer) customContainer.classList.remove('hidden');
                if (customInput) customInput.focus();
            } else {
                if (customContainer) customContainer.classList.add('hidden');
            }
        };

        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    function closeBatchMoveModal() {
        const modal = document.getElementById('batch-move-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    async function handleBatchMoveSubmit() {
        if (selectedDocIds.size === 0) return;
        const select = document.getElementById('batch-move-folder-select');
        const customInput = document.getElementById('batch-move-custom-folder-input');
        const confirmBtn = document.getElementById('btn-batch-move-confirm');
        const spinner = document.getElementById('batch-move-spinner');

        let targetCat = select ? select.value : '';
        if (targetCat === '__custom__') {
            targetCat = customInput ? customInput.value.trim() : '';
        }
        if (!targetCat) {
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('Please select or specify a target category folder.', 'error');
            return;
        }

        const activeArea = getBatchResolvedArea();
        const activeHouse = getBatchResolvedHouse();

        if (confirmBtn) confirmBtn.disabled = true;
        if (spinner) spinner.classList.remove('hidden');

        try {
            const tenantSelect = document.getElementById('batch-move-tenant-select');
            const targetTenantVal = tenantSelect ? tenantSelect.value : '';

            const movePayload = {
                vault_ids: Array.from(selectedDocIds),
                target_category: targetCat
            };
            if (targetTenantVal) {
                const parsedId = parseInt(targetTenantVal, 10);
                if (!isNaN(parsedId)) {
                    movePayload.target_tenant_id = parsedId;
                }
            }

            const res = await fetch(`/api/areas/${encodeURIComponent(activeArea)}/houses/${encodeURIComponent(activeHouse)}/documents/batch-move`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(movePayload)
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || err.error || 'Failed to move documents');
            }

            const data = await res.json();
            closeBatchMoveModal();
            const movedCount = (typeof data.moved_count === 'number') ? data.moved_count : selectedDocIds.size;
            deselectAllDocs();

            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast(`Successfully moved ${movedCount} documents to "${data.target_category || targetCat}"`, 'success');

            if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                await window.refreshCurrentTab(activeArea, activeHouse);
            }
        } catch (err) {
            console.error(err);
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast(err.message || 'Error moving documents', 'error');
        } finally {
            if (confirmBtn) confirmBtn.disabled = false;
            if (spinner) spinner.classList.add('hidden');
        }
    }

    function openBatchCopyModal() {
        if (selectedDocIds.size === 0) return;
        const modal = document.getElementById('batch-copy-modal');
        const select = document.getElementById('batch-copy-folder-select');
        const subtitle = document.getElementById('batch-copy-subtitle');
        const customContainer = document.getElementById('batch-copy-custom-folder-container');
        const customInput = document.getElementById('batch-copy-custom-folder-input');

        if (!modal || !select) return;

        populateBatchTenantSelect('batch-copy-tenant-select');

        if (subtitle) {
            subtitle.textContent = `Copy ${selectedDocIds.size} ${selectedDocIds.size === 1 ? 'document' : 'documents'} to a target category folder.`;
        }

        if (customContainer) customContainer.classList.add('hidden');
        if (customInput) customInput.value = '';

        select.innerHTML = '';
        const stdOptGroup = document.createElement('optgroup');
        stdOptGroup.label = 'Standard Folders';
        for (const [folderName, prefix] of Object.entries(FOLDER_PREFIXES)) {
            const opt = document.createElement('option');
            const formatted = `${prefix} - ${folderName}`;
            opt.value = formatted;
            opt.textContent = formatted;
            stdOptGroup.appendChild(opt);
        }
        select.appendChild(stdOptGroup);

        const customFolders = new Set();
        const activeCats = (typeof currentCategories !== 'undefined' ? currentCategories : (typeof window !== 'undefined' ? window.currentCategories : [])) || [];
        if (Array.isArray(activeCats)) {
            activeCats.forEach(c => {
                if (c && c.name && !isStandardCategoryName(c.name)) {
                    customFolders.add(c.name);
                }
            });
        }
        if (customFolders.size > 0) {
            const custGroup = document.createElement('optgroup');
            custGroup.label = 'Custom Folders';
            Array.from(customFolders).sort().forEach(cf => {
                const opt = document.createElement('option');
                opt.value = cf;
                opt.textContent = cf;
                custGroup.appendChild(opt);
            });
            select.appendChild(custGroup);
        }

        const newOpt = document.createElement('option');
        newOpt.value = '__custom__';
        newOpt.textContent = '+ Create New Folder...';
        select.appendChild(newOpt);

        select.onchange = () => {
            if (select.value === '__custom__') {
                if (customContainer) customContainer.classList.remove('hidden');
                if (customInput) customInput.focus();
            } else {
                if (customContainer) customContainer.classList.add('hidden');
            }
        };

        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    function closeBatchCopyModal() {
        const modal = document.getElementById('batch-copy-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    async function handleBatchCopySubmit() {
        if (selectedDocIds.size === 0) return;
        const select = document.getElementById('batch-copy-folder-select');
        const customInput = document.getElementById('batch-copy-custom-folder-input');
        const confirmBtn = document.getElementById('btn-batch-copy-confirm');
        const spinner = document.getElementById('batch-copy-spinner');

        let targetCat = select ? select.value : '';
        if (targetCat === '__custom__') {
            targetCat = customInput ? customInput.value.trim() : '';
        }
        if (!targetCat) {
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('Please select or specify a target category folder.', 'error');
            return;
        }

        const activeArea = getBatchResolvedArea();
        const activeHouse = getBatchResolvedHouse();

        if (confirmBtn) confirmBtn.disabled = true;
        if (spinner) spinner.classList.remove('hidden');

        try {
            const tenantSelect = document.getElementById('batch-copy-tenant-select');
            const targetTenantVal = tenantSelect ? tenantSelect.value : '';

            const copyPayload = {
                vault_ids: Array.from(selectedDocIds),
                target_category: targetCat
            };
            if (targetTenantVal) {
                const parsedId = parseInt(targetTenantVal, 10);
                if (!isNaN(parsedId)) {
                    copyPayload.target_tenant_id = parsedId;
                }
            }

            const res = await fetch(`/api/areas/${encodeURIComponent(activeArea)}/houses/${encodeURIComponent(activeHouse)}/documents/batch-copy`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(copyPayload)
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || err.error || 'Failed to copy documents');
            }

            const data = await res.json();
            closeBatchCopyModal();
            deselectAllDocs();

            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('تم نسخ الوثائق المحددة بنجاح', 'success');

            if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                await window.refreshCurrentTab(activeArea, activeHouse);
            }
        } catch (err) {
            console.error(err);
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast(err.message || 'Error copying documents', 'error');
        } finally {
            if (confirmBtn) confirmBtn.disabled = false;
            if (spinner) spinner.classList.add('hidden');
        }
    }

    function openBatchMoveForDoc(doc) {
        if (!doc || !doc.vault_id) return;
        selectedDocIds.clear();
        selectedDocIds.add(doc.vault_id);
        updateBatchActionBar();
        if (typeof document !== 'undefined') {
            document.querySelectorAll('.doc-select-checkbox').forEach(cb => {
                cb.checked = (cb.dataset.vaultId === doc.vault_id);
            });
        }
        openBatchMoveModal();
    }

    function openBatchCopyForDoc(doc) {
        if (!doc || !doc.vault_id) return;
        selectedDocIds.clear();
        selectedDocIds.add(doc.vault_id);
        updateBatchActionBar();
        if (typeof document !== 'undefined') {
            document.querySelectorAll('.doc-select-checkbox').forEach(cb => {
                cb.checked = (cb.dataset.vaultId === doc.vault_id);
            });
        }
        openBatchCopyModal();
    }

    function openBatchDeleteModal() {
        if (selectedDocIds.size === 0) return;
        const modal = document.getElementById('batch-delete-modal');
        const msg = document.getElementById('batch-delete-message');
        const subtitle = document.getElementById('batch-delete-subtitle');
        if (!modal) return;

        const count = selectedDocIds.size;
        if (subtitle) {
            subtitle.textContent = `${count} ${count === 1 ? 'document' : 'documents'} selected for deletion.`;
        }
        if (msg) {
            msg.textContent = `Are you sure you want to permanently delete the ${count} selected ${count === 1 ? 'document' : 'documents'}? All associated files and database records will be removed.`;
        }

        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    function closeBatchDeleteModal() {
        const modal = document.getElementById('batch-delete-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    async function handleBatchDeleteSubmit() {
        if (selectedDocIds.size === 0) return;
        const confirmBtn = document.getElementById('btn-batch-delete-confirm');
        const spinner = document.getElementById('batch-delete-spinner');

        const activeArea = getBatchResolvedArea();
        const activeHouse = getBatchResolvedHouse();

        if (confirmBtn) confirmBtn.disabled = true;
        if (spinner) spinner.classList.remove('hidden');

        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(activeArea)}/houses/${encodeURIComponent(activeHouse)}/documents/batch-delete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vault_ids: Array.from(selectedDocIds)
                })
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || err.error || 'Failed to delete documents');
            }

            const data = await res.json();
            closeBatchDeleteModal();
            const delCount = (typeof data.deleted_count === 'number') ? data.deleted_count : selectedDocIds.size;
            deselectAllDocs();

            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast(`Successfully deleted ${delCount} documents`, 'success');

            if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                await window.refreshCurrentTab(activeArea, activeHouse);
            }
        } catch (err) {
            console.error(err);
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast(err.message || 'Error deleting documents', 'error');
        } finally {
            if (confirmBtn) confirmBtn.disabled = false;
            if (spinner) spinner.classList.add('hidden');
        }
    }

    function initBatchOperations() {
        const btnMove = document.getElementById('btn-batch-move');
        if (btnMove) btnMove.onclick = openBatchMoveModal;

        const btnCopy = document.getElementById('btn-batch-copy');
        if (btnCopy) btnCopy.onclick = openBatchCopyModal;

        const btnDelete = document.getElementById('btn-batch-delete');
        if (btnDelete) btnDelete.onclick = openBatchDeleteModal;

        const btnDeselect = document.getElementById('btn-batch-deselect');
        if (btnDeselect) btnDeselect.onclick = deselectAllDocs;

        const btnMoveCancel = document.getElementById('btn-batch-move-cancel');
        if (btnMoveCancel) btnMoveCancel.onclick = closeBatchMoveModal;

        const btnMoveClose = document.getElementById('batch-move-close');
        if (btnMoveClose) btnMoveClose.onclick = closeBatchMoveModal;

        const btnMoveConfirm = document.getElementById('btn-batch-move-confirm');
        if (btnMoveConfirm) btnMoveConfirm.onclick = handleBatchMoveSubmit;

        const btnCopyCancel = document.getElementById('btn-batch-copy-cancel');
        if (btnCopyCancel) btnCopyCancel.onclick = closeBatchCopyModal;

        const btnCopyClose = document.getElementById('batch-copy-close');
        if (btnCopyClose) btnCopyClose.onclick = closeBatchCopyModal;

        const btnCopyConfirm = document.getElementById('btn-batch-copy-confirm');
        if (btnCopyConfirm) btnCopyConfirm.onclick = handleBatchCopySubmit;

        const btnDeleteCancel = document.getElementById('btn-batch-delete-cancel');
        if (btnDeleteCancel) btnDeleteCancel.onclick = closeBatchDeleteModal;

        const btnDeleteClose = document.getElementById('batch-delete-close');
        if (btnDeleteClose) btnDeleteClose.onclick = closeBatchDeleteModal;

        const btnDeleteConfirm = document.getElementById('btn-batch-delete-confirm');
        if (btnDeleteConfirm) btnDeleteConfirm.onclick = handleBatchDeleteSubmit;
    }

    async function loadCategories(areaId, houseId) {
        deselectAllDocs();
        const docListEl = document.getElementById('document-list');
        const statsBadge = document.getElementById('stats-badge');
        if (!docListEl) return;
        docListEl.innerHTML = '<p class="text-xs text-slate-500 p-3">Loading categories...</p>';
        try {
            const isStatic = (typeof isStaticMode !== 'undefined' && isStaticMode) || (typeof window !== 'undefined' && window.isStaticMode);
            if (isStatic) {
                const stateData = await fetchHouseState(areaId, houseId);
                const groups = getDocumentGroups(stateData);
                const catMap = {};
                
                groups.forEach(g => {
                    const tenant = g.primary_tenant;
                    const catRaw = g.folder_path || g.category;
                    if (tenant && catRaw) {
                        const prefix = FOLDER_PREFIXES[catRaw] || '';
                        const catNumbered = prefix ? `${prefix} - ${catRaw}` : catRaw;
                        const key = `${tenant}:::${catNumbered}`;
                        if (!catMap[key]) {
                            catMap[key] = {
                                tenant: tenant,
                                name: catNumbered,
                                documents: []
                            };
                        }
                        catMap[key].documents.push({
                            vault_id: g.vault_id || '',
                            filename: g.filename || '',
                            start_page: g.start_page || 1,
                            end_page: g.end_page || 1,
                            date: (g.dates && g.dates[0]) ? g.dates[0] : '',
                            tenant: tenant,
                            brief_arabic_title: g.brief_arabic_title || '',
                            is_manual: g.is_manual || 0,
                            notes: g.notes || '',
                            category: catNumbered
                        });
                    }
                });
                
                currentCategories = Object.values(catMap).map(c => ({
                    tenant: c.tenant,
                    name: c.name,
                    document_count: c.documents.length,
                    documents: c.documents
                }));
            } else {
                const res = await fetch(`/api/areas/${encodeURIComponent(areaId)}/houses/${encodeURIComponent(houseId)}/categories`);
                if (!res.ok) throw new Error('Failed to load categories');
                currentCategories = await res.json();
            }
            
            const totalDocs = currentCategories.reduce((sum, cat) => sum + cat.document_count, 0);
            if (statsBadge) {
                statsBadge.textContent = `${currentCategories.length} Categories (${totalDocs} Docs)`;
                statsBadge.classList.remove('hidden');
            }
            
            renderCategories();
        } catch (err) {
            console.error(err);
            docListEl.innerHTML = '<p class="text-xs text-rose-500 p-3">Error loading categories.</p>';
        }
    }

    function handleInlineRename(e, doc, titleEl, currentArea, currentHouse) {
        if (e) {
            if (typeof e.stopPropagation === 'function') e.stopPropagation();
            if (typeof e.preventDefault === 'function') e.preventDefault();
        }

        if (!titleEl || titleEl.querySelector('.inline-rename-input')) {
            return;
        }

        const originalTitle = doc.brief_arabic_title || doc.filename || titleEl.textContent.trim() || 'Document';
        titleEl.classList.remove('truncate');
        titleEl.innerHTML = `<input type="text" class="inline-rename-input px-2 py-0.5 text-xs font-normal border border-slate-300 rounded-md bg-white text-slate-800 focus:outline-hidden focus:border-blue-400 focus:ring-1 focus:ring-blue-400/30 w-full min-w-0" value="${escapeHtml(originalTitle)}" />`;

        const input = titleEl.querySelector('.inline-rename-input');
        if (!input) return;

        input.onclick = (ev) => {
            if (ev && typeof ev.stopPropagation === 'function') ev.stopPropagation();
        };
        input.ondblclick = (ev) => {
            if (ev && typeof ev.stopPropagation === 'function') ev.stopPropagation();
        };
        input.onmousedown = (ev) => {
            if (ev && typeof ev.stopPropagation === 'function') ev.stopPropagation();
        };
        input.ondragstart = (ev) => {
            if (ev) {
                if (typeof ev.stopPropagation === 'function') ev.stopPropagation();
                if (typeof ev.preventDefault === 'function') ev.preventDefault();
            }
        };

        input.focus();
        input.select();

        let committed = false;

        const restoreOriginal = () => {
            titleEl.classList.add('truncate');
            titleEl.textContent = originalTitle;
            titleEl.title = 'Double-click to rename';
        };

        const commitRename = async () => {
            if (committed) return;
            committed = true;

            const newTitle = input.value.trim();
            if (!newTitle || newTitle === originalTitle) {
                restoreOriginal();
                return;
            }

            const area = (doc && doc.area_id)
                || (typeof currentArea !== 'undefined' && currentArea)
                || (typeof window !== 'undefined' && window.currentArea)
                || (typeof window !== 'undefined' && typeof window.getResolvedArea === 'function' ? window.getResolvedArea(doc) : '')
                || (typeof window !== 'undefined' && window.location && window.location.hash ? (window.location.hash.match(/#\/area\/([^/]+)/) ? decodeURIComponent(window.location.hash.match(/#\/area\/([^/]+)/)[1]).replace(/^area_/, '') : '') : '');

            const house = (doc && doc.house_id)
                || (typeof currentHouse !== 'undefined' && currentHouse)
                || (typeof window !== 'undefined' && window.currentHouse)
                || (typeof window !== 'undefined' && typeof window.getResolvedHouse === 'function' ? window.getResolvedHouse(doc) : '')
                || (typeof window !== 'undefined' && window.location && window.location.hash ? (window.location.hash.match(/house\/([^/]+)/) ? decodeURIComponent(window.location.hash.match(/house\/([^/]+)/)[1]) : '') : '');

            try {
                const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(doc.vault_id)}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ arabic_title: newTitle })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Failed to rename document');
                }

                doc.brief_arabic_title = newTitle;
                doc.filename = newTitle;
                titleEl.classList.add('truncate');
                titleEl.textContent = newTitle;
                titleEl.title = 'Double-click to rename';

                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' && window.showToast ? window.showToast : null);
                if (toast) toast('Document renamed successfully.');
            } catch (err) {
                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' && window.showToast ? window.showToast : null);
                if (toast) toast('Failed to rename document: ' + err.message, 'error');
                restoreOriginal();
            }
        };

        input.onkeydown = (ev) => {
            if (ev && typeof ev.stopPropagation === 'function') ev.stopPropagation();
            if (ev.key === 'Enter') {
                if (typeof ev.preventDefault === 'function') ev.preventDefault();
                commitRename();
            } else if (ev.key === 'Escape') {
                if (typeof ev.preventDefault === 'function') ev.preventDefault();
                committed = true;
                restoreOriginal();
            }
        };

        input.onblur = () => {
            commitRename();
        };
    }

    function renderCategories() {
        const docListEl = document.getElementById('document-list');
        if (!docListEl) return;
        docListEl.innerHTML = '';

        const activeTenant = (typeof currentTenant !== 'undefined' ? currentTenant : (typeof window !== 'undefined' ? window.currentTenant : null));
        const activeCategories = (typeof currentCategories !== 'undefined' ? currentCategories : (typeof window !== 'undefined' ? window.currentCategories : [])) || [];
        
        let displayCategories = [];
        
        if (activeTenant) {
            displayCategories = activeCategories.filter(cat => cat.tenant === activeTenant);
        } else {
            const agg = {};
            activeCategories.forEach(cat => {
                if (!agg[cat.name]) {
                    agg[cat.name] = { count: 0, documents: [] };
                }
                agg[cat.name].count += cat.document_count;
                if (cat.documents) {
                    agg[cat.name].documents = agg[cat.name].documents.concat(cat.documents);
                }
            });
            for (const [name, data] of Object.entries(agg)) {
                displayCategories.push({ name: name, document_count: data.count, documents: data.documents });
            }
        }
        
        displayCategories.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
        
        if (displayCategories.length === 0) {
            const emptyP = document.createElement('p');
            emptyP.className = 'text-xs text-slate-400 p-4 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200';
            emptyP.textContent = 'No folders found for this selection.';
            docListEl.appendChild(emptyP);
            return;
        }

        const totalDocsInView = displayCategories.reduce((sum, c) => sum + (c.documents ? c.documents.length : 0), 0);
        if (totalDocsInView > 0) {
            const allDocIds = [];
            displayCategories.forEach(c => {
                if (c.documents) {
                    c.documents.forEach(d => {
                        if (d.vault_id) allDocIds.push(d.vault_id);
                    });
                }
            });
            const allSelected = allDocIds.length > 0 && allDocIds.every(id => selectedDocIds.has(id));
            const topBar = document.createElement('div');
            topBar.className = 'flex items-center justify-between pb-2 px-1 text-xs';
            topBar.innerHTML = `
                <span class="text-[11px] font-medium text-slate-400">Category Folders</span>
                <button id="btn-toggle-select-all-categories" type="button" class="text-[11px] font-semibold text-blue-600 hover:text-blue-800 transition-colors cursor-pointer">
                    ${allSelected ? 'Deselect All' : 'Select All'}
                </button>
            `;
            const toggleAllBtn = topBar.querySelector('#btn-toggle-select-all-categories');
            if (toggleAllBtn) {
                toggleAllBtn.onclick = (e) => {
                    e.stopPropagation();
                    toggleSelectAllGlobal(displayCategories);
                };
            }
            docListEl.appendChild(topBar);
        }
        
        displayCategories.forEach(cat => {
            const card = document.createElement('div');
            card.className = 'p-3 bg-white rounded-xl border border-slate-200 shadow-2xs hover:border-slate-300 transition-all mb-2 cursor-pointer category-folder-card group/card';
            card.setAttribute('data-category-name', cat.name);
            
            card.ondragover = (e) => {
                if (e.dataTransfer && e.dataTransfer.types && Array.from(e.dataTransfer.types).includes('Files') && !window.draggedDoc) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.dataTransfer.dropEffect = 'copy';
                    card.classList.add('ring-2', 'ring-blue-500', 'bg-blue-50/40');
                } else if (typeof window !== 'undefined' && typeof window.handleCategoryDragOver === 'function') {
                    window.handleCategoryDragOver(e, card);
                }
            };

            card.ondragleave = (e) => {
                card.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-50/40');
                if (typeof window !== 'undefined' && typeof window.handleCategoryDragLeave === 'function') {
                    window.handleCategoryDragLeave(e, card);
                }
            };

            card.ondrop = (e) => {
                card.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-50/40');
                if (e.dataTransfer && e.dataTransfer.types && Array.from(e.dataTransfer.types).includes('Files') && !window.draggedDoc) {
                    e.preventDefault();
                    e.stopPropagation();
                    if (typeof window !== 'undefined' && typeof window.resetDragCounter === 'function') {
                        window.resetDragCounter();
                    } else {
                        const overlay = document.getElementById('ingest-dropzone-overlay');
                        if (overlay) overlay.classList.add('hidden');
                    }
                    if (typeof window !== 'undefined' && typeof window.handleDirectCategoryDrop === 'function') {
                        const activeArea = (typeof currentArea !== 'undefined' ? currentArea : window.currentArea) || '';
                        const activeHouse = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse) || '';
                        window.handleDirectCategoryDrop(e.dataTransfer.files, cat.name, activeHouse, activeArea);
                    }
                } else if (typeof window !== 'undefined' && typeof window.handleCategoryDrop === 'function') {
                    window.handleCategoryDrop(e, cat.name, card);
                }
            };

            const isCustomFolder = !isStandardCategoryName(cat.name);
            const deleteFolderBtn = isCustomFolder
                ? `<button type="button" class="btn-delete-folder opacity-0 group-hover/card:opacity-100 p-1 hover:bg-rose-50 rounded text-slate-400 hover:text-rose-600 transition-all text-xs flex-shrink-0" title="Delete Custom Folder" data-category-name="${escapeHtml(cat.name)}">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>`
                : '';

            const hasNotedDoc = Boolean(cat.documents && cat.documents.some(d => d.notes && d.notes.trim()));
            const noteFolderBadge = hasNotedDoc 
                ? '<span class="bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full text-[10px] font-bold border border-amber-300/80 flex-shrink-0" title="Contains documents with notes">📝 Notes</span>'
                : '';
            const docsContainerClasses = hasNotedDoc 
                ? 'category-docs mt-2.5 pt-2.5 border-t border-slate-100 space-y-1'
                : 'category-docs hidden mt-2.5 pt-2.5 border-t border-slate-100 space-y-1';

            const folderDocIds = (cat.documents || []).map(d => d.vault_id).filter(Boolean);
            const allFolderDocsSelected = folderDocIds.length > 0 && folderDocIds.every(id => selectedDocIds.has(id));
            const someFolderDocsSelected = folderDocIds.length > 0 && !allFolderDocsSelected && folderDocIds.some(id => selectedDocIds.has(id));
            const hasDocs = Boolean(cat.documents && cat.documents.length > 0);

            const folderSelectCheckbox = hasDocs
                ? `<input type="checkbox" class="folder-select-checkbox w-3.5 h-3.5 rounded text-blue-600 focus:ring-blue-500 border-slate-300 cursor-pointer flex-shrink-0" data-folder-category="${escapeHtml(cat.name)}" title="Select / Deselect all in this folder" ${allFolderDocsSelected ? 'checked' : ''} />`
                : `<span class="w-3.5 h-3.5 flex-shrink-0"></span>`;

            const folderIconSvg = getFolderIconSvg(cat.name);

            card.innerHTML = `
                <div class="flex justify-between items-center">
                    <div class="flex items-center gap-2 min-w-0">
                        ${folderSelectCheckbox}
                        <div class="folder-icon-box w-6 h-6 rounded-lg bg-blue-50 text-blue-600 border border-blue-100 flex items-center justify-center flex-shrink-0" data-category="${escapeHtml(cat.name)}">
                            ${folderIconSvg}
                        </div>
                        <h4 class="text-xs font-semibold text-slate-800 truncate">${escapeHtml(cat.name)}</h4>
                    </div>
                    <div class="flex items-center gap-1.5 flex-shrink-0">
                        ${noteFolderBadge}
                        <span class="doc-count-badge min-w-[20px] h-5 px-1 rounded-full bg-slate-100 text-slate-600 text-[10px] font-bold border border-slate-200 flex items-center justify-center flex-shrink-0 select-none" title="${cat.document_count} ${cat.document_count === 1 ? 'Document' : 'Documents'}">${cat.document_count}</span>
                        ${deleteFolderBtn}
                    </div>
                </div>
                <div class="${docsContainerClasses}">
                </div>
            `;

            const folderCheckboxEl = card.querySelector('.folder-select-checkbox');
            if (folderCheckboxEl) {
                if (someFolderDocsSelected) {
                    folderCheckboxEl.indeterminate = true;
                }
                folderCheckboxEl.onclick = (e) => {
                    e.stopPropagation();
                    toggleSelectAllInFolder(cat, card);
                };
            }
            
            if (cat.documents && cat.documents.length > 0) {
                const docsContainer = card.querySelector('.category-docs');
                cat.documents.forEach(doc => {
                    const docEl = document.createElement('div');
                    const hasNotes = Boolean(doc.notes && doc.notes.trim());
                    const snippet = hasNotes ? getNoteSnippet(doc.notes) : '';
                    const noteBadge = hasNotes 
                        ? `<span class="doc-note-badge inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded font-medium bg-amber-100 text-amber-800 border border-amber-300/60 flex-shrink-0" title="${escapeHtml(doc.notes)}">📝 ${escapeHtml(snippet)}</span>` 
                        : '';

                    const highlightClasses = hasNotes
                        ? 'bg-amber-50/80 border-l-4 border-l-amber-400 border border-amber-200/80 text-amber-900 hover:bg-amber-100/70 hover:border-amber-300 shadow-2xs'
                        : 'text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50';

                    docEl.className = `${highlightClasses} px-2.5 py-1.5 rounded-lg cursor-pointer transition-all flex items-center justify-between gap-2 font-medium group/doc`;
                    docEl.draggable = true;
                    docEl.setAttribute('data-vault-id', doc.vault_id);
                    if (typeof window !== 'undefined' && typeof window.handleDocDragStart === 'function') {
                        docEl.ondragstart = (e) => window.handleDocDragStart(e, doc, cat.name);
                        docEl.ondragend = (e) => window.handleDocDragEnd(e);
                    }

                    const title = doc.brief_arabic_title || doc.filename || 'Document';
                    const isManual = Boolean(doc.is_manual);
                    const lockIcon = isManual ? '<span title="Manually assigned - protected from auto-reallocation" class="text-[10px] text-amber-600 flex-shrink-0">🔒</span>' : '';
                    const isChecked = selectedDocIds.has(doc.vault_id);
                    const rawDate = doc.date || (doc.dates && doc.dates[0]) || doc.primary_date || '';
                    const docDate = (rawDate && rawDate !== 'NONE' && rawDate !== 'null') ? rawDate : 'No Date';

                    docEl.innerHTML = `
                        <div class="flex items-center gap-2 min-w-0 flex-1">
                            <input type="checkbox" class="doc-select-checkbox w-3.5 h-3.5 rounded text-blue-600 focus:ring-blue-500 border-slate-300 cursor-pointer flex-shrink-0" data-vault-id="${escapeHtml(doc.vault_id)}" ${isChecked ? 'checked' : ''} />
                            <span class="doc-icon-preview p-0.5 rounded text-blue-500 hover:text-blue-700 hover:bg-blue-100 cursor-pointer flex-shrink-0 transition-colors" title="Document Details & Notes (Spacebar)">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                            </span>
                            <span class="truncate flex-1 min-w-0 ${hasNotes ? 'text-amber-950 font-semibold' : 'text-slate-800'} doc-title-text cursor-text" title="Double-click to rename">${escapeHtml(title)}</span>
                            ${lockIcon}
                            ${noteBadge}
                        </div>
                        <div class="flex items-center gap-1 flex-shrink-0">
                            <span class="doc-date-badge text-[9px] font-mono tracking-tight text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200/70 flex-shrink-0 select-none" title="Document Date: ${escapeHtml(docDate)}">${escapeHtml(docDate)}</span>
                            <button type="button" class="doc-menu-btn opacity-0 group-hover/doc:opacity-100 p-1 hover:bg-blue-100 rounded text-slate-400 hover:text-slate-700 transition-opacity" data-vault-id="${escapeHtml(doc.vault_id)}" title="Manage Document">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/></svg>
                            </button>
                        </div>
                    `;

                    const checkbox = docEl.querySelector('.doc-select-checkbox');
                    if (checkbox) {
                        checkbox.onclick = (e) => {
                            e.stopPropagation();
                        };
                        checkbox.onchange = (e) => {
                            e.stopPropagation();
                            toggleDocSelection(doc.vault_id, checkbox.checked);
                            updateFolderCheckboxState(card, cat);
                        };
                    }

                    const previewIcon = docEl.querySelector('.doc-icon-preview');
                    const menuBtn = docEl.querySelector('.doc-menu-btn');
                    const titleSpan = docEl.querySelector('.doc-title-text');

                    if (titleSpan) {
                        titleSpan.ondblclick = (e) => {
                            handleInlineRename(e, doc, titleSpan, (typeof currentArea !== 'undefined' ? currentArea : (typeof window !== 'undefined' ? window.currentArea : '')), (typeof currentHouse !== 'undefined' ? currentHouse : (typeof window !== 'undefined' ? window.currentHouse : '')));
                        };
                    }

                    if (!doc.category) {
                        doc.category = cat.name;
                    }

                    // Zero-click Live Peek in the right panel on hover (250ms debounce)
                    if (typeof window !== 'undefined' && typeof window.attachPreview === 'function') {
                        window.attachPreview(docEl, doc.vault_id, title, doc);
                    }

                    // Info icon on left before name: opens Document Inspector & Notes modal
                    if (previewIcon) {
                        previewIcon.onclick = (e) => {
                            e.stopPropagation();
                            if (typeof window !== 'undefined' && typeof window.setSelectedDoc === 'function') {
                                window.setSelectedDoc(doc, title, docEl);
                            }
                            if (typeof window !== 'undefined' && typeof window.openDocInspector === 'function') {
                                window.openDocInspector(doc.vault_id, title, doc);
                            } else if (typeof window !== 'undefined' && typeof window.openQuickLook === 'function') {
                                window.openQuickLook(doc.vault_id, title, doc);
                            }
                        };
                    }

                    // 3-dot Menu: hover immediately cancels any pending peek so action menu is 100% free
                    if (menuBtn) {
                        menuBtn.onmouseenter = () => {
                            if (typeof window !== 'undefined' && typeof window.cancelPeek === 'function') {
                                window.cancelPeek();
                            }
                        };
                        menuBtn.onclick = (e) => {
                            e.stopPropagation();
                            if (typeof window !== 'undefined' && typeof window.cancelPeek === 'function') {
                                window.cancelPeek();
                            }
                            if (typeof window !== 'undefined' && typeof window.openDocDropdownMenu === 'function') {
                                window.openDocDropdownMenu(e, doc, cat.name, menuBtn);
                            } else if (typeof window !== 'undefined' && typeof window.openDocModal === 'function') {
                                window.openDocModal(doc, cat.name);
                            }
                        };
                    }

                    docEl.onclick = (e) => {
                        e.stopPropagation();
                        const currentTitle = doc.brief_arabic_title || doc.filename || title;
                        if (typeof window !== 'undefined' && typeof window.setSelectedDoc === 'function') {
                            window.setSelectedDoc(doc, currentTitle, docEl);
                        }
                        if (typeof openDocument === 'function') {
                            openDocument(doc.vault_id, currentTitle, doc.category || cat.name);
                        } else if (typeof window !== 'undefined' && typeof window.openDocument === 'function') {
                            window.openDocument(doc.vault_id, currentTitle, doc.category || cat.name);
                        }
                    };
                    docsContainer.appendChild(docEl);
                });
            }

            const selectAllBtn = card.querySelector('.btn-select-all-folder');
            if (selectAllBtn) {
                selectAllBtn.onclick = (e) => {
                    e.stopPropagation();
                    toggleSelectAllInFolder(cat, card);
                };
            }
            
            const deleteBtn = card.querySelector('.btn-delete-folder');
            if (deleteBtn) {
                deleteBtn.onclick = async (e) => {
                    e.stopPropagation();
                    const catName = cat.name;
                    if (!window.confirm(`Are you sure you want to delete custom folder "${catName}"?\nAny documents in it will be moved to "13 - رسائل متنوعة".`)) {
                        return;
                    }
                    try {
                        const activeArea = (typeof currentArea !== 'undefined' ? currentArea : window.currentArea) || '';
                        const activeHouse = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse) || '';
                        const res = await fetch(`/api/areas/${encodeURIComponent(activeArea)}/houses/${encodeURIComponent(activeHouse)}/categories/${encodeURIComponent(catName)}`, {
                            method: 'DELETE'
                        });
                        if (!res.ok) {
                            const err = await res.json().catch(() => ({}));
                            throw new Error(err.detail || 'Failed to delete folder');
                        }
                        const toast = (typeof showToast === 'function') ? showToast : (window.showToast || null);
                        if (toast) toast(`Folder "${catName}" deleted successfully.`);
                        if (typeof window.refreshCurrentTab === 'function') {
                            await window.refreshCurrentTab(activeArea, activeHouse);
                        }
                    } catch (err) {
                        const toast = (typeof showToast === 'function') ? showToast : (window.showToast || null);
                        if (toast) toast(err.message, 'error');
                    }
                };
            }

            card.onclick = () => {
                const docsContainer = card.querySelector('.category-docs');
                if (docsContainer) {
                    docsContainer.classList.toggle('hidden');
                }
            };
            docListEl.appendChild(card);
        });
    }

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initBatchOperations);
        } else {
            initBatchOperations();
        }
    }

    if (typeof window !== 'undefined') {
        window.loadCategories = loadCategories;
        window.renderCategories = renderCategories;
        window.FOLDER_PREFIXES = FOLDER_PREFIXES;
        window.FOLDER_ICONS = FOLDER_ICONS;
        window.EMPTY_FOLDER_SVG = EMPTY_FOLDER_SVG;
        window.getFolderIconSvg = getFolderIconSvg;
        window.selectedDocIds = selectedDocIds;
        window.getSelectedDocIds = getSelectedDocIds;
        window.toggleDocSelection = toggleDocSelection;
        window.toggleSelectAllInFolder = toggleSelectAllInFolder;
        window.updateFolderCheckboxState = updateFolderCheckboxState;
        window.toggleSelectAllGlobal = toggleSelectAllGlobal;
        window.deselectAllDocs = deselectAllDocs;
        window.updateBatchActionBar = updateBatchActionBar;
        window.populateBatchTenantSelect = populateBatchTenantSelect;
        window.openBatchMoveModal = openBatchMoveModal;
        window.closeBatchMoveModal = closeBatchMoveModal;
        window.handleBatchMoveSubmit = handleBatchMoveSubmit;
        window.openBatchCopyModal = openBatchCopyModal;
        window.closeBatchCopyModal = closeBatchCopyModal;
        window.handleBatchCopySubmit = handleBatchCopySubmit;
        window.openBatchDeleteModal = openBatchDeleteModal;
        window.closeBatchDeleteModal = closeBatchDeleteModal;
        window.handleBatchDeleteSubmit = handleBatchDeleteSubmit;
        window.initBatchOperations = initBatchOperations;
        window.openBatchMoveForDoc = openBatchMoveForDoc;
        window.openBatchCopyForDoc = openBatchCopyForDoc;
        window.handleInlineRename = handleInlineRename;
        window.getBatchResolvedArea = getBatchResolvedArea;
        window.getBatchResolvedHouse = getBatchResolvedHouse;
        window.formatBatchTenantLabel = formatBatchTenantLabel;
        window.getBatchSelectedDocsInfo = getBatchSelectedDocsInfo;
    }

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            loadCategories,
            renderCategories,
            handleInlineRename,
            openBatchMoveForDoc,
            openBatchCopyForDoc,
            FOLDER_PREFIXES,
            FOLDER_ICONS,
            EMPTY_FOLDER_SVG,
            getFolderIconSvg,
            selectedDocIds,
            getSelectedDocIds,
            toggleDocSelection,
            toggleSelectAllInFolder,
            updateFolderCheckboxState,
            toggleSelectAllGlobal,
            deselectAllDocs,
            updateBatchActionBar,
            populateBatchTenantSelect,
            getBatchResolvedArea,
            getBatchResolvedHouse,
            formatBatchTenantLabel,
            getBatchSelectedDocsInfo,
            openBatchMoveModal,
            closeBatchMoveModal,
            handleBatchMoveSubmit,
            openBatchCopyModal,
            closeBatchCopyModal,
            handleBatchCopySubmit,
            openBatchDeleteModal,
            closeBatchDeleteModal,
            handleBatchDeleteSubmit,
            initBatchOperations,
            isStandardCategoryName,
        };
    }
})();

